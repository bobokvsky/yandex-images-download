from setuptools import setup, find_packages
from codecs import open
from os import path

__version__ = '2.8.0'

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

# get the dependencies and installs
with open(path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    all_reqs = f.read().split('\n')

install_requires = [x.strip() for x in all_reqs]

setup(
    name='yandex_images_download',
    packages=['yandex_images_download'],
    version='v1.0',
    license='MIT',
    description="Python Script to download images from Yandex.Images",
    long_description=long_description,
    author = 'Alexander Kozlov',
    author_email='alexander.kozlovsky.m@gmail.com',
    url='https://github.com/bobokvsky/yandex-images-download',
    download_url = 'https://github.com/bobokvsky/yandex-images-download/archive/v1.0.tar.gz',    # I explain this later on
    keywords='yandex images download save terminal command-line scrapper',
    install_requires=install_requires,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
    ]
)
