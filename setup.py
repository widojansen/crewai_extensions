from setuptools import setup, find_packages

setup(
    name="crewai-extensions",
    version="0.1.2",
    packages=find_packages(),
    install_requires=[
        "crewai",  # Base package dependency
        "litellm",
        "pydantic",
        "python-dotenv",
    ],
    author="Wido Jansen",
    author_email="widojansen@gmail.com",
    description="Extensions for CrewAI with enhanced LLM functionality",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/widojansen/crewai-extensions",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
