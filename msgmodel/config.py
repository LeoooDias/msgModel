"""
msgmodel.config
~~~~~~~~~~~~~~~

Configuration dataclasses for LLM providers.

These classes provide type-safe, runtime-configurable settings
for each supported provider. Defaults match the original script's
hardcoded values.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum


class Provider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    GEMINI = "gemini"
    
    @classmethod
    def from_string(cls, value: str) -> "Provider":
        """
        Convert string to Provider enum.
        
        Args:
            value: Provider name or shorthand ('o', 'g', 'openai', 'gemini')
            
        Returns:
            Provider enum member
            
        Raises:
            ValueError: If the value is not a valid provider
        """
        value = value.lower().strip()
        
        # Support shorthand codes
        shortcuts = {
            'o': cls.OPENAI,
            'g': cls.GEMINI,
        }
        
        if value in shortcuts:
            return shortcuts[value]
        
        # Support full names
        for provider in cls:
            if provider.value == value:
                return provider
        
        valid = ", ".join([f"'{p.value}'" for p in cls] + ["'o'", "'g'"])
        raise ValueError(f"Invalid provider '{value}'. Valid options: {valid}")


# ============================================================================
# API URLs (constants, not configurable per-request)
# ============================================================================
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
GEMINI_URL = "https://generativelanguage.googleapis.com"

# Environment variable names for API keys
OPENAI_API_KEY_ENV = "OPENAI_API_KEY"
GEMINI_API_KEY_ENV = "GEMINI_API_KEY"

# Default API key file names (for backward compatibility)
OPENAI_API_KEY_FILE = "openai-api.key"
GEMINI_API_KEY_FILE = "gemini-api.key"


@dataclass
class OpenAIConfig:
    """
    Configuration for OpenAI API calls.
    
    **PRIVACY ENFORCEMENT**: Zero Data Retention (ZDR) is REQUIRED and non-negotiable.
    The X-OpenAI-No-Store header is automatically added to all requests.
    
    OpenAI will NOT use your prompts or responses for model training or improvements.
    See: https://platform.openai.com/docs/guides/zero-data-retention
    
    Attributes:
        model: Model identifier (e.g., 'gpt-4o', 'gpt-4o-mini')
        temperature: Sampling temperature (0.0 to 2.0)
        top_p: Nucleus sampling parameter
        max_tokens: Maximum tokens to generate
        n: Number of completions to generate
        api_key: Optional API key. If provided, overrides environment variable.
    
    Note: File uploads are only supported via inline base64-encoding in prompts.
    Files are limited to practical API size constraints (~15-20MB).
    """
    model: str = "gpt-4o"
    temperature: float = 1.0
    top_p: float = 1.0
    max_tokens: int = 1000
    n: int = 1
    api_key: Optional[str] = None


@dataclass
class GeminiConfig:
    """
    Configuration for Google Gemini API calls.
    
    **PRIVACY ENFORCEMENT**: PAID API TIER IS REQUIRED AND ENFORCED.
    
    Gemini paid services (with active Google Cloud Billing and paid quota):
    - Do NOT use your prompts or responses for model training
    - Retain data temporarily for abuse detection only (24-72 hours)
    - Provide near-stateless operation for sensitive materials
    
    UNPAID TIER IS NOT SUPPORTED. Google retains data indefinitely for training
    on unpaid services. This library will verify paid access and raise an error
    if you attempt to use unpaid quota.
    
    See: https://ai.google.dev/gemini-api/terms
    
    Attributes:
        model: Model identifier (e.g., 'gemini-2.5-flash', 'gemini-1.5-pro')
        temperature: Sampling temperature (0.0 to 2.0)
        top_p: Nucleus sampling parameter
        top_k: Top-k sampling parameter
        max_tokens: Maximum tokens to generate
        candidate_count: Number of response candidates
        safety_threshold: Content safety filtering level
        api_version: API version to use
        cache_control: Whether to enable caching
        api_key: Optional API key. If provided, overrides environment variable.
    
    Note: File uploads are only supported via inline base64-encoding in prompts.
    Files are limited to practical API size constraints (~22MB).
    """
    model: str = "gemini-2.5-flash"
    temperature: float = 1.0
    top_p: float = 0.95
    top_k: int = 40
    max_tokens: int = 1000
    candidate_count: int = 1
    safety_threshold: str = "BLOCK_NONE"
    api_version: str = "v1beta"
    cache_control: bool = False
    api_key: Optional[str] = None

# Type alias for supported configs
ProviderConfig = OpenAIConfig | GeminiConfig


def get_default_config(provider: Provider) -> ProviderConfig:
    """
    Get the default configuration for a provider.
    
    Args:
        provider: The LLM provider
        
    Returns:
        Default configuration dataclass for the provider
    """
    configs = {
        Provider.OPENAI: OpenAIConfig,
        Provider.GEMINI: GeminiConfig,
    }
    return configs[provider]()
