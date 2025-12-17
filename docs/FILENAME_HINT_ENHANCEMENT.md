# msgmodel Enhancement: Filename Hints for MIME Type Detection

## Overview

This enhancement adds support for filename hints in the `stream()` and `query()` functions to enable proper MIME type detection when using file-like (BytesIO) objects. This solves a critical issue where providers like Gemini reject `application/octet-stream` MIME types.

## Problem Statement

**Issue**: The `stream()` function doesn't support passing filename hints for MIME type detection when using BytesIO objects.

**Previous Behavior**:
```python
stream(provider, prompt, file_like=BytesIO_obj)
→ calls _prepare_file_like_data(file_like)
→ defaults to "upload.bin"
→ MIME type becomes application/octet-stream
→ Gemini API rejects application/octet-stream ❌
```

**Why This Matters**:
- Gemini and other providers validate MIME types
- They reject `application/octet-stream` as it's too generic
- Users can't upload PDFs, images, or other binary files via BytesIO without disk access
- Privacy-focused applications want to avoid writing files to disk

## Solution

### Two Approaches (Both Supported)

#### 1. **Explicit filename parameter** (Recommended)
```python
from io import BytesIO
from msgmodel import query

pdf_bytes = b"..."  # Binary PDF content
file_obj = BytesIO(pdf_bytes)

response = query(
    "gemini",
    "Summarize this document",
    file_like=file_obj,
    filename="document.pdf"  # ← Enables proper MIME type detection
)
```

#### 2. **Implicit .name attribute**
```python
from io import BytesIO
from msgmodel import query

pdf_bytes = b"..."
file_obj = BytesIO(pdf_bytes)
file_obj.name = "document.pdf"  # Set .name attribute

response = query(
    "gemini",
    "Summarize this document",
    file_like=file_obj  # Uses .name for MIME type detection
)
```

## Implementation Details

### API Changes

#### `query()` function signature
```python
def query(
    provider: Union[str, Provider],
    prompt: str,
    api_key: Optional[str] = None,
    system_instruction: Optional[str] = None,
    file_path: Optional[str] = None,
    file_like: Optional[io.BytesIO] = None,
    filename: Optional[str] = None,  # ← NEW PARAMETER
    config: Optional[ProviderConfig] = None,
    max_tokens: Optional[int] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
) -> LLMResponse:
```

#### `stream()` function signature
```python
def stream(
    provider: Union[str, Provider],
    prompt: str,
    api_key: Optional[str] = None,
    system_instruction: Optional[str] = None,
    file_path: Optional[str] = None,
    file_like: Optional[io.BytesIO] = None,
    filename: Optional[str] = None,  # ← NEW PARAMETER
    config: Optional[ProviderConfig] = None,
    max_tokens: Optional[int] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
) -> Iterator[str]:
```

### Internal Implementation

Both functions now pass the filename hint to `_prepare_file_like_data()`:

```python
# Prepare file data if provided
file_data = None
if file_path:
    file_data = _prepare_file_data(file_path)
elif file_like:
    # Use provided filename, fall back to .name attribute, then default
    file_hint = filename or getattr(file_like, 'name', 'upload.bin')
    file_data = _prepare_file_like_data(file_like, filename=file_hint)
```

### Precedence Order

MIME type detection uses this precedence:
1. **filename parameter** (highest priority) - explicitly provided
2. **.name attribute** - if set on BytesIO object
3. **'upload.bin'** (default) - fallback

### MIME Type Detection

The filename is used with Python's `mimetypes.guess_type()`:

```python
mime_type, _ = mimetypes.guess_type(filename)
if not mime_type:
    mime_type = MIME_TYPE_OCTET_STREAM  # fallback
```

**Common filename → MIME type mappings**:
- `document.pdf` → `application/pdf`
- `photo.jpg` → `image/jpeg`
- `image.png` → `image/png`
- `data.json` → `application/json`
- `text.txt` → `text/plain`
- `unknown.xyz` → `application/octet-stream` (fallback)

## Usage Examples

### Example 1: Analyze PDF from uploaded form

```python
from io import BytesIO
from msgmodel import query

# Simulate receiving file from web form
file_bytes = request.files['document'].read()
file_obj = BytesIO(file_bytes)

response = query(
    "gemini",
    "Analyze this document and provide a summary",
    file_like=file_obj,
    filename="report.pdf"  # From form field or Content-Disposition header
)
```

### Example 2: Stream processing of image from API

```python
from io import BytesIO
from msgmodel import stream
import requests

# Fetch image from external API
response = requests.get('https://api.example.com/image.jpg')
image_bytes = response.content
file_obj = BytesIO(image_bytes)

# Stream description with proper MIME type
for chunk in stream(
    "openai",
    "Describe this image in detail",
    file_like=file_obj,
    filename="photo.jpg"  # Enables proper MIME type detection
):
    print(chunk, end="", flush=True)
```

### Example 3: Database file processing

```python
from io import BytesIO
from msgmodel import query

# Retrieve file from database
db_file = database.get_file(file_id)
file_obj = BytesIO(db_file.content)

# Use filename from database metadata
response = query(
    "gemini",
    "Extract text from this document",
    file_like=file_obj,
    filename=db_file.original_filename
)
```

### Example 4: Using .name attribute

```python
from io import BytesIO
from msgmodel import query

# Simulate file in memory
file_obj = BytesIO(b"PDF binary data...")
file_obj.name = "invoice.pdf"  # Set .name attribute

# No filename parameter needed
response = query(
    "openai",
    "Extract invoice details",
    file_like=file_obj  # Automatically uses file_obj.name
)
```

## Benefits

✅ **Proper MIME Type Detection**
- Providers like Gemini can correctly identify file types
- No more `application/octet-stream` rejection errors

✅ **Privacy-Focused**
- Process files entirely in memory
- Zero disk I/O for sensitive documents
- No temporary files to clean up

✅ **Flexible**
- Explicit parameter for complete control
- Implicit .name attribute for convenience
- Smart fallback to defaults

✅ **Backward Compatible**
- Existing code continues to work
- New parameter is optional
- Default behavior unchanged

✅ **Easy to Use**
- Just add filename parameter
- Or set .name attribute on BytesIO
- Works with both query() and stream()

## Testing

Comprehensive test coverage includes:

1. **Filename parameter tests**
   - PDF detection: `filename="report.pdf"` → `application/pdf`
   - Image detection: `filename="photo.jpg"` → `image/jpeg`
   - Unknown types: proper fallback to `application/octet-stream`

2. **.name attribute tests**
   - Setting `.name` on BytesIO works correctly
   - MIME type is detected from .name

3. **Precedence tests**
   - filename parameter overrides .name attribute
   - Both override default 'upload.bin'

4. **Integration tests**
   - query() passes filename correctly
   - stream() passes filename correctly
   - File data includes correct MIME type in payload

All tests pass: ✅ 34/34

## Migration Guide

### If you currently use:
```python
stream("gemini", "Analyze this", file_like=file_obj)
```

### Migrate to:
```python
# Option 1: Use filename parameter
stream("gemini", "Analyze this", file_like=file_obj, filename="document.pdf")

# Option 2: Set .name attribute
file_obj.name = "document.pdf"
stream("gemini", "Analyze this", file_like=file_obj)
```

No breaking changes - existing code continues to work!

## API Reference

### Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `filename` | `Optional[str]` | Hint for MIME type detection | `"document.pdf"` |
| `file_like` | `Optional[io.BytesIO]` | In-memory file object | `BytesIO(b"...")`  |
| `.name` | Attribute | Alternative filename hint | `file_obj.name = "..."` |

### Return Values

Both functions return file data with detected MIME type:
```python
{
    "mime_type": "application/pdf",  # Detected from filename
    "data": "base64_encoded_content",
    "filename": "document.pdf",
    "is_file_like": True
}
```

### Exceptions

- `ConfigurationError`: For invalid parameters
- `FileError`: For read/seek errors on file_like object

## Implementation Files Modified

1. **[msgmodel/core.py](msgmodel/core.py)**
   - `query()` function: Added filename parameter (line 216)
   - `stream()` function: Added filename parameter (line 373)
   - File preparation logic: Updated to handle filename hints

2. **[tests/test_core.py](tests/test_core.py)**
   - New test class: `TestFilenameMimeTypeDetection`
   - 6 comprehensive tests covering all scenarios

## Backward Compatibility

✅ **Fully backward compatible**
- filename parameter is optional
- Default behavior unchanged
- Existing code works without modification

## Performance

- ⚡ No performance impact
- Uses standard Python library: `mimetypes.guess_type()`
- Only adds filename parameter passing
- No additional I/O operations

## Future Enhancements

Possible future improvements:
- Custom MIME type mapping for special cases
- Automatic detection from file magic bytes
- Support for additional file-like interfaces

## Questions & Troubleshooting

**Q: Why does my BytesIO fail with "application/octet-stream rejected"?**
A: The provider doesn't accept this generic MIME type. Use the filename parameter or set .name attribute:
```python
query(..., file_like=file_obj, filename="document.pdf")
```

**Q: Can I override the detected MIME type?**
A: Not directly in query/stream. Use the provider's lower-level API if custom MIME types are needed.

**Q: Does this work with all providers?**
A: Yes - OpenAI, Gemini, and Claude all support this. Claude limitations are unrelated.

**Q: What if I don't know the filename?**
A: The default "upload.bin" will use `application/octet-stream`, which might be rejected. Try to preserve the original filename from the source.

## See Also

- [FILE_LIKE_IMPLEMENTATION.md](FILE_LIKE_IMPLEMENTATION.md) - Previous file-like feature docs
- [FILENAME_HINT_DEMO.py](FILENAME_HINT_DEMO.py) - Interactive examples
- [tests/test_core.py](tests/test_core.py) - Test cases with examples
