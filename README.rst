# cloud-language-tools
Interface with various cloud APIs for translation, text to speech


## encryption
encrypting:
gpg --batch --yes --passphrase-file gpg_passphrase_file --output tts_keys.sh.gpg --symmetric tts_keys.sh

decrypting:
gpg --batch --yes --passphrase-file gpg_passphrase_file --output tts_keys.sh.test_decrypt  --decrypt tts_keys.sh.gpg


# regenerate requirements_frozen.txt
pip freeze | grep -v -E 'en-core-web-trf|zh-core-web-trf|fr-dep-news-trf|patreon' > requirements_frozen.txt