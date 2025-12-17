# Release Notes: msgmodel v3.2.0

**Release Date**: December 17, 2025

## Overview

msgmodel v3.2.0 is a **major simplification** focused on privacy, statelessness, and reducing complexity. All file transfers now use **BytesIO-only** with base64 inline encoding. **Claude/Anthropic support has been completely removed**, and **OpenAI's Files API has been removed** in favor of inline file transfers.

## Major Changes

### 1. **BytesIO-Only File Transfers** ⚠️

**What changed:**
- The `file_path` parameter has been **completely removed** from `query()` and `stream()`
- All file uploads now use `file_like: Optional[io.BytesIO]` exclusively
- Files are base64-encoded and embedded directly in prompts (no server-side uploads)

**Why:**
- Better privacy—files never stored on provider servers
- Stateless operation—each request is completely independent
- Simpler code path—no file upload/cleanup logic
- Works consistently across all providers

**Migration:**
```python
# OLD (v3.1.x) - Using file_path
response = query("openai", "Describe this", file_path="photo.jpg")

# NEW (v3.2.0+) - Using file_like only
import io

with open("photo.jpg", "rb") as f:
    file_obj = io.BytesIO(f.read())

response = query("openai", "Describe this", file_like=file_obj, filename="photo.jpg")
```

**File Size Limits:**
- **OpenAI**: ~15-20MB practical limit (base64 overhead + token limits)
- **Gemini**: ~22MB practical limit (base64 overhead + token limits)
- If files exceed these limits, the API will return an error. Use provider APIs directly for larger files.

### 2. **OpenAI Files API Removed** ⚠️

**What changed:**
- Removed `upload_file()` method from OpenAIProvider
- Removed `delete_file()` method from OpenAIProvider
- Removed `cleanup()` method from OpenAIProvider
- Removed `delete_files_after_use` config parameter
- Removed all Files API endpoint references

**Why:**
- BytesIO inline encoding provides better privacy
- Eliminates server-side file persistence
- Reduces code complexity and potential failure points
- Aligns with stateless design philosophy

**What this means:**
- All file uploads to OpenAI now use base64 inline encoding
- No more file cleanup logic—each request is stateless
- Files are not persisted on OpenAI servers between requests

### 3. **Claude/Anthropic Support Removed** ⚠️

**What changed:**
- Completely removed `ClaudeConfig` class
- Completely removed `ClaudeProvider` class
- Removed all Claude-related references from configs, imports, and documentation
- Removed Claude from `Provider` enum

**Why:**
- Claude retains data for up to 30 days for abuse prevention
- This retention period is incompatible with msgmodel's zero-retention privacy requirements
- Simplifies the codebase and reduces maintenance burden

**Migration for Claude users:**
If you were using Claude, you must switch to:
- **OpenAI** (recommended): Zero data retention with ZDR header (enforced by default)
- **Gemini** (paid tier): ~24-72 hour retention for abuse monitoring only (requires Google Cloud Billing)

Example:
```python
# OLD - Claude no longer supported
# response = query("claude", "Hello")  # ❌ This will raise ConfigurationError

# NEW - Use OpenAI (zero retention)
response = query("openai", "Hello")  # ✅ Enforced ZDR

# NEW - Or use Gemini (paid tier)
response = query("gemini", "Hello", api_key="your-gemini-key")
```

## Configuration Changes

### Removed Config Parameters

**OpenAIConfig:**
- ❌ `delete_files_after_use` (no longer applicable—files never uploaded to server)

**GeminiConfig:**
- No changes to parameters, but documentation updated

**ClaudeConfig:**
- ❌ **Entire class removed**

### New Configuration Notes

Both `OpenAIConfig` and `GeminiConfig` now include file size limit documentation:

```python
# Files are limited to practical API constraints when using BytesIO
# OpenAI: ~15-20MB
# Gemini: ~22MB
```

## API Changes

### Function Signatures Updated

**`query()`:**
```python
# OLD (v3.1.x)
def query(
    provider: Union[str, Provider],
    prompt: str,
    api_key: Optional[str] = None,
    system_instruction: Optional[str] = None,
    file_path: Optional[str] = None,  # ❌ REMOVED
    file_like: Optional[io.BytesIO] = None,
    filename: Optional[str] = None,
    config: Optional[ProviderConfig] = None,
    max_tokens: Optional[int] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
) -> LLMResponse:
    ...

# NEW (v3.2.0+)
def query(
    provider: Union[str, Provider],
    prompt: str,
    api_key: Optional[str] = None,
    system_instruction: Optional[str] = None,
    file_like: Optional[io.BytesIO] = None,  # ✅ BytesIO only
    filename: Optional[str] = None,
    config: Optional[ProviderConfig] = None,
    max_tokens: Optional[int] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
) -> LLMResponse:
    ...
```

**`stream()`:**
- Same changes as `query()`

### Removed Functions

- `_prepare_file_data()` — File disk access is no longer supported

### Updated Functions

- `_prepare_file_like_data()` — Now the **only** file preparation method
  - Simplified documentation
  - All files must be BytesIO objects

## Provider Support

**Supported Providers:**
- ✅ OpenAI (GPT models) — Zero Data Retention enforced
- ✅ Google Gemini (Paid tier) — Abuse-monitoring retention only

**Unsupported Providers:**
- ❌ Anthropic Claude — Removed due to 30-day data retention incompatibility

## Testing

- All tests updated to use `file_like` parameter only
- Tests for `upload_file()`, `delete_file()`, and `cleanup()` removed
- New tests added for BytesIO-only file handling
- Tests verify file size error handling via API responses (not client-side validation)

## Documentation Updates

- README.md completely rewritten
- Removed all Claude references
- Added BytesIO file upload guide
- Updated privacy section (removed Claude comparison)
- Updated data retention comparison table
- Added practical file size limits documentation

## Breaking Changes Summary

| Change | Impact | Migration |
|--------|--------|-----------|
| `file_path` parameter removed | Code using disk files will break | Use BytesIO instead |
| `file_like` now required for files | No more mixed-mode file handling | Wrap disk files in BytesIO |
| `upload_file()` removed | No OpenAI Files API access | Use inline encoding (automatic) |
| `delete_file()` removed | No file cleanup available | Not needed—stateless design |
| `cleanup()` removed | No explicit cleanup method | Not needed—stateless design |
| `delete_files_after_use` config removed | Config parameter no longer exists | Remove from code |
| Claude support removed | Code using Claude will break | Migrate to OpenAI or Gemini (paid) |
| `ClaudeConfig` removed | Import will fail | Remove from imports |

## Upgrade Path

### For users with `file_path`:

```python
# Before (v3.1.x)
response = query("openai", "Analyze this PDF", file_path="/path/to/file.pdf")

# After (v3.2.0+)
import io

with open("/path/to/file.pdf", "rb") as f:
    file_obj = io.BytesIO(f.read())

response = query("openai", "Analyze this PDF", file_like=file_obj, filename="file.pdf")
```

### For Claude users:

```python
# Before (v3.1.x)
response = query("claude", "Hello", api_key=claude_key)

# After (v3.2.0+) - Use OpenAI
response = query("openai", "Hello", api_key=openai_key)

# After (v3.2.0+) - Or use Gemini (paid)
response = query("gemini", "Hello", api_key=gemini_key)
```

### For OpenAI config:

```python
# Before (v3.1.x)
config = OpenAIConfig(
    model="gpt-4o",
    delete_files_after_use=True  # ❌ Remove this line
)

# After (v3.2.0+)
config = OpenAIConfig(
    model="gpt-4o"
    # delete_files_after_use no longer needed
)
```

## Performance Impact

- **Faster API calls**: No file upload/cleanup overhead
- **Less network traffic**: Files embedded inline (slightly larger requests, but fewer total requests)
- **Reduced complexity**: Fewer edge cases and failure modes

## Privacy Impact

- ✅ **Enhanced**: Files never persist on provider servers
- ✅ **Enhanced**: Each request is completely stateless
- ✅ **Enhanced**: Eliminates OpenAI Files API with its additional retention

## Known Limitations

- Files are limited to practical API constraints (~15-22MB depending on provider)
- No support for file chunking or multipart uploads
- For files >20MB, use provider APIs directly outside msgmodel

## Bug Fixes

- N/A (this is a refactoring release)

## Dependencies

- No dependency changes
- No new dependencies added
- No dependencies removed

## Version Numbering

- **v3.1.x** → **v3.2.0** represents a **major refactor**
- This is a **breaking change** release (see Breaking Changes Summary above)
- Next minor version will be v3.3.0 (additive features only)

## Support & Questions

For questions or issues related to the upgrade:
- Check the [BREAKING_CHANGES.md](BREAKING_CHANGES.md) document
- Review the [README.md](../README.md) for updated usage examples
- See [FILE_LIKE_IMPLEMENTATION.md](FILE_LIKE_IMPLEMENTATION.md) for file handling details

---

**Recommend reading**: [BREAKING_CHANGES.md](BREAKING_CHANGES.md) for complete migration guide
