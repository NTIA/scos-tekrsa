from os import path

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

repo_root = path.dirname(path.realpath(__file__))
requirements_path = repo_root + "/requirements.in"
install_requires = []
if path.isfile(requirements_path):
    with open(requirements_path) as f:
        lines = f.read().splitlines()
        for line in lines:
            install_requires.append(path.expandvars(line))

setup(
    name="scos_tekrsa",
    version="1.0.0",
    author="The Institute for Telecommunication Sciences",
    description="Tektronix RSA support for scos-sensor",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/NTIA/scos-tekrsa",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.7",
    install_requires=install_requires,
    package_data={"scos_tekrsa": ["configs/*example.json", "configs/actions*/*.yml"]},
)
