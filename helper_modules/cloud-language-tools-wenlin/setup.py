from setuptools import setup
from setuptools.command.install import install

# build instructions
# python setup.py sdist
# twine upload dist/*

def post_installation():
    import clt_wenlin
    clt_wenlin.download_wenlin_db()

class PostInstallCommand(install):
    """Post-installation for installation mode."""

    def run(self):
        install.run(self)
        post_installation()


setup(name='clt_wenlin',
      version='0.7',
      description='Helper module for Cloud Language Tools, download wenlin data',
      url='https://github.com/Language-Tools/cloud-language-tools-core',
      author='Luc',
      author_email='languagetools@mailc.net',
      classifiers=[
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Text Processing :: Linguistic',
      ],      
      license='GPL',
      packages=['clt_wenlin'],
      install_requires=[
      ],
      cmdclass={
          'install': PostInstallCommand
      }      
      )