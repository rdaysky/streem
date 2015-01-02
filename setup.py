from distutils.core import setup

setup(
    name = "streem",
    packages = ["streem"],
    version = "1.0",
    description = "Turning streams into trees",
    author = "Roman Odaisky",
    author_email = "roma@qwertty.com",
    url = "https://github.com/rdaysky/streem",
    download_url = "https://github.com/rdaysky/streem/tarball/1.0",
    keywords = ["stream", "tree"],
    install_requires = ["more_itertools"],
    classifiers = [
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development",
    ],
)
