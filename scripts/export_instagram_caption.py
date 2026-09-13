#!/usr/bin/env python3
"""Export the same merged caption used by the Instagram publisher."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from instagram_caption import build_instagram_caption


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("metadata", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    caption = build_instagram_caption(json.loads(args.metadata.read_text(encoding="utf-8")))
    if not caption.strip():
        parser.error("Metadata produced an empty caption")
    if args.output.exists() and args.output.read_text(encoding="utf-8").rstrip("\n") != caption:
        parser.error("Output contains different text; choose a new versioned filename")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(caption + "\n", encoding="utf-8")
    print(f"Wrote {len(caption)} caption characters to {args.output}")


if __name__ == "__main__":
    main()
