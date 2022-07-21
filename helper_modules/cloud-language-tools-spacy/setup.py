from setuptools import setup
from setuptools.command.install import install

# build instructions
# python setup.py sdist
# twine upload dist/*

def post_installation():
    import clt_spacy
    clt_spacy.install_all_packages()

class PostInstallCommand(install):
    """Post-installation for installation mode."""

    def run(self):
        install.run(self)
        post_installation()


setup(name='clt_spacy',
      version='0.1',
      description='Helper module for Cloud Language Tools, install spacy and language packages',
      url='https://github.com/Language-Tools/cloud-language-tools-core',
      author='Luc',
      author_email='languagetools@mailc.net',
      classifiers=[
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Text Processing :: Linguistic',
      ],      
      license='GPL',
      packages=['clt_spacy'],
      install_requires=[
          'spacy',
      ],
      cmdclass={
          'install': PostInstallCommand
      }      
      )