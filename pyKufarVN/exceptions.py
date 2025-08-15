"""
Exception classes for pyKufarVN
"""

class KufarException(Exception):
    """Base exception for Kufar operations"""
    pass

class KufarAPIException(KufarException):
    """Exception for API-related errors"""
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data

class KufarConnectionException(KufarException):
    """Exception for connection-related errors"""
    pass

class KufarParsingException(KufarException):
    """Exception for data parsing errors"""
    pass

class KufarRateLimitException(KufarAPIException):
    """Exception for rate limiting (429 errors)"""
    pass

class KufarBlockedException(KufarAPIException):
    """Exception for blocked requests (403 errors)"""
    pass
