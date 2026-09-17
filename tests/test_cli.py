from argparse import Namespace

import pytest

import run_pipeline


def test_dq_cli_mode_preserves_exit_code_two(monkeypatch):
    monkeypatch.setattr(
        run_pipeline,
        "parse_args",
        lambda argv=None: Namespace(
            mode="dq",
            batch_id=None,
        ),
    )
    monkeypatch.setattr(
        run_pipeline,
        "print_startup_configuration",
        lambda mode: None,
    )
    monkeypatch.setattr(
        run_pipeline,
        "run_dq_mode",
        lambda: 2,
    )

    with pytest.raises(SystemExit) as exc_info:
        run_pipeline.main([])

    assert exc_info.value.code == 2
