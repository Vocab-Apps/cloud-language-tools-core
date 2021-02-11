import cloudlanguagetools.constants


class UsageSlice():
    def __init__(self, 
                request_type: cloudlanguagetools.constants.RequestType, 
                usage_scope: cloudlanguagetools.constants.UsageScope, 
                usage_period: cloudlanguagetools.constants.UsagePeriod, 
                service: cloudlanguagetools.constants.Service, 
                api_key: str):
        self.request_type = request_type
        self.usage_scope = usage_scope
        self.usage_period = usage_period
        self.service = service
        self.api_key = api_key

    def over_quota(self, characters, requests) -> bool:
        if self.usage_scope == cloudlanguagetools.constants.UsageScope.User:
            if self.usage_period == cloudlanguagetools.constants.UsagePeriod.daily:
                if characters > 100000:
                    return True
        return False


