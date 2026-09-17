from contextlib import nullcontext

import pytest

from pipeline import data_quality


def test_dq_pass_summary_returns_exit_code_zero():
    assert data_quality.exit_code_from_summary(
        {"fail_count": 0}
    ) == 0


def test_dq_failure_summary_returns_exit_code_two():
    assert data_quality.exit_code_from_summary(
        {"fail_count": 1}
    ) == 2


def test_dq_framework_error_propagates_instead_of_becoming_violation(monkeypatch):
    class ExplodingCursor:
        description = []

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, *args, **kwargs):
            raise RuntimeError("forced SQL framework failure")

    class FakeConnection:
        autocommit = True

        def transaction(self):
            return nullcontext()

        def cursor(self):
            return ExplodingCursor()

    monkeypatch.setattr(
        data_quality,
        "DQ_RULES",
        [
            {
                "rule_id": "DQ-TEST",
                "name": "forced framework error",
                "domain": "test",
                "violation_sql": "SELECT 1",
            }
        ],
    )

    with pytest.raises(RuntimeError, match="forced SQL framework failure"):
        data_quality.run_data_quality_checks(
            FakeConnection()
        )
