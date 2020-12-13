import unittest
import json
from app import app

class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(ApiTests, cls).setUpClass()
        cls.client = app.test_client()

    def test_language_list(self):
        response = self.client.get('/language_list')
        actual_language_list = json.loads(response.data) 
        self.assertTrue('fr' in actual_language_list)
        self.assertEqual(actual_language_list['fr'], 'French')
        self.assertEqual(actual_language_list['yue'], 'Chinese (Cantonese, Traditional)')
        self.assertEqual(actual_language_list['zh_cn'], 'Chinese (Simplified)')

    def test_voice_list(self):
        response = self.client.get('/voice_list')
        voice_list = json.loads(response.data)
        self.assertTrue(len(voice_list) > 100) # with google and azure, we already have 400 voices or so
        

if __name__ == '__main__':
    unittest.main()  


#rv = client.get('/jyutping/我哋盪失咗')
#print(rv.data)

#url_base = "http://localhost:5000"
#url = "{}/jyutping/我哋盪失咗".format(url_base)
#response = requests.get(url)
#print(json.loads(response.content)["jyutping"])
