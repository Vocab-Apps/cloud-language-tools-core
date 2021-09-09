import spacy
import spacy.lang.zh
import logging

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.tokenization


class SpacyTokenization(cloudlanguagetools.tokenization.Tokenization):
    def __init__(self, language, model_name, variant=None):
        self.language = language
        self.service = cloudlanguagetools.constants.Service.Spacy
        self.model_name = model_name
        self.variant = variant

    def get_tokenization_name(self):
        if self.variant != None:
            result = f'{self.language.lang_name} ({self.variant}) {self.service.name}'
        else:
            result = f'{self.language.lang_name} {self.service.name}'
        return result

    def get_tokenization_key(self):
        return {
            'model_name': self.model_name
        }

class SpacyService(cloudlanguagetools.service.Service):
    def __init__(self):
        self.nlp_engine_cache = {}

    def build_nlp_engine(self, model_name):
        if model_name == 'chinese_char':
            return spacy.lang.zh.Chinese()
        if model_name == 'chinese_jieba':
            return spacy.lang.zh.Chinese.from_config({"nlp": {"tokenizer": {"segmenter": "jieba"}}})
        if model_name == 'chinese_pkuseg':
            return spacy.lang.zh.Chinese.from_config({"nlp": {"tokenizer": {"segmenter": "pkuseg"}}})
        return spacy.load(model_name)        

    def get_nlp_engine(self, model_name):
        if model_name in self.nlp_engine_cache:
            return self.nlp_engine_cache[model_name]

        nlp_engine = self.build_nlp_engine(model_name)
        self.nlp_engine_cache[model_name] = nlp_engine
        return nlp_engine

    def get_tokenization(self, text, tokenization_key):
        model_name = tokenization_key['model_name']
        nlp_engine = self.get_nlp_engine(model_name)

        doc = nlp_engine(text)
        result = []
        for token in doc:
            lemma = token.lemma_
            if len(lemma) == 0:
                lemma = str(token)
            pos_description = spacy.explain(token.tag_)
            entry = {
                'token': str(token),
                'lemma': lemma,
                'can_translate': token.is_alpha,
                'can_transliterate': token.is_alpha
            }
            if pos_description != None:
                entry['pos_description'] = pos_description
            result.append(entry)
        return result

        # raise exception
        raise cloudlanguagetools.errors.RequestError(f'unsupported tokenization mode: {mode.name}')


    def get_tokenization_options(self):
        result = [
            SpacyTokenization(cloudlanguagetools.constants.Language.en, 'en_core_web_md'),
            SpacyTokenization(cloudlanguagetools.constants.Language.fr, 'fr_core_news_md'),

            # chinese variants
            SpacyTokenization(cloudlanguagetools.constants.Language.zh_cn, 'chinese_char', 'Characters'),
            SpacyTokenization(cloudlanguagetools.constants.Language.zh_cn, 'chinese_jieba', 'Jieba (words)'),
            SpacyTokenization(cloudlanguagetools.constants.Language.zh_cn, 'chinese_jieba', 'PKUSeg (words)'),
        ]
        return result