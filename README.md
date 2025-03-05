# CrewAI Extensions

This package provides extensions and enhancements for the [CrewAI](https://github.com/joaomdmoura/crewai) library, allowing you to maintain custom modifications while still benefiting from updates to the original library.

## Features

- Enhanced LLM module with additional functionality and fixes
- Compatible with the latest CrewAI release
- Easy to install and use across multiple projects

## Installation

```bash
pip install crewai-extensions
```

Or install directly from GitHub:

```bash
pip install git+https://github.com/yourusername/crewai-extensions.git
```

## Usage

Simply import the enhanced LLM module from crewai_extensions instead of from crewai:

```python
# Instead of:
# from crewai.llm import LLM

# Use:
from crewai_extensions.llm import LLM

# Then use as normal:
llm = LLM(model="gpt-4")
response = llm.call("Hello, world!")
```

## Maintaining Compatibility

This extension package is designed to work with CrewAI v0.X.X. When new versions of CrewAI are released, this package will be updated to maintain compatibility.

## License

MIT
