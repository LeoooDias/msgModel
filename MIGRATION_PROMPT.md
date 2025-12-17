# Migration Prompt for Projects Using msgmodel v1.x → v2.0

**Use this prompt with an AI agent to update projects that depend on msgmodel.**

---

## Prompt Template

Copy and paste this into your AI agent context for a project that depends on msgmodel:

---

### START PROMPT

```
You are updating a Python project that uses the msgmodel library.

msgmodel has been upgraded from v1.x to v2.0 with BREAKING CHANGES focused on 
strict zero-retention privacy enforcement.

## What Changed in msgmodel v2.0:

1. **OpenAI**: The `store_data` parameter has been REMOVED from OpenAIConfig.
   - Zero Data Retention (ZDR) is now ALWAYS enforced and cannot be disabled.
   - Migration: Remove `store_data=False` (or `store_data=True`) from any OpenAIConfig instantiation.

2. **Gemini**: The `use_paid_api` parameter has been REMOVED from GeminiConfig.
   - Paid tier is now REQUIRED and automatically verified.
   - Migration: Remove `use_paid_api=True` (or `use_paid_api=False`) from any GeminiConfig instantiation.
   - Requirement: User's Google Cloud project must have Cloud Billing linked with PAID quota enabled.

3. **Claude**: Claude provider is NO LONGER SUPPORTED.
   - Raises ConfigurationError: "Claude is not supported in msgmodel."
   - Migration: Switch all Claude queries to OpenAI (recommended) or Gemini (paid only).

4. **Billing Verification**: Gemini queries now verify paid access on first API call.
   - If billing verification fails, ConfigurationError is raised with clear instructions.

## Your Task:

Find all uses of msgmodel in this codebase and update them according to the rules above.

Specifically:
1. Search for all OpenAIConfig instantiations and remove the `store_data` parameter if present.
2. Search for all GeminiConfig instantiations and remove the `use_paid_api` parameter if present.
3. Search for all calls to query() or stream() with provider="claude" and change them to "openai" or "gemini".
4. Update any documentation or comments that mention store_data or use_paid_api.
5. Update any configuration files that set these parameters.
6. Ensure that any Gemini usage is aware that billing verification will occur on first API call.

## Important Notes:

- OpenAI will work identically to before, just without the `store_data` parameter.
- Gemini will work identically to before, just without the `use_paid_api` parameter, BUT:
  - The user MUST have Google Cloud Billing set up with PAID quota (not free tier).
  - If billing is not properly configured, the first query() call will raise ConfigurationError.
  - The error message will be clear about what's wrong.
- Claude queries MUST be migrated to OpenAI or Gemini.
- No other changes are required (no logic changes, just configuration cleanup).

## Files to Check:

- Source code files (*.py) - look for OpenAIConfig, GeminiConfig, ClaudeConfig, query(), stream()
- Configuration files (*.yaml, *.json, *.toml) - look for store_data, use_paid_api, claude references
- Documentation files (*.md, *.rst) - look for examples using store_data, use_paid_api, or claude
- Test files (test_*.py, *_test.py) - look for mock configs with these parameters

## What NOT to Change:

- Do not change the underlying logic of the project.
- Do not change OpenAI API behavior (ZDR is still enforced, just not optional anymore).
- Do not change Gemini API behavior (paid tier is still used, just required now).
- Do not change authentication (api_key parameter, environment variables, all still work).
- Do not change model names, temperature, max_tokens, or any other parameters.

## Report Back:

After making changes, provide:
1. A summary of all files modified
2. A count of OpenAIConfig, GeminiConfig, ClaudeConfig references found and removed/changed
3. A list of any Claude queries that were migrated to OpenAI or Gemini
4. Any remaining code that references `store_data`, `use_paid_api`, or Claude that should be reviewed manually
5. Confirmation that the code compiles/imports without errors (if possible to check)

Begin now. Search the codebase and make the necessary updates.
```

### END PROMPT

---

## Example Output You Should Receive

When using the prompt with an AI agent, you should get output like:

```
## Migration Summary

### Files Modified:
1. src/config.py - Removed store_data from OpenAIConfig usage (3 locations)
2. src/llm_client.py - Removed use_paid_api from GeminiConfig usage (1 location)
3. tests/test_openai.py - Updated test fixtures (2 locations)
4. docs/usage.md - Updated example code (1 location)

### Changes Made:

#### OpenAI Configuration
- ✓ Removed `store_data=False` from OpenAIConfig in src/config.py:45
- ✓ Removed `store_data=False` from OpenAIConfig in tests/test_openai.py:12
- ✓ Removed `store_data=False` from OpenAIConfig in docs/usage.md:87

#### Gemini Configuration
- ✓ Removed `use_paid_api=True` from GeminiConfig in src/llm_client.py:123

#### Claude Migration
- ✗ No Claude references found (already using OpenAI)

#### Documentation Updates
- ✓ Updated docs/usage.md to remove store_data parameter example
- ✓ Added note about Gemini billing verification requirement

### Files That Compiled Successfully:
- src/config.py ✓
- src/llm_client.py ✓
- tests/test_openai.py ✓

### Manual Review Needed:
- None

### Summary:
- 6 total changes made
- 0 issues encountered
- Code is ready for msgmodel v2.0
```

---

## Quick Reference: Migration Patterns

### OpenAI Before → After

```python
# BEFORE
from msgmodel import OpenAIConfig
config = OpenAIConfig(store_data=False)

# AFTER
from msgmodel import OpenAIConfig
config = OpenAIConfig()
```

### Gemini Before → After

```python
# BEFORE
from msgmodel import GeminiConfig
config = GeminiConfig(use_paid_api=True)

# AFTER
from msgmodel import GeminiConfig
config = GeminiConfig()
# REQUIREMENT: Google Cloud Billing with PAID quota must be active
```

### Claude Before → After

```python
# BEFORE
response = query("claude", "prompt")

# AFTER (Option 1: OpenAI)
response = query("openai", "prompt")

# AFTER (Option 2: Gemini - requires paid quota)
response = query("gemini", "prompt")
```

---

## Manual Verification Steps

After the AI agent completes the migration, manually verify:

1. **Check imports**:
   ```bash
   python3 -c "from msgmodel import OpenAIConfig, GeminiConfig; print('✓ Imports OK')"
   ```

2. **Check no references to removed parameters**:
   ```bash
   grep -r "store_data" . --include="*.py"  # Should return nothing
   grep -r "use_paid_api" . --include="*.py"  # Should return nothing
   ```

3. **Check no Claude references**:
   ```bash
   grep -r "claude" . --include="*.py"  # Should show only comments/strings, not active code
   ```

4. **Test OpenAI config creation**:
   ```python
   from msgmodel import OpenAIConfig
   config = OpenAIConfig(model="gpt-4o")
   print(f"✓ OpenAI config created: {config}")
   ```

5. **Test Gemini config creation**:
   ```python
   from msgmodel import GeminiConfig
   config = GeminiConfig(model="gemini-2.5-flash")
   print(f"✓ Gemini config created: {config}")
   ```

---

## If Things Go Wrong

### Error: `TypeError: __init__() got an unexpected keyword argument 'store_data'`

**Cause**: You still have `store_data=...` in your code  
**Fix**: Remove the `store_data` parameter from OpenAIConfig instantiation

```python
# WRONG
config = OpenAIConfig(store_data=False)  # TypeError

# RIGHT
config = OpenAIConfig()
```

### Error: `TypeError: __init__() got an unexpected keyword argument 'use_paid_api'`

**Cause**: You still have `use_paid_api=...` in your code  
**Fix**: Remove the `use_paid_api` parameter from GeminiConfig instantiation

```python
# WRONG
config = GeminiConfig(use_paid_api=True)  # TypeError

# RIGHT
config = GeminiConfig()
```

### Error: `ConfigurationError: Claude is not supported in msgmodel.`

**Cause**: You're trying to use Claude  
**Fix**: Switch to OpenAI or Gemini

```python
# WRONG
response = query("claude", "prompt")

# RIGHT (Option 1)
response = query("openai", "prompt")

# RIGHT (Option 2)
response = query("gemini", "prompt")
```

### Error: `ConfigurationError: BILLING VERIFICATION FAILED`

**Cause**: Gemini billing verification failed (not paid tier)  
**Fix**: 
1. Go to https://console.cloud.google.com/billing
2. Ensure Cloud Billing is linked to your project
3. Ensure PAID quota is enabled (not just free tier)
4. Try again

---

## Checklist for Your Project

After running the prompt, verify:

- [ ] All OpenAIConfig instantiations have `store_data` parameter removed
- [ ] All GeminiConfig instantiations have `use_paid_api` parameter removed
- [ ] All Claude queries have been migrated to OpenAI or Gemini
- [ ] Code compiles/imports without errors
- [ ] Tests pass (if applicable)
- [ ] Documentation has been updated
- [ ] Team is aware that Gemini now requires Google Cloud Billing

---

## Questions?

Refer to:
- [BREAKING_CHANGES.md](BREAKING_CHANGES.md) - Complete breaking changes documentation
- [README.md](README.md) - Updated usage documentation
- [msgmodel/config.py](msgmodel/config.py) - See the updated config classes

---

**Prompt Version**: 1.0  
**For msgmodel**: v3.0.0  
**Date**: December 16, 2025
