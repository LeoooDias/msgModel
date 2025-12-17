# msgmodel v3.0.0 — Privacy-Focused Zero-Retention LLM Middleware

**Release Date**: December 16, 2025  
**Status**: ✅ Released to PyPI  
**Release URL**: https://pypi.org/project/msgmodel/3.0.0/

---

## Executive Summary

msgmodel v3.0.0 transforms the library into a **strict, zero-tolerance privacy-focused LLM middleware**. All optional privacy parameters have been removed and replaced with mandatory, code-level enforced policies.

This is a **breaking release**. All dependent projects must update their configuration to remove deprecated privacy parameters.

---

## What's New

### 1. OpenAI: Zero Data Retention (Always Enforced)

**Breaking Change**: Removed `store_data` parameter

```python
# v2.x - Optional parameter
config = OpenAIConfig(store_data=False)

# v3.0.0 - No parameter needed (ZDR always enforced)
config = OpenAIConfig()
```

**Enforcement Method**: `X-OpenAI-No-Store` header automatically sent with every request. No configuration option to disable.

**What Users Get**:
- ✅ Data NOT retained for model training
- ✅ Files deleted immediately
- ✅ No option to misconfigure

---

### 2. Google Gemini: Paid Tier Required + Verified

**Breaking Change**: Removed `use_paid_api` parameter. Billing verification added.

```python
# v2.x - Optional, no enforcement
config = GeminiConfig(use_paid_api=True)

# v3.0.0 - Mandatory, billing verified on first call
config = GeminiConfig()  # Must have Google Cloud Billing enabled
response = query("gemini", "prompt")  # Verifies paid access
```

**Enforcement Method**:
- Billing verification happens on provider initialization (first API call)
- Test API call checks for paid quota access
- Fails with clear error message if billing not set up
- User cannot proceed without paid access

**What Users Get**:
- ✅ Data NOT retained for model training
- ✅ Paid tier required (verified)
- ✅ ~24-72 hour retention for abuse monitoring only
- ✅ Clear errors if billing not configured

---

### 3. Claude: Excluded from Library

**Breaking Change**: Claude provider completely removed. Raises `ConfigurationError`.

```python
# v2.x - Supported
response = query("claude", "prompt")

# v3.0.0 - Not supported
response = query("claude", "prompt")
# ConfigurationError: Claude is not supported in msgmodel
# Reason: 30-day minimum retention is incompatible with zero-retention requirements
# Alternatives: Use 'openai' or 'gemini' (paid) instead
```

**Why Excluded**:
- Claude retains data for 30 days minimum for abuse prevention
- No configuration option to reduce retention period
- Incompatible with zero-retention privacy requirements
- Better to reject upfront than allow unsafe usage

**Migration Path**:
- For OpenAI users: Drop-in replacement, existing code works
- For Gemini users: Ensure Google Cloud Billing is enabled (paid quota)

---

## Migration Guide

### For OpenAI Users

**Change Required**: Remove `store_data` parameter

```python
# Before (v2.x)
from msgmodel import query, OpenAIConfig
config = OpenAIConfig(store_data=False)
response = query("openai", "prompt", config=config)

# After (v3.0.0)
from msgmodel import query, OpenAIConfig
config = OpenAIConfig()  # Just remove the parameter
response = query("openai", "prompt", config=config)
```

**Effort**: Trivial (parameter removal only)

---

### For Gemini Users

**Changes Required**: Remove `use_paid_api` parameter + verify Google Cloud Billing

```python
# Before (v2.x)
from msgmodel import query, GeminiConfig
config = GeminiConfig(use_paid_api=True)
response = query("gemini", "prompt", config=config)

# After (v3.0.0)
from msgmodel import query, GeminiConfig
config = GeminiConfig()  # Remove parameter
# Before first query, ensure:
# 1. Google Cloud project exists
# 2. Cloud Billing is linked
# 3. Billing has paid quota active (not just free tier)
response = query("gemini", "prompt", config=config)  # Billing verified here
```

**Effort**: Parameter removal + billing verification setup

**Billing Setup Instructions**:
1. Go to https://console.cloud.google.com/billing
2. Create or select a billing account
3. Link it to your Google Cloud project
4. Ensure you have paid quota (not just free tier)
5. msgmodel will verify on first API call

---

### For Claude Users

**Migration Required**: Switch to OpenAI or Gemini (paid)

```python
# Before (v2.x)
from msgmodel import query
response = query("claude", "prompt")

# After (v3.0.0) - Option 1: Use OpenAI
from msgmodel import query, OpenAIConfig
config = OpenAIConfig()
response = query("openai", "prompt", config=config)

# After (v3.0.0) - Option 2: Use Gemini (paid)
from msgmodel import query, GeminiConfig
config = GeminiConfig()
response = query("gemini", "prompt", config=config)
```

**Effort**: Provider switch + billing setup (for Gemini)

**Recommendation**: OpenAI for lowest complexity (drop-in replacement)

---

## Error Messages

### Claude Attempt
```python
ConfigurationError: Claude is not supported in msgmodel.

REASON: Claude retains data for up to 30 days for abuse prevention.
This is incompatible with msgmodel's zero-retention privacy requirements.

ALTERNATIVES:
  - Google Gemini (paid tier): ~24-72 hour retention for abuse monitoring only
    • Requires Google Cloud Billing with paid API quota
    • See: https://ai.google.dev/gemini-api/terms

  - OpenAI: Zero data retention (enforced non-negotiably)
    • See: https://platform.openai.com/docs/guides/zero-data-retention

Use 'openai' or 'gemini' provider instead.
```

### Gemini Without Billing
```python
ConfigurationError: Failed to verify paid Gemini API access.

Details: [403 - Access Denied] Billing must be enabled.

ACTION REQUIRED:
1. Enable billing for your Google Cloud project
2. Ensure 'Generative Language API' is enabled
3. Verify you have paid quota (not just free tier)

See: https://console.cloud.google.com/billing
```

---

## Verification Checklist

Before upgrading to v3.0.0, verify:

- [ ] All projects using msgmodel have identified their LLM provider
- [ ] OpenAI users: Have valid OPENAI_API_KEY
- [ ] Gemini users: Have Google Cloud Billing enabled with paid quota
- [ ] Claude users: Have identified migration path (OpenAI or Gemini)
- [ ] Code updated: Removed `store_data` and `use_paid_api` parameters
- [ ] First test: Ran initial queries to verify billing verification works

---

## Installing v3.0.0

```bash
# Upgrade from v2.x
pip install --upgrade msgmodel

# Fresh install
pip install msgmodel>=3.0.0

# Install with extras (none for v3.0.0 since Claude is excluded)
pip install msgmodel[all]
```

---

## Backward Compatibility

**NOT backward compatible**. This is intentional.

| Feature | v2.x | v3.0.0 | Migration |
|---------|------|--------|-----------|
| OpenAI `store_data` | Optional parameter | Removed | Delete parameter |
| Gemini `use_paid_api` | Optional parameter | Removed | Delete parameter + verify billing |
| Claude support | Included | Excluded | Switch to OpenAI/Gemini |
| Config enforcement | Warnings | Code-level (mandatory) | No changes needed |

---

## Documentation

Complete migration guidance available:

- **BREAKING_CHANGES.md** — Detailed before/after for all changes (400+ lines)
- **MIGRATION_PROMPT.md** — AI agent automation template
- **AGENT_MIGRATION_PROMPT.txt** — Copy-paste ready for any AI agent
- **README.md** — Updated with v3.0.0 patterns

---

## Philosophy

msgmodel v3.0.0 enforces this principle:

> **Privacy settings must never be optional for sensitive data use cases. Code-level enforcement prevents mistakes better than configuration options and warnings.**

- Removed options that could weaken privacy
- Made enforcement automatic and mandatory
- Provided clear error messages guiding to compliant alternatives
- Eliminated "accidental privacy leaks" through misconfiguration

---

## Support & Feedback

If you encounter issues during migration:

1. **OpenAI questions**: See https://platform.openai.com/docs/guides/zero-data-retention
2. **Gemini/GCP questions**: See https://console.cloud.google.com/billing
3. **Migration help**: Use AGENT_MIGRATION_PROMPT.txt with any AI agent
4. **Library issues**: File issue on GitHub

---

## Version History

- **v3.0.0** (Dec 16, 2025) — Privacy enforcement release
- **v2.0.2** (Oct 12, 2024) — OpenAI Messages API fix
- **v2.0.1** (Oct 10, 2024) — Streaming endpoint fix
- **v1.x** — Initial releases

---

**Next Steps**:
1. Read BREAKING_CHANGES.md
2. Identify all projects using msgmodel
3. Update each project using AGENT_MIGRATION_PROMPT.txt (or manually)
4. Verify with `pip install --upgrade msgmodel`
5. Test with your API keys

---

**Status**: ✅ Live on PyPI  
**Install**: `pip install msgmodel==3.0.0`  
**Package**: https://pypi.org/project/msgmodel/3.0.0/
