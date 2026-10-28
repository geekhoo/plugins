"""CLI for offline translation or an explicitly started local bridge."""

import argparse
import json
import os
from pathlib import Path
import signal
import sys
import threading

from .mapper import BridgeState, MappingError, translate_request
from .server import make_server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    translate = sub.add_parser("translate", help="Map stdin/file to stdout/file, without network")
    translate.add_argument("--input", type=Path)
    translate.add_argument("--output", type=Path)
    serve = sub.add_parser("serve", help="Listen on 127.0.0.1; fixed upstream from environment")
    serve.add_argument("--port", type=int, default=0)
    serve.add_argument("--ready-file", type=Path, required=True)
    for command in (translate, serve):
        command.add_argument("--known-plaintext", type=Path, help="Explicit SHA256-to-plaintext JSON object")
    args = parser.parse_args()
    server = None
    ready_written = False
    try:
        known = json.loads(args.known_plaintext.read_text(encoding="utf-8")) if args.known_plaintext else {}
        state = BridgeState(known)
        if args.command == "translate":
            source = args.input.read_text(encoding="utf-8") if args.input else sys.stdin.read()
            mapped, _ = translate_request(json.loads(source), state)
            result = json.dumps(mapped, ensure_ascii=False, indent=2) + "\n"
            if args.output:
                args.output.write_text(result, encoding="utf-8")
            else:
                sys.stdout.write(result)
            return 0
        server = make_server(os.environ.get("LITELLM_PROXY_API_BASE", ""),
                             os.environ.get("LITELLM_PROXY_API_KEY", ""), port=args.port, state=state)
        ready = {"base_url": f"http://127.0.0.1:{server.server_port}/v1", "pid": os.getpid()}
        # Exclusive creation prevents a stale file from masquerading as readiness.
        with args.ready_file.open("x", encoding="utf-8") as handle:
            json.dump(ready, handle)
        ready_written = True

        def stop(_signum, _frame):
            threading.Thread(target=server.shutdown, daemon=True).start()

        signal.signal(signal.SIGINT, stop)
        signal.signal(signal.SIGTERM, stop)
        server.serve_forever(poll_interval=0.2)
        return 0
    except (OSError, ValueError, TypeError, MappingError):
        print("Bridge failed: invalid configuration, mapping, or I/O", file=sys.stderr)
        return 1
    finally:
        if server:
            server.server_close()
        if ready_written:
            args.ready_file.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
