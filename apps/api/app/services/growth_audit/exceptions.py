"""Growth Audit domain exceptions."""


class GrowthAuditError(Exception):
    """Base error for Growth Audit operations."""


class GrowthAuditValidationError(GrowthAuditError):
    """Invalid input or configuration."""


class GrowthAuditRunNotFoundError(GrowthAuditError):
    """Run not found for the given project."""
