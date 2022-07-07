from setuptools import setup
from setuptools.command.install import install

# build instructions
# python setup.py sdist
# twine upload dist/*

def post_installation():
    import spacy
    import spacy.cli
    spacy.cli.download('zh_core_web_trf')
    spacy.cli.download('en_core_web_trf')
    spacy.cli.download('fr_dep_news_trf')
    spacy.cli.download('ja_core_news_lg')
    spacy.cli.download('de_dep_news_trf')
    spacy.cli.download('es_dep_news_trf')
    spacy.cli.download('ru_core_news_lg')
    spacy.cli.download('pl_core_news_lg')
    spacy.cli.download('it_core_news_lg')    


class PostInstallCommand(install):
    """Post-installation for installation mode."""

    def run(self):
        install.run(self)
        post_installation()


setup(name='cloudlanguagetools',
      version='0.2',
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
      ],
      cmdclass={
          'install': PostInstallCommand
      }      
      )