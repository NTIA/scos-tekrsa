from os import path
from setuptools import setup, find_packages

with open("README.md", "r", encoding='utf-8') as fh:
    long_description = fh.read()

repo_root = path.dirname(path.realpath(__file__))
requirements_path = repo_root + "/requirements.txt"
install_requires = []  # Examples: ["gunicorn", "docutils>=0.3", "lxml==0.5a7"]
if path.isfile(requirements_path):
    with open(requirements_path) as f:
        lines = f.read().splitlines()
        for line in lines:
            install_requires.append(path.expandvars(line))

setup(
    name="scos_tekrsa",
    version="0.0.0",
    author="The Institute for Telecommunication Sciences",
    # author_email="author@example.com",
    description="Tektronix RSA support for scos-sensor",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/NTIA/scos-tekrsa",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        # "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=install_requires,
    package_data={"scos_tekrsa": ["configs/*.example",
                                  "configs/actions*/*.yml"]},
)
