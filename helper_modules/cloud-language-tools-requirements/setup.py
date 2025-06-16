from setuptools import setup

# build instructions
# python setup.py sdist
# twine upload dist/*


setup(name='clt_requirements',
      version='2.2',
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
        'google-genai',
        'boto3',
        'jieba',
        'cryptography',
        'pydub',
        'openai>=1.76.0',
        'pydantic',
        'cachetools',
        'clt_wenlin',
        'pinyin_jyutping'
      ],
      )
