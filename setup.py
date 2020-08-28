import os

from setuptools import setup

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django_widgets',
    version='1.0.' + os.getenv('BUILD_NUMBER', '1'),
    packages=['django_widgets'],
    include_package_data=True,
    install_requires=[
        'django'
    ]
)
