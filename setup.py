from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="gac",
    version="1.0.0",
    author="GAC Team",
    author_email="user@example.com",
    description="Git Auto Commit - Automatically commit local folders to GitHub",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/user/gac",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",  # Linux only
    ],
    python_requires=">=3.6",
    install_requires=[
        "watchdog>=2.1.0",
        "ttkbootstrap",
    ],
    entry_points={
        "console_scripts": [
            "gac=gac.cli:main",
        ],
    },
)