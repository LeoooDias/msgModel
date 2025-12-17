# msgmodel

[![PyPI version](https://badge.fury.io/py/msgmodel.svg)](https://badge.fury.io/py/msgmodel)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A unified Python library and CLI for interacting with multiple Large Language Model (LLM) providers.

## Overview

`msgmodel` provides both a **Python library** and a **command-line interface** to interact with three major LLM providers:
- **OpenAI** (GPT models)
- **Google Gemini**
- **Anthropic Claude**

Use it as a library in your Python projects or as a CLI tool for quick interactions.

## Features

- **Unified API**: Single `query()` and `stream()` functions work with all providers
- **Library & CLI**: Use as a Python module or command-line tool
- **Streaming support**: Stream responses in real-time
- **File attachments**: Process images, PDFs, and text files with your prompts
- **Flexible configuration**: Dataclass-based configs with sensible defaults
- **Multiple API key sources**: Direct parameter, environment variable, or key file
- **Exception-based error handling**: Clean errors, no `sys.exit()` in library code
- **Type-safe**: Full type hints throughout
- **Privacy-focused**: Minimal data retention settings by default

## Installation

### From PyPI (Recommended)

```bash
# Basic installation
pip install msgmodel

# With Claude support
pip install msgmodel[claude]

# With all optional dependencies
pip install msgmodel[all]
```

### From Source

```bash
# Clone the repository
git clone https://github.com/LeoooDias/msgmodel.git
cd msgmodel

# Install the package
pip install -e .

# Or with Claude support
pip install -e ".[claude]"

# Or with development dependencies
pip install -e ".[dev]"
```

### Prerequisites

- Python 3.10 or higher
- API keys from the providers you wish to use

## Quick Start

### As a Library

```python
from msgmodel import query, stream

# Simple query (uses OPENAI_API_KEY env var)
response = query("openai", "What is Python?")
print(response.text)

# With explicit API key
response = query("gemini", "Hello!", api_key="your-api-key")

# Streaming
for chunk in stream("claude", "Tell me a story"):
    print(chunk, end="", flush=True)

# With file attachment
response = query("gemini", "Describe this image", file_path="photo.jpg")

# With custom configuration
from msgmodel import OpenAIConfig

config = OpenAIConfig(model="gpt-4o-mini", temperature=0.7, max_tokens=2000)
response = query("openai", "Write a poem", config=config)
```

### As a CLI

```bash
# Basic usage
python -m msgmodel -p openai "What is Python?"

# Using shorthand provider codes
python -m msgmodel -p g "Hello, Gemini!"  # g = gemini
python -m msgmodel -p c "Hello, Claude!"  # c = claude
python -m msgmodel -p o "Hello, OpenAI!"  # o = openai

# With streaming
python -m msgmodel -p openai "Tell me a story" --stream

# From a file
python -m msgmodel -p gemini -f prompt.txt

# With system instruction
python -m msgmodel -p claude "Analyze this" -i "You are a data analyst"

# With file attachment
python -m msgmodel -p gemini "Describe this" -b image.jpg

# Custom parameters
python -m msgmodel -p openai "Hello" -m gpt-4o-mini -t 500 --temperature 0.7

# Get full JSON response instead of just text
python -m msgmodel -p openai "Hello" --json

# Verbose output (shows model, provider, token usage)
python -m msgmodel -p openai "Hello" -v
```

## API Key Configuration

API keys can be provided in three ways (in order of priority):

1. **Direct parameter**: `query("openai", "Hello", api_key="sk-...")`
2. **Environment variable**:
   - `OPENAI_API_KEY` for OpenAI
   - `GEMINI_API_KEY` for Gemini
   - `ANTHROPIC_API_KEY` for Claude
3. **Key file** in current directory:
   - `openai-api.key`
   - `gemini-api.key`
   - `claude-api.key`

## Configuration

Each provider has its own configuration dataclass with sensible defaults:

```python
from msgmodel import OpenAIConfig, GeminiConfig, ClaudeConfig

# OpenAI configuration
openai_config = OpenAIConfig(
    model="gpt-4o",           # Model to use
    temperature=1.0,           # Sampling temperature
    top_p=1.0,                 # Nucleus sampling
    max_tokens=1000,           # Max output tokens
    store_data=False,          # Don't store data for training
)

# Gemini configuration
gemini_config = GeminiConfig(
    model="gemini-2.5-flash",
    temperature=1.0,
    top_p=0.95,
    top_k=40,
    safety_threshold="BLOCK_NONE",
)

# Claude configuration
claude_config = ClaudeConfig(
    model="claude-sonnet-4-20250514",
    temperature=1.0,
    top_p=0.95,
    top_k=40,
)
```

## Data Retention & Privacy

`msgmodel` is designed with **statelessness** as a core principle. Here's what you need to know:

### OpenAI (Default: Zero Data Retention)

When using OpenAI with `store_data=False` (the default):

- **What's protected**: Input prompts, system instructions, and model responses
- **How**: The `X-OpenAI-No-Store` header is automatically added to all Chat Completions requests
- **Result**: OpenAI does **not** use these interactions for service improvements or model training
- **Persistence**: Inputs/outputs are **not stored** beyond the immediate request-response cycle
- **File retention**: Files uploaded for processing are **automatically deleted** after the request completes (unless `delete_files_after_use=False`)

**Important limitations**:
- OpenAI's **API logs** may retain minimal metadata (timestamps, API version, token counts) for ~30 days for debugging purposes, but not the actual content
- **Billing records** will still show API usage but not interaction content
- Enabling `store_data=True` disables ZDR and allows OpenAI to use your data for service improvements

Example (ZDR enabled):
```python
from msgmodel import query, OpenAIConfig

config = OpenAIConfig(
    store_data=False,          # Enables Zero Data Retention (default)
    delete_files_after_use=True  # Auto-delete uploaded files (default)
)
response = query("openai", "Sensitive prompt", config=config)
```

Example (Opt-out of ZDR):
```python
from msgmodel import query, OpenAIConfig

config = OpenAIConfig(store_data=True)  # Disables ZDR
response = query("openai", "Can use for training", config=config)
```

### Google Gemini (Service-Tier Dependent)

Google Gemini's data retention policy **depends on which service tier you use**. No API parameter controls this; it's determined by your Google Cloud account configuration.

#### Unpaid Services (Default: Free Tier, Google AI Studio)

**When this applies**: You're using the free API quota without Cloud Billing enabled

- **What's retained**: Prompts, system instructions, and all model responses
- **How long**: Indefinitely (for model training and product improvement)
- **Additional processing**: Human reviewers may read and annotate your prompts
- **Statelessness**: ❌ **NOT POSSIBLE** — data is fundamentally retained for training

**Configuration in msgmodel**:
```python
from msgmodel import query, GeminiConfig

# Default (unpaid): Data IS retained for training
config = GeminiConfig(use_paid_api=False)  # Default
response = query("gemini", "Your prompt", config=config)
# WARNING: Library will emit warning: "Gemini is configured for UNPAID SERVICES..."
```

#### Paid Services (Google Cloud Billing + Paid Quota)

**When this applies**: Your Google Cloud project has Cloud Billing enabled AND you're using paid API quota

- **What's protected**: Data is NOT used for model training or product improvement
- **What IS retained**: Prompts and responses retained temporarily for abuse detection and legal compliance (typically 24-72 hours; exact duration unspecified by Google)
- **Human review**: ❌ NO (unless abuse is detected)
- **Statelessness**: ✅ **ACHIEVABLE** — within abuse monitoring requirements
- **Backups**: Encrypted backups retained up to 6 months per Google's standard deletion process

**Configuration in msgmodel**:
```python
from msgmodel import query, GeminiConfig

# Paid services: Data protected from training, used only for abuse monitoring
config = GeminiConfig(use_paid_api=True)
response = query("gemini", "Sensitive prompt", config=config)
# No warning; library assumes you have paid quota active
```

**Important**: Setting `use_paid_api=True` assumes your Google Cloud project has:
1. Cloud Billing account linked
2. Paid API quota enabled (not on free quota tier)

If this is not the case, Google will apply unpaid service terms regardless of your code setting.

**Learn more**: [Google Gemini API Terms — How Google Uses Your Data](https://ai.google.dev/gemini-api/terms)

#### File Handling in Gemini

- **Inline files** (msgmodel default): Base64-encoded files embedded in each request; **no persistent storage**; stateless by design ✅
- **Google Files API** (not used by msgmodel): Would upload to Google's servers; 48-hour auto-delete; encrypted backup up to 6 months
- **Verdict**: Current inline approach is **more privacy-preserving** for statelessness goals

### Anthropic Claude

- **Retention period**: Content retained for up to 30 days for abuse prevention
- **No configuration available**: Google and Anthropic do not provide client-side controls for this
- **Statelessness**: ❌ **NOT ACHIEVABLE** — 30-day minimum retention is inherent to the service

See [Anthropic Privacy](https://www.anthropic.com/privacy) for details.

### Summary Comparison

| Provider | Statelessness Achievable | How | Caveat |
|----------|--------------------------|-----|---------|
| **OpenAI** | ✅ YES | `store_data=False` (default) | Zero-retention header; metadata ~30 days |
| **Gemini (Paid)** | ✅ MOSTLY | Cloud Billing + `use_paid_api=True` | Abuse monitoring retention ~24-72 hours |
| **Gemini (Unpaid)** | ❌ NO | No configuration possible | Data retained for training indefinitely |
| **Claude** | ❌ NO | No configuration possible | 30-day minimum retention |

For maximum privacy across all providers, consider:
1. **OpenAI with ZDR**: True zero-retention option with `store_data=False` (default)
2. **Gemini with Paid Services**: Near-stateless with Cloud Billing and `use_paid_api=True` (abuse monitoring only)
3. **Running models locally** (e.g., Ollama, LLaMA)
4. **Using on-premise deployments**

For detailed privacy analysis of Gemini, see [GEMINI_PRIVACY_ANALYSIS.md](GEMINI_PRIVACY_ANALYSIS.md).

## Error Handling

The library uses exceptions instead of `sys.exit()`:

```python
from msgmodel import query, MsgModelError, AuthenticationError, APIError

try:
    response = query("openai", "Hello")
except AuthenticationError as e:
    print(f"API key issue: {e}")
except APIError as e:
    print(f"API call failed: {e}")
    print(f"Status code: {e.status_code}")
except MsgModelError as e:
    print(f"General error: {e}")
```

## Response Object

The `query()` function returns an `LLMResponse` object:

```python
response = query("openai", "Hello")

print(response.text)          # The generated text
print(response.model)         # Model used (e.g., "gpt-4o")
print(response.provider)      # Provider name (e.g., "openai")
print(response.usage)         # Token usage dict (if available)
print(response.raw_response)  # Complete API response
```

## Project Structure

```
msgModel/
├── msgmodel/                    # Python package
│   ├── __init__.py              # Public API exports
│   ├── __main__.py              # CLI entry point
│   ├── core.py                  # Core query/stream functions
│   ├── config.py                # Configuration dataclasses
│   ├── exceptions.py            # Custom exceptions
│   ├── py.typed                 # PEP 561 marker for typed package
│   └── providers/               # Provider implementations
│       ├── __init__.py
│       ├── openai.py
│       ├── gemini.py
│       └── claude.py
├── tests/                       # Test suite
│   ├── test_config.py
│   ├── test_core.py
│   └── test_exceptions.py
├── pyproject.toml               # Package configuration
├── LICENSE                      # MIT License
├── MANIFEST.in                  # Distribution manifest
├── requirements.txt             # Dependencies
└── README.md
```

## CLI Usage

After installation, the `msgmodel` command is available:

```bash
# Basic usage
msgmodel -p openai "What is Python?"

# Or using python -m
python -m msgmodel -p openai "What is Python?"

# Provider shortcuts: o=openai, g=gemini, c=claude
msgmodel -p g "Hello, Gemini!"
msgmodel -p c "Hello, Claude!"

# With streaming
msgmodel -p openai "Tell me a story" --stream

# From a file
msgmodel -p gemini -f prompt.txt
```

## Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=msgmodel
```

## Building & Publishing

```bash
# Install build tools
pip install build twine

# Build the package
python -m build

# Check the distribution
twine check dist/*

# Upload to PyPI (requires PyPI account)
twine upload dist/*

# Upload to TestPyPI first (recommended)
twine upload --repository testpypi dist/*
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

Leo Dias (but mostly AI)
  
