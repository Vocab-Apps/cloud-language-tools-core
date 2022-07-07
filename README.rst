# cloud-language-tools
Interface with various cloud APIs for translation, text to speech


## encryption
encrypting:
gpg --batch --yes --passphrase-file gpg_passphrase_file --output tts_keys.sh.gpg --symmetric tts_keys.sh

decrypting:
gpg --batch --yes --passphrase-file gpg_passphrase_file --output tts_keys.sh.test_decrypt  --decrypt tts_keys.sh.gpg


# regenerate requirements_frozen.txt
pip freeze | grep -v -E 'en-core-web-trf|zh-core-web-trf|fr-dep-news-trf|de-dep-news-trf|es-dep-news-trf|it-core-news-lg|ja-core-news-lg|pl-core-news-lg|ru-core-news-lg|patreon' > requirements_frozen.txt

# for building
see package.sh


# additional modules for spacy

python -m spacy download zh_core_web_trf
python -m spacy download en_core_web_trf
python -m spacy download fr_dep_news_trf
python -m spacy download ja_core_news_lg
python -m spacy download de_dep_news_trf
python -m spacy download es_dep_news_trf
python -m spacy download ru_core_news_lg
python -m spacy download pl_core_news_lg
python -m spacy download it_core_news_lg