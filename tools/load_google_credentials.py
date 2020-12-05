import json
import base64
import os


def encode():
    json_path = '/mnt/d/storage/dev/account_keys/cloudlanguagetools.json'

    with open(json_path) as json_file:
        data = json.load(json_file)
        s = json.dumps(data) 
        result = base64.b64encode(s.encode('utf-8'))
        print(result)

def decode():
    key = os.environ['GOOGLE_KEY']
    data_bytes = base64.b64decode(key)
    data_str = data_bytes.decode('utf-8')
    print(data_str)


if __name__ == '__main__':
    # encode()
    decode()



