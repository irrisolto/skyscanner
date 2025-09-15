
class AttemptsExhaustedIncompleteResponse(Exception):
    """Raised when all attempts are exhausted and the response is incomplete."""
    def __init__(self, message="All attempts exhausted and response is still incomplete."):
        super().__init__(message)

class BannedWithCaptcha(Exception):
    """Raised when access is banned and a CAPTCHA challenge is presented."""
    def __init__(self, captcha_url: str, message: str = None):
        if message is None:
            message = f"Access banned. CAPTCHA challenge encountered: {captcha_url}"
        self.captcha_url = captcha_url
        super().__init__(message)

class PerimeterXError(Exception):
    """Raised for PerimeterX exceptions"""
    def __init__(self, message : str):
        super().__init__(message)

class GenericError(Exception):
    """Raised for generic errors"""
    def __init__(self, message):
        super().__init__(message)