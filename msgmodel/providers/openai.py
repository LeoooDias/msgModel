"""
msgmodel.providers.openai
~~~~~~~~~~~~~~~~~~~~~~~~~

OpenAI API provider implementation.

ZERO DATA RETENTION (ZDR) - ENFORCED:
- The X-OpenAI-No-Store header is ALWAYS sent with all requests.
- This header instructs OpenAI not to store inputs and outputs for service improvements.
- ZDR is non-negotiable and cannot be disabled.
- See: https://platform.openai.com/docs/guides/zero-data-retention

FILE UPLOADS:
- All file uploads are via inline base64-encoding in prompts (no Files API)
- Files are limited to practical API size constraints (~15-20MB)
- This approach provides better privacy and stateless operation
"""

import json
import base64
import logging
from typing import Optional, Dict, Any, Iterator, List

import requests

from ..config import OpenAIConfig, OPENAI_URL
from ..exceptions import APIError, ProviderError, StreamingError

logger = logging.getLogger(__name__)

# MIME type constants
MIME_TYPE_JSON = "application/json"


class OpenAIProvider:
    """
    OpenAI API provider for making LLM requests.
    
    Handles API calls and response parsing for OpenAI models.
    All file uploads use inline base64-encoding for privacy and statelessness.
    """
    
    def __init__(self, api_key: str, config: Optional[OpenAIConfig] = None):
        """
        Initialize the OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            config: Optional configuration (uses defaults if not provided)
        """
        self.api_key = api_key
        self.config = config or OpenAIConfig()
    
    def _build_headers(self) -> Dict[str, str]:
        """
        Build HTTP headers for OpenAI API requests.
        
        ENFORCES Zero Data Retention (ZDR) by always including the X-OpenAI-No-Store header.
        This header instructs OpenAI not to store inputs and outputs for service improvements.
        
        ZDR is non-negotiable and cannot be disabled.
        
        Returns:
            Dictionary of HTTP headers with ZDR enforced
        """
        headers: Dict[str, str] = {
            "Content-Type": MIME_TYPE_JSON,
            "Authorization": f"Bearer {self.api_key}",
            "X-OpenAI-No-Store": "true"  # ← ALWAYS enforced, no option to disable
        }
        
        return headers
    
    def _build_content(
        self,
        prompt: str,
        file_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Build the content array for the API request."""
        content: List[Dict[str, Any]] = []
        
        if file_data:
            mime_type = file_data["mime_type"]
            encoded_data = file_data.get("data", "")
            filename = file_data.get("filename", "input.bin")
            
            if mime_type.startswith("image/"):
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{encoded_data}"
                    }
                })
            elif mime_type.startswith("text/"):
                try:
                    decoded_text = base64.b64decode(encoded_data).decode("utf-8", errors="ignore")
                except Exception:
                    decoded_text = ""
                if decoded_text.strip():
                    content.append({
                        "type": "text",
                        "text": f"(Contents of {filename}):\n\n{decoded_text}"
                    })
            else:
                content.append({
                    "type": "text",
                    "text": (
                        f"[Note: A file named '{filename}' with MIME type '{mime_type}' "
                        f"was provided. You may not be able to read it directly, but you "
                        f"can still respond based on the description and prompt.]"
                    )
                })
        
        content.append({
            "type": "text",
            "text": prompt
        })
        
        return content
    
    def _build_payload(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        file_data: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Build the API request payload for OpenAI Chat Completions API."""
        content = self._build_content(prompt, file_data)
        
        # Build messages array with system message first (if provided)
        messages: List[Dict[str, Any]] = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": content})
        
        payload: Dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
        }
        
        if stream:
            payload["stream"] = True
        
        return payload
    
    def query(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        file_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a non-streaming API call to OpenAI.
        
        With store_data=False (default), this request opts into Zero Data Retention (ZDR)
        via the X-OpenAI-No-Store header, ensuring OpenAI does not store this interaction
        for service improvements.
        
        Args:
            prompt: The user prompt
            system_instruction: Optional system instruction
            file_data: Optional file data dict
            
        Returns:
            The API response as a dictionary
            
        Raises:
            APIError: If the API call fails
        """
        payload = self._build_payload(prompt, system_instruction, file_data)
        headers = self._build_headers()
        
        try:
            response = requests.post(
                OPENAI_URL,
                headers=headers,
                data=json.dumps(payload)
            )
        except requests.RequestException as e:
            raise APIError(f"Request failed: {e}")
        
        if not response.ok:
            raise APIError(
                f"OpenAI API error: {response.text}",
                status_code=response.status_code,
                response_text=response.text
            )
        
        return response.json()
    
    def stream(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        file_data: Optional[Dict[str, Any]] = None
    ) -> Iterator[str]:
        """
        Make a streaming API call to OpenAI.
        
        With store_data=False (default), this request opts into Zero Data Retention (ZDR)
        via the X-OpenAI-No-Store header, ensuring OpenAI does not store this interaction
        for service improvements.
        
        Args:
            prompt: The user prompt
            system_instruction: Optional system instruction
            file_data: Optional file data dict
            
        Yields:
            Text chunks as they arrive
            
        Raises:
            APIError: If the API call fails
            StreamingError: If streaming fails
        """
        payload = self._build_payload(prompt, system_instruction, file_data, stream=True)
        headers = self._build_headers()
        
        try:
            response = requests.post(
                OPENAI_URL,
                headers=headers,
                data=json.dumps(payload),
                stream=True
            )
        except requests.RequestException as e:
            raise APIError(f"Request failed: {e}")
        
        if not response.ok:
            raise APIError(
                f"OpenAI API error: {response.text}",
                status_code=response.status_code,
                response_text=response.text
            )
        
        chunks_received = 0
        try:
            for line in response.iter_lines():
                if line:
                    line_text = line.decode("utf-8")
                    if line_text.startswith("data: "):
                        data = line_text[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            # Extract text from OpenAI Chat Completions streaming response
                            # Format: {"choices": [{"delta": {"content": "..."}}], ...}
                            if "choices" in chunk and isinstance(chunk["choices"], list):
                                for choice in chunk["choices"]:
                                    if isinstance(choice, dict):
                                        delta = choice.get("delta", {})
                                        if isinstance(delta, dict):
                                            text = delta.get("content", "")
                                            if text:
                                                chunks_received += 1
                                                yield text
                        except json.JSONDecodeError:
                            continue
            
            if chunks_received == 0:
                logger.error("No text chunks extracted from streaming response. Response format may not match OpenAI Chat Completions delta structure or stream may have ended prematurely.")
        except Exception as e:
            raise StreamingError(f"Streaming interrupted: {e}")
    
    @staticmethod
    def extract_text(response: Dict[str, Any]) -> str:
        """
        Extract text from an OpenAI Chat Completions response.
        
        Args:
            response: The raw API response
            
        Returns:
            Extracted text content
        """
        # OpenAI Chat Completions response format:
        # {"choices": [{"message": {"content": "..."}}], ...}
        if "choices" in response and isinstance(response["choices"], list):
            for choice in response["choices"]:
                if isinstance(choice, dict):
                    message = choice.get("message", {})
                    if isinstance(message, dict):
                        content = message.get("content", "")
                        if content:
                            return content
        
        return ""
