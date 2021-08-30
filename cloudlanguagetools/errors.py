
class ApiKeyNotFoundError(ValueError):
    pass

class RequestError(ValueError):
    pass

class NotFoundError(ValueError):
    pass

class OverQuotaError(Exception):
    pass