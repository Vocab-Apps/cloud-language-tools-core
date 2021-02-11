import unittest
import quotas

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