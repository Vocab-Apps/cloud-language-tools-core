import os
import logging
import requests
import urllib.parse
import xml.dom.minidom

PRODUCT_CODE='LANGUAGE_TOOLS'
TRACKED_ITEM_CODE='thousand_chars'

class GetCheddarUtils():
    def __init__(self):
        self.user = os.environ['GETCHEDDAR_USER']
        self.api_key = os.environ['GETCHEDDAR_API_KEY']
    

    def report_customer_usage(self, customer_code):
        customer_code_encoded = urllib.parse.quote(customer_code)
        url = f'https://getcheddar.com/xml/customers/add-item-quantity/productCode/{PRODUCT_CODE}/code/{customer_code_encoded}/itemCode/{TRACKED_ITEM_CODE}'
        print(url)
        params = {'quantity': 123.45}
        response = requests.post(url, auth=(self.user, self.api_key), data=params)
        if response.status_code == 200:
            # success
            dom = xml.dom.minidom.parseString(response.content)
            pretty_xml_as_string = dom.toprettyxml(newl='')
            print(pretty_xml_as_string)
        else:
            print(response.content)

    def get_customer(self, customer_code):
        # /customers/get/productCode/MY_PRODUCT_CODE/code/MY_CUSTOMER_CODE
        customer_code_encoded = urllib.parse.quote(customer_code)
        url = f'https://getcheddar.com/xml/customers/get/productCode/{PRODUCT_CODE}/code/{customer_code_encoded}'
        print(url)
        response = requests.get(url, auth=(self.user, self.api_key))
        if response.status_code == 200:
            # success
            dom = xml.dom.minidom.parseString(response.content)
            pretty_xml_as_string = dom.toprettyxml(newl='')
            print(pretty_xml_as_string)
        else:
            print(response.content)

if __name__ == '__main__':

    logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', 
                        datefmt='%Y%m%d-%H:%M:%S',
                        level=logging.INFO)

    cheddar_utils = GetCheddarUtils()
    customer_code = 'languagetools+customer2@mailc.net '
    cheddar_utils.report_customer_usage(customer_code)
    # cheddar_utils.get_customer(customer_code)