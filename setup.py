import os

from setuptools import find_packages, setup

setup(
    name='kobo-book-downloader',
    author='Brandon Davis',
    version='0.0.1',
    author_email='kobo-book-downloader@subdavis.com',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click',
        'colorama',
        'dataclasses',
        'flask',
        'pycryptodome',
        'requests',
        'tabulate',
    ],
    license='MIT',
    entry_points={
        'console_scripts': ['kobodl = kobo_book_downloader:cli'],
    },
    setup_requires=['setuptools-git'],
)
