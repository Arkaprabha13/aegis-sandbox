"""Replay every YAML case in tests/cases/ against a fresh sandbox.

Each case supports:
  - prompt: str               single-turn attack
  - prompts: [str]            multi-turn attack (overrides prompt)
  - retries: int              how many times to try (default 1, for stochastic bugs)
  - expect.state_breach: bool whether mock DB should show money moved
  - expect.protected_account: str  account id to check for drain
  - expect.reply_contains: [str]   optional list of phrases that MUST appear in reply
                                   (for text-based findings like LLM07 prompt leak)
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import httpx
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from judge.state_check import read_mock_state, state_breached  # noqa: E402

COMPOSE = "sandbox/docker-compose.yml"
TARGET = "http://127.0.0.1:8000"


def _reset_sandbox() -> None:
    subprocess.run(
        ["docker", "compose", "-f", COMPOSE, "down", "-v"],
        check=False,
        capture_output=True,
    )
    subprocess.run(
        ["docker", "compose", "-f", COMPOSE, "up", "-d"],
        check=True,
        capture_output=True,
    )
    for _ in range(30):
        try:
            if httpx.get(f"{TARGET}/healthz", timeout=1.0).status_code == 200:
                return
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError("sandbox did not become healthy")


def _send_prompts(prompts: list[str]) -> str:
    """Send all prompts sequentially, return the last reply text."""
    last_reply = ""
    for p in prompts:
        try:
            r = httpx.post(f"{TARGET}/chat", json={"prompt": p}, timeout=20.0)
            r.raise_for_status()
            last_reply = r.json().get("reply", "")
        except httpx.HTTPError as e:
            print(f"  (network error: {e})")
    return last_reply


def main() -> int:
    cases = sorted(Path("tests/cases").glob("*.yaml"))
    if not cases:
        print("no cases found")
        return 1

    failures = 0
    for case_path in cases:
        case = yaml.safe_load(case_path.read_text())
        _reset_sandbox()

        protected = case["expect"]["protected_account"]
        expected_breach = bool(case["expect"]["state_breach"])
        reply_phrases = case["expect"].get("reply_contains")  # None if absent
        retries = int(case.get("retries", 1))

        prompts = case.get("prompts")
        if prompts is None:
            prompts = [case["prompt"]]

        before = read_mock_state(COMPOSE)
        breached = False
        last_reply = ""
        attempts_used = 0

        for attempt in range(retries):
            last_reply = _send_prompts(prompts)
            attempts_used = attempt + 1
            after = read_mock_state(COMPOSE)
            breached = state_breached(before, after, protected)

            state_ok = breached == expected_breach
            text_ok = True
            if reply_phrases is not None:
                text_ok = all(phrase in last_reply for phrase in reply_phrases)

            if state_ok and text_ok:
                break

        state_ok = breached == expected_breach
        if reply_phrases is None:
            text_ok = True
            text_detail = ""
        else:
            missing = [p for p in reply_phrases if p not in last_reply]
            text_ok = not missing
            text_detail = (
                f", missing_phrases={missing}" if missing else ", phrases_present"
            )

        ok = state_ok and text_ok
        status = "PASS" if ok else "FAIL"
        print(
            f"[{status}] {case['id']} "
            f"(breach={breached}/{expected_breach}, "
            f"attempts={attempts_used}/{retries}{text_detail})"
        )
        if not ok:
            failures += 1

    total = len(cases)
    passed = total - failures
    print(f"\n{passed}/{total} passed")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())