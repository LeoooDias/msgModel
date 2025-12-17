# Breaking Changes in msgmodel

## Summary

msgmodel has undergone significant architectural changes to prioritize **privacy**, **statelessness**, and **code simplification**. This document details all breaking changes and migration paths.

---

## Version 3.2.0 (Current)

### Major Breaks

#### 1. File Upload Method Changed to BytesIO-Only

**What broke:**
- The `file_path` parameter in `query()` and `stream()` has been **completely removed**
- All file uploads must now use `file_like: Optional[io.BytesIO]`
- Disk file access for uploads is **no longer supported**

**Error you'll see:**
```python
query("openai", "Hello", file_path="photo.jpg")
# TypeError: query() got an unexpected keyword argument 'file_path'
```

**Migration:**
```python
# OLD (v3.1.x and earlier)
response = query("openai", "Describe this", file_path="photo.jpg")

# NEW (v3.2.0+)
import io

with open("photo.jpg", "rb") as f:
    file_obj = io.BytesIO(f.read())

response = query("openai", "Describe this", file_like=file_obj, filename="photo.jpg")
```

**Why this change:**
- Better privacy: Files never uploaded to provider servers
- Stateless operation: Each request is completely independent
- Simpler codebase: Eliminates file upload/cleanup complexity

**File size limits (no validation, errors returned by API):**
- OpenAI: ~15-20MB practical limit
- Gemini: ~22MB practical limit

---

#### 2. OpenAI Files API Removed

**What broke:**
- `OpenAIProvider.upload_file()` method removed
- `OpenAIProvider.delete_file()` method removed  
- `OpenAIProvider.cleanup()` method removed
- `delete_files_after_use` parameter removed from `OpenAIConfig`

**Error you'll see:**
```python
# If you were calling these methods directly
prov = OpenAIProvider(api_key, config)
prov.upload_file("file.pdf")  # ❌ AttributeError: 'OpenAIProvider' has no attribute 'upload_file'
prov.cleanup()  # ❌ AttributeError: 'OpenAIProvider' has no attribute 'cleanup'

# If you were using this config parameter
config = OpenAIConfig(delete_files_after_use=True)  # ❌ TypeError: unexpected keyword argument 'delete_files_after_use'
```

**Migration:**
- Stop calling `upload_file()`, `delete_file()`, and `cleanup()` directly
- Let the base64 inline encoding handle file transfers automatically
- Remove `delete_files_after_use` from any OpenAIConfig instantiations

**Old code:**
```python
# OLD (v3.1.x)
prov = OpenAIProvider(api_key, config)
try:
    file_id = prov.upload_file("document.pdf")
    response = prov.query(prompt, None, {"file_id": file_id})
finally:
    prov.cleanup()
```

**New code:**
```python
# NEW (v3.2.0+)
import io

with open("document.pdf", "rb") as f:
    file_obj = io.BytesIO(f.read())

prov = OpenAIProvider(api_key, config)
file_data = _prepare_file_like_data(file_obj, "document.pdf")
response = prov.query(prompt, None, file_data)
# No cleanup needed—stateless design
```

**Actually, don't call provider methods directly. Use the public API:**

```python
# RECOMMENDED (v3.2.0+)
import io
from msgmodel import query

with open("document.pdf", "rb") as f:
    file_obj = io.BytesIO(f.read())

response = query("openai", "Summarize this", file_like=file_obj, filename="document.pdf")
```

**Why this change:**
- Eliminates server-side file persistence
- Reduces code complexity
- Aligns with stateless design philosophy

---

#### 3. Claude/Anthropic Support Completely Removed

**What broke:**
- `ClaudeConfig` class removed entirely
- `ClaudeProvider` class removed entirely
- `Provider.CLAUDE` enum value removed
- All Claude imports will fail
- Attempting to use Claude will raise `ValueError`

**Error you'll see:**
```python
# If you try to import ClaudeConfig
from msgmodel import ClaudeConfig  # ❌ ImportError: cannot import name 'ClaudeConfig'

# If you try to use Claude provider
response = query("claude", "Hello")  # ❌ ValueError: Invalid provider 'claude'

# If you try to create ClaudeConfig
config = ClaudeConfig()  # ❌ NameError: name 'ClaudeConfig' is not defined
```

**Migration:**
Switch to one of these providers:

**Option 1: OpenAI (Recommended for zero-retention)**
```python
# OLD (v3.1.x)
response = query("claude", "Hello", api_key=claude_key)

# NEW (v3.2.0+) - Zero Data Retention enforced
response = query("openai", "Hello", api_key=openai_key)
```

**Option 2: Google Gemini (Paid Tier - ~24-72h abuse monitoring retention)**
```python
# OLD (v3.1.x)
response = query("claude", "Hello", api_key=claude_key)

# NEW (v3.2.0+) - Requires Google Cloud Billing with paid quota
response = query("gemini", "Hello", api_key=gemini_key)
```

**Why this change:**
- Claude retains data for up to 30 days for abuse prevention
- This is incompatible with msgmodel's zero-retention privacy requirements
- Simplifies codebase and reduces maintenance burden

**Privacy comparison:**
| Provider | Retention | Recommendation |
|----------|-----------|-----------------|
| OpenAI | Zero (ZDR enforced) | ✅ Best for privacy |
| Gemini (Paid) | ~24-72h (abuse monitoring only) | ✅ Good for privacy |
| Claude | 30 days (abuse prevention) | ❌ Not supported |

---

#### 4. Configuration Changes

**Removed from OpenAIConfig:**
- `delete_files_after_use: bool` parameter (no longer applicable)

**Updated OpenAIConfig docstring:**
- Added note: "File uploads are only supported via inline base64-encoding in prompts"
- Added note: "Files are limited to practical API size constraints (~15-20MB)"

**Updated GeminiConfig docstring:**
- Added note: "File uploads are only supported via inline base64-encoding in prompts"
- Added note: "Files are limited to practical API size constraints (~22MB)"

**Migration for OpenAIConfig:**
```python
# OLD (v3.1.x)
config = OpenAIConfig(
    model="gpt-4o",
    delete_files_after_use=True  # ❌ Remove this
)

# NEW (v3.2.0+)
config = OpenAIConfig(
    model="gpt-4o"
)
```

---

#### 5. Core Module Function Signature Changes

**`query()` signature changed:**
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

**`stream()` signature changed:**
- Same changes as `query()`

**Removed functions:**
- `_prepare_file_data()` — No longer needed (disk file access removed)

**Updated functions:**
- `_prepare_file_like_data()` — Now the **only** file preparation function

---

### Summary Table

| Item | v3.1.x | v3.2.0+ | Status |
|------|--------|---------|--------|
| `file_path` param in `query()` | ✅ Supported | ❌ Removed | **Breaking** |
| `file_path` param in `stream()` | ✅ Supported | ❌ Removed | **Breaking** |
| `file_like` param in `query()` | ✅ Supported | ✅ Supported | OK |
| `file_like` param in `stream()` | ✅ Supported | ✅ Supported | OK |
| `OpenAIProvider.upload_file()` | ✅ Available | ❌ Removed | **Breaking** |
| `OpenAIProvider.delete_file()` | ✅ Available | ❌ Removed | **Breaking** |
| `OpenAIProvider.cleanup()` | ✅ Available | ❌ Removed | **Breaking** |
| `delete_files_after_use` config | ✅ Parameter | ❌ Removed | **Breaking** |
| Claude/Anthropic support | ✅ Supported | ❌ Removed | **Breaking** |
| `ClaudeConfig` class | ✅ Available | ❌ Removed | **Breaking** |
| `ClaudeProvider` class | ✅ Available | ❌ Removed | **Breaking** |
| `Provider.CLAUDE` enum | ✅ Available | ❌ Removed | **Breaking** |
| OpenAI ZDR enforcement | ✅ Enforced | ✅ Enforced | OK |
| Gemini paid tier requirement | ✅ Required | ✅ Required | OK |

---

## Migration Checklist

Use this checklist to migrate your code to v3.2.0:

- [ ] Remove all `file_path` parameters from `query()` and `stream()` calls
- [ ] Convert all disk file access to BytesIO:
  ```python
  # Old
  response = query(..., file_path="file.pdf")
  
  # New
  with open("file.pdf", "rb") as f:
      response = query(..., file_like=io.BytesIO(f.read()), filename="file.pdf")
  ```
- [ ] Remove any calls to `provider.upload_file()`, `provider.delete_file()`, `provider.cleanup()`
- [ ] Remove `delete_files_after_use` parameter from any `OpenAIConfig` instantiations
- [ ] Replace all `claude` provider calls with `openai` or `gemini`
- [ ] Remove `from msgmodel import ClaudeConfig` imports
- [ ] Update tests to use `file_like` parameter instead of `file_path`
- [ ] Review error messages for any references to removed functionality
- [ ] Test with files up to ~15-20MB (OpenAI) or ~22MB (Gemini)

---

## Testing Your Migration

### Test file uploads with BytesIO:
```python
import io
from msgmodel import query

# Test with small file
data = b"Hello, world!"
file_obj = io.BytesIO(data)

response = query(
    "openai",
    "What is this?",
    file_like=file_obj,
    filename="test.txt"
)
print(response.text)

# Test with larger file (but stay under limits)
with open("large_file.pdf", "rb") as f:
    file_data = f.read()
    if len(file_data) > 20_000_000:  # 20MB
        print("⚠️ Warning: File may exceed OpenAI limits")
    
    file_obj = io.BytesIO(file_data)
    response = query(
        "openai",
        "Summarize this PDF",
        file_like=file_obj,
        filename="large_file.pdf"
    )
```

### Test provider selection:
```python
from msgmodel import query

# ✅ This works
response = query("openai", "Hello")
response = query("o", "Hello")  # shorthand
response = query("gemini", "Hello")
response = query("g", "Hello")  # shorthand

# ❌ This raises ValueError
try:
    response = query("claude", "Hello")
except ValueError as e:
    print(f"Expected error: {e}")
```

---

## Further Reading

- [RELEASE_NOTES_v3.2.0.md](RELEASE_NOTES_v3.2.0.md) — Full release notes
- [README.md](../README.md) — Updated usage guide
- [FILE_LIKE_IMPLEMENTATION.md](FILE_LIKE_IMPLEMENTATION.md) — File handling details
