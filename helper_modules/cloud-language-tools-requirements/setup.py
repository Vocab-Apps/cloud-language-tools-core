from setuptools import setup

# build instructions
# python setup.py sdist
# twine upload dist/*


setup(name='clt_requirements',
      version='2.0',
      description='Helper module for Cloud Language Tools, additional dependencies',
      url='https://github.com/Vocab-Apps/cloud-language-tools-core',
      author='Luc',
      author_email='languagetools@mailc.net',
      classifiers=[
        'Programming Language :: Python :: 3.12',
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
        'jieba',
        'cryptography',
        'pydub',
        'openai>=1.7.2',
        'pydantic',
        'cachetools',
        'clt_wenlin',
        'pinyin_jyutping'
      ],
      )
