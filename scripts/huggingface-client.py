#!/usr/bin/env python3
"""
HuggingFace Inference API Client
=================================
Wraps HuggingFace's free inference API for image generation and text.
Endpoint: https://router.huggingface.co/hf-inference/models/{model}

Verified working models (2026-03-26):
  Image: black-forest-labs/FLUX.1-schnell, stabilityai/stable-diffusion-xl-base-1.0
  Text:  meta-llama/Llama-3.3-70B-Instruct (via router/v1, Groq-routed)

Not available on free tier:
  SD 3.5, Bark TTS, MMS TTS, SpeechT5, NLLB translation, DistilBERT sentiment
"""

import json
import os
import time
import urllib.request
import urllib.error

WORKSPACE = os.path.expanduser("~/.openclaw/workspace")
CONFIG_PATH = f"{WORKSPACE}/config/huggingface.json"
HF_INFERENCE_URL = "https://router.huggingface.co/hf-inference/models"
HF_CHAT_URL = "https://router.huggingface.co/v1/chat/completions"


def _load_token():
    """Load HuggingFace token from config."""
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)["token"]
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        raise RuntimeError(f"HuggingFace token not found at {CONFIG_PATH}")


# ── Image Generation ─────────────────────────────────────────────────────────

def generate_image(prompt, model="black-forest-labs/FLUX.1-schnell",
                   output_path=None, timeout=60, retries=2):
    """Generate an image from a text prompt using HF Inference API.

    Args:
        prompt: Text description of the image to generate
        model: HF model ID (default: FLUX.1-schnell)
        output_path: Where to save the image (default: /tmp/hf-gen-{timestamp}.jpg)
        timeout: Request timeout in seconds
        retries: Number of retry attempts on failure

    Returns:
        dict with keys: success, path, model, size_kb, error
    """
    token = _load_token()
    url = f"{HF_INFERENCE_URL}/{model}"

    if output_path is None:
        output_path = f"/tmp/hf-gen-{int(time.time())}.jpg"

    data = json.dumps({"inputs": prompt}).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                content_type = resp.headers.get("Content-Type", "")
                body = resp.read()

                # Check if response is an image (not JSON error)
                if "image" in content_type or (len(body) > 1000 and body[:4] in [b'\xff\xd8\xff\xe0', b'\x89PNG']):
                    with open(output_path, "wb") as f:
                        f.write(body)
                    size_kb = len(body) // 1024
                    return {
                        "success": True,
                        "path": output_path,
                        "model": model.split("/")[-1],
                        "size_kb": size_kb,
                    }
                else:
                    # JSON response - likely an error or model loading
                    try:
                        error_data = json.loads(body)
                        error_msg = error_data.get("error", str(error_data))
                        if "loading" in error_msg.lower() and attempt < retries:
                            wait = error_data.get("estimated_time", 20)
                            print(f"  ⏳ Model loading, waiting {wait:.0f}s...")
                            time.sleep(min(wait, 30))
                            continue
                        return {"success": False, "error": error_msg}
                    except json.JSONDecodeError:
                        return {"success": False, "error": f"Unexpected response: {body[:200]}"}

        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")[:200]
            if e.code == 503 and attempt < retries:
                # Model loading
                print(f"  ⏳ 503 - model loading, retry {attempt + 1}...")
                time.sleep(15)
                continue
            elif e.code == 429 and attempt < retries:
                print(f"  ⏳ Rate limited, waiting 10s...")
                time.sleep(10)
                continue
            return {"success": False, "error": f"HTTP {e.code}: {error_body}"}
        except Exception as e:
            if attempt < retries:
                time.sleep(5)
                continue
            return {"success": False, "error": str(e)}

    return {"success": False, "error": "Max retries exceeded"}


# ── Text Generation (Chat) ───────────────────────────────────────────────────

def chat(messages, model="meta-llama/Llama-3.3-70B-Instruct",
         max_tokens=500, temperature=0.7, timeout=30):
    """Chat completion via HF router (OpenAI-compatible).

    Args:
        messages: List of {"role": "user/system/assistant", "content": "..."}
        model: Model ID
        max_tokens: Max response tokens
        temperature: Sampling temperature
        timeout: Request timeout

    Returns:
        dict with keys: success, content, model, usage, error
    """
    token = _load_token()
    data = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }).encode("utf-8")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        req = urllib.request.Request(HF_CHAT_URL, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read())
            content = result["choices"][0]["message"]["content"]
            return {
                "success": True,
                "content": content,
                "model": result.get("model", model),
                "usage": result.get("usage", {}),
            }
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")[:300]
        return {"success": False, "error": f"HTTP {e.code}: {error_body}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Available Models ──────────────────────────────────────────────────────────

MODELS = {
    "image": {
        "flux-schnell": "black-forest-labs/FLUX.1-schnell",       # Fast, 1024x1024
        "sdxl": "stabilityai/stable-diffusion-xl-base-1.0",       # Quality, 1024x1024
    },
    "text": {
        "llama-3.3-70b": "meta-llama/Llama-3.3-70B-Instruct",
    },
}


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="HuggingFace Inference Client")
    sub = parser.add_subparsers(dest="command")

    # Image generation
    img = sub.add_parser("image", help="Generate image from text")
    img.add_argument("prompt", help="Text prompt")
    img.add_argument("--model", default="flux-schnell",
                     choices=list(MODELS["image"].keys()))
    img.add_argument("--output", "-o", help="Output path")

    # Chat
    chat_p = sub.add_parser("chat", help="Chat completion")
    chat_p.add_argument("prompt", help="User message")
    chat_p.add_argument("--model", default="llama-3.3-70b",
                        choices=list(MODELS["text"].keys()))
    chat_p.add_argument("--max-tokens", type=int, default=500)

    # Test
    sub.add_parser("test", help="Test all endpoints")

    args = parser.parse_args()

    if args.command == "image":
        model_id = MODELS["image"][args.model]
        print(f"Generating with {args.model} ({model_id})...")
        result = generate_image(args.prompt, model=model_id, output_path=args.output)
        if result["success"]:
            print(f"✅ {result['path']} ({result['size_kb']}KB)")
        else:
            print(f"❌ {result['error']}")

    elif args.command == "chat":
        model_id = MODELS["text"][args.model]
        print(f"Chatting with {args.model}...")
        result = chat([{"role": "user", "content": args.prompt}],
                      model=model_id, max_tokens=args.max_tokens)
        if result["success"]:
            print(result["content"])
        else:
            print(f"❌ {result['error']}")

    elif args.command == "test":
        print("=== HuggingFace Free Tier Test ===\n")

        print("1. FLUX.1-schnell image generation...")
        r = generate_image("Professional dark blue tech abstract, minimalist",
                           model=MODELS["image"]["flux-schnell"])
        print(f"   {'✅' if r['success'] else '❌'} {r.get('path', r.get('error'))}\n")

        print("2. Stable Diffusion XL image generation...")
        r = generate_image("Professional corporate landscape, blue gradient",
                           model=MODELS["image"]["sdxl"])
        print(f"   {'✅' if r['success'] else '❌'} {r.get('path', r.get('error'))}\n")

        print("3. Llama 3.3 70B chat...")
        r = chat([{"role": "user", "content": "Reply with: HuggingFace test passed"}])
        print(f"   {'✅' if r['success'] else '❌'} {r.get('content', r.get('error'))}\n")

        print("Done.")
    else:
        parser.print_help()
