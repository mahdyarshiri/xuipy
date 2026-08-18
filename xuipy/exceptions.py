class XUIError(Exception):
    """Base exception for all xuipy errors."""


class XUIAuthError(XUIError):
    """Raised when login or authentication fails."""


class XUIRequestError(XUIError):
    """Raised when an API request to the panel fails."""