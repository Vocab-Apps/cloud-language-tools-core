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
        models = ['en_core_web_trf', 'fr_dep_news_trf']
        for model in models:
            logging.info(f'loading spacy model {model}')
            self.nlp_engine_cache[model] = spacy.load(model)

        # initialize chinese models
        self.nlp_engine_cache['chinese_char'] = spacy.lang.zh.Chinese()
        self.nlp_engine_cache['chinese_jieba'] = spacy.lang.zh.Chinese.from_config({"nlp": {"tokenizer": {"segmenter": "jieba"}}})
        self.nlp_engine_cache['chinese_pkuseg'] = spacy.lang.zh.Chinese.from_config({"nlp": {"tokenizer": {"segmenter": "pkuseg"}}})

        

    def get_tokenization(self, text, tokenization_key):
        model_name = tokenization_key['model_name']
        nlp_engine = self.nlp_engine_cache[model_name]

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
            SpacyTokenization(cloudlanguagetools.constants.Language.en, 'en_core_web_trf'),
            SpacyTokenization(cloudlanguagetools.constants.Language.fr, 'fr_dep_news_trf'),

            # chinese variants
            SpacyTokenization(cloudlanguagetools.constants.Language.zh_cn, 'chinese_char', 'Characters'),
            SpacyTokenization(cloudlanguagetools.constants.Language.zh_cn, 'chinese_jieba', 'Jieba (words)'),
            SpacyTokenization(cloudlanguagetools.constants.Language.zh_cn, 'chinese_jieba', 'PKUSeg (words)'),
        ]
        return result