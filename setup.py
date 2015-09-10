from distutils.core import setup

setup(
    name = "streem",
    packages = ["streem"],
    version = "1.0.2",
    description = "Turning streams into trees",
    author = "Roman Odaisky",
    author_email = "roma@qwertty.com",
    url = "https://github.com/rdaysky/streem",
    download_url = "https://github.com/rdaysky/streem/archive/v1.0.2.tar.gz",
    keywords = ["stream", "tree"],
    install_requires = ["more_itertools"],
    classifiers = [
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development",
    ],
)
