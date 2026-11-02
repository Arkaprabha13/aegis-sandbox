"""Entrypoint: run one attack campaign against a target and log to telemetry."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from attacker import run_campaign  # noqa: E402
from telemetry.logger import init_db, log_eval, log_turn, new_run  # noqa: E402


def main() -> int:
    
    ap = argparse.ArgumentParser()
    
    ap.add_argument("--target", default="http://127.0.0.1:8000")
    ap.add_argument("--description", default="A banking assistant with an internal transfer tool.")
    ap.add_argument("--max-attempts", type=int, default=5)
    ap.add_argument("--retries", type=int, default=1, help="retry each prompt N times")

    args = ap.parse_args()

    init_db()
    run_id = new_run(target_id=args.target)
    print(f"[run {run_id}] target={args.target} max_attempts={args.max_attempts}")

    result = run_campaign(args.target, args.description, args.max_attempts)

    for i, turn in enumerate(result["history"], 1):
        log_turn(run_id, i, turn["prompt"], turn["reply"], tool_called=turn.get("owasp"))
        print(f"\n--- turn {i} [{turn.get('owasp')}] ---")
        print(f"prompt: {turn['prompt']}")
        print(f"reply:  {turn['reply']}")
        print(f"state_changed: {turn['state_changed']}")

    breached_turns = [t for t in result["history"] if t["state_changed"]]
    reason = (
        f"state changed on turn {result['history'].index(breached_turns[0]) + 1}"
        if breached_turns
        else f"no breach in {result['attempts']} attempts"
    )
    owasp = breached_turns[0]["owasp"] if breached_turns else "n/a"
    log_eval(run_id, result["success"], reason, owasp)
    print(f"\n[run {run_id}] success={result['success']} reason={reason}")
    print(json.dumps({"run_id": run_id, "success": result["success"], "reason": reason}))
    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
