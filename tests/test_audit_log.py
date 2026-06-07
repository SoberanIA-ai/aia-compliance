"""Tests for the immutable SHA-256 audit log."""
import json
import pytest

from aia_compliance.audit_log import AuditLog, AuditEntry, _sha256, _canonical_json
from aia_compliance.exceptions import AuditLogError, IntegrityError


@pytest.fixture
def log():
    """In-memory SQLite audit log for testing."""
    audit_log = AuditLog(storage="sqlite:///:memory:")
    yield audit_log
    audit_log.close()


@pytest.fixture
def sample_entry_kwargs():
    return dict(
        action="authorization_decision",
        actor="ai_agent",
        input_data={"patient": "p-001", "insurer": "acme"},
        output_data={"decision": "approved", "confidence": 0.92},
        model_used="mistral-large",
        human_reviewed=False,
    )


class TestAuditLogCreation:
    def test_in_memory_sqlite(self):
        log = AuditLog(storage="sqlite:///:memory:")
        assert log is not None
        log.close()

    def test_file_sqlite(self, tmp_path):
        db_path = tmp_path / "audit.db"
        log = AuditLog(storage=f"sqlite:///{db_path}")
        assert db_path.exists()
        log.close()

    def test_invalid_storage_scheme_raises(self):
        with pytest.raises(AuditLogError, match="Unsupported"):
            AuditLog(storage="mongodb://localhost/test")


class TestAuditLogRecord:
    def test_record_returns_audit_entry(self, log, sample_entry_kwargs):
        entry = log.record(**sample_entry_kwargs)
        assert isinstance(entry, AuditEntry)

    def test_entry_has_id(self, log, sample_entry_kwargs):
        entry = log.record(**sample_entry_kwargs)
        assert isinstance(entry.entry_id, str)
        assert len(entry.entry_id) == 36  # UUID format

    def test_entry_has_timestamp(self, log, sample_entry_kwargs):
        entry = log.record(**sample_entry_kwargs)
        assert "T" in entry.timestamp  # ISO format

    def test_entry_has_hash(self, log, sample_entry_kwargs):
        entry = log.record(**sample_entry_kwargs)
        assert isinstance(entry.hash_sha256, str)
        assert len(entry.hash_sha256) == 64

    def test_entry_has_chain_hash(self, log, sample_entry_kwargs):
        entry = log.record(**sample_entry_kwargs)
        assert isinstance(entry.chain_hash, str)
        assert len(entry.chain_hash) == 64

    def test_first_entry_chain_hash_from_genesis(self, log, sample_entry_kwargs):
        entry = log.record(**sample_entry_kwargs)
        genesis_prev = "0" * 64
        expected_chain = _sha256(entry.hash_sha256 + genesis_prev)
        assert entry.chain_hash == expected_chain

    def test_second_entry_chain_links_to_first(self, log, sample_entry_kwargs):
        entry1 = log.record(**sample_entry_kwargs)
        entry2 = log.record(**sample_entry_kwargs)
        expected_chain2 = _sha256(entry2.hash_sha256 + entry1.chain_hash)
        assert entry2.chain_hash == expected_chain2

    def test_fields_stored_correctly(self, log):
        entry = log.record(
            action="test_action",
            actor="test_actor",
            input_data={"key": "value"},
            output_data={"result": 42},
            model_used="test-model",
            human_reviewed=True,
            metadata={"env": "test"},
        )
        assert entry.action == "test_action"
        assert entry.actor == "test_actor"
        assert entry.input_data == {"key": "value"}
        assert entry.output_data == {"result": 42}
        assert entry.model_used == "test-model"
        assert entry.human_reviewed is True
        assert entry.metadata == {"env": "test"}

    def test_metadata_defaults_to_empty_dict(self, log, sample_entry_kwargs):
        entry = log.record(**sample_entry_kwargs)
        assert entry.metadata == {}

    def test_to_dict_returns_dict(self, log, sample_entry_kwargs):
        entry = log.record(**sample_entry_kwargs)
        d = entry.to_dict()
        assert isinstance(d, dict)
        assert "entry_id" in d
        assert "hash_sha256" in d


class TestAuditLogIntegrity:
    def test_empty_log_is_valid(self, log):
        assert log.verify_integrity() is True

    def test_single_entry_is_valid(self, log, sample_entry_kwargs):
        log.record(**sample_entry_kwargs)
        assert log.verify_integrity() is True

    def test_multiple_entries_are_valid(self, log, sample_entry_kwargs):
        for _ in range(5):
            log.record(**sample_entry_kwargs)
        assert log.verify_integrity() is True

    def test_tampered_hash_raises_integrity_error(self, log, sample_entry_kwargs):
        log.record(**sample_entry_kwargs)
        # Directly corrupt the database
        assert log._conn is not None
        log._conn.execute(
            "UPDATE audit_log SET hash_sha256 = 'deadbeef' || substr(hash_sha256, 9)"
        )
        log._conn.commit()
        with pytest.raises(IntegrityError):
            log.verify_integrity()

    def test_integrity_error_contains_entry_id(self, log, sample_entry_kwargs):
        entry = log.record(**sample_entry_kwargs)
        assert log._conn is not None
        log._conn.execute("UPDATE audit_log SET hash_sha256 = 'a' * 64")
        log._conn.commit()
        try:
            log.verify_integrity()
        except IntegrityError as exc:
            assert exc.entry_id == entry.entry_id


class TestAuditLogExport:
    def test_export_returns_dict(self, log, sample_entry_kwargs):
        log.record(**sample_entry_kwargs)
        report = log.export_audit_report()
        assert isinstance(report, dict)

    def test_export_integrity_true_on_clean_log(self, log, sample_entry_kwargs):
        log.record(**sample_entry_kwargs)
        report = log.export_audit_report()
        assert report["integrity_verified"] is True
        assert report["integrity_error"] is None

    def test_export_total_entries_count(self, log, sample_entry_kwargs):
        for _ in range(3):
            log.record(**sample_entry_kwargs)
        report = log.export_audit_report()
        assert report["total_entries"] == 3

    def test_export_contains_entries(self, log, sample_entry_kwargs):
        log.record(**sample_entry_kwargs)
        report = log.export_audit_report()
        assert "entries" in report
        assert len(report["entries"]) == 1

    def test_export_entry_has_parsed_json_fields(self, log):
        log.record(
            action="test",
            actor="agent",
            input_data={"x": 1},
            output_data={"y": 2},
            model_used="m",
            human_reviewed=False,
        )
        report = log.export_audit_report()
        entry = report["entries"][0]
        assert isinstance(entry["input_data"], dict)
        assert isinstance(entry["output_data"], dict)
        assert isinstance(entry["metadata"], dict)

    def test_export_has_exported_at(self, log, sample_entry_kwargs):
        log.record(**sample_entry_kwargs)
        report = log.export_audit_report()
        assert "exported_at" in report

    def test_export_integrity_false_on_tampered_log(self, log, sample_entry_kwargs):
        log.record(**sample_entry_kwargs)
        assert log._conn is not None
        log._conn.execute(
            "UPDATE audit_log SET hash_sha256 = 'badhash' || substr(hash_sha256, 8)"
        )
        log._conn.commit()
        report = log.export_audit_report()
        assert report["integrity_verified"] is False
        assert report["integrity_error"] is not None


class TestHashFunctions:
    def test_sha256_length(self):
        assert len(_sha256("hello")) == 64

    def test_sha256_deterministic(self):
        assert _sha256("test") == _sha256("test")

    def test_sha256_different_inputs(self):
        assert _sha256("a") != _sha256("b")

    def test_canonical_json_is_stable(self):
        d1 = {"b": 2, "a": 1}
        d2 = {"a": 1, "b": 2}
        assert _canonical_json(d1) == _canonical_json(d2)

    def test_canonical_json_nested(self):
        obj = {"x": {"z": 3, "y": 2}, "a": [1, 2, 3]}
        result = _canonical_json(obj)
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed == obj
