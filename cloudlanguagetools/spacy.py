import spacy
import logging
import os

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.languages
import cloudlanguagetools.tokenization

class SpacyTokenization(cloudlanguagetools.tokenization.Tokenization):
    def __init__(self, language, model_name, variant=None):
        self.language = language
        self.service = cloudlanguagetools.constants.Service.Spacy
        self.model_name = model_name
        self.variant = variant

    def get_tokenization_name(self):
        if self.variant != None:
            result = f'{self.language.lang_name} ({self.variant}), {self.service.name}'
        else:
            result = f'{self.language.lang_name}, {self.service.name}'
        return result

    def get_tokenization_key(self):
        return {
            'model_name': self.model_name
        }

class SpacyService(cloudlanguagetools.service.Service):
    def __init__(self):
        self.nlp_engine_cache = {}
        os.environ["TOKENIZERS_PARALLELISM"] = "false"

    def preload_data(self):
        # pre-load nlp engines (to test ram utilization)
        for tokenization_option in self.get_tokenization_options():
            model_name = tokenization_option.get_tokenization_key()['model_name']
            nlp_engine = self.get_nlp_engine(model_name)
        

    def build_nlp_engine(self, model_name):
        import spacy.lang.zh
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

        logging.info(f'loading model {model_name}')
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
            SpacyTokenization(cloudlanguagetools.languages.Language.en, 'en_core_web_trf'),
            SpacyTokenization(cloudlanguagetools.languages.Language.fr, 'fr_dep_news_trf'),
            SpacyTokenization(cloudlanguagetools.languages.Language.ja, 'ja_core_news_lg'),
            SpacyTokenization(cloudlanguagetools.languages.Language.de, 'de_dep_news_trf'),
            SpacyTokenization(cloudlanguagetools.languages.Language.es, 'es_dep_news_trf'),
            SpacyTokenization(cloudlanguagetools.languages.Language.ru, 'ru_core_news_lg'),
            SpacyTokenization(cloudlanguagetools.languages.Language.pl, 'pl_core_news_lg'),
            SpacyTokenization(cloudlanguagetools.languages.Language.it, 'it_core_news_lg'),

        ]
        chinese_language_list = [
            cloudlanguagetools.languages.Language.zh_cn,
            cloudlanguagetools.languages.Language.zh_tw,
            cloudlanguagetools.languages.Language.yue
        ]
        for language in chinese_language_list:
            # chinese variants
            result.extend([
                SpacyTokenization(language, 'chinese_char', 'Characters'),
                SpacyTokenization(language, 'chinese_jieba', 'Jieba (words)'),
                SpacyTokenization(language, 'chinese_jieba', 'PKUSeg (words)')
            ])
        return result