import argparse
import json
import re
import sys
from collections import Counter


def positive_int(value):
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer >= 1") from exc
    if number < 1:
        raise argparse.ArgumentTypeError("must be an integer >= 1")
    return number


def main():
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    sys.stderr.reconfigure(encoding="utf-8", newline="\n")
    parser = argparse.ArgumentParser(prog="wordstat")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--top", type=positive_int, default=3)
    parser.add_argument("FILE")
    args = parser.parse_args()

    try:
        with open(args.FILE, encoding="utf-8-sig", newline="") as source:
            text = source.read()
    except UnicodeDecodeError:
        print(f"wordstat: error: {args.FILE}: not valid UTF-8", file=sys.stderr)
        return 3
    except OSError:
        print(f"wordstat: error: {args.FILE}: cannot read file", file=sys.stderr)
        return 3

    counts = Counter(re.findall(r"[a-z0-9]+", text.lower()))
    top = [
        {"word": word, "count": count}
        for word, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[
            : args.top
        ]
    ]
    result = {
        "lines": len(text.splitlines()),
        "words": sum(counts.values()),
        "chars": len(text),
        "top": top,
    }

    if args.json:
        output = json.dumps(result)
    else:
        top_text = " ".join(f"{item['word']}={item['count']}" for item in top)
        output = (
            f"lines: {result['lines']}\n"
            f"words: {result['words']}\n"
            f"chars: {result['chars']}\n"
            f"top:{' ' + top_text if top_text else ''}"
        )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
