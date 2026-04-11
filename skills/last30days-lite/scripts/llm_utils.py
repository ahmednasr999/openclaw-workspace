#!/usr/bin/env python3
"""
llm_utils.py — Shared LLM access helpers for NASR Research v2.

Prefers the local OpenClaw gateway because it works in this environment without
requiring the user to provision a provider API key. Falls back to direct OpenAI
if OPENAI_API_KEY is set.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional
import urllib.error
import urllib.request

GATEWAY_URL_DEFAULT = "http://127.0.0.1:18789"
GATEWAY_MODEL_DEFAULT = "openclaw/main"

# Map openclaw configured provider/model IDs → gateway-compatible alias names.
# The gateway accepts "openclaw", "openclaw/default", "openclaw/<agentId>"
# but NOT bare provider/model strings like "openai-codex/gpt-5.4".
_GATEWAY_MODEL_ALIAS_MAP = {
    "openai-codex/gpt-5.4": "openclaw/main",
    "openai-codex/gpt-5.4-pro": "openclaw/main",
    "openai-codex/gpt-5.3-codex": "openclaw/main",
    "minimax-portal/MiniMax-M2.7": "openclaw/main",
}


def _map_to_gateway_model(model: str) -> str:
    """Map a provider/model string to the gateway-compatible alias."""
    return _GATEWAY_MODEL_ALIAS_MAP.get(model.strip(), model)


def _load_openclaw_config() -> dict:
    cfg_path = Path.home() / ".openclaw" / "openclaw.json"
    if not cfg_path.exists():
        return {}
    try:
        return json.loads(cfg_path.read_text())
    except Exception:
        return {}


def load_gateway_config() -> tuple[str, str, str]:
    cfg = _load_openclaw_config()
    gateway_url = os.environ.get("OPENCLAW_GATEWAY_URL", "").strip() or GATEWAY_URL_DEFAULT
    gateway_token = os.environ.get("OPENCLAW_GATEWAY_TOKEN", "").strip()
    if not gateway_token:
        gateway_token = (
            cfg.get("gateway", {})
            .get("auth", {})
            .get("token", "")
            .strip()
        )
    configured_primary = (
        cfg.get("agents", {})
        .get("defaults", {})
        .get("model", {})
        .get("primary", "")
        .strip()
    )
    gateway_model = (
        os.environ.get("OPENCLAW_GATEWAY_MODEL", "").strip()
        or configured_primary
        or GATEWAY_MODEL_DEFAULT
    )
    return gateway_url.rstrip("/"), gateway_token, gateway_model


def _openai_chat(api_url: str, headers: dict[str, str], body: dict, timeout: int) -> str:
    req = urllib.request.Request(
        api_url,
        data=json.dumps(body).encode(),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read())
    return payload["choices"][0]["message"]["content"].strip()


def chat_complete(
    messages: list[dict[str, str]],
    *,
    max_tokens: int = 800,
    temperature: float = 0.2,
    timeout: int = 60,
    gateway_model: Optional[str] = None,
    openai_model: str = "gpt-4o",
) -> tuple[str, str]:
    """Return (text, backend_label). Empty text means all model paths failed."""
    gateway_url, gateway_token, default_gateway_model = load_gateway_config()
    if gateway_token:
        body = {
            "model": _map_to_gateway_model(gateway_model or default_gateway_model),
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        try:
            text = _openai_chat(
                f"{gateway_url}/v1/chat/completions",
                {
                    "Authorization": f"Bearer {gateway_token}",
                    "Content-Type": "application/json",
                },
                body,
                timeout,
            )
            if text:
                return text, "openclaw-gateway"
        except Exception:
            pass

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if api_key:
        try:
            text = _openai_chat(
                "https://api.openai.com/v1/chat/completions",
                {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                {
                    "model": openai_model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
                timeout,
            )
            if text:
                return text, "openai-direct"
        except Exception:
            pass

    return "", "fallback"


def extract_json_object(text: str) -> str:
    if not text:
        return ""
    clean = text.strip()
    if clean.startswith("```"):
        clean = clean.strip("`").strip()
        if clean.startswith("json"):
            clean = clean[4:].strip()
    start = clean.find("{")
    end = clean.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return clean
    return clean[start : end + 1]
