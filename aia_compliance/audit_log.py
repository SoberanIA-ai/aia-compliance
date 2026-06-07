"""Immutable SHA-256 audit log for AI decisions.

Implements chain-hashing to create a tamper-evident log of AI actions,
compliant with Art. 12 (record-keeping) and Art. 19 (logging obligations)
of the EU AI Act (2024/1689).

Supports SQLite (built-in) and PostgreSQL (via SQLAlchemy).
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Optional

from .exceptions import AuditLogError, IntegrityError


@dataclass
class AuditEntry:
    """A single immutable audit log entry."""

    entry_id: str
    timestamp: str
    action: str
    actor: str
    input_data: dict
    output_data: dict
    model_used: str
    human_reviewed: bool
    hash_sha256: str
    chain_hash: str
    metadata: dict

    def to_dict(self) -> dict:
        return asdict(self)


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _canonical_json(obj: Any) -> str:
    """Stable JSON serialization — same dict always yields same bytes."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


class AuditLog:
    """Tamper-evident audit log backed by SQLite or PostgreSQL.

    Usage
    -----
    .. code-block:: python

        log = AuditLog(storage="sqlite:///audit.db")

        entry = log.record(
            action="authorization_decision",
            actor="ai_agent",
            input_data={"patient": "...", "insurer": "..."},
            output_data={"decision": "approved", "confidence": 0.92},
            model_used="mistral-large",
            human_reviewed=False,
        )
        print(entry.hash_sha256)
        print(log.verify_integrity())
    """

    def __init__(self, storage: str = "sqlite:///:memory:") -> None:
        self._storage = storage
        self._conn: Optional[sqlite3.Connection] = None
        self._sa_engine: Any = None
        self._backend = self._init_backend(storage)

    def _init_backend(self, storage: str) -> str:
        if storage.startswith("sqlite:///"):
            # sqlite:///:memory: → :memory:  |  sqlite:///file.db → file.db  |  sqlite:////abs → /abs
            path = storage[len("sqlite:///"):]
            self._conn = sqlite3.connect(path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._create_sqlite_table()
            return "sqlite"
        elif storage.startswith("postgresql://") or storage.startswith("postgres://"):
            try:
                from sqlalchemy import create_engine, text
                self._sa_engine = create_engine(storage)
                self._create_pg_table(text)
                return "postgresql"
            except ImportError as exc:
                raise AuditLogError(
                    "PostgreSQL support requires SQLAlchemy: pip install aia-compliance[postgres]"
                ) from exc
        else:
            raise AuditLogError(
                f"Unsupported storage scheme in '{storage}'. "
                "Use 'sqlite:///path.db' or 'postgresql://user:pass@host/db'."
            )

    def _create_sqlite_table(self) -> None:
        assert self._conn is not None
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                entry_id        TEXT PRIMARY KEY,
                timestamp       TEXT NOT NULL,
                action          TEXT NOT NULL,
                actor           TEXT NOT NULL,
                input_data      TEXT NOT NULL,
                output_data     TEXT NOT NULL,
                model_used      TEXT NOT NULL,
                human_reviewed  INTEGER NOT NULL,
                hash_sha256     TEXT NOT NULL,
                chain_hash      TEXT NOT NULL,
                metadata        TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def _create_pg_table(self, text: Any) -> None:
        with self._sa_engine.begin() as conn:
            conn.execute(text(
                """
                CREATE TABLE IF NOT EXISTS audit_log (
                    entry_id        TEXT PRIMARY KEY,
                    timestamp       TEXT NOT NULL,
                    action          TEXT NOT NULL,
                    actor           TEXT NOT NULL,
                    input_data      TEXT NOT NULL,
                    output_data     TEXT NOT NULL,
                    model_used      TEXT NOT NULL,
                    human_reviewed  BOOLEAN NOT NULL,
                    hash_sha256     TEXT NOT NULL,
                    chain_hash      TEXT NOT NULL,
                    metadata        TEXT NOT NULL
                )
                """
            ))

    def _get_last_chain_hash(self) -> str:
        if self._backend == "sqlite":
            assert self._conn is not None
            row = self._conn.execute(
                "SELECT chain_hash FROM audit_log ORDER BY timestamp DESC LIMIT 1"
            ).fetchone()
            return row["chain_hash"] if row else "0" * 64
        else:
            from sqlalchemy import text
            with self._sa_engine.connect() as conn:
                row = conn.execute(
                    text("SELECT chain_hash FROM audit_log ORDER BY timestamp DESC LIMIT 1")
                ).fetchone()
                return row[0] if row else "0" * 64

    def record(
        self,
        action: str,
        actor: str,
        input_data: dict,
        output_data: dict,
        model_used: str,
        human_reviewed: bool = False,
        metadata: Optional[dict] = None,
    ) -> AuditEntry:
        """Record an AI decision in the immutable audit log.

        Parameters
        ----------
        action:
            Identifier for the action taken (e.g. ``"authorization_decision"``).
        actor:
            Who or what performed the action (e.g. ``"ai_agent"``, ``"user:123"``).
        input_data:
            Inputs provided to the AI system. Personally identifiable information
            should be pseudonymised before logging.
        output_data:
            Outputs produced by the AI system.
        model_used:
            Model identifier (e.g. ``"mistral-large"``).
        human_reviewed:
            Whether a human reviewed the decision before it took effect.
        metadata:
            Optional extra key/value pairs.

        Returns
        -------
        AuditEntry
            Immutable entry with SHA-256 hash and chain hash.
        """
        entry_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        meta = metadata or {}

        payload = {
            "entry_id": entry_id,
            "timestamp": timestamp,
            "action": action,
            "actor": actor,
            "input_data": input_data,
            "output_data": output_data,
            "model_used": model_used,
            "human_reviewed": human_reviewed,
            "metadata": meta,
        }
        hash_sha256 = _sha256(_canonical_json(payload))
        prev_chain = self._get_last_chain_hash()
        chain_hash = _sha256(hash_sha256 + prev_chain)

        entry = AuditEntry(
            entry_id=entry_id,
            timestamp=timestamp,
            action=action,
            actor=actor,
            input_data=input_data,
            output_data=output_data,
            model_used=model_used,
            human_reviewed=human_reviewed,
            hash_sha256=hash_sha256,
            chain_hash=chain_hash,
            metadata=meta,
        )
        self._insert(entry)
        return entry

    def _insert(self, entry: AuditEntry) -> None:
        row = (
            entry.entry_id,
            entry.timestamp,
            entry.action,
            entry.actor,
            _canonical_json(entry.input_data),
            _canonical_json(entry.output_data),
            entry.model_used,
            int(entry.human_reviewed),
            entry.hash_sha256,
            entry.chain_hash,
            _canonical_json(entry.metadata),
        )
        if self._backend == "sqlite":
            assert self._conn is not None
            self._conn.execute(
                """
                INSERT INTO audit_log VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """,
                row,
            )
            self._conn.commit()
        else:
            from sqlalchemy import text
            with self._sa_engine.begin() as conn:
                conn.execute(
                    text(
                        "INSERT INTO audit_log VALUES "
                        "(:id,:ts,:act,:actor,:inp,:out,:model,:hr,:hash,:chain,:meta)"
                    ),
                    dict(
                        zip(
                            ["id", "ts", "act", "actor", "inp", "out", "model", "hr", "hash", "chain", "meta"],
                            row,
                        )
                    ),
                )

    def verify_integrity(self) -> bool:
        """Verify the hash chain has not been tampered with.

        Returns ``True`` if the chain is intact, raises ``IntegrityError`` otherwise.
        """
        entries = self._fetch_all_ordered()
        prev_chain = "0" * 64
        for row in entries:
            payload = {
                "entry_id": row["entry_id"],
                "timestamp": row["timestamp"],
                "action": row["action"],
                "actor": row["actor"],
                "input_data": json.loads(row["input_data"]),
                "output_data": json.loads(row["output_data"]),
                "model_used": row["model_used"],
                "human_reviewed": bool(row["human_reviewed"]),
                "metadata": json.loads(row["metadata"]),
            }
            expected_hash = _sha256(_canonical_json(payload))
            if expected_hash != row["hash_sha256"]:
                raise IntegrityError(row["entry_id"], expected_hash, row["hash_sha256"])

            expected_chain = _sha256(expected_hash + prev_chain)
            if expected_chain != row["chain_hash"]:
                raise IntegrityError(row["entry_id"], expected_chain, row["chain_hash"])

            prev_chain = row["chain_hash"]

        return True

    def _fetch_all_ordered(self) -> list[dict]:
        if self._backend == "sqlite":
            assert self._conn is not None
            rows = self._conn.execute(
                "SELECT * FROM audit_log ORDER BY timestamp ASC"
            ).fetchall()
            return [dict(r) for r in rows]
        else:
            from sqlalchemy import text
            with self._sa_engine.connect() as conn:
                rows = conn.execute(
                    text("SELECT * FROM audit_log ORDER BY timestamp ASC")
                ).fetchall()
                return [dict(r._mapping) for r in rows]

    def export_audit_report(self) -> dict:
        """Export a full audit report as a serialisable dictionary.

        The report includes all entries and a top-level integrity verification result.
        """
        try:
            integrity_ok = self.verify_integrity()
        except IntegrityError as exc:
            integrity_ok = False
            integrity_error = str(exc)
        else:
            integrity_error = None

        entries = self._fetch_all_ordered()
        return {
            "integrity_verified": integrity_ok,
            "integrity_error": integrity_error,
            "total_entries": len(entries),
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "entries": [
                {
                    **{k: v for k, v in e.items() if k not in ("input_data", "output_data", "metadata")},
                    "input_data": json.loads(e["input_data"]),
                    "output_data": json.loads(e["output_data"]),
                    "metadata": json.loads(e["metadata"]),
                }
                for e in entries
            ],
        }

    def close(self) -> None:
        """Release database resources."""
        if self._conn is not None:
            self._conn.close()
        if self._sa_engine is not None:
            self._sa_engine.dispose()
