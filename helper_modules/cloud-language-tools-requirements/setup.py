from setuptools import setup

# build instructions
# python setup.py sdist
# twine upload dist/*

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(name='clt_requirements',
      version='1.4',
      description='Helper module for Cloud Language Tools, additional dependencies',
      url='https://github.com/Language-Tools/cloud-language-tools-core',
      author='Luc',
      author_email='languagetools@mailc.net',
      classifiers=[
        'Programming Language :: Python :: 3.11',
        'Topic :: Text Processing :: Linguistic',
      ],      
      license='GPL',
      packages=['clt_requirements'],
      install_requires=requirements,
      )
