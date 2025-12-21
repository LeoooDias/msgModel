# msgmodel v4.0.0 Release Notes

**Release Date:** December 2024  
**Type:** Major release (breaking changes)

---

## Highlights

🎯 **API Purity**: `file_like` is now the **only** file upload method for both `query()` and `stream()`  
🔑 **Google Standard**: Gemini now uses `GOOGLE_API_KEY` environment variable  
🤖 **Model Update**: Anthropic defaults to the new Claude Haiku 4.5  
✅ **100% Test Coverage**: 403 tests covering every line of code  

---

## Breaking Changes

### 1. `file_path` Removed from `stream()`

The `file_path` parameter has been removed from `stream()`. Use `file_like` instead.

```python
# Before (v3.x)
for chunk in stream("openai", "Describe", file_path="image.jpg"):
    print(chunk, end="")

# After (v4.0.0)
import io
with open("image.jpg", "rb") as f:
    file_obj = io.BytesIO(f.read())
for chunk in stream("openai", "Describe", file_like=file_obj, filename="image.jpg"):
    print(chunk, end="")
```

**Rationale:** API consistency. Both `query()` and `stream()` now have identical signatures for file handling. The `file_like` approach ensures stateless, privacy-preserving operation with base64 inline encoding.

### 2. Gemini Environment Variable Renamed

```bash
# Before
export GEMINI_API_KEY="your-key"

# After
export GOOGLE_API_KEY="your-key"
```

**Rationale:** Aligns with Google's official naming convention used across their SDK ecosystem.

### 3. Anthropic Default Model Changed

| Before | After |
|--------|-------|
| `claude-3-5-sonnet-20241022` | `claude-haiku-4-5-20251001` |

Claude Haiku 4.5 is faster and more cost-effective. If you need Sonnet, specify it explicitly:

```python
config = AnthropicConfig(model="claude-sonnet-4-20250514")
response = query("anthropic", "Hello", config=config)
```

---

## Quality Improvements

### 100% Test Coverage

- **403 tests** covering all modules
- **1,158 statements** fully covered
- Comprehensive async testing (`aquery`, `astream`)
- All three providers tested (OpenAI, Gemini, Anthropic)

### Bug Fixes

- Fixed `async_core.py` calling non-existent method `create_with_cached_verification` → `create_with_cached_validation`

---

## Supported Providers

| Provider | Shorthand | Environment Variable | Default Model |
|----------|-----------|---------------------|---------------|
| OpenAI | `o` | `OPENAI_API_KEY` | `gpt-4o` |
| Gemini | `g` | `GOOGLE_API_KEY` | `gemini-1.5-pro` |
| Anthropic | `a`, `c`, `claude` | `ANTHROPIC_API_KEY` | `claude-haiku-4-5-20251001` |

---

## Migration Checklist

- [ ] Update `stream()` calls: replace `file_path` with `file_like` + `filename`
- [ ] Rename env var: `GEMINI_API_KEY` → `GOOGLE_API_KEY`
- [ ] Test Anthropic calls with new default model (or explicitly set model)
- [ ] Update any CI/CD pipelines with the new env var name

---

## Full Changelog

- Removed `file_path` parameter from `stream()` function
- Renamed `GEMINI_API_KEY` constant to `GOOGLE_API_KEY` in `config.py`
- Updated Anthropic default model to `claude-haiku-4-5-20251001`
- Fixed `async_core.py` method call bug
- Added comprehensive async tests
- Achieved 100% test coverage
- Updated all documentation for v4.0.0

---

## Thank You

Thanks for using msgmodel! Report issues at: https://github.com/LeoooDias/msgmodel/issues
