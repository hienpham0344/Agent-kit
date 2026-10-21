#!/usr/bin/env python3
"""
Token Estimator for Agents-kit
Calculates approximate token footprint for prompts, skills, and files.
"""

import sys
import os
from pathlib import Path

def estimate_tokens(text: str) -> dict:
    chars = len(text)
    words = len(text.split())
    # Standard rule of thumb: ~4 characters per token for English/Code
    tokens = max(1, chars // 4)
    lines = text.count('\n') + 1

    return {
        "characters": chars,
        "words": words,
        "lines": lines,
        "estimated_tokens": tokens,
        "context_pct_128k": round((tokens / 128000) * 100, 2),
        "context_pct_200k": round((tokens / 200000) * 100, 2),
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 token_estimator.py <file_or_string>")
        sys.exit(1)

    target = sys.argv[1]
    path = Path(target)
    if path.is_file():
        content = path.read_text(encoding="utf-8", errors="ignore")
        name = path.name
    else:
        content = target
        name = "Inline Text"

    res = estimate_tokens(content)
    print(f"\n📊 TOKEN FOOTPRINT ANALYSIS: {name}")
    print("-" * 50)
    print(f"  • Lines of Text    : {res['lines']}")
    print(f"  • Total Words      : {res['words']:,}")
    print(f"  • Total Characters : {res['characters']:,}")
    print(f"  • Estimated Tokens : ~{res['estimated_tokens']:,}")
    print(f"  • 128k Context Win : {res['context_pct_128k']}%")
    print(f"  • 200k Context Win : {res['context_pct_200k']}%\n")

if __name__ == "__main__":
    main()
