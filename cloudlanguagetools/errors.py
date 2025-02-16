
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

class RequestError(TransientError):
    pass

class TimeoutError(TransientError):
    pass

class NotFoundError(PermanentError):
    pass

class OverQuotaError(PermanentError):
    pass