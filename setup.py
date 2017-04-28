from distutils.core import setup

VERSION = "1.1"

setup(
    name = "streem",
    packages = ["streem"],
    version = VERSION,
    description = "Turning streams into trees",
    author = "Roman Odaisky",
    author_email = "roma@qwertty.com",
    url = "https://github.com/rdaysky/streem",
    download_url = "https://github.com/rdaysky/streem/archive/v%s.tar.gz" % VERSION,
    keywords = ["stream", "tree"],
    install_requires = ["more_itertools"],
    classifiers = [
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development",
    ],
)
