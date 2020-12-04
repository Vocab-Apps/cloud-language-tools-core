from setuptools import setup

# build instructions
# python setup.py sdist
# python setup.py sdist upload

setup(name='cloud-language-tools',
      version='0.1',
      description='Interface with various cloud APIs for language processing such as translation, text to speech',
      long_description=open('README.rst', encoding='utf-8').read(),
      url='https://github.com/lucwastiaux/cloud-language-tools',
      author='Luc Wastiaux',
      author_email='lucw@airpost.net',
      classifiers=[
        'Programming Language :: Python :: 3.8',
        'Topic :: Text Processing :: Linguistic',
      ],      
      license='GPL',
      packages=['cloudlanguagetools'],
      install_requires=[
          #'jieba',
      ])