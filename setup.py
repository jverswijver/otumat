import setuptools
import pathlib
import otumat as package

setuptools.setup(
    name=package.__name__,
    version=package.__version__,
    author="Raphael Guzman",
    author_email="raphael.h.guzman@gmail.com",
    description="A suite of maintainer tools and utilities for pip packages.",
    long_description=pathlib.Path('README.md').read_text(),
    long_description_content_type="text/markdown",
    url="https://github.com/datajoint/otumat",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "distutils.setup_keywords": [
            "privkey_path = {}:assert_string".format(package.__name__),
            "pubkey_path = {}:assert_string".format(package.__name__),
        ],
        "egg_info.writers": [
            ".sig = {}:write_arg".format(package.__name__),
            ".pub = {}:write_arg".format(package.__name__),
        ],
        'console_scripts': [
            f'{package.__name__}={package.__name__}.command_line:{package.__name__}'],
    },
    install_requires=['cryptography<=3.3.2', 'flask', 'appdirs'],
)
