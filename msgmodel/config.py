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
    CLAUDE = "claude"
    
    @classmethod
    def from_string(cls, value: str) -> "Provider":
        """
        Convert string to Provider enum.
        
        Args:
            value: Provider name or shorthand ('o', 'g', 'c', 'openai', 'gemini', 'claude')
            
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
            'c': cls.CLAUDE,
        }
        
        if value in shortcuts:
            return shortcuts[value]
        
        # Support full names
        for provider in cls:
            if provider.value == value:
                return provider
        
        valid = ", ".join([f"'{p.value}'" for p in cls] + ["'o'", "'g'", "'c'"])
        raise ValueError(f"Invalid provider '{value}'. Valid options: {valid}")


# ============================================================================
# API URLs (constants, not configurable per-request)
# ============================================================================
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_FILES_URL = "https://api.openai.com/v1/files"
GEMINI_URL = "https://generativelanguage.googleapis.com"
CLAUDE_URL = "https://api.anthropic.com"

# Environment variable names for API keys
OPENAI_API_KEY_ENV = "OPENAI_API_KEY"
GEMINI_API_KEY_ENV = "GEMINI_API_KEY"  
CLAUDE_API_KEY_ENV = "ANTHROPIC_API_KEY"

# Default API key file names (for backward compatibility)
OPENAI_API_KEY_FILE = "openai-api.key"
GEMINI_API_KEY_FILE = "gemini-api.key"
CLAUDE_API_KEY_FILE = "claude-api.key"


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
        delete_files_after_use: Whether to delete uploaded files after use (default: True).
                               Ensures cleanup of temporary files for statelessness.
    
    Note: store_data parameter has been removed. Zero Data Retention is enforced
    for all requests and cannot be disabled.
    """
    model: str = "gpt-4o"
    temperature: float = 1.0
    top_p: float = 1.0
    max_tokens: int = 1000
    n: int = 1
    delete_files_after_use: bool = True


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
    
    Note: use_paid_api parameter has been removed. Paid tier is now required
    and automatically enforced. Billing verification occurs on first use.
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


@dataclass
class ClaudeConfig:
    """
    Configuration for Anthropic Claude API calls.
    
    **NOT SUPPORTED**: Claude is excluded from this library.
    
    Reason: Claude retains data for up to 30 days for abuse prevention.
    For sensitive information and privacy-critical applications, this retention
    period is incompatible with zero-retention requirements.
    
    Supported alternatives:
    - Google Gemini (paid tier): ~24-72 hour retention for abuse monitoring
    - OpenAI: Zero data retention (non-negotiable enforcement)
    
    If you attempt to use Claude, you will receive a ConfigurationError
    with instructions to use Gemini (paid) or OpenAI instead.
    
    See: https://www.anthropic.com/privacy
    """
    model: str = "claude-sonnet-4-20250514"
    temperature: float = 1.0
    top_p: float = 0.95
    top_k: int = 40
    max_tokens: int = 1000
    cache_control: bool = False


# Type alias for any config
ProviderConfig = OpenAIConfig | GeminiConfig | ClaudeConfig


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
        Provider.CLAUDE: ClaudeConfig,
    }
    return configs[provider]()
