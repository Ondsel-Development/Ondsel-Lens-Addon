from setuptools import setup

setup(
    name="Part",
    version="0.0.1",
    install_requires=[
        "requests",
        'importlib-metadata; python_version<"3.13"',
    ],
    packages=["Part"],
)
