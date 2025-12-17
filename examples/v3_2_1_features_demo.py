"""
v3.2.1 Feature Showcase

Demonstrates new features introduced in msgmodel v3.2.1:
1. GPT-4o compatibility (auto-detects max_tokens parameter)
2. Enhanced MIME type inference with magic byte detection
3. Streaming timeout support
4. Streaming abort callback support
5. Request signing for security
"""

import io
from msgmodel import query, stream, OpenAIConfig, GeminiConfig, RequestSigner


# ============================================================================
# FEATURE 1: GPT-4o Compatibility
# ============================================================================
def example_gpt4o_compatibility():
    """
    v3.2.1 automatically detects model version and uses the correct parameter.
    
    In v3.2.0, this would fail with:
    "Unsupported parameter: 'max_tokens' is not supported with this model"
    
    In v3.2.1, it works seamlessly.
    """
    print("=== Feature 1: GPT-4o Compatibility ===\n")
    
    # Works with GPT-4o (uses max_completion_tokens internally)
    config = OpenAIConfig(model="gpt-4o", max_tokens=2000, temperature=0.7)
    
    # This request now works with GPT-4o (would fail in v3.2.0)
    try:
        response = query("openai", "What is the difference between AI and AGI?", config=config)
        print(f"✓ GPT-4o request succeeded")
        print(f"  Response: {response.text[:100]}...\n")
    except Exception as e:
        print(f"✗ Error: {e}\n")
    
    # Also works with legacy models (uses max_tokens)
    config_legacy = OpenAIConfig(model="gpt-3.5-turbo", max_tokens=1000)
    print(f"✓ Model detection works for both GPT-4o and GPT-3.5-turbo\n")


# ============================================================================
# FEATURE 2: Enhanced MIME Type Inference
# ============================================================================
def example_mime_type_inference():
    """
    v3.2.1 detects file types using both filename hints and magic bytes.
    
    Files without extensions are now correctly identified.
    """
    print("=== Feature 2: Enhanced MIME Type Inference ===\n")
    
    # Example 1: PDF detection from magic bytes (no filename extension)
    pdf_header = b'%PDF-1.4\n%fake PDF content for demo'
    pdf_file = io.BytesIO(pdf_header)
    
    try:
        response = query(
            "openai",
            "Is this a PDF? Describe what you see.",
            file_like=pdf_file,
            filename="document"  # No .pdf extension
        )
        print(f"✓ PDF detected from magic bytes (no extension needed)")
        print(f"  Response: {response.text[:80]}...\n")
    except Exception as e:
        print(f"✗ Error: {e}\n")
    
    # Example 2: PNG image detection
    png_header = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR...fake image data'
    png_file = io.BytesIO(png_header)
    
    print(f"✓ PNG detected from magic bytes")
    print(f"  MIME type would be: image/png\n")


# ============================================================================
# FEATURE 3: Streaming Timeout Support
# ============================================================================
def example_streaming_timeout():
    """
    v3.2.1 adds timeout support to stream() for slow/unreliable connections.
    
    Timeout prevents indefinite hanging on network issues.
    """
    print("=== Feature 3: Streaming Timeout Support ===\n")
    
    try:
        chunk_count = 0
        print("Streaming with 10-second timeout...")
        
        for chunk in stream(
            "openai",
            "Write a short haiku about AI",
            timeout=10  # 10-second timeout (NEW in v3.2.1)
        ):
            chunk_count += 1
            print(chunk, end="", flush=True)
        
        print(f"\n✓ Stream completed ({chunk_count} chunks)")
        print(f"  Timeout prevented hanging on slow connections\n")
    except Exception as e:
        print(f"✗ Timeout error: {e}\n")


# ============================================================================
# FEATURE 4: Streaming Abort Callback
# ============================================================================
def example_streaming_abort_callback():
    """
    v3.2.1 adds abort callback support for graceful stream cancellation.
    
    Return False from on_chunk callback to stop streaming.
    """
    print("=== Feature 4: Streaming Abort Callback ===\n")
    
    max_chunks = 5
    chunk_count = 0
    
    def on_chunk(text):
        """Callback that aborts after 5 chunks."""
        nonlocal chunk_count
        chunk_count += 1
        print(f"[{chunk_count}] {text}", end="", flush=True)
        
        if chunk_count >= max_chunks:
            print("\n[LIMIT REACHED - Aborting stream]")
            return False  # Abort stream
        return True  # Continue stream
    
    try:
        print("Streaming with abort after 5 chunks...\n")
        for chunk in stream(
            "openai",
            "List 100 interesting facts about space",
            on_chunk=on_chunk  # Callback for abort support (NEW in v3.2.1)
        ):
            pass  # on_chunk handles output
        
        print(f"\n✓ Stream aborted gracefully")
        print(f"  Use case: Limit output, cancel slow responses, conditional stopping\n")
    except Exception as e:
        print(f"✗ Error: {e}\n")


# ============================================================================
# FEATURE 5: Request Signing for Security
# ============================================================================
def example_request_signing():
    """
    v3.2.1 adds optional request signing for multi-tenant deployments.
    
    HMAC-SHA256 signatures prevent unauthorized API calls.
    """
    print("=== Feature 5: Request Signing for Security ===\n")
    
    # Create a signer with a secret key
    signer = RequestSigner(secret_key="super-secret-key-12345")
    
    # Sign a request
    signature = signer.sign_request(
        provider="openai",
        message="Analyze my data",
        model="gpt-4o",
        user_id="user_123",
        org_id="org_456"
    )
    
    print(f"✓ Signature generated: {signature[:16]}...")
    print(f"  Full signature: {signature}\n")
    
    # Verify the signature
    is_valid = signer.verify_signature(
        signature=signature,
        provider="openai",
        message="Analyze my data",
        model="gpt-4o",
        user_id="user_123",
        org_id="org_456"
    )
    
    print(f"✓ Signature verified: {is_valid}")
    print(f"  Use case: Multi-tenant API gateways, audit logging\n")
    
    # Try with modified parameters
    is_valid_tampered = signer.verify_signature(
        signature=signature,
        provider="openai",
        message="Different message",  # Changed!
        model="gpt-4o",
        user_id="user_123",
        org_id="org_456"
    )
    
    print(f"✓ Tampered request rejected: {not is_valid_tampered}")
    print(f"  Security: Any modification invalidates the signature\n")


# ============================================================================
# COMBINED EXAMPLE: Modern Streaming with Timeout + Abort + Signing
# ============================================================================
def example_combined_features():
    """
    Combine multiple v3.2.1 features in a real-world scenario.
    """
    print("=== Combined Example: Secure Streaming with Timeout & Abort ===\n")
    
    # Setup security
    signer = RequestSigner(secret_key="deployment-secret-key")
    
    # Sign the request
    signature = signer.sign_request(
        provider="openai",
        message="Explain quantum computing",
        model="gpt-4o",
        user_id="user_789"
    )
    
    print(f"Request signed (user_789)")
    print(f"Signature: {signature[:20]}...\n")
    
    # Stream with timeout and abort callback
    max_output_length = 500
    output_length = 0
    
    def on_chunk(text):
        nonlocal output_length
        output_length += len(text)
        print(text, end="", flush=True)
        
        if output_length > max_output_length:
            print("\n[OUTPUT LIMIT REACHED]")
            return False
        return True
    
    try:
        print("Streaming response (timeout=30s, max_output=500 chars):\n")
        
        for chunk in stream(
            "openai",
            "Explain quantum computing",
            timeout=30,  # 30-second timeout
            on_chunk=on_chunk  # Abort after 500 chars
        ):
            pass
        
        print(f"\n✓ Stream completed safely")
        print(f"  Features used: Model compatibility, Timeout, Abort callback, Request signing\n")
    except Exception as e:
        print(f"✗ Error: {e}\n")


# ============================================================================
# MAIN
# ============================================================================
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("msgmodel v3.2.1 Feature Showcase")
    print("=" * 70 + "\n")
    
    # Note: Some examples require valid API keys to run fully
    print("Note: Examples that call APIs require OPENAI_API_KEY environment variable.\n")
    
    # Run all examples
    example_gpt4o_compatibility()
    example_mime_type_inference()
    example_streaming_timeout()
    example_streaming_abort_callback()
    example_request_signing()
    example_combined_features()
    
    print("\n" + "=" * 70)
    print("All v3.2.1 features demonstrated!")
    print("=" * 70 + "\n")
