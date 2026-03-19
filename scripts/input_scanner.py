#!/usr/bin/env python3
"""Deterministic input scanner for prompt injection detection.

Scans inbound text for known injection patterns before LLM processing.
Returns risk score and flagged patterns. No LLM calls - pure regex/keyword.
"""

import re
import sys

# Injection patterns - deterministic, no LLM needed
PATTERNS = [
    # Direct instruction override
    (r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions|prompts|rules)", "instruction_override", 90),
    (r"disregard\s+(all\s+)?(previous|above|prior)", "instruction_override", 90),
    (r"forget\s+(everything|all|your)\s+(you|instructions|rules)", "instruction_override", 85),
    
    # Role hijacking
    (r"you\s+are\s+now\s+(a|an|the)\s+", "role_hijack", 80),
    (r"act\s+as\s+(a|an|if)\s+", "role_hijack", 60),
    (r"pretend\s+(you|to\s+be)\s+", "role_hijack", 70),
    (r"new\s+system\s+prompt", "role_hijack", 95),
    
    # Data exfiltration
    (r"(show|print|display|reveal|output)\s+(your|the|all)\s+(system|secret|api|token|key|password|prompt)", "data_exfil", 85),
    (r"what\s+(is|are)\s+your\s+(system|secret|api|initial)\s+(prompt|instructions|key)", "data_exfil", 80),
    
    # Encoding tricks
    (r"base64\s*(decode|encode)", "encoding_trick", 50),
    (r"\\x[0-9a-f]{2}", "hex_encoding", 40),
    
    # Jailbreak markers
    (r"DAN\s*mode", "jailbreak", 95),
    (r"developer\s+mode\s*(enabled|on|activated)", "jailbreak", 95),
    (r"bypass\s+(safety|filter|content|restriction)", "jailbreak", 90),
    
    # Wallet draining (loop induction)
    (r"(repeat|loop|iterate)\s+(this|the\s+above)\s+(\d{2,}|forever|indefinitely)", "loop_attack", 85),
    (r"call\s+(this|the)\s+(function|tool|api)\s+(\d{3,}|unlimited)\s+times", "loop_attack", 90),
]

# PII patterns for outbound scanning
PII_PATTERNS = [
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "email"),
    (r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "phone"),
    (r"\b\d{3}-\d{2}-\d{4}\b", "ssn"),
    (r"\b(?:sk-|ak_|xoxb-|ntn_|ghp_|gho_)[A-Za-z0-9_-]{20,}\b", "api_key"),
    (r"\b[A-Za-z0-9+/]{40,}={0,2}\b", "possible_token"),
]


def scan_input(text):
    """Scan text for injection patterns. Returns (risk_score, flags)."""
    if not text:
        return 0, []
    
    text_lower = text.lower()
    flags = []
    max_score = 0
    
    for pattern, category, score in PATTERNS:
        if re.search(pattern, text_lower):
            flags.append({"pattern": category, "score": score})
            max_score = max(max_score, score)
    
    return max_score, flags


def scan_outbound(text):
    """Scan outbound text for PII leaks. Returns list of detected PII types."""
    if not text:
        return []
    
    detected = []
    for pattern, pii_type in PII_PATTERNS:
        matches = re.findall(pattern, text)
        if matches:
            detected.append({"type": pii_type, "count": len(matches)})
    
    return detected


def scan_for_loops(text):
    """Detect potential wallet-draining loop instructions."""
    indicators = 0
    
    if re.search(r"(for each|for every|iterate over)\s+.{0,50}(call|execute|run|send)", text.lower()):
        indicators += 1
    if re.search(r"\b(1000|10000|unlimited|infinite|all)\s+(times|iterations|requests)", text.lower()):
        indicators += 1
    if re.search(r"(don't stop|never stop|keep going|continue until)", text.lower()):
        indicators += 1
    
    return indicators >= 2


if __name__ == "__main__":
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
    else:
        text = sys.stdin.read()
    
    score, flags = scan_input(text)
    pii = scan_outbound(text)
    loop_risk = scan_for_loops(text)
    
    if score >= 70:
        print(f"🚨 HIGH RISK ({score}/100): {[f['pattern'] for f in flags]}")
    elif score >= 40:
        print(f"⚠️ MEDIUM RISK ({score}/100): {[f['pattern'] for f in flags]}")
    elif flags:
        print(f"ℹ️ LOW RISK ({score}/100): {[f['pattern'] for f in flags]}")
    else:
        print("✅ CLEAN")
    
    if pii:
        print(f"📋 PII detected: {pii}")
    
    if loop_risk:
        print("🔄 LOOP RISK: Potential wallet-draining pattern detected")
