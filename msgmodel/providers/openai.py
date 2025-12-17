"""
msgmodel.providers.openai
~~~~~~~~~~~~~~~~~~~~~~~~~

OpenAI API provider implementation.

ZERO DATA RETENTION (ZDR) - ENFORCED:
- The X-OpenAI-No-Store header is ALWAYS sent with all requests.
- This header instructs OpenAI not to store inputs and outputs for service improvements.
- ZDR is non-negotiable and cannot be disabled.
- See: https://platform.openai.com/docs/guides/zero-data-retention
"""

import json
import base64
import logging
import time
from typing import Optional, Dict, Any, List, Iterator

import requests

from ..config import OpenAIConfig, OPENAI_URL, OPENAI_FILES_URL
from ..exceptions import APIError, ProviderError, StreamingError

logger = logging.getLogger(__name__)

# MIME type constants
MIME_TYPE_JSON = "application/json"
MIME_TYPE_PDF = "application/pdf"

# Retry configuration for file deletion (to ensure cleanup)
FILE_DELETE_MAX_RETRIES = 3
FILE_DELETE_RETRY_DELAY = 0.5  # seconds


class OpenAIProvider:
    """
    OpenAI API provider for making LLM requests.
    
    Handles file uploads, API calls, and response parsing for OpenAI models.
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
        self._uploaded_file_ids: List[str] = []
    
    def upload_file(self, file_path: str, purpose: str = "assistants") -> str:
        """
        Upload a file to OpenAI Files API.
        
        Args:
            file_path: Path to the file to upload
            purpose: Purpose of the upload
            
        Returns:
            The file ID assigned by OpenAI
            
        Raises:
            APIError: If the upload fails
        """
        from pathlib import Path
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        try:
            with open(file_path, "rb") as f:
                files = {"file": (Path(file_path).name, f)}
                data = {"purpose": purpose}
                response = requests.post(
                    OPENAI_FILES_URL, 
                    headers=headers, 
                    files=files, 
                    data=data
                )
        except IOError as e:
            raise APIError(f"Failed to read file for upload: {e}")
        
        if not response.ok:
            raise APIError(
                f"File upload failed: {response.text}",
                status_code=response.status_code,
                response_text=response.text
            )
        
        file_id = response.json().get("id")
        self._uploaded_file_ids.append(file_id)
        return file_id
    
    def delete_file(self, file_id: str, max_retries: int = FILE_DELETE_MAX_RETRIES) -> bool:
        """
        Delete a file from OpenAI Files API with retry logic.
        
        Implements exponential backoff to handle transient failures and ensure
        files are cleaned up even if the API is temporarily unavailable.
        
        Args:
            file_id: The file ID to delete
            max_retries: Maximum number of retry attempts (default: 3)
            
        Returns:
            True if deletion was successful, False if all retries exhausted
        """
        url = f"{OPENAI_FILES_URL}/{file_id}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        for attempt in range(max_retries):
            try:
                response = requests.delete(url, headers=headers, timeout=10)
                if response.ok:
                    if file_id in self._uploaded_file_ids:
                        self._uploaded_file_ids.remove(file_id)
                    logger.info(f"Successfully deleted file {file_id}")
                    return True
                elif response.status_code == 404:
                    # File already deleted or doesn't exist
                    if file_id in self._uploaded_file_ids:
                        self._uploaded_file_ids.remove(file_id)
                    logger.info(f"File {file_id} not found (already deleted)")
                    return True
                else:
                    # Transient error, retry
                    if attempt < max_retries - 1:
                        wait_time = FILE_DELETE_RETRY_DELAY * (2 ** attempt)
                        logger.warning(
                            f"Delete file {file_id} failed (attempt {attempt + 1}/{max_retries}): "
                            f"{response.status_code} - {response.text}. Retrying in {wait_time}s..."
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(
                            f"Failed to delete file {file_id} after {max_retries} attempts: "
                            f"{response.status_code} - {response.text}"
                        )
                        return False
            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = FILE_DELETE_RETRY_DELAY * (2 ** attempt)
                    logger.warning(
                        f"Request exception while deleting file {file_id} "
                        f"(attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        f"Request exception while deleting file {file_id} after {max_retries} attempts: {e}"
                    )
                    return False
        
        return False
    
    def cleanup(self) -> None:
        """
        Delete all uploaded files if configured to do so.
        
        This ensures that temporary files uploaded to OpenAI are removed to maintain
        statelessness. Failures are logged but do not raise exceptions to avoid
        masking the original operation's success/failure.
        """
        if not self.config.delete_files_after_use:
            return
        
        failed_deletions = []
        for file_id in list(self._uploaded_file_ids):
            if not self.delete_file(file_id):
                failed_deletions.append(file_id)
        
        if failed_deletions:
            logger.error(
                f"Cleanup incomplete: Failed to delete {len(failed_deletions)} file(s): {failed_deletions}. "
                f"Manual cleanup may be required."
            )
        else:
            if self._uploaded_file_ids:
                logger.info(f"All uploaded files cleaned up successfully")
            self._uploaded_file_ids.clear()
    
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
