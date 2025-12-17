"""
Demonstration of filename hint feature for MIME type detection in msgmodel.

This script shows how to use the filename parameter and .name attribute to
enable proper MIME type detection for BytesIO objects, which solves the issue
where Gemini API rejects application/octet-stream MIME types.
"""

import io
from msgmodel.core import query, stream


def demo_filename_parameter():
    """Example 1: Using the filename parameter."""
    print("=" * 70)
    print("DEMO 1: Using filename parameter for MIME type detection")
    print("=" * 70)
    
    # Simulate uploaded PDF content
    pdf_content = b"%PDF-1.4\n... (binary PDF data) ..."
    file_obj = io.BytesIO(pdf_content)
    
    # Without filename parameter, would use "upload.bin" → application/octet-stream
    # With filename parameter, gets proper MIME type detection
    try:
        response = query(
            "gemini",
            "Summarize this PDF document",
            file_like=file_obj,
            filename="report.pdf"  # ← Enables proper MIME type detection!
        )
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Note: {e}")
        print("\nIn production, this would use the proper MIME type:")
        print("  - filename: report.pdf → MIME type: application/pdf ✓")
        print("  - (instead of application/octet-stream which Gemini rejects)")
    
    print()


def demo_name_attribute():
    """Example 2: Using the .name attribute on BytesIO."""
    print("=" * 70)
    print("DEMO 2: Using .name attribute for MIME type detection")
    print("=" * 70)
    
    # Simulate uploaded image content
    image_content = b"\x89PNG\r\n\x1a\n... (binary PNG data) ..."
    file_obj = io.BytesIO(image_content)
    
    # Set .name attribute on BytesIO
    file_obj.name = "photo.png"
    
    # The library automatically uses .name for MIME type detection
    try:
        response = query(
            "openai",
            "Describe this image in detail",
            file_like=file_obj
            # No filename parameter needed - uses .name attribute!
        )
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Note: {e}")
        print("\nIn production, this would use the MIME type from .name:")
        print("  - .name attribute: photo.png → MIME type: image/png ✓")
    
    print()


def demo_filename_parameter_precedence():
    """Example 3: filename parameter takes precedence over .name attribute."""
    print("=" * 70)
    print("DEMO 3: filename parameter takes precedence over .name attribute")
    print("=" * 70)
    
    file_obj = io.BytesIO(b"data")
    file_obj.name = "wrong_extension.txt"  # ← This would be ignored
    
    # filename parameter overrides .name attribute
    try:
        response = query(
            "gemini",
            "Analyze this",
            file_like=file_obj,
            filename="correct_type.pdf"  # ← This takes precedence!
        )
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Note: {e}")
        print("\nPrecedence order for MIME type detection:")
        print("  1. filename parameter (highest priority)")
        print("  2. .name attribute")
        print("  3. 'upload.bin' (default)")
    
    print()


def demo_stream_with_filename():
    """Example 4: Using streaming with filename hints."""
    print("=" * 70)
    print("DEMO 4: Streaming with filename hints")
    print("=" * 70)
    
    # Simulate uploaded document
    doc_content = b"Document binary data..."
    file_obj = io.BytesIO(doc_content)
    
    try:
        print("Streaming response with proper MIME type:")
        for chunk in stream(
            "gemini",
            "Analyze this document and provide summary",
            file_like=file_obj,
            filename="document.pdf"  # ← Enables proper MIME type detection!
        ):
            print(chunk, end="", flush=True)
        print("\n")
    except Exception as e:
        print(f"Note: {e}")
        print("\nWould stream response with:")
        print("  - Proper MIME type: application/pdf")
        print("  - Instead of rejected: application/octet-stream")
    
    print()


def demo_use_cases():
    """Show practical use cases for this feature."""
    print("=" * 70)
    print("PRACTICAL USE CASES")
    print("=" * 70)
    
    print("""
1. UPLOADED FILES FROM WEB FORMS
   ├─ User uploads file via HTML form
   ├─ Server receives bytes without filename
   ├─ Solution: Preserve filename from Content-Disposition header
   └─ Code: filename = request.headers.get('Content-Disposition')
            file_like = io.BytesIO(file_bytes)
            query('gemini', prompt, file_like=file_like, filename=filename)

2. API RESPONSES WITH BINARY DATA
   ├─ Receive file from another API
   ├─ Only have binary content, no original filename
   ├─ Solution: Infer filename from Content-Type or add it manually
   └─ Code: file_like = io.BytesIO(response.content)
            query('gemini', prompt, file_like=file_like, 
                  filename='document.pdf')

3. DATABASE-STORED FILES
   ├─ Files stored as BLOB in database
   ├─ Metadata (original filename) stored separately
   ├─ Solution: Use filename from metadata
   └─ Code: file_like = io.BytesIO(db_blob)
            file_like.name = db_metadata['filename']
            query('gemini', prompt, file_like=file_like)

4. PRIVACY-FOCUSED PROCESSING
   ├─ Want to process file without writing to disk
   ├─ Prevents temporary files with sensitive data
   ├─ Solution: Use BytesIO with filename hint
   └─ Code: # Zero-disk approach
            file_like = io.BytesIO(sensitive_bytes)
            query('gemini', 'Analyze securely', 
                  file_like=file_like, filename='secret.pdf')
    """)
    
    print()


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║ " + "msgmodel Filename Hint Demo".center(66) + " ║")
    print("║ " + "MIME Type Detection for BytesIO Objects".center(66) + " ║")
    print("╚" + "=" * 68 + "╝")
    print("\n")
    
    # Run demonstrations
    demo_filename_parameter()
    demo_name_attribute()
    demo_filename_parameter_precedence()
    demo_stream_with_filename()
    demo_use_cases()
    
    print("=" * 70)
    print("KEY TAKEAWAYS")
    print("=" * 70)
    print("""
✓ The filename parameter enables proper MIME type detection for BytesIO
✓ Solves Gemini API rejection of application/octet-stream
✓ Two approaches:
    - filename="document.pdf" parameter (explicit)
    - file_obj.name = "document.pdf" attribute (implicit)
✓ filename parameter takes precedence over .name attribute
✓ Maintains privacy by avoiding disk writes
✓ Works with both query() and stream() functions

BEFORE THIS FEATURE:
    ❌ stream("gemini", prompt, file_like=BytesIO)
       → MIME type: application/octet-stream
       → Gemini API REJECTS this

AFTER THIS FEATURE:
    ✓ stream("gemini", prompt, file_like=BytesIO, filename="doc.pdf")
       → MIME type: application/pdf
       → Gemini API ACCEPTS this
    """)
    print()
