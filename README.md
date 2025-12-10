# msgModel

A unified Python script for interacting with multiple Large Language Model (LLM) providers through a single interface.

## Overview

`msgModel.py` provides a consistent command-line interface to interact with three major LLM providers:
- **OpenAI** (GPT models)
- **Google Gemini**
- **Anthropic Claude**

This tool allows you to send prompts with optional file attachments (images, PDFs, text files) and receive responses from any of these providers using a simple, unified syntax.

## Features

- **Multi-provider support**: Switch between OpenAI, Gemini, and Claude with a single character flag
- **File attachment support**: Process images, PDFs, and text files alongside your prompts
- **System instructions**: Define custom system-level instructions to guide model behavior
- **Configurable parameters**: Control temperature, top-p, top-k, and other generation parameters
- **Automatic file handling**: Handles base64 encoding and provider-specific file upload requirements
- **Error handling**: Clear error messages and status codes

## Installation

### Prerequisites

- Python 3.7 or higher
- API keys from the providers you wish to use

### Setup

1. Clone or download this repository

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Create API key files in the project directory:
   - `openai-api.key` - containing your OpenAI API key
   - `gemini-api.key` - containing your Google Gemini API key
   - `claude-api.key` - containing your Anthropic Claude API key

   Each file should contain only the API key string with no extra whitespace.

4. Make the script executable (optional):
```bash
chmod +x msgModel.py
```

## Usage

### Basic Syntax

```bash
./msgModel.py <ai_family> <max_tokens> <system_instruction_file> <user_prompt_file> [binary_file]
```

or

```bash
python msgModel.py <ai_family> <max_tokens> <system_instruction_file> <user_prompt_file> [binary_file]
```

### Parameters

- **ai_family**: Choose the LLM provider
  - `o` - OpenAI (GPT models)
  - `g` - Gemini (Google)
  - `c` - Claude (Anthropic)

- **max_tokens**: Maximum number of tokens to generate (e.g., 150, 1000, 5000)

- **system_instruction_file**: Path to a text file containing system instructions (persona, behavior guidelines)

- **user_prompt_file**: Path to a text file containing your main prompt/question

- **binary_file** (optional): Path to an attachment (image, PDF, or text file)

### Examples

**Simple text prompt with Claude:**
```bash
./msgModel.py c 500 max.instruction random.prompt
```

**Image analysis with GPT-4:**
```bash
./msgModel.py o 1000 analyst.instruction describe_image.prompt photo.jpg
```

**PDF document processing with Gemini:**
```bash
./msgModel.py g 2000 summarizer.instruction analyze_doc.prompt report.pdf
```

**Multi-page document with Claude:**
```bash
./msgModel.py c 5000 max.instruction random.prompt "document.pdf"
```

### Sample Files

Create instruction and prompt files as plain text:

**max.instruction**:
```
You are a seasoned technology strategist and operator with decades across infrastructure, software, product, security, and enterprise IT.
```

**random.prompt**:
```
Summarize this report in no more than 5 sentences, to a national healthcare policy advisor.
```

## Configuration

You can customize the following settings in `msgModel.py`:

### Model Selection
- `OPENAI_MODEL` - default: `"gpt-4o"`
- `GEMINI_MODEL` - default: `"gemini-2.5-pro"`
- `CLAUDE_MODEL` - default: `"claude-sonnet-4-20250514"`

### Generation Parameters
Each provider has configurable temperature, top_p, and top_k values. Modify the constants at the top of the script:
- `OPENAI_TEMPERATURE`, `OPENAI_TOP_P`
- `GEMINI_TEMPERATURE`, `GEMINI_TOP_P`, `GEMINI_TOP_K`
- `CLAUDE_TEMPERATURE`, `CLAUDE_TOP_P`, `CLAUDE_TOP_K`

### Safety Settings (Gemini)
- `GEMINI_SAFETY_THRESHOLD` - default: `"BLOCK_NONE"`

## Supported File Types

- **Images**: JPEG, PNG, GIF, WebP (automatically converted to base64)
- **PDFs**: Uploaded and processed by supported providers
- **Text files**: Decoded and included directly in prompts
- **Other binary files**: Noted but may not be fully processed

## Output

The script outputs:
- The generated response text to stdout
- Status messages and errors to stderr
- Exit code 0 on success, non-zero on failure

## Error Handling

Common issues and solutions:

- **"Error: Missing API key file"**: Ensure you've created the appropriate `.key` file
- **"File upload failed"**: Check file path and permissions
- **HTTP 401/403**: Verify your API key is valid and has proper permissions
- **HTTP 429**: Rate limit exceeded, wait before retrying
- **HTTP 500**: Provider service error, try again later

## API Rate Limits

Be aware of rate limits for each provider:
- **OpenAI**: Varies by plan and model
- **Gemini**: Check Google AI Studio for current limits
- **Claude**: Varies by plan tier

## Security Notes

- Keep your API key files secure and never commit them to version control
- Add `*.key` to your `.gitignore` file
- API keys grant access to paid services - treat them like passwords
- Consider using environment variables for production deployments

## License

This project is provided as-is for educational and development purposes.

## Contributing

Feel free to submit issues or pull requests to improve functionality or add support for additional providers.

## Support

For issues related to:
- **Script functionality**: Check error messages and verify API key configuration
- **API-specific issues**: Consult the respective provider's documentation:
  - [OpenAI API Docs](https://platform.openai.com/docs)
  - [Gemini API Docs](https://ai.google.dev/docs)
  - [Claude API Docs](https://docs.anthropic.com)
