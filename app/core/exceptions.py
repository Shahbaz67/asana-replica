"""
Asana API Exception Classes

Based on: https://developers.asana.com/docs/errors
"""
from typing import Optional


class AsanaAPIException(Exception):
    """Base exception for Asana API errors.
    
    Standard error response format:
    {
        "errors": [
            {
                "message": "...",
                "help": "...",
                "phrase": "..."  // 500 errors only
            }
        ]
    }
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        help_text: Optional[str] = None,
        phrase: Optional[str] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.help_text = help_text or "For more information on API status codes and how to handle them, read the docs on errors: https://developers.asana.com/docs/errors"
        self.phrase = phrase
        super().__init__(self.message)


class NotFoundError(AsanaAPIException):
    """404 - Resource not found error."""
    
    def __init__(self, resource: str, gid: str):
        super().__init__(
            message=f"{resource}: Unknown object: {gid}",
            status_code=404,
            help_text=f"The {resource.lower()} you requested does not exist or you do not have access to it.",
        )


class ForbiddenError(AsanaAPIException):
    """403 - Forbidden error."""
    
    def __init__(self, message: str = "Forbidden"):
        super().__init__(
            message=message,
            status_code=403,
            help_text="The authentication and request syntax was valid but the server is refusing to complete the request. This can happen if you try to read or write to objects or properties that the user does not have access to.",
        )


class UnauthorizedError(AsanaAPIException):
    """401 - Unauthorized error."""
    
    def __init__(self, message: str = "Not Authorized"):
        super().__init__(
            message=message,
            status_code=401,
            help_text="A valid authentication token was not provided with the request, so the API could not associate a user with the request.",
        )


class ValidationError(AsanaAPIException):
    """400 - Bad request / validation error."""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=400,
            help_text="This usually occurs because of a missing or malformed parameter. Check the documentation and the syntax of your request and try again.",
        )


class RateLimitError(AsanaAPIException):
    """429 - Rate limit exceeded error."""
    
    def __init__(self, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(
            message="Rate limit exceeded",
            status_code=429,
            help_text=f"You have exceeded the rate limit. Please wait {retry_after} seconds before making another request.",
        )


class ConflictError(AsanaAPIException):
    """409 - Conflict error."""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=409,
            help_text="The request could not be completed due to a conflict with the current state of the resource.",
        )


class PaymentRequiredError(AsanaAPIException):
    """402 - Payment required error."""
    
    def __init__(self, message: str = "Payment Required"):
        super().__init__(
            message=message,
            status_code=402,
            help_text="The request failed because the workspace is on a free tier that does not support this feature.",
        )


class ServerError(AsanaAPIException):
    """500 - Internal server error."""
    
    def __init__(self, message: str = "Server Error", phrase: Optional[str] = None):
        super().__init__(
            message=message,
            status_code=500,
            help_text="There was a problem on the server. If the problem persists, contact support with the error phrase.",
            phrase=phrase or "unknown_error",
        )
