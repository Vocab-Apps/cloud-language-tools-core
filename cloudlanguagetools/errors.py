
# these exceptions can be retried
class TransientError(Exception):
    pass

# no need to retry, something is wrong which won't be fixed on retry
class PermanentError(Exception):
    pass

class InputError(PermanentError):
    pass

class ApiKeyNotFoundError(PermanentError):
    pass

class AuthenticationError(PermanentError):
    pass

class RequestError(TransientError):
    pass

class TimeoutError(TransientError):
    pass

class NotFoundError(PermanentError):
    pass

class OverQuotaError(PermanentError):
    pass

class RateLimitError(TransientError):
    def __init__(self, message, retry_after=None):
        super().__init__(message)
        self.retry_after = retry_after