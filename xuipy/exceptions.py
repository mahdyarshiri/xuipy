class XUIError(Exception):
    """Base exception for all xuipy errors."""


class XUIAuthError(XUIError):
    """Raised when login, authentication, or authorization fails (401/403 responses)."""


class XUIRequestError(XUIError):
    """Raised when a request to the panel fails (network error, HTTP error, or API-reported failure)."""


class XUIValidationError(XUIError):
    """Raised when arguments fail local validation before a request is even sent."""