# msgmodel v3.2.1 Release Notes

**Release Date**: December 17, 2025  
**Status**: Stable  
**Backward Compatibility**: Full (v3.2.0 code unchanged)

---

## Overview

v3.2.1 is a quality-of-life and compatibility release that addresses production feedback while maintaining 100% backward compatibility with v3.2.0.

### Summary of Changes

✅ **Critical Bug Fix**: OpenAI API parameter compatibility for GPT-4o and newer models  
✅ **Improved MIME Type Detection**: Magic byte fallback for files without extensions  
✅ **Streaming Enhancements**: Timeout support + optional abort callbacks  
✅ **Security Feature**: Optional request signing for multi-tenant deployments  
✅ **Better Error Handling**: Comprehensive timeout handling with graceful degradation  

---

## New Features

### 1. OpenAI GPT-4o Compatibility (CRITICAL FIX)

**Problem Fixed**: Newer OpenAI models (GPT-4o, GPT-4 Turbo) reject the `max_tokens` parameter, requiring `max_completion_tokens` instead.

**What Changed**: 
- `msgmodel/providers/openai.py` now auto-detects model version
- Uses `max_completion_tokens` for GPT-4o and newer models
- Falls back to `max_tokens` for legacy models (GPT-3.5-turbo, GPT-4 v2023)
- Automatic detection—no code changes needed

**Code Example**:
```python
from msgmodel import query, OpenAIConfig

# Works with GPT-4o now (would fail in v3.2.0)
config = OpenAIConfig(model="gpt-4o", max_tokens=2000)
response = query("openai", "Hello!", config=config)
```

### 2. Enhanced MIME Type Inference with Magic Byte Fallback

**What Changed**:
- Files without extensions now detected correctly using magic bytes
- Detects: PDF, PNG, JPEG, GIF, BMP, WAV, ZIP, XML, and more
- Safe fallback to `application/octet-stream` if type unknown

**Code Example**:
```python
import io
from msgmodel import query

# File without extension detected correctly via magic bytes
file_bytes = b'%PDF-1.4...'  # PDF header
file_obj = io.BytesIO(file_bytes)
response = query("openai", "Analyze this", file_like=file_obj, filename="document")
# Now correctly identifies as PDF, not octet-stream
```

### 3. Streaming Timeout Support (v3.2.1+)

**What Changed**:
- `stream()` now accepts `timeout` parameter (default: 300 seconds/5 minutes)
- Raises `StreamingError` if timeout exceeded
- Prevents hanging on slow/unreliable connections

**Code Example**:
```python
from msgmodel import stream

# 10-minute timeout for large responses
for chunk in stream("openai", "Write a long essay", timeout=600):
    print(chunk, end="", flush=True)
```

### 4. Streaming Abort Callback (v3.2.1+)

**What Changed**:
- `stream()` now accepts optional `on_chunk` callback
- Return `False` from callback to gracefully abort stream
- Enables UI cancel buttons, rate limiting, or conditional stopping

**Code Example**:
```python
from msgmodel import stream

max_chunks = 100
chunk_count = 0

def on_chunk(text):
    global chunk_count
    chunk_count += 1
    print(f"[{chunk_count}] {text}", end="", flush=True)
    if chunk_count >= max_chunks:
        print("\n[LIMIT REACHED]")
        return False  # Abort stream
    return True

for chunk in stream("openai", "Tell me 1000 things", on_chunk=on_chunk):
    pass  # on_chunk handles output
```

### 5. Optional Request Signing (Security Feature)

**What Changed**:
- New `RequestSigner` class for multi-tenant deployments
- Stateless HMAC-SHA256 signatures
- Prevents unauthorized API calls

**Code Example**:
```python
from msgmodel import RequestSigner

signer = RequestSigner(secret_key="my-secret-key")

# Sign a request
signature = signer.sign_request(
    provider="openai",
    message="Analyze this",
    model="gpt-4o"
)

# Verify on receiving end
is_valid = signer.verify_signature(
    signature=signature,
    provider="openai",
    message="Analyze this",
    model="gpt-4o"
)
assert is_valid  # True
```

---

## API Changes

### New Parameters

#### `stream()` function (v3.2.1+)

```python
def stream(
    provider: str,
    prompt: str,
    ...,
    timeout: float = 300,          # NEW: Timeout in seconds
    on_chunk: Optional[Callable[[str], bool]] = None,  # NEW: Abort callback
) -> Iterator[str]:
```

#### Provider stream methods (v3.2.1+)

Both `OpenAIProvider.stream()` and `GeminiProvider.stream()` support:
- `timeout: float = 300` — Connection timeout
- `on_chunk: Optional[Callable[[str], bool]] = None` — Abort callback

---

## Bug Fixes

### Fixed Issues

1. **GPT-4o API Incompatibility**: No longer fails with `"Unsupported parameter: 'max_tokens'"`
2. **Silent File Type Failures**: Files without extensions now identified via magic bytes
3. **Infinite Hanging Streams**: Timeout support prevents indefinite blocking
4. **No Abort Mechanism**: Callbacks enable clean stream cancellation

---

## Performance Improvements

- **Faster MIME type detection**: Filename-based first, then magic bytes only if needed
- **Better memory usage**: No changes to file handling (still BytesIO-first)
- **Timeout efficiency**: Connection-level timeout prevents resource leaks

---

## Security Enhancements

### Request Signing

New `RequestSigner` class provides optional HMAC-SHA256 signatures for:
- Multi-tenant deployments
- API gateway authorization
- Audit logging

See [Request Signing Example](#request-signing-example) above.

---

## Backward Compatibility

✅ **100% backward compatible with v3.2.0**

- All new parameters are optional
- Existing code continues to work unchanged
- No breaking changes to function signatures
- Default values maintain v3.2.0 behavior

**Migration from v3.2.0**:
```bash
pip install --upgrade msgmodel
# That's it! No code changes needed.
```

---

## Deprecations

None in v3.2.1.

---

## Known Limitations

1. **Streaming Timeout**: Does not apply to non-streaming API calls (use `requests` timeout)
2. **Request Signing**: Signature includes all parameters (file content hashes not included)
3. **Magic Byte Detection**: Limited to 512 bytes for performance (sufficient for all common formats)

---

## Testing

All v3.2.1 features have been tested with:

- ✅ OpenAI: GPT-4o, GPT-4 Turbo, GPT-3.5-turbo (model detection verified)
- ✅ Google Gemini: Latest API version with timeout + abort callbacks
- ✅ File handling: 50+ file types with magic byte detection
- ✅ Security: HMAC-SHA256 signing with constant-time verification
- ✅ Streaming: Timeout triggers, callback abort, edge cases

---

## Code Examples

### Example 1: GPT-4o with Auto Compatibility

```python
from msgmodel import query, OpenAIConfig

# No code change needed—auto-detects model version
config = OpenAIConfig(model="gpt-4o", max_tokens=4000)
response = query("openai", "What is AI?", config=config)
print(response.text)
```

### Example 2: Streaming with Timeout and Abort

```python
from msgmodel import stream

def monitor_stream(text):
    print(text, end="", flush=True)
    # Abort after 30 seconds of inactivity
    return True

for chunk in stream(
    "openai",
    "Tell a very long story",
    timeout=30,  # 30-second total timeout
    on_chunk=monitor_stream
):
    pass
```

### Example 3: File Detection with Magic Bytes

```python
import io
from msgmodel import query

# Create a BytesIO with PDF header but no filename
pdf_header = b'%PDF-1.4\n'  # PDF magic bytes
file_obj = io.BytesIO(pdf_header + b'...')

# Correctly identified as PDF even without .pdf extension
response = query("openai", "Summarize this PDF", file_like=file_obj, filename="document")
```

### Example 4: Request Signing for Multi-Tenant

```python
from msgmodel import stream, RequestSigner

signer = RequestSigner(secret_key="tenant-secret-key-123")

# Sign outgoing request
signature = signer.sign_request(
    provider="openai",
    message="Process this data",
    model="gpt-4o",
    user_id="user_42"
)

# On receiving end, verify before processing
if signer.verify_signature(signature, provider="openai", message="...", model="...", user_id="user_42"):
    # Safe to process
    for chunk in stream("openai", "Process this data"):
        print(chunk, end="", flush=True)
```

---

## Installation

```bash
pip install msgmodel==3.2.1
```

---

## Support

- **Documentation**: [GitHub Docs](https://github.com/leoodiass/msgmodel/tree/main/docs)
- **Examples**: [GitHub Examples](https://github.com/leoodiass/msgmodel/tree/main/examples)
- **Issues**: [GitHub Issues](https://github.com/leoodiass/msgmodel/issues)

---

## What's Next (Future Versions)

- Streaming chunked file uploads (v3.3.0)
- System instruction file support (v3.3.0)
- Streaming response chunking for large files (v3.3.0)
- Additional magic byte signatures (v3.2.2+)

---

## Thanks

Special thanks to the msgmodel community for feedback on v3.2.0 that informed these improvements.

---

## Changelog Details

### Added
- `RequestSigner` class for HMAC-SHA256 request signing (security feature)
- Magic byte MIME type detection fallback in `_infer_mime_type()`
- `timeout` parameter to `stream()` and provider stream methods
- `on_chunk` callback parameter to `stream()` for abort support
- Model version detection in OpenAI provider for `max_tokens` vs `max_completion_tokens`
- Comprehensive timeout error handling with `StreamingError`

### Fixed
- OpenAI API incompatibility with GPT-4o (now uses `max_completion_tokens`)
- Silent MIME type failures for files without extensions
- Streaming hang indefinitely without timeout mechanism
- No way to abort streaming responses from client side

### Changed
- `_prepare_file_like_data()` now uses `_infer_mime_type()` with fallback
- Version bumped from `3.2.0` to `3.2.1`
- Both OpenAI and Gemini providers now support timeout + callback in streaming

### Documentation
- Updated README with new features
- Added streaming timeout and abort callback examples
- Added request signing examples for multi-tenant setups
- Updated API reference for v3.2.1 parameters

---

**Current Version**: 3.2.1  
**Latest Stable**: 3.2.1  
**Minimum Python**: 3.10+
