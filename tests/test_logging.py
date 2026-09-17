import logging

from pipeline import logging_config


def test_persistent_log_contains_context_and_redacts_secret(
    tmp_path,
):
    log_path = (
        tmp_path
        / "pipeline.log"
    )

    logging_config.configure_logging(
        log_path=log_path,
        secrets=(
            "super-secret",
        ),
    )

    logging_config.set_log_context(
        run_id="RUN-TEST",
        mode="validate",
        batch_id="B-TEST",
    )

    logger = logging.getLogger(
        "saas_pipeline.test"
    )

    try:
        logger.error(
            "credential=%s",
            "super-secret",
        )

    finally:
        logging_config.clear_log_context()
        logging_config.shutdown_logging()

    content = log_path.read_text(
        encoding="utf-8"
    )

    assert (
        "run=RUN-TEST"
        in content
    )

    assert (
        "mode=validate"
        in content
    )

    assert (
        "batch=B-TEST"
        in content
    )

    assert (
        "super-secret"
        not in content
    )

    assert (
        "***REDACTED***"
        in content
    )