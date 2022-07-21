from setuptools import setup

# build instructions
# python setup.py sdist
# twine upload dist/*

setup(name='clt_requirements',
      version='0.1',
      description='Helper module for Cloud Language Tools, additional dependencies',
      url='https://github.com/Language-Tools/cloud-language-tools-core',
      author='Luc',
      author_email='languagetools@mailc.net',
      classifiers=[
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Text Processing :: Linguistic',
      ],      
      license='GPL',
      packages=['clt_requirements'],
      install_requires=[
          'azure-cognitiveservices-speech',
          'requests',
          'google-cloud-texttospeech',
          'google-cloud-translate',
          'boto3',
          'epitran',
          'pythainlp[thai2rom,ipa]',
          'jieba',
          'pinyin_jyutping_sentence',
          'cryptography',
          'pydub'
      ],
      )