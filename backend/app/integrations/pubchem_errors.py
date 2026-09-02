class PubChemClientError(Exception):
    """Base exception for all PubChem client errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class PubChemNotFoundError(PubChemClientError):
    """Valid search, no matching molecule."""


class PubChemRateLimitError(PubChemClientError):
    """PubChem rejected the request for too many requests."""


class PubChemTemporaryError(PubChemClientError):
    """Timeout, connection failure, or temporary server problem."""


class PubChemMalformedResponseError(PubChemClientError):
    """Response missing required data or failing validation."""
