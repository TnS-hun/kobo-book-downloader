import os

from setuptools import find_packages, setup

setup(
    name='kobodl',
    author='Brandon Davis',
    version='0.3.0',
    author_email='kobodl@subdavis.com',
    url="https://github.com/subdavis/kobo-book-downloader",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click',
        'colorama',
        'dataclasses',
        'dataclasses-json',
        'flask',
        'pycryptodome',
        'requests',
        'tabulate',
    ],
    license='MIT',
    entry_points={'console_scripts': ['kobodl = kobodl:cli'],},
    python_requires='>=3.6',
    setup_requires=['setuptools-git'],
)
