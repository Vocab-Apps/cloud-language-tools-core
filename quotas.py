import datetime
import cloudlanguagetools.constants


DEFAULT_USER_DAILY_CHAR_LIMIT = 80000
NAVER_USER_DAILY_CHAR_LIMIT = 30000

TRIAL_USER_CHARACTER_LIMIT = 10000

class UsageSlice():
    def __init__(self, 
                request_type: cloudlanguagetools.constants.RequestType, 
                usage_scope: cloudlanguagetools.constants.UsageScope, 
                usage_period: cloudlanguagetools.constants.UsagePeriod, 
                service: cloudlanguagetools.constants.Service, 
                api_key: str,
                api_key_type: cloudlanguagetools.constants.ApiKeyType,
                character_limit):
        self.request_type = request_type
        self.usage_scope = usage_scope
        self.usage_period = usage_period
        self.service = service
        self.api_key = api_key
        self.api_key_type = api_key_type
        self.character_limit = character_limit

    def build_key_suffix(self) -> str:
        if self.usage_scope == cloudlanguagetools.constants.UsageScope.User and self.usage_period == cloudlanguagetools.constants.UsagePeriod.lifetime:
            return f'{self.usage_scope.key_str}:{self.usage_period.name}:{self.api_key}'

        date_str = datetime.datetime.today().strftime('%Y%m')
        if self.usage_period == cloudlanguagetools.constants.UsagePeriod.daily:
            date_str = datetime.datetime.today().strftime('%Y%m%d')

        api_key_suffix = ''
        if self.usage_scope == cloudlanguagetools.constants.UsageScope.User:
            api_key_suffix = f':{self.api_key}'

        return f'{self.usage_scope.key_str}:{self.usage_period.name}:{date_str}:{self.service.name}:{self.request_type.name}{api_key_suffix}'


    def over_quota(self, characters, requests) -> bool:
        if self.usage_scope == cloudlanguagetools.constants.UsageScope.User:
            if self.usage_period == cloudlanguagetools.constants.UsagePeriod.daily:
                if self.service == cloudlanguagetools.constants.Service.Naver:
                    if characters > NAVER_USER_DAILY_CHAR_LIMIT:
                        return True
                if characters > DEFAULT_USER_DAILY_CHAR_LIMIT:
                    return True
        return False


