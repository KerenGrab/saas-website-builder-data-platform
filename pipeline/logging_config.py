"""Central logging configuration for Part 9G."""

import contextvars
import logging
import sys
import time
from pathlib import Path

from pipeline import config, paths


LOGGER_NAME = "saas_pipeline"

_run_id_var = contextvars.ContextVar(
    "run_id",
    default="-",
)

_mode_var = contextvars.ContextVar(
    "mode",
    default="-",
)

_batch_id_var = contextvars.ContextVar(
    "batch_id",
    default="-",
)


class UTCSecretSafeFormatter(logging.Formatter):
    """UTC formatter that also redacts configured secret values."""

    converter = time.gmtime

    def __init__(
        self,
        *args,
        secrets=(),
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        self._secrets = tuple(
            str(secret)
            for secret in secrets
            if secret not in (
                None,
                "",
            )
        )

    def format(
        self,
        record,
    ):
        record.run_id = _run_id_var.get()
        record.mode = _mode_var.get()
        record.batch_id = _batch_id_var.get()

        rendered = super().format(record)

        for secret in self._secrets:
            rendered = rendered.replace(
                secret,
                "***REDACTED***",
            )

        return rendered


def default_log_path():
    return (
        Path(paths.PROJECT_ROOT)
        / "logs"
        / "pipeline.log"
    )


def configure_logging(
    *,
    log_path=None,
    level=logging.INFO,
    secrets=None,
):
    """Configure one console handler and one persistent file handler."""

    path = (
        Path(log_path)
        if log_path is not None
        else default_log_path()
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if secrets is None:
        secrets = (
            config.DB_PASSWORD,
        )

    formatter = UTCSecretSafeFormatter(
        fmt=(
            "%(asctime)sZ | "
            "%(levelname)s | "
            "run=%(run_id)s | "
            "mode=%(mode)s | "
            "batch=%(batch_id)s | "
            "%(name)s | "
            "%(message)s"
        ),
        datefmt="%Y-%m-%dT%H:%M:%S",
        secrets=secrets,
    )

    logger = logging.getLogger(
        LOGGER_NAME
    )

    logger.setLevel(
        level
    )

    logger.propagate = False

    for handler in list(
        logger.handlers
    ):
        logger.removeHandler(
            handler
        )
        handler.close()

    console_handler = logging.StreamHandler(
        sys.stdout
    )

    console_handler.setLevel(
        level
    )

    console_handler.setFormatter(
        formatter
    )

    file_handler = logging.FileHandler(
        path,
        encoding="utf-8",
    )

    file_handler.setLevel(
        level
    )

    file_handler.setFormatter(
        formatter
    )

    logger.addHandler(
        console_handler
    )

    logger.addHandler(
        file_handler
    )

    return path


def set_log_context(
    *,
    run_id=None,
    mode=None,
    batch_id=None,
):
    if run_id is not None:
        _run_id_var.set(
            str(run_id)
        )

    if mode is not None:
        _mode_var.set(
            str(mode)
        )

    if batch_id is not None:
        _batch_id_var.set(
            str(batch_id)
        )


def set_batch_id(
    batch_id,
):
    _batch_id_var.set(
        "-"
        if batch_id is None
        else str(batch_id)
    )


def clear_log_context():
    _run_id_var.set("-")
    _mode_var.set("-")
    _batch_id_var.set("-")


def redact_text(
    value,
    *,
    secrets=None,
):
    text = str(
        value
    )

    if secrets is None:
        secrets = (
            config.DB_PASSWORD,
        )

    for secret in secrets:
        if secret not in (
            None,
            "",
        ):
            text = text.replace(
                str(secret),
                "***REDACTED***",
            )

    return text


def shutdown_logging():
    logger = logging.getLogger(
        LOGGER_NAME
    )

    for handler in list(
        logger.handlers
    ):
        handler.flush()

        logger.removeHandler(
            handler
        )

        handler.close()