from setuptools import setup, find_packages

setup(
    name="crewai_extensions",
    version="0.6.2.1",
    packages=find_packages(),
    install_requires=[
        "crewai",  # Base package dependency
        "litellm",
        "pydantic",
        "python-dotenv",
        "langchain",
        "streamlit",
        "psutil"
    ],
    author="Wido Jansen",
    author_email="widojansen@gmail.com",
    description="Extensions for CrewAI with enhanced LLM functionality",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/widojansen/crewai_extensions",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
