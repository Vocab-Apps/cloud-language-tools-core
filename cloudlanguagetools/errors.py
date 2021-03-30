

class RequestError(ValueError):
    pass

class NotFoundError(ValueError):
    pass

class OverQuotaError(Exception):
    pass