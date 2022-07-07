
class ApiKeyNotFoundError(ValueError):
    pass

class RequestError(ValueError):
    pass

class TimeoutError(ValueError):
    pass

class NotFoundError(ValueError):
    pass

class OverQuotaError(Exception):
    pass