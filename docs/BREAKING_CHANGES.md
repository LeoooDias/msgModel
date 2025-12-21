# Breaking Changes in msgmodel

## Summary

msgmodel has undergone significant architectural changes to prioritize **privacy**, **statelessness**, and **code simplification**. This document details all breaking changes and migration paths.

---

## Version 4.0.0 (Current)

### Breaking Changes

#### 1. `file_path` Removed from `stream()` — file_like Only

**What broke:**
- The `file_path` parameter no longer exists in `stream()`
- `stream()` now exclusively uses `file_like` for file attachments (same as `query()`)

**Error you'll see:**
```python
for chunk in stream("openai", "Describe this", file_path="photo.jpg"):
    print(chunk, end="")
# TypeError: stream() got an unexpected keyword argument 'file_path'
```

**Migration:**
```python
# OLD (v3.x)
for chunk in stream("openai", "Describe this", file_path="photo.jpg"):
    print(chunk, end="")

# NEW (v4.0.0+)
import io

with open("photo.jpg", "rb") as f:
    file_obj = io.BytesIO(f.read())

for chunk in stream("openai", "Describe this", file_like=file_obj, filename="photo.jpg"):
    print(chunk, end="")
```

**Why this change:**
- API consistency: Both `query()` and `stream()` now have identical file handling
- Privacy: `file_like` with base64 encoding means no server-side file uploads
- Simplicity: One way to do things = fewer bugs, clearer docs

---

#### 2. Gemini Environment Variable Renamed

**What broke:**
- `GEMINI_API_KEY` → `GOOGLE_API_KEY`

**Error you'll see:**
```python
# If you only have GEMINI_API_KEY set
response = query("gemini", "Hello")
# AuthenticationError: Gemini API key not found
```

**Migration:**
```bash
# OLD
export GEMINI_API_KEY="your-key"

# NEW
export GOOGLE_API_KEY="your-key"
```

**Why this change:**
- Aligns with Google's official naming convention
- Consistent with other Google Cloud tools

---

#### 3. Anthropic Default Model Updated

**What changed:**
- Default model: `claude-3-5-sonnet-20241022` → `claude-haiku-4-5-20251001`

**Impact:**
- If you relied on the default model, you'll get Claude Haiku 4.5 instead of Claude 3.5 Sonnet
- Haiku is faster and cheaper; Sonnet is more capable

**Migration (if you need Sonnet):**
```python
from msgmodel import query, AnthropicConfig

# Explicitly specify the model you want
config = AnthropicConfig(model="claude-sonnet-4-20250514")
response = query("anthropic", "Hello", config=config)
```

---

### Migration Checklist for v4.0.0

- [ ] Replace any `file_path` in `stream()` calls with `file_like` + `filename`
- [ ] Update `GEMINI_API_KEY` to `GOOGLE_API_KEY` in your environment
- [ ] If using Anthropic, verify the new default model works for your use case (or explicitly set model)

---

## Version 3.2.0

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

#### 3. Configuration Changes (v3.2.0)

**Removed from OpenAIConfig:**

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

### Summary Table (v3.2.0)

| Item | v3.1.x | v3.2.0+ | Status |
|------|--------|---------|--------|
| `file_path` param in `query()` | ✅ Supported | ❌ Removed | **Breaking** |
| `file_like` param in `query()` | ✅ Supported | ✅ Supported | OK |
| `file_like` param in `stream()` | ✅ Supported | ✅ Supported | OK |
| `OpenAIProvider.upload_file()` | ✅ Available | ❌ Removed | **Breaking** |
| `OpenAIProvider.delete_file()` | ✅ Available | ❌ Removed | **Breaking** |
| `OpenAIProvider.cleanup()` | ✅ Available | ❌ Removed | **Breaking** |
| `delete_files_after_use` config | ✅ Parameter | ❌ Removed | **Breaking** |
| OpenAI ZDR enforcement | ✅ Enforced | ✅ Enforced | OK |

---

## Migration Checklist (v3.1.x → v3.2.0)

Use this checklist to migrate your code to v3.2.0:

- [ ] Remove all `file_path` parameters from `query()` calls
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
- [ ] Update tests to use `file_like` parameter instead of `file_path`

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

# ✅ All of these work
response = query("openai", "Hello")
response = query("o", "Hello")        # shorthand
response = query("gemini", "Hello")
response = query("g", "Hello")        # shorthand
response = query("anthropic", "Hello")
response = query("a", "Hello")        # shorthand
response = query("claude", "Hello")   # alias for anthropic
response = query("c", "Hello")        # shorthand
```

---

## Further Reading

- [RELEASE_NOTES_v3.2.0.md](RELEASE_NOTES_v3.2.0.md) — Full release notes
- [README.md](../README.md) — Updated usage guide
- [FILE_LIKE_IMPLEMENTATION.md](FILE_LIKE_IMPLEMENTATION.md) — File handling details
