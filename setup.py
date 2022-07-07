from setuptools import setup

# build instructions
# python setup.py sdist
# python setup.py sdist upload

setup(name='cloudlanguagetools',
      version='0.1',
      description='Interface with various cloud APIs for language processing such as translation, text to speech',
      long_description=open('README.rst', encoding='utf-8').read(),
      url='https://github.com/Language-Tools/cloud-language-tools-core',
      author='Luc',
      author_email='languagetools@mailc.net',
      classifiers=[
        'Programming Language :: Python :: 3.8',
        'Topic :: Text Processing :: Linguistic',
      ],      
      license='GPL',
      packages=['cloudlanguagetools'],
      install_requires=[
          'azure-cognitiveservices-speech',
          'requests',
          'google-cloud-texttospeech',
          'google-cloud-translate',
          'boto3',
          'epitran',
          'pythainlp[thai2rom,ipa]',
          'spacy',
          'jieba',
          'pinyin_jyutping_sentence',
          'cryptography'
      ])