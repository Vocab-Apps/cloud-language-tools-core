import unittest
import quotas
import datetime

import cloudlanguagetools.constants

class TestQuotas(unittest.TestCase):
    def test_quotas_global(self):
        usage_slice_monthly_global = quotas.UsageSlice(
            cloudlanguagetools.constants.RequestType.audio,
            cloudlanguagetools.constants.UsageScope.Global, 
            cloudlanguagetools.constants.UsagePeriod.monthly, 
            cloudlanguagetools.constants.Service.Azure,
            'api_key_1')
        self.assertEqual(usage_slice_monthly_global.over_quota(200000, 30000), False)

        usage_slice_daily_global = quotas.UsageSlice(
            cloudlanguagetools.constants.RequestType.audio,
            cloudlanguagetools.constants.UsageScope.Global, 
            cloudlanguagetools.constants.UsagePeriod.daily, 
            cloudlanguagetools.constants.Service.Azure,
            'api_key_2')
        self.assertEqual(usage_slice_monthly_global.over_quota(200000, 30000), False)



    def test_quotas_user(self):
        usage_slice_monthly_user = quotas.UsageSlice(
            cloudlanguagetools.constants.RequestType.audio,
            cloudlanguagetools.constants.UsageScope.User, 
            cloudlanguagetools.constants.UsagePeriod.monthly, 
            cloudlanguagetools.constants.Service.Azure,
            'api_key_1')
        self.assertEqual(usage_slice_monthly_user.over_quota(300000, 30000), False)

        usage_slice_daily_user = quotas.UsageSlice(
            cloudlanguagetools.constants.RequestType.audio,
            cloudlanguagetools.constants.UsageScope.User, 
            cloudlanguagetools.constants.UsagePeriod.daily, 
            cloudlanguagetools.constants.Service.Azure,
            'api_key_2')
        self.assertEqual(usage_slice_daily_user.over_quota(50000, 30000), False)
        self.assertEqual(usage_slice_daily_user.over_quota(200000, 30000), True)

    def test_quotas_user_naver(self):
        usage_slice_daily_user = quotas.UsageSlice(
            cloudlanguagetools.constants.RequestType.audio,
            cloudlanguagetools.constants.UsageScope.User, 
            cloudlanguagetools.constants.UsagePeriod.daily, 
            cloudlanguagetools.constants.Service.Naver,
            'api_key_3')
        self.assertEqual(usage_slice_daily_user.over_quota(29900, 30000), False)
        self.assertEqual(usage_slice_daily_user.over_quota(30100, 30000), True)

    def test_build_key_suffix(self):
        # clt:usage:user:daily:20210209:Naver:audio:zrrVDK3svzDOLzI6

        usage_slice_daily_user = quotas.UsageSlice(
            cloudlanguagetools.constants.RequestType.audio,
            cloudlanguagetools.constants.UsageScope.User, 
            cloudlanguagetools.constants.UsagePeriod.daily, 
            cloudlanguagetools.constants.Service.Naver,
            'zrrVDK3svzDOLzI6')
        
        date_str = datetime.datetime.today().strftime('%Y%m%d')
        self.assertEqual(usage_slice_daily_user.build_key_suffix(), f'user:daily:{date_str}:Naver:audio:zrrVDK3svzDOLzI6')

        # clt:usage:user:monthly:202102:Azure:audio:zrrVDK3svzDOLzI6
        usage_slice_monthly_user = quotas.UsageSlice(
            cloudlanguagetools.constants.RequestType.audio,
            cloudlanguagetools.constants.UsageScope.User, 
            cloudlanguagetools.constants.UsagePeriod.monthly, 
            cloudlanguagetools.constants.Service.Azure,
            'zrrVDK3svzDOLzI6')
        
        date_str = datetime.datetime.today().strftime('%Y%m')
        self.assertEqual(usage_slice_monthly_user.build_key_suffix(), f'user:monthly:{date_str}:Azure:audio:zrrVDK3svzDOLzI6')

        # clt:usage:global:monthly:202102:Amazon:audio
        usage_slice_monthly_global = quotas.UsageSlice(
            cloudlanguagetools.constants.RequestType.audio,
            cloudlanguagetools.constants.UsageScope.Global, 
            cloudlanguagetools.constants.UsagePeriod.monthly, 
            cloudlanguagetools.constants.Service.Amazon,
            'zrrVDK3svzDOLzI6')
        
        date_str = datetime.datetime.today().strftime('%Y%m')
        self.assertEqual(usage_slice_monthly_global.build_key_suffix(), f'global:monthly:{date_str}:Amazon:audio')

        # clt:usage:global:daily:20210205:MandarinCantonese:transliteration
        usage_slice_monthly_user = quotas.UsageSlice(
            cloudlanguagetools.constants.RequestType.transliteration,
            cloudlanguagetools.constants.UsageScope.Global, 
            cloudlanguagetools.constants.UsagePeriod.daily, 
            cloudlanguagetools.constants.Service.MandarinCantonese,
            'zrrVDK3svzDOLzI6')
        
        date_str = datetime.datetime.today().strftime('%Y%m%d')
        self.assertEqual(usage_slice_monthly_user.build_key_suffix(), f'global:daily:{date_str}:MandarinCantonese:transliteration')

        # clt:usage:user:lifetime:zrrVDK3svzDOLzI6
        usage_slice_lifetime_user = quotas.UsageSlice(
            cloudlanguagetools.constants.RequestType.audio,
            cloudlanguagetools.constants.UsageScope.User, 
            cloudlanguagetools.constants.UsagePeriod.lifetime, 
            cloudlanguagetools.constants.Service.Azure,
            'zrrVDK3svzDOLzI6')

        self.assertEqual(usage_slice_lifetime_user.build_key_suffix(), f'user:lifetime:zrrVDK3svzDOLzI6')