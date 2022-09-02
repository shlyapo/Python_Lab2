# Always prefer setuptools over distutils
from setuptools import setup, find_packages

# To use a consistent encoding
from codecs import open
from os import path

# The directory containing this file
HERE = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(HERE, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="shlseril",
    version="15.2.3",
    description="Demo library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/shlyapo?tab=repositories",
    author="shlyapo",
    author_email="shlyapoelizzz@gmail.com",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent"
    ],
    packages=find_packages(),
    include_package_data=True,

)
