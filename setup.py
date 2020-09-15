import os
from io import open

from setuptools import setup

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-widgets-engine',
    version='1.0.1',
    packages=['django_widgets'],
    include_package_data=True,
    license='BSD',
    description='Custom widgets for Django templates',
    long_description=open('README.md', 'r', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/LeonLegion/django-widgets',
    author='Leonid Evstigneev',
    author_email='mail@leonidevstigneev.ru',
    keywords='django widget template jinja2',
    install_requires=[
        'django'
    ],
    classifiers=[
      'Development Status :: 5 - Production/Stable',
      'Framework :: Django',
      'Intended Audience :: Developers',
      'Programming Language :: Python',
      'Programming Language :: Python :: 3',
      'Topic :: Software Development :: Libraries :: Python Modules'
  ],
)
