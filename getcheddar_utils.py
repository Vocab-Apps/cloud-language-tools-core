import os
import logging
import requests
import urllib.parse
import xml.dom.minidom
import xml.etree.ElementTree
import pprint

PRODUCT_CODE='LANGUAGE_TOOLS'
TRACKED_ITEM_CODE='thousand_chars'

class GetCheddarUtils():
    def __init__(self):
        self.user = os.environ['GETCHEDDAR_USER']
        self.api_key = os.environ['GETCHEDDAR_API_KEY']

    def decode_webhook(self, data):
        activity_type = data['activityType']
        overage_allowed = data['subscription']['plan']['items'][0]['overageAmount'] != '0.00' and activity_type != 'subscriptionCanceled'
        return {
            'type': activity_type,
            'code': data['customer']['code'],
            'email': data['customer']['email'],
            'thousand_char_quota': data['subscription']['plan']['items'][0]['quantityIncluded'],
            'thousand_char_overage_allowed': overage_allowed,
            'thousand_char_used': data['subscription']['invoice']['items'][0]['quantity']
        }


    def decode_customer_xml(self, xml_str):
        root = xml.etree.ElementTree.fromstring(xml_str)

        customer_code = root.find('./customer').attrib['code']
        customer_email = root.find('./customer/email').text

        quantity_included = int(root.find('./customer/subscriptions/subscription[1]/plans/plan[1]/items/item[@code="thousand_chars"]/quantityIncluded').text)
        overage_amount = float(root.find('./customer/subscriptions/subscription[1]/plans/plan[1]/items/item[@code="thousand_chars"]/overageAmount').text)
        overage_allowed = overage_amount > 0
        current_usage = float(root.find('./customer/subscriptions/subscription[1]/items/item[@code="thousand_chars"]/quantity').text)

        return {
            'code': customer_code,
            'email': customer_email,
            'thousand_char_quota': quantity_included,
            'thousand_char_overage_allowed': overage_allowed,
            'thousand_char_used': current_usage,
        }


    def print_xml_response(self, content):
        dom = xml.dom.minidom.parseString(content)
        pretty_xml_as_string = dom.toprettyxml(newl='')
        f = open('getcheddar_response.xml', 'w')
        f.write(pretty_xml_as_string)
        f.close()
        # print(pretty_xml_as_string)

    def report_customer_usage(self, customer_code):
        customer_code_encoded = urllib.parse.quote(customer_code)
        url = f'https://getcheddar.com/xml/customers/add-item-quantity/productCode/{PRODUCT_CODE}/code/{customer_code_encoded}/itemCode/{TRACKED_ITEM_CODE}'
        print(url)
        params = {'quantity': 1.01}
        response = requests.post(url, auth=(self.user, self.api_key), data=params)
        if response.status_code == 200:
            # success
            self.print_xml_response(response.content)
            print(self.decode_customer_xml(response.content))
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
            self.print_xml_response(response.content)
            print(self.decode_customer_xml(response.content))
        else:
            print(response.content)



if __name__ == '__main__':

    logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', 
                        datefmt='%Y%m%d-%H:%M:%S',
                        level=logging.INFO)

    cheddar_utils = GetCheddarUtils()
    customer_code = 'languagetools+customer4@mailc.net'
    cheddar_utils.report_customer_usage(customer_code)
    # cheddar_utils.get_customer(customer_code)