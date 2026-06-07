"""Custom exceptions for aia-compliance."""


class AIAComplianceError(Exception):
    """Base exception for all aia-compliance errors."""


class InvalidSectorError(AIAComplianceError):
    """Raised when an unsupported sector is provided."""

    def __init__(self, sector: str, valid_sectors: list[str]) -> None:
        self.sector = sector
        self.valid_sectors = valid_sectors
        super().__init__(
            f"Invalid sector '{sector}'. Valid sectors: {', '.join(valid_sectors)}"
        )


class InvalidInputError(AIAComplianceError):
    """Raised when input data fails validation."""


class AuditLogError(AIAComplianceError):
    """Raised when an audit log operation fails."""


class IntegrityError(AIAComplianceError):
    """Raised when audit log chain integrity verification fails."""

    def __init__(self, entry_id: str, expected_hash: str, actual_hash: str) -> None:
        self.entry_id = entry_id
        self.expected_hash = expected_hash
        self.actual_hash = actual_hash
        super().__init__(
            f"Integrity violation at entry '{entry_id}': "
            f"expected hash {expected_hash[:16]}…, got {actual_hash[:16]}…"
        )
