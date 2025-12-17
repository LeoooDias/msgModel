# Breaking Changes: Privacy Enforcement Update

**Version**: 3.0.0 (Breaking Release)  
**Date**: December 16, 2025  
**Scope**: msgmodel library - strict zero-retention privacy enforcement for all sensitive data

---

## Summary of Breaking Changes

This release enforces **zero-retention data policies** across all providers. The library now **requires** paid API tiers for all providers and removes all options to accept data retention.

### What Changed

| Component | Before | After | Impact |
|-----------|--------|-------|--------|
| **OpenAI** | `store_data` parameter optional (default False) | `store_data` parameter removed | ✅ Always ZDR |
| **Gemini** | `use_paid_api` parameter optional (default False) | `use_paid_api` parameter removed | ✅ Paid tier required |
| **Claude** | Supported (30-day retention) | **NOT SUPPORTED** | ❌ Raises ConfigurationError |
| **Billing** | Not verified | Verified on first API call | ✅ Ensures paid access |
| **Error handling** | Silent warnings | Stern, security-focused errors | ✅ Clear requirements |

---

## Detailed Breaking Changes

### 1. OpenAI: `store_data` Parameter Removed

**Before**:
```python
from msgmodel import query, OpenAIConfig

# Explicitly set store_data
config = OpenAIConfig(store_data=False)  # Zero Data Retention
response = query("openai", "prompt", config=config)

# Or allow it to default
config = OpenAIConfig()  # store_data=False by default
response = query("openai", "prompt", config=config)

# Or disable ZDR (not recommended)
config = OpenAIConfig(store_data=True)  # ❌ No longer possible
response = query("openai", "prompt", config=config)
```

**After**:
```python
from msgmodel import query, OpenAIConfig

# store_data parameter no longer exists
# ZDR is enforced automatically with X-OpenAI-No-Store header
config = OpenAIConfig()  # No parameters needed
response = query("openai", "prompt", config=config)

# Attempting to set store_data raises TypeError
config = OpenAIConfig(store_data=False)
# TypeError: __init__() got an unexpected keyword argument 'store_data'
```

**Migration**:
```python
# OLD CODE
config = OpenAIConfig(store_data=False)

# NEW CODE - Just remove the parameter
config = OpenAIConfig()
```

**Why**: ZDR is non-negotiable for privacy-critical applications. Removing the parameter eliminates the possibility of accidental data retention.

---

### 2. Gemini: `use_paid_api` Parameter Removed + Billing Verification

**Before**:
```python
from msgmodel import query, GeminiConfig

# Unpaid services (default) - data retained for training
config = GeminiConfig()
response = query("gemini", "prompt", config=config)
# Warning: "Gemini is configured for UNPAID SERVICES..."

# Paid services - requires Cloud Billing
config = GeminiConfig(use_paid_api=True)
response = query("gemini", "prompt", config=config)
# No warning (assumes you have paid quota)

# This was allowed but data was retained
config = GeminiConfig(use_paid_api=False)
response = query("gemini", "prompt", config=config)
# Warning issued but request proceeded
```

**After**:
```python
from msgmodel import query, GeminiConfig

# use_paid_api parameter no longer exists
# Paid tier is automatically required and verified
config = GeminiConfig()
response = query("gemini", "prompt", config=config)
# Billing verification happens on first API call

# Attempting to set use_paid_api raises TypeError
config = GeminiConfig(use_paid_api=True)
# TypeError: __init__() got an unexpected keyword argument 'use_paid_api'
```

**Billing Verification**:
```python
from msgmodel import query, GeminiConfig
from msgmodel.exceptions import ConfigurationError

config = GeminiConfig()

try:
    response = query("gemini", "prompt", config=config)
except ConfigurationError as e:
    print(f"BILLING VERIFICATION FAILED: {e}")
    # Message will indicate why: rate limit, access denied, no billing, etc.
```

**Migration**:
```python
# OLD CODE
config = GeminiConfig(use_paid_api=True)

# NEW CODE - Just remove the parameter
config = GeminiConfig()

# REQUIREMENT: Ensure your Google Cloud project has:
# 1. Cloud Billing account linked
# 2. PAID API quota enabled (not free tier)
# 3. Sufficient billing credits
# See: https://console.cloud.google.com/billing
```

**Why**: Paid tier is mandatory for zero-retention enforcement. Removing the parameter eliminates the possibility of accidentally using unpaid tier with data retention.

---

### 3. Claude: No Longer Supported

**Before**:
```python
from msgmodel import query, ClaudeConfig

# Claude was supported
config = ClaudeConfig()
response = query("claude", "prompt", config=config)
# Worked fine (data retained for 30 days)
```

**After**:
```python
from msgmodel import query
from msgmodel.exceptions import ConfigurationError

try:
    response = query("claude", "prompt")
except ConfigurationError as e:
    print(e)
    # Error: "Claude is not supported in msgmodel.
    #        Claude retains data for up to 30 days for abuse prevention.
    #        This is incompatible with msgmodel's zero-retention privacy requirements.
    #        Use: Google Gemini (paid tier) or OpenAI instead."
```

**Migration**:
```python
# OLD CODE
response = query("claude", "prompt")

# NEW CODE - Switch to Gemini (paid) or OpenAI
response = query("openai", "prompt")  # Zero data retention
# OR
response = query("gemini", "prompt")  # Paid tier only, abuse monitoring only
```

**Why**: Claude's 30-day minimum retention is incompatible with zero-retention privacy requirements.

---

## Required Setup for Each Provider

### OpenAI

✅ **No changes to your API setup required**

```python
from msgmodel import query, OpenAIConfig

# Just use it - ZDR is enforced automatically
config = OpenAIConfig(model="gpt-4o")
response = query("openai", "sensitive prompt", config=config)

# ✅ Data will NOT be retained for training
# ✅ Files (if any) will be deleted immediately
```

---

### Google Gemini

⚠️ **REQUIRES Google Cloud Billing setup**

**Prerequisite Checklist**:
- [ ] You have a Google Cloud project
- [ ] Cloud Billing account is linked to the project
- [ ] **PAID** API quota is enabled (not free tier)
- [ ] You have billing credits available

**Verification**:
```bash
# Go to Google Cloud Console
https://console.cloud.google.com/billing

# Verify:
# 1. Billing account is linked
# 2. Payment method is active
# 3. Budget shows paid quota (not just free tier)
```

**Code**:
```python
from msgmodel import query, GeminiConfig
from msgmodel.exceptions import ConfigurationError

config = GeminiConfig(model="gemini-2.5-flash")

try:
    response = query("gemini", "sensitive prompt", config=config)
    # Billing verified! Data protected from training use.
except ConfigurationError as e:
    # Billing verification failed
    print(f"Fix: {e}")
    # Check:
    # 1. Cloud Billing is actually linked
    # 2. Paid quota is enabled (not free tier)
    # 3. API key is valid for that project
```

**If billing verification fails**:
```
ConfigurationError: BILLING VERIFICATION FAILED: Rate limit exceeded.
This may indicate unpaid quota. Ensure your Google Cloud project has:
  1. Cloud Billing account linked
  2. PAID API quota enabled (not free tier)
  3. Sufficient billing credits
See: https://console.cloud.google.com/billing
```

---

## Migration Checklist

### For Projects Using OpenAI

```python
# 1. Update imports (no change needed)
from msgmodel import query, OpenAIConfig

# 2. Remove store_data parameter if present
# BEFORE:
# config = OpenAIConfig(store_data=False)

# AFTER:
config = OpenAIConfig()

# 3. Test
response = query("openai", "test", config=config)
assert response.text  # Should work
```

### For Projects Using Gemini

```python
# 1. Update imports (no change needed)
from msgmodel import query, GeminiConfig

# 2. Remove use_paid_api parameter if present
# BEFORE:
# config = GeminiConfig(use_paid_api=True)

# AFTER:
config = GeminiConfig()

# 3. Verify Google Cloud Billing is active
# Go to: https://console.cloud.google.com/billing
# Check: Billing account linked + Paid quota enabled

# 4. Test (will verify billing on first call)
try:
    response = query("gemini", "test", config=config)
    assert response.text  # Should work
except ConfigurationError as e:
    print(f"Billing verification failed. Fix and retry.")
    print(f"Details: {e}")
```

### For Projects Using Claude

```python
# 1. Switch to OpenAI (preferred) or Gemini (paid)

# BEFORE:
# response = query("claude", "prompt")

# AFTER - Option 1: OpenAI (recommended)
response = query("openai", "prompt")

# AFTER - Option 2: Gemini (requires paid quota)
response = query("gemini", "prompt")
```

---

## Error Messages You'll See

### OpenAI

**No changes expected** — OpenAI will work as before, just without `store_data` parameter.

---

### Gemini - Billing Verification Failed (Rate Limited)

```
ConfigurationError: BILLING VERIFICATION FAILED: Rate limit exceeded.
This may indicate unpaid quota. Ensure your Google Cloud project has:
  1. Cloud Billing account linked
  2. PAID API quota enabled (not free tier)
  3. Sufficient billing credits
See: https://console.cloud.google.com/billing
```

**Fix**: Wait a moment and retry. If persistent, check billing console.

---

### Gemini - Billing Verification Failed (Access Denied)

```
ConfigurationError: BILLING VERIFICATION FAILED: Access denied (403).
Ensure your API key has paid quota access:
  1. Verify API key is valid
  2. Confirm Cloud Billing is enabled
  3. Check that paid quota is active (not free tier)
See: https://console.cloud.google.com/billing
```

**Fix**: Regenerate API key or verify it's for the correct project with billing.

---

### Claude (Not Supported)

```
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

**Fix**: Switch to OpenAI or Gemini (paid).

---

## Configuration Classes - Before & After

### OpenAIConfig

```python
# BEFORE (v1.x)
@dataclass
class OpenAIConfig:
    model: str = "gpt-4o"
    temperature: float = 1.0
    top_p: float = 1.0
    max_tokens: int = 1000
    n: int = 1
    store_data: bool = False  # ← REMOVED
    delete_files_after_use: bool = True

# AFTER (v2.0)
@dataclass
class OpenAIConfig:
    model: str = "gpt-4o"
    temperature: float = 1.0
    top_p: float = 1.0
    max_tokens: int = 1000
    n: int = 1
    delete_files_after_use: bool = True
    # store_data removed - ZDR always enforced
```

### GeminiConfig

```python
# BEFORE (v1.x)
@dataclass
class GeminiConfig:
    model: str = "gemini-2.5-flash"
    temperature: float = 1.0
    top_p: float = 0.95
    top_k: int = 40
    max_tokens: int = 1000
    candidate_count: int = 1
    safety_threshold: str = "BLOCK_NONE"
    api_version: str = "v1beta"
    cache_control: bool = False
    use_paid_api: bool = False  # ← REMOVED

# AFTER (v2.0)
@dataclass
class GeminiConfig:
    model: str = "gemini-2.5-flash"
    temperature: float = 1.0
    top_p: float = 0.95
    top_k: int = 40
    max_tokens: int = 1000
    candidate_count: int = 1
    safety_threshold: str = "BLOCK_NONE"
    api_version: str = "v1beta"
    cache_control: bool = False
    # use_paid_api removed - paid tier always required & verified
```

### ClaudeConfig

```python
# BEFORE (v1.x)
@dataclass
class ClaudeConfig:
    model: str = "claude-sonnet-4-20250514"
    temperature: float = 1.0
    top_p: float = 0.95
    top_k: int = 40
    max_tokens: int = 1000
    cache_control: bool = False

# AFTER (v2.0)
# ClaudeConfig still exists but attempting to use Claude raises:
# ConfigurationError: Claude is not supported in msgmodel.
# Do not instantiate or pass this config to query().
```

---

## Testing Your Migration

### Test 1: OpenAI Works

```python
from msgmodel import query, OpenAIConfig

try:
    config = OpenAIConfig()
    response = query("openai", "test prompt")
    print("✓ OpenAI works")
    print(f"Response: {response.text[:50]}...")
except Exception as e:
    print(f"✗ OpenAI failed: {e}")
```

### Test 2: Gemini Works (with billing)

```python
from msgmodel import query, GeminiConfig
from msgmodel.exceptions import ConfigurationError

try:
    config = GeminiConfig()
    response = query("gemini", "test prompt")
    print("✓ Gemini works (billing verified)")
    print(f"Response: {response.text[:50]}...")
except ConfigurationError as e:
    print(f"✗ Billing verification failed: {e}")
except Exception as e:
    print(f"✗ Gemini failed: {e}")
```

### Test 3: Claude Rejected

```python
from msgmodel import query
from msgmodel.exceptions import ConfigurationError

try:
    response = query("claude", "test prompt")
    print("✗ Claude should have been rejected")
except ConfigurationError as e:
    print("✓ Claude correctly rejected")
    print(f"Reason: Claude is not supported (30-day retention)")
except Exception as e:
    print(f"✗ Unexpected error: {e}")
```

---

## FAQ

### Q: Why remove store_data? Can't users choose?

**A**: For privacy-critical applications, choice is dangerous. A developer might accidentally set `store_data=True` thinking it's safe, or forget the parameter entirely. Enforcement eliminates this risk.

### Q: Why require paid Gemini tier?

**A**: Unpaid Gemini indefinitely retains data for training. Sensitive data must not be used for AI training. Paid tier is the only Gemini option that prevents this.

### Q: Why exclude Claude?

**A**: Claude's minimum 30-day retention is incompatible with zero-retention privacy requirements. For comparison: OpenAI = 0 days, Gemini (paid) = 24-72 hours, Claude = 30 days. Claude doesn't meet the standard.

### Q: What if I need to use a provider temporarily?

**A**: Don't. If you're processing sensitive data, all requests must meet the standard. If you need to test with lower-security data, use a different script/environment.

### Q: Can I downgrade to v1.x?

**A**: Yes, but then you'll lose the enforcement. The whole point of v2.0 is to make mistakes impossible at the configuration level.

### Q: My code breaks. Can you help?

**A**: Yes. Use this guide to understand the changes, then update your configuration. Most changes are just removing parameters.

---

## Support

If you encounter issues during migration:

1. **OpenAI**: Remove `store_data=...` from your config
2. **Gemini**: Remove `use_paid_api=...` AND verify Cloud Billing is actually active
3. **Claude**: Switch to OpenAI or Gemini

For detailed privacy information, see the library's privacy documentation.

---

**Release Date**: December 16, 2025  
**Version**: 2.0.0  
**Status**: Breaking changes required for strict privacy enforcement
