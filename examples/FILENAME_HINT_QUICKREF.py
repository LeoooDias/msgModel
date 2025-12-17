#!/usr/bin/env python3
"""
Quick Reference: Filename Hints for MIME Type Detection

This is a quick reference guide for using filename hints to enable
proper MIME type detection with BytesIO objects in msgmodel.
"""

# ============================================================================
# BEFORE (Problem: Gemini rejects application/octet-stream)
# ============================================================================

from io import BytesIO
from msgmodel import query

pdf_bytes = b"%PDF-1.4\n..."  # Binary PDF content
file_obj = BytesIO(pdf_bytes)

# ❌ Without filename hint:
# response = query("gemini", "Summarize", file_like=file_obj)
# → MIME type: application/octet-stream
# → Gemini API: REJECTED ❌


# ============================================================================
# AFTER (Solution: Use filename parameter)
# ============================================================================

# ✅ APPROACH 1: Explicit filename parameter (Recommended)
response = query(
    "gemini",
    "Summarize this document",
    file_like=file_obj,
    filename="document.pdf"  # ← Proper MIME type detection!
)
# → MIME type: application/pdf
# → Gemini API: ACCEPTED ✅

# ✅ APPROACH 2: Set .name attribute on BytesIO
file_obj.name = "report.pdf"
response = query(
    "gemini",
    "Analyze this report",
    file_like=file_obj  # Uses .name for MIME type
)
# → MIME type: application/pdf
# → Gemini API: ACCEPTED ✅


# ============================================================================
# QUICK USAGE EXAMPLES
# ============================================================================

from io import BytesIO
from msgmodel import query, stream

# --- Example 1: Query with PDF ---
pdf_data = open("document.pdf", "rb").read()
file_obj = BytesIO(pdf_data)
response = query(
    "openai",
    "Extract key information from this PDF",
    file_like=file_obj,
    filename="contract.pdf"
)

# --- Example 2: Stream with Image ---
image_data = open("photo.jpg", "rb").read()
file_obj = BytesIO(image_data)
for chunk in stream(
    "gemini",
    "Describe this image",
    file_like=file_obj,
    filename="photo.jpg"  # Enables image/jpeg MIME type
):
    print(chunk, end="", flush=True)

# --- Example 3: Using .name attribute ---
file_obj = BytesIO(b"...")
file_obj.name = "spreadsheet.xlsx"
response = query(
    "openai",
    "Summarize this spreadsheet",
    file_like=file_obj  # .name attribute used for MIME type
)

# --- Example 4: Web form file upload ---
from flask import request
uploaded_file = request.files['document']
file_bytes = uploaded_file.read()
file_obj = BytesIO(file_bytes)
response = query(
    "gemini",
    "Analyze this document",
    file_like=file_obj,
    filename=uploaded_file.filename  # Preserve original filename
)


# ============================================================================
# MIME TYPE DETECTION PRIORITY
# ============================================================================

# The library uses this precedence for MIME type detection:
#
# 1. filename parameter (explicit, highest priority)
# 2. .name attribute (implicit)
# 3. 'upload.bin' (default fallback)
#
# Example:
file_obj = BytesIO(b"data")
file_obj.name = "wrong.txt"

response = query(
    "gemini",
    "Analyze",
    file_like=file_obj,
    filename="correct.pdf"  # ← This takes precedence!
)
# → MIME type: application/pdf (from filename parameter)


# ============================================================================
# COMMON FILENAME → MIME TYPE MAPPINGS
# ============================================================================

# Supported extensions (using Python's mimetypes module):
#
# .pdf           → application/pdf
# .jpg, .jpeg    → image/jpeg
# .png           → image/png
# .gif           → image/gif
# .txt           → text/plain
# .json          → application/json
# .xml           → application/xml
# .csv           → text/csv
# .docx          → application/vnd.openxmlformats-officedocument.wordprocessingml.document
# .xlsx          → application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
# .ppt, .pptx    → application/vnd.openxmlformats-officedocument.presentationml.presentation
# (+ hundreds more)


# ============================================================================
# WHY THIS MATTERS
# ============================================================================

# Problem without filename hints:
# - All BytesIO objects default to "upload.bin"
# - All get MIME type: application/octet-stream
# - Gemini API (and others) reject this generic type
# - Users can't upload files without disk access

# Solution with filename hints:
# - Can detect actual file type from filename
# - Proper MIME types are sent to APIs
# - Gemini and others accept the files
# - Works entirely in memory (privacy-focused)


# ============================================================================
# KEY FEATURES
# ============================================================================

# ✅ MIME Type Detection
#    Use filename parameter to enable proper MIME type detection
#
# ✅ Backward Compatible
#    Existing code works without changes
#
# ✅ Flexible
#    Two approaches: parameter or .name attribute
#
# ✅ Privacy-Focused
#    Process files in memory without disk I/O
#
# ✅ Works Everywhere
#    Both query() and stream() functions
#    All supported providers


# ============================================================================
# TROUBLESHOOTING
# ============================================================================

# Q: My Gemini query fails with "unsupported media type"
# A: Use filename parameter to set proper MIME type:
#    query("gemini", prompt, file_like=file_obj, filename="doc.pdf")

# Q: How do I know what MIME type is being used?
# A: The MIME type is detected from the filename extension using
#    Python's mimetypes.guess_type() function

# Q: What if I don't know the filename?
# A: Try to get it from the source (form field, HTTP header, etc.)
#    If unknown, at least infer the extension from file content

# Q: Can I use this with file_path instead of file_like?
# A: No, filename parameter only works with file_like.
#    file_path objects already have the full path for detection.

# Q: Do I need to update my existing code?
# A: No! The filename parameter is optional.
#    Existing code continues to work as-is.


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                       msgmodel Filename Hints                              ║
║                                                                            ║
║ Enable proper MIME type detection for BytesIO objects                      ║
║ Solves Gemini "application/octet-stream rejected" errors                  ║
╚════════════════════════════════════════════════════════════════════════════╝

USAGE:
  1. Add filename parameter to query() or stream()
  2. Or set .name attribute on BytesIO object
  3. MIME type is automatically detected from filename

EXAMPLE:
  from io import BytesIO
  from msgmodel import query

  file_obj = BytesIO(pdf_bytes)
  query("gemini", "Analyze", file_like=file_obj, filename="doc.pdf")

THAT'S IT! Proper MIME type detection is now enabled.

For more details, see: FILENAME_HINT_ENHANCEMENT.md
For examples, see: FILENAME_HINT_DEMO.py
    """)
