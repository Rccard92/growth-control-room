"""Import batch processor status resolution tests."""


def _resolve_final_status(success_count: int, fail_count: int) -> str:
    if fail_count > 0 and success_count > 0:
        return "partially_failed"
    if fail_count > 0 and success_count == 0:
        return "failed"
    return "review_ready"


def test_partial_failure_status() -> None:
    assert _resolve_final_status(2, 1) == "partially_failed"


def test_total_failure_status() -> None:
    assert _resolve_final_status(0, 3) == "failed"


def test_success_status() -> None:
    assert _resolve_final_status(3, 0) == "review_ready"
