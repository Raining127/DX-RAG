"""Offline T1202 error-contract audit; no live provider evidence or requests.

Run from the repository root: python backend/scripts/verify_t1202_failure_contract.py
Uses the existing unit-test fixtures and the unmodified DeepSeekClient.
"""

import json
import logging
from pathlib import Path
import sys
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.errors import AppError
from app.services.qa import DeepSeekClient, SYSTEM_PROMPT
from tests.test_qa import StatusError, make_completion


def main() -> int:
    logging.disable(logging.CRITICAL)
    results = []
    # Both retry success positions and exhaustion, including 5xx boundaries.
    for status in (429, 500, 503, 599):
        for failures in (1, 2, 3):
            client = Mock()
            client.chat.completions.create.side_effect = [
                StatusError(status) for _ in range(failures)
            ] + ([] if failures == 3 else [make_completion("controlled recovery")])
            with patch("app.services.qa.time.sleep") as sleep:
                try:
                    answer = DeepSeekClient(client=client).generate_answer(
                        SYSTEM_PROMPT, "", "fixture", "question"
                    )
                    passed = failures < 3 and answer == "controlled recovery"
                except AppError as exc:
                    passed = failures == 3 and (exc.http_status, exc.code) == (
                        502, "LLM_UNAVAILABLE"
                    )
            attempts = client.chat.completions.create.call_count
            backoff = [call.args[0] for call in sleep.call_args_list]
            passed = passed and attempts == min(failures + 1, 3)
            passed = passed and backoff == [1.0, 2.0][:min(failures, 2)]
            results.append(dict(status=status, failures=failures, attempts=attempts,
                                backoff=backoff, passed=passed))
    for status in (401, 403, 400):
        client = Mock()
        client.chat.completions.create.side_effect = StatusError(status)
        passed = False
        with patch("app.services.qa.time.sleep") as sleep:
            try:
                DeepSeekClient(client=client).generate_answer(
                    SYSTEM_PROMPT, "", "fixture", "question"
                )
            except AppError as exc:
                expected = "LLM_AUTH_FAILED" if status in (401, 403) else "LLM_RESPONSE_ERROR"
                passed = (exc.http_status, exc.code) == (500, expected)
        attempts = client.chat.completions.create.call_count
        passed = passed and attempts == 1 and not sleep.called
        results.append(dict(status=status, attempts=attempts, backoff=[], passed=passed))
    print(json.dumps(dict(evidence="DETERMINISTIC fault injection; NOT live HTTP",
                          provider_requests=0, results=results,
                          passed=sum(row["passed"] for row in results),
                          total=len(results)), indent=2))
    return 0 if all(row["passed"] for row in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
