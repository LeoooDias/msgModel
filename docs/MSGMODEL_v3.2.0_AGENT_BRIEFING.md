# msgmodel v3.2.0: Agent Briefing Document

**Version**: 3.2.0  
**Date**: December 17, 2025  
**Status**: Released  
**Compatibility**: Breaking changes—migration required for v3.1.x users

---

## Executive Summary

msgmodel v3.2.0 is a **major architectural refactor** focusing on:
1. **Privacy-first design**: Eliminates server-side file uploads; all files use in-memory BytesIO with base64 inline encoding
2. **Stateless operation**: Each request is completely independent with no server-side persistence
3. **Simplified codebase**: Removed OpenAI Files API complexity and Claude/Anthropic support

**This is a BREAKING RELEASE.** Projects using v3.1.x must be updated to migrate.

---

## What Changed

### Three Major Removals

| Component | Reason |
|-----------|--------|
| **File uploads from disk** | Better privacy—files never stored on servers |
| **OpenAI Files API** | Unnecessary with inline base64 encoding; eliminates cleanup complexity |
| **Claude/Anthropic support** | 30-day data retention incompatible with zero-retention requirements |

### Provider Support

**Now Supported:**
- ✅ **OpenAI** (GPT models) — Zero Data Retention enforced (non-negotiable)
- ✅ **Google Gemini** (paid tier) — Abuse-monitoring retention only (~24-72 hours)

**No Longer Supported:**
- ❌ **Anthropic Claude** — Removed (30-day retention incompatible with privacy goals)

---

## Required Updates for Projects Using msgmodel

### If you're using msgmodel in production or development:

#### 1. **Remove all `file_path` parameters**
```python
# OLD ❌
response = query("openai", "Summarize this", file_path="document.pdf")

# NEW ✅
import io
with open("document.pdf", "rb") as f:
    response = query("openai", "Summarize this", 
                     file_like=io.BytesIO(f.read()), 
                     filename="document.pdf")
```

#### 2. **Remove Claude usage**
```python
# OLD ❌
response = query("claude", "Hello", api_key=claude_key)

# NEW ✅ - Use OpenAI
response = query("openai", "Hello", api_key=openai_key)

# OR NEW ✅ - Use Gemini (paid tier)
response = query("gemini", "Hello", api_key=gemini_key)
```

#### 3. **Remove Claude config imports**
```python
# OLD ❌
from msgmodel import ClaudeConfig

# This import now raises ImportError
```

#### 4. **Update OpenAI config**
```python
# OLD ❌
config = OpenAIConfig(model="gpt-4o", delete_files_after_use=True)

# NEW ✅
config = OpenAIConfig(model="gpt-4o")  # delete_files_after_use removed
```

#### 5. **Remove direct provider method calls**
```python
# OLD ❌
provider.upload_file("file.pdf")
provider.cleanup()

# These methods no longer exist
# Use the query()/stream() functions instead, they handle everything
```

---

## File Upload Migration Guide

### The New Approach

All file uploads in v3.2.0+ work exclusively through **in-memory BytesIO objects**:

```python
import io
from msgmodel import query

# 1. Read file into memory
with open("photo.jpg", "rb") as f:
    file_data = f.read()

# 2. Wrap in BytesIO
file_obj = io.BytesIO(file_data)

# 3. Use in query/stream
response = query(
    "openai",
    "Describe this image",
    file_like=file_obj,
    filename="photo.jpg"  # For MIME type detection
)
```

### Why BytesIO Only?

| Benefit | Detail |
|---------|--------|
| **Privacy** | Files never uploaded to provider servers |
| **Stateless** | Each request is completely independent |
| **Simple** | No cleanup, no file management, no persistence |
| **Fast** | No network overhead for file uploads |

### File Size Limits

Files are **not validated client-side**. If you exceed limits, the API returns an error:

| Provider | Practical Limit |
|----------|-----------------|
| OpenAI | ~15-20MB |
| Gemini | ~22MB |

For larger files, use the provider APIs directly.

---

## Privacy Configuration

### OpenAI: Zero Data Retention (Automatic)

```python
from msgmodel import query

# ZDR is ENFORCED automatically
# The X-OpenAI-No-Store header is added to every request
response = query("openai", "Sensitive data here")

# ✅ Your data is NOT stored for training
# ✅ Your data is NOT used for service improvements
```

**Note**: Metadata (timestamps, token counts) may be retained for ~30 days for debugging, but not your actual content.

### Gemini: Paid Tier Required

```python
from msgmodel import query

# Requires Google Cloud Billing with paid quota enabled
response = query("gemini", "Sensitive data here", api_key="your-key")

# ✅ Data NOT used for training
# ✅ Data retained only for abuse detection (~24-72 hours)
```

**Important**: If you're on the free tier, Google will retain data indefinitely for training. Ensure your Cloud account has:
- Billing enabled
- Paid API quota (not free quota)

---

## Testing Strategy

### Quick validation:

```python
import io
from msgmodel import query

# Test 1: Simple query
response = query("openai", "Hello, world!")
assert response.text  # Should have response

# Test 2: File with BytesIO
file_obj = io.BytesIO(b"Test data")
response = query("openai", "What is this?", file_like=file_obj, filename="test.txt")
assert response.text

# Test 3: Claude should fail
try:
    response = query("claude", "Hello")
except ValueError:
    print("✅ Claude correctly rejected")
```

### Full migration tests:

```python
import io
from msgmodel import query, OpenAIConfig, GeminiConfig

# Test different configurations
openai_config = OpenAIConfig(model="gpt-4o-mini")
response = query("openai", "Test", config=openai_config)

gemini_config = GeminiConfig()
response = query("gemini", "Test", config=gemini_config)

# Test file uploads with various file types
for filename in ["image.jpg", "doc.pdf", "text.txt", "data.json"]:
    file_obj = io.BytesIO(b"sample data")
    response = query("openai", f"Analyze {filename}", 
                     file_like=file_obj, filename=filename)
    print(f"✅ {filename} works")
```

---

## Code Patterns to Replace

### Pattern 1: Disk file access

**Before:**
```python
response = query("openai", "Analyze", file_path="/path/to/file.pdf")
```

**After:**
```python
import io
with open("/path/to/file.pdf", "rb") as f:
    response = query("openai", "Analyze", 
                     file_like=io.BytesIO(f.read()),
                     filename="file.pdf")
```

### Pattern 2: Claude calls

**Before:**
```python
response = query("claude", "Hello", api_key=claude_key)
```

**After (OpenAI):**
```python
response = query("openai", "Hello", api_key=openai_key)
```

**After (Gemini - paid tier):**
```python
response = query("gemini", "Hello", api_key=gemini_key)
```

### Pattern 3: File cleanup

**Before:**
```python
try:
    response = query(...)
finally:
    provider.cleanup()
```

**After:**
```python
# No cleanup needed—stateless design
response = query(...)
```

---

## Deprecation & Removal Timeline

| Version | Date | Status | Action |
|---------|------|--------|--------|
| v3.1.x | Historic | EOL | Update your code |
| v3.2.0 | Dec 17, 2025 | Current | Migrate now |
| v3.3.0 | Future | Planned | New features only |
| v4.0.0 | Future | Planned | May consolidate APIs further |

**Recommendation**: Update to v3.2.0 immediately. v3.1.x will not receive updates.

---

## Error Messages You'll Encounter

### If you use `file_path`:
```
TypeError: query() got an unexpected keyword argument 'file_path'
```
**Fix**: Replace with `file_like=io.BytesIO(...)`

### If you try to import Claude:
```
ImportError: cannot import name 'ClaudeConfig' from 'msgmodel'
```
**Fix**: Remove Claude imports and use OpenAI or Gemini instead

### If you use invalid provider:
```
ValueError: Invalid provider 'claude'. Valid options: 'openai', 'gemini', 'o', 'g'
```
**Fix**: Switch to `'openai'` or `'gemini'`

### If you call upload_file():
```
AttributeError: 'OpenAIProvider' object has no attribute 'upload_file'
```
**Fix**: Don't call provider methods directly; use `query(file_like=...)`

---

## FAQ for AI Development Agents

**Q: Do I need to update my code if I'm not using files?**  
A: If you don't use `file_path` or Claude, minimal changes needed. Update any imports and config.

**Q: Can I still upload large files (>20MB)?**  
A: No. Files are limited to practical API constraints. Use provider APIs directly for larger files.

**Q: Will my data retention behavior change?**  
A: OpenAI: No change (ZDR still enforced). Gemini: Check your cloud billing. Claude: No longer supported.

**Q: Do I need to handle file cleanup manually?**  
A: No. The new stateless design handles everything automatically.

**Q: What about backwards compatibility?**  
A: This is a breaking release. No backwards compatibility with v3.1.x.

**Q: How do I verify my migration is correct?**  
A: Run the test patterns in the **Testing Strategy** section above.

---

## Key Takeaways

1. **BytesIO Only**: All files must be in-memory BytesIO objects
2. **No Files API**: OpenAI's Files API is no longer used
3. **No Claude**: Claude support removed (30-day retention incompatible)
4. **Stateless**: Each request is completely independent
5. **ZDR**: OpenAI Zero Data Retention is enforced non-negotiably
6. **Privacy First**: Files never persist on provider servers

---

## Resources

- [RELEASE_NOTES_v3.2.0.md](../docs/RELEASE_NOTES_v3.2.0.md) — Full release notes
- [BREAKING_CHANGES.md](../docs/BREAKING_CHANGES.md) — Detailed breaking changes & migration
- [README.md](../README.md) — Updated usage documentation
- [FILE_LIKE_IMPLEMENTATION.md](../docs/FILE_LIKE_IMPLEMENTATION.md) — BytesIO implementation details

---

**For questions**: Refer to [BREAKING_CHANGES.md](BREAKING_CHANGES.md) for the detailed migration guide.
