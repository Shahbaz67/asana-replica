from typing import Optional


class AsanaAPIException(Exception):
    """Base exception for Asana API errors."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        help_text: Optional[str] = None,
        phrase: Optional[str] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.help_text = help_text or "Please check your request and try again."
        self.phrase = phrase or "bad_request"
        super().__init__(self.message)


class NotFoundError(AsanaAPIException):
    """Resource not found error."""
    
    def __init__(self, resource: str, gid: str):
        super().__init__(
            message=f"{resource} with gid '{gid}' not found",
            status_code=404,
            help_text=f"The {resource.lower()} you requested does not exist or you do not have access to it.",
            phrase="not_found",
        )


class ForbiddenError(AsanaAPIException):
    """Access forbidden error."""
    
    def __init__(self, message: str = "You do not have permission to perform this action"):
        super().__init__(
            message=message,
            status_code=403,
            help_text="You do not have the necessary permissions for this action.",
            phrase="forbidden",
        )


class UnauthorizedError(AsanaAPIException):
    """Authentication required error."""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            status_code=401,
            help_text="Please provide valid authentication credentials.",
            phrase="unauthorized",
        )


class ValidationError(AsanaAPIException):
    """Validation error."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        help_text = f"Invalid value for field '{field}'." if field else "Please check your input."
        super().__init__(
            message=message,
            status_code=400,
            help_text=help_text,
            phrase="invalid_request",
        )


class ConflictError(AsanaAPIException):
    """Resource conflict error."""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=409,
            help_text="The request conflicts with the current state of the resource.",
            phrase="conflict",
        )


class RateLimitError(AsanaAPIException):
    """Rate limit exceeded error."""
    
    def __init__(self, retry_after: int = 60):
        super().__init__(
            message="Rate limit exceeded",
            status_code=429,
            help_text=f"Please wait {retry_after} seconds before making another request.",
            phrase="rate_limited",
        )

