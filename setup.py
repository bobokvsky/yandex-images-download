from setuptools import setup, find_packages
from codecs import open
from os import path

__version__ = 'v1.0.4'

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
    version=__version__,
    license='MIT',
    description="Python Script to download images from Yandex.Images",
    long_description=long_description,
    long_description_content_type='text/markdown',
    author = 'Alexander Kozlov',
    author_email='alexander.kozlovsky.m@gmail.com',
    url='https://github.com/bobokvsky/yandex-images-download',
    download_url = f'https://github.com/bobokvsky/yandex-images-download/archive/{__version__}.tar.gz',
    keywords='yandex images download save terminal command-line scrapper',
    install_requires=install_requires,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
    ],
    entry_points={
        "console_scripts": [
            'yandex-images-download = yandex_images_download:run_main'
        ]
    }
)
