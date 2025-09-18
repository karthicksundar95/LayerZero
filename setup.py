from setuptools import setup, find_packages

setuptools = (
    name="privacy_ai",
    version="0.0.1",
    author="karthicksundar",
    author_email="karthicksundar1510@gmail.com",
    package=find_packages(where="src"),
    package_dir={"": "src"},
)