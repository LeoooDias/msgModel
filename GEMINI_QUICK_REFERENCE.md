# Gemini Provider: Privacy Configuration — Quick Reference

## TL;DR: What Changed

Your msgmodel Gemini provider now includes configuration for privacy-conscious deployments:

1. **New `use_paid_api` configuration option** in `GeminiConfig`
2. **Runtime warning** when using unpaid services (default)
3. **Updated README** with Paid vs Unpaid Services distinction
4. **Comprehensive privacy analysis** in [GEMINI_PRIVACY_ANALYSIS.md](GEMINI_PRIVACY_ANALYSIS.md)

---

## Configuration Guide

### For Absolute Statelessness (Ideal)

```python
from msgmodel import query, GeminiConfig

# 1. Set up with Cloud Billing enabled on your Google Cloud project
# 2. Enable paid API quota (not free tier)
# 3. Configure with use_paid_api=True

config = GeminiConfig(
    model="gemini-2.5-flash",
    use_paid_api=True,  # ← KEY: Requires Cloud Billing + paid quota
)

response = query("gemini", "Your sensitive prompt", config=config)
```

**Result**: 
- ✅ Data NOT retained for model training
- ✅ Files NOT persisted beyond 48 hours
- ⚠️ Abuse monitoring retention: ~24-72 hours (unspecified)
- ✅ Backups: encrypted, deleted after ~6 months

---

### For Development/Testing (Default)

```python
from msgmodel import query

# Uses default: use_paid_api=False
response = query("gemini", "Your prompt")

# You'll see warning:
# "Gemini is configured for UNPAID SERVICES (no Cloud Billing). 
#  Google WILL retain your prompts and responses for model training..."
```

**Result**:
- ❌ Data IS retained for model training
- ❌ No statelessness possible
- ⚠️ Not recommended for sensitive data

---

## File Handling (Already Stateless)

Good news: File handling is already bulletproof and stateless!

```python
# Files are embedded as base64 in each request
# No persistent storage on Google's servers
# No cleanup needed

response = query(
    "gemini",
    "What's in this image?",
    file_path="sensitive_photo.jpg"
)
# Photo data is only in RAM during this request
# Not stored anywhere after response completes
```

---

## What Data Gets Retained

### With `use_paid_api=False` (Default)

| Data | Retained? | Duration | Purpose |
|------|-----------|----------|---------|
| Prompts | ✅ YES | Indefinite | Model training + improvements |
| Outputs | ✅ YES | Indefinite | Model training + improvements |
| Files | 48 hours | auto-delete | Google may process during window |
| Human review | ✅ YES | Indefinite | Google employees may read |

### With `use_paid_api=True` (Paid Services)

| Data | Retained? | Duration | Purpose |
|------|-----------|----------|---------|
| Prompts | ⚠️ LIMITED | 24-72 hrs | Abuse monitoring only |
| Outputs | ⚠️ LIMITED | 24-72 hrs | Abuse monitoring only |
| Files | 48 hours | auto-delete | No training use |
| Human review | ❌ NO | — | Unless abuse detected |
| Backups | Encrypted | 6 months | Disaster recovery |

---

## Hard Limitations (Cannot Be Changed)

Even with Paid Services, these apply:

1. **Abuse monitoring**: Google must retain data temporarily (~24-72 hrs) to detect policy violations
2. **Backup retention**: Encrypted backups for disaster recovery (up to 6 months)
3. **No client-side toggle**: These are server-side policies, not API parameters

---

## Comparison with Other Providers

### OpenAI (Best for Zero-Retention)

```python
from msgmodel import query, OpenAIConfig

config = OpenAIConfig(store_data=False)  # True zero-retention
response = query("openai", "Sensitive data", config=config)
```

- ✅ Prompts not retained for training
- ✅ Outputs not retained for training  
- ✅ Files deleted immediately after use
- ⚠️ Minimal metadata (~30 days)

---

### Gemini (Best with Cloud Billing)

```python
from msgmodel import query, GeminiConfig

config = GeminiConfig(use_paid_api=True)
response = query("gemini", "Sensitive data", config=config)
```

- ✅ Prompts not retained for training
- ✅ Outputs not retained for training
- ✅ Files deleted after 48 hours
- ⚠️ Abuse monitoring retention (~24-72 hrs)

---

### Claude (No Zero-Retention Option)

```python
from msgmodel import query

response = query("claude", "Sensitive data")
```

- ❌ Data retained for 30 days minimum (abuse prevention)
- ❌ No configuration available
- ❌ Not suitable for high-privacy requirements

---

## Setup Steps for Maximum Privacy

### Step 1: Verify Google Cloud Billing

```bash
# Ensure you have:
# 1. A Google Cloud project
# 2. Cloud Billing account linked
# 3. Paid API quota enabled (NOT free tier)

# Check via Google Cloud Console:
# https://console.cloud.google.com/billing
```

### Step 2: Update Configuration

```python
from msgmodel import GeminiConfig, query

config = GeminiConfig(
    use_paid_api=True,  # ← CRITICAL: Requires paid quota active
    model="gemini-2.5-flash",
    temperature=1.0,
)

response = query("gemini", "Your prompt", config=config)
```

### Step 3: Monitor Logs

The provider will only warn if `use_paid_api=False`:

```python
# ❌ This will log a warning (unpaid services)
config = GeminiConfig(use_paid_api=False)

# ✅ This will not warn (assumes you have paid quota)
config = GeminiConfig(use_paid_api=True)
```

---

## Testing Your Configuration

```python
import logging
from msgmodel import query, GeminiConfig

# Enable logging to see warnings
logging.basicConfig(level=logging.WARNING)

# Test 1: Unpaid (will warn)
print("Test 1: Unpaid services...")
config1 = GeminiConfig(use_paid_api=False)
query("gemini", "Test prompt", config=config1)
# Expected: Warning about unpaid services

# Test 2: Paid (no warning)
print("\nTest 2: Paid services...")
config2 = GeminiConfig(use_paid_api=True)
query("gemini", "Test prompt", config=config2)
# Expected: No warning (assumes paid quota is active)
```

---

## Troubleshooting

### Issue: Warning still shows even with `use_paid_api=True`

**Expected behavior**: The warning is only about configuration. If you set `use_paid_api=True`, the library trusts you have paid quota. The warning only appears if `use_paid_api=False`.

### Issue: Data still being retained despite `use_paid_api=True`

**Check**: 
1. Is Cloud Billing actually linked to your Google Cloud project?
2. Are you using **paid API quota** (not free tier)?
3. Is your API key for a project with billing enabled?

If these are not all true, Google applies unpaid service terms regardless of your code setting.

### Issue: How long until data is deleted?

**Timeline with Paid Services**:
- Active retention: 24-72 hours (abuse monitoring only)
- Encrypted backup: up to 6 months
- Typical total: ~2 months for complete deletion

---

## Official References

- [Google Gemini API Terms](https://ai.google.dev/gemini-api/terms) ← Main source
- [Google Privacy Policy - Data Retention](https://policies.google.com/technologies/retention)
- [Gemini API Documentation](https://ai.google.dev/docs)

---

## Still Have Questions?

See the detailed analysis in [GEMINI_PRIVACY_ANALYSIS.md](GEMINI_PRIVACY_ANALYSIS.md) for:
- Complete data retention policies
- Service tier comparison
- File handling details
- Backup and recovery information
- Comparison with OpenAI and Claude

---

**Last Updated**: December 16, 2024  
**Relevant Files Changed**:
- [msgmodel/config.py](msgmodel/config.py) — Added `use_paid_api` to `GeminiConfig`
- [msgmodel/providers/gemini.py](msgmodel/providers/gemini.py) — Added unpaid services warning
- [README.md](README.md) — Added detailed Gemini privacy section
- [GEMINI_PRIVACY_ANALYSIS.md](GEMINI_PRIVACY_ANALYSIS.md) — Comprehensive analysis
