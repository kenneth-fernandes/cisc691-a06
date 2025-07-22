from setuptools import setup, find_packages

setup(
    name="visa-bulletin-ai",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "python-dotenv",
        "langchain",
        "langchain-core",
        "langchain-community",
        "langchain-google-genai"
    ]
)