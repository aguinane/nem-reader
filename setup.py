"""A setuptools based setup module.
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages

# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the version information
about = {}
ver_path = path.join(here, "nemreader", "version.py")
with open(ver_path) as ver_file:
    exec(ver_file.read(), about)

# Get the long description from the README file
try:
    with open(path.join(here, "README.md"), encoding="utf-8") as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = ""

setup(
    name="nemreader",
    version=about["__version__"],
    description="Parse NEM12 (interval metering data) and NEM13 (accumulated metering data) data files ",
    packages=find_packages(exclude=["contrib", "docs", "tests*"]),
    include_package_data=True,
    python_requires=">=3.6",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Alex Guinman",
    author_email="alex@guinman.id.au",
    url="https://github.com/aguinane/nem-reader",
    keywords=["energy", "NEM12", "NEM13"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=["click", "pandas"],
    tests_require=["pytest", "pytest-runner"],
    license="MIT",
    entry_points="""
        [console_scripts]
        nemreader=nemreader.cli:cli
    """,
)
