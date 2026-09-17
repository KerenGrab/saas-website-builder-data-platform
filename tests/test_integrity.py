import hashlib

import pytest

from pipeline import integrity, paths


def test_frozen_row_count_mismatch_is_rejected():
    dataset = {
        "number": 1,
        "rows": 2,
        "sha256": "0" * 64,
    }

    with pytest.raises(ValueError, match="row-count mismatch"):
        integrity.validate_frozen_reference_integrity(
            dataset,
            actual_row_count=1,
        )


def test_sha256_mismatch_uses_temporary_file(tmp_path, monkeypatch):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    source_file = raw_dir / "sample.csv"
    source_file.write_bytes(b"account_id\nA1\n")

    monkeypatch.setattr(
        paths,
        "SOURCE_ROOT",
        tmp_path,
    )

    actual_digest = hashlib.sha256(
        source_file.read_bytes()
    ).hexdigest()

    dataset = {
        "number": 1,
        "path": "raw/sample.csv",
        "rows": 1,
        "sha256": (
            "0" * 64
            if actual_digest != "0" * 64
            else "1" * 64
        ),
    }

    with pytest.raises(ValueError, match="SHA256 mismatch"):
        integrity.validate_frozen_reference_integrity(
            dataset,
            actual_row_count=1,
        )
