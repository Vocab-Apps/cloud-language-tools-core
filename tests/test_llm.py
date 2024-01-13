import os
import sys
import logging
import unittest
import pytest
import json
import pprint

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cloudlanguagetools
import cloudlanguagetools.servicemanager
import cloudlanguagetools.errors

def get_manager():
    manager = cloudlanguagetools.servicemanager.ServiceManager()
    manager.configure_default()
    return manager

class TestTranslation(unittest.TestCase):
    def setUp(self):
        self.manager = get_manager()


    def sanitize_text(self, translation_text):
        result_text = translation_text.replace('.', '').\
            replace(',', '').\
            replace('。', '').\
            replace('?', '').\
            replace('？', '').\
            replace('您', '你').\
            replace(':', '').lower()
        return result_text

    def test_single_prompt(self):
        prompt = 'translate to French: speak slowly please.'
        response, tokens = self.manager.openai_single_prompt(prompt)
        self.assertIn(self.sanitize_text(response),
                      [
                         self.sanitize_text("Parlez lentement s'il vous plaît."),
                         self.sanitize_text("parle lentement s'il te plaît") 
                      ])

    def test_full_query(self):
        # pytest --log-cli-level=DEBUG tests/test_llm.py -k test_full_query
        messages = [
                {"role": "system", "content": "You are a friendly assistant who will translate languages"},
                {"role": "user", "content": "translate into english: 成本很低"},
        ]
        response = self.manager.openai_full_query(messages)
        new_message = response.choices[0].message
        # pprint.pprint(new_message)
        messages.append(new_message)
        messages.append({
            'role': 'user',
            'content': 'take the last message  and translate into French.'
        })
        pprint.pprint(messages)
        response = self.manager.openai_full_query(messages)
        pprint.pprint(response)
        new_message = response.choices[0].message
        pprint.pprint(new_message)
        sanitized_output = self.sanitize_text(new_message.content)
        self.assertTrue(self.sanitize_text('coût') in sanitized_output, f'output: [{sanitized_output}]')
        self.assertTrue(self.sanitize_text('faible') in sanitized_output or self.sanitize_text('bas') in sanitized_output, 
            f'output: [{sanitized_output}]')