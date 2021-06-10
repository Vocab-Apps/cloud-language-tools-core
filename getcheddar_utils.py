import os
import logging
import requests
import urllib.parse
import xml.dom.minidom
import xml.etree.ElementTree
import pprint
import datetime

TRACKED_ITEM_CODE='thousand_chars'

class GetCheddarUtils():
    def __init__(self):
        self.product_code = os.environ['GETCHEDDAR_PRODUCT_CODE']
        self.user = os.environ['GETCHEDDAR_USER']
        self.api_key = os.environ['GETCHEDDAR_API_KEY']

    def get_api_secret(self):
        return self.api_key

    def decode_webhook(self, data):
        activity_type = data['activityType']
        overage_allowed = data['subscription']['plan']['items'][0]['overageAmount'] != '0.00' and activity_type != 'subscriptionCanceled'
        return {
            'type': activity_type,
            'code': data['customer']['code'],
            'email': data['customer']['email'],
            'thousand_char_quota': data['subscription']['plan']['items'][0]['quantityIncluded'],
            'thousand_char_overage_allowed': int(overage_allowed == True),
            'thousand_char_used': data['subscription']['invoice']['items'][0]['quantity']
        }


    def decode_customer_xml(self, xml_str):
        root = xml.etree.ElementTree.fromstring(xml_str)

        customer_code = root.find('./customer').attrib['code']
        customer_email = root.find('./customer/email').text

        quantity_included = int(root.find('./customer/subscriptions/subscription[1]/plans/plan[1]/items/item[@code="thousand_chars"]/quantityIncluded').text)
        overage_amount = float(root.find('./customer/subscriptions/subscription[1]/plans/plan[1]/items/item[@code="thousand_chars"]/overageAmount').text)
        canceled_date = root.find('./customer/subscriptions/subscription[1]/canceledDatetime').text
        overage_allowed = overage_amount > 0 and canceled_date == None
        current_usage = float(root.find('./customer/subscriptions/subscription[1]/items/item[@code="thousand_chars"]/quantity').text)

        return {
            'code': customer_code,
            'email': customer_email,
            'thousand_char_quota': quantity_included,
            'thousand_char_overage_allowed': int(overage_allowed == True),
            'thousand_char_used': current_usage,
        }


    def print_xml_response(self, content):
        dom = xml.dom.minidom.parseString(content)
        pretty_xml_as_string = dom.toprettyxml(newl='')
        f = open('getcheddar_response.xml', 'w')
        f.write(pretty_xml_as_string)
        f.close()
        # print(pretty_xml_as_string)

    def report_customer_usage(self, customer_code, thousand_char_quantity):
        customer_code_encoded = urllib.parse.quote(customer_code)
        url = f'https://getcheddar.com/xml/customers/add-item-quantity/productCode/{self.product_code}/code/{customer_code_encoded}/itemCode/{TRACKED_ITEM_CODE}'
        print(url)
        params = {'quantity': thousand_char_quantity}
        response = requests.post(url, auth=(self.user, self.api_key), data=params)
        if response.status_code == 200:
            # success
            return self.decode_customer_xml(response.content)
        else:
            error_message = f'Could not report customer usage: {response.content}'
            raise Exception(error_message)

    def get_customer(self, customer_code):
        # /customers/get/productCode/MY_self.product_code/code/MY_CUSTOMER_CODE
        customer_code_encoded = urllib.parse.quote(customer_code)
        url = f'https://getcheddar.com/xml/customers/get/productCode/{self.product_code}/code/{customer_code_encoded}'
        print(url)
        response = requests.get(url, auth=(self.user, self.api_key))
        if response.status_code == 200:
            # success
            self.print_xml_response(response.content)
            print(self.decode_customer_xml(response.content))
        else:
            print(response.content)


    # for testing purposes
    # ====================

    def create_test_customer(self, code, email, first_name, last_name, plan):
        url = f'https://getcheddar.com/xml/customers/new/productCode/{self.product_code}'
        params = {
            'code': code,
            'email': email,
            'firstName': first_name,
            'lastName': last_name,
            'subscription[planCode]': plan,
            'subscription[ccFirstName]': first_name,
            'subscription[ccLastName]': last_name,
            'subscription[ccNumber]': '370000000000002',
            'subscription[ccCardCode]': '1234',
            'subscription[ccExpiration]': '04/2025'
        }
        response = requests.post(url, auth=(self.user, self.api_key), data=params)
        if response.status_code == 200:
            # success
            # self.print_xml_response(response.content)
            print(self.decode_customer_xml(response.content))
            logging.info(f'created customer {code}')
        else:
            print(response.content)        

    def update_test_customer(self, code, plan):
        customer_code_encoded = urllib.parse.quote(code)
        url = f'https://getcheddar.com/xml/customers/edit-subscription/productCode/{self.product_code}/code/{customer_code_encoded}'
        params = {
            'planCode': plan
        }
        response = requests.post(url, auth=(self.user, self.api_key), data=params)
        if response.status_code == 200:
            # success
            self.print_xml_response(response.content)
            print(self.decode_customer_xml(response.content))
        else:
            print(response.content)            

    def cancel_test_customer(self, code, plan):
        customer_code_encoded = urllib.parse.quote(code)
        url = f'https://getcheddar.com/xml/customers/cancel/productCode/{self.product_code}/code/{customer_code_encoded}'
        response = requests.post(url, auth=(self.user, self.api_key))
        if response.status_code == 200:
            # success
            self.print_xml_response(response.content)
            print(self.decode_customer_xml(response.content))
        else:
            print(response.content)            


    def delete_test_customer(self, code):
        # /customers/delete/productCode/MY_self.product_code/code/MY_CUSTOMER_CODE
        customer_code_encoded = urllib.parse.quote(code)
        url = f'https://getcheddar.com/xml/customers/delete/productCode/{self.product_code}/code/{customer_code_encoded}'
        response = requests.post(url, auth=(self.user, self.api_key))
        if response.status_code == 200:
            # success
            logging.info(f'customer {code} deleted')
        else:
            print(response.content)                    

    def delete_all_test_customers(self):
        # /customers/delete-all/confirm/[current unix timestamp]/productCode/MY_PRODUCT_CODE
        timestamp = int(datetime.datetime.now().timestamp())
        url = f'https://getcheddar.com/xml/customers/delete-all/confirm/{timestamp}/productCode/{self.product_code}'
        response = requests.post(url, auth=(self.user, self.api_key))
        if response.status_code == 200:
            # success
            logging.info('all test customers deleted')
        else:
            print(response.content)                    


if __name__ == '__main__':

    logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', 
                        datefmt='%Y%m%d-%H:%M:%S',
                        level=logging.INFO)

    cheddar_utils = GetCheddarUtils()
    customer_code = 'languagetools+customer5@mailc.net'
    # cheddar_utils.report_customer_usage(customer_code)
    # cheddar_utils.get_customer(customer_code)
    # cheddar_utils.create_test_customer('languagetools+customer5@mailc.net', 'languagetools+customer5@mailc.net', 'Luc', 'Customer5')
    # cheddar_utils.update_test_customer(customer_code, 'MEDIUM')
    # cheddar_utils.cancel_test_customer(customer_code, 'MEDIUM')
    # cheddar_utils.delete_all_test_customers()