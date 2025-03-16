"""
Configuration handling for the Lightroom AI script.
"""

import json
import os
import re
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Union


@dataclass
class AiProviderConfig:
    """Base class for AI provider configurations."""
    provider_type: str


@dataclass
class ClaudeConfig(AiProviderConfig):
    """Claude API configuration."""
    provider_type: str = "claude"
    api_key: str = ""
    api_url: str = "https://api.anthropic.com/v1/messages"
    model: str = "claude-v1"
    use_batch_api: bool = False


@dataclass
class OllamaConfig(AiProviderConfig):
    """Ollama API configuration."""
    provider_type: str = "ollama"
    api_url: str = "http://localhost:11434/api/generate"
    model: str = ""


@dataclass
class OpenRouterConfig(AiProviderConfig):
    """OpenRouter API configuration."""
    provider_type: str = "openrouter"
    api_key: str = ""
    api_url: str = "https://openrouter.ai/api/v1/chat/completions"
    model: str = "anthropic/claude-3-opus"
    site_url: str = "https://lightroom-ai-tool.example.com"
    title: str = "Lightroom AI Tool"


@dataclass
class AppConfig:
    """Main application configuration."""
    provider: Union[ClaudeConfig, OllamaConfig, OpenRouterConfig] = field(default_factory=ClaudeConfig)
    max_retries: int = 3
    batch_size: int = 10
    preview_max_resolution: int = 1024
    log_level: str = "INFO"
    debug_mode: bool = False
    use_smart_previews: bool = True
    max_workers: int = 1
    use_checkpoint: bool = True
    checkpoint_interval: int = 5
    memory_limit_mb: int = 1024
    log_file: Optional[str] = None
    max_images: Optional[int] = None
    deep_search: bool = True
    use_original_if_no_preview: bool = False
    known_preview_patterns: List[str] = field(default_factory=list)
    use_preview_db: bool = True
    use_id_global: bool = True
    db_busy_timeout: int = 5000
    use_categorical_keywords: bool = False
    use_hierarchical_keywords: bool = False
    keyword_delimiter: str = "|"
    categories: List[str] = field(default_factory=list)
    keyword_consolidation: bool = False
    keyword_cluster_threshold: float = 0.7  # Similarity threshold for clustering keywords
    keyword_similarity_threshold: float = 0.92  # Added to match config.json
    use_llm_grouping: bool = False  # Whether to use LLM for keyword grouping
    use_llm_clustering: bool = False  # Whether to use LLM for keyword clustering
    purge_unused_keywords: bool = False  # Whether to purge unused keywords after harmonization


def _substitute_env_vars(value: Any) -> Any:
    """
    Substitute environment variables in string values.
    
    Args:
        value: Value to process for environment variables
        
    Returns:
        Value with environment variables substituted
    """
    if not isinstance(value, str):
        return value
        
    # Pattern to match ${ENV_VAR} syntax
    pattern = r'\${([^}]+)}'
    
    def replace_env_var(match):
        env_var = match.group(1)
        env_value = os.environ.get(env_var)
        if env_value is None:
            print(f"Warning: Environment variable {env_var} not found")
            return ""
        return env_value
    
    return re.sub(pattern, replace_env_var, value)


def _process_config_dict(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a configuration dictionary to substitute environment variables.
    
    Args:
        config_dict: Dictionary containing configuration values
        
    Returns:
        Processed dictionary with environment variables substituted
    """
    result = {}
    
    for key, value in config_dict.items():
        if isinstance(value, dict):
            # Recursively process nested dictionaries
            result[key] = _process_config_dict(value)
        elif isinstance(value, list):
            # Process lists
            result[key] = [
                _process_config_dict(item) if isinstance(item, dict) else _substitute_env_vars(item)
                for item in value
            ]
        else:
            # Process scalar values
            result[key] = _substitute_env_vars(value)
    
    return result


def load_config(config_path: str) -> AppConfig:
    """
    Load and validate configuration from JSON file.
    
    Args:
        config_path: Path to the configuration JSON file
        
    Returns:
        AppConfig object
    
    Raises:
        ValueError: If the configuration is invalid
        RuntimeError: If the configuration file cannot be loaded
    """
    # Resolve the config path
    config_path = os.path.abspath(os.path.expanduser(config_path))
    
    try:
        with open(config_path, 'r') as cfg:
            config_dict = json.load(cfg)
        
        # Process environment variables in the config
        config_dict = _process_config_dict(config_dict)
        
        # Validate provider
        if 'provider' not in config_dict:
            raise ValueError("Missing required configuration field: provider")
        
        # Create provider-specific config
        provider_type = config_dict.pop('provider', 'claude')
        provider_config = None
        
        if provider_type == 'claude':
            if 'claude_api_key' not in config_dict:
                raise ValueError("Missing Claude API key in configuration")
            
            provider_config = ClaudeConfig(
                api_key=config_dict.pop('claude_api_key', ''),
                api_url=config_dict.pop('claude_api_url', "https://api.anthropic.com/v1/messages"),
                model=config_dict.pop('claude_model', "claude-v1"),
                use_batch_api=config_dict.pop('use_batch_api', False)
            )
        elif provider_type == 'ollama':
            if 'ollama_model' not in config_dict:
                raise ValueError("Missing Ollama model in configuration")
                
            provider_config = OllamaConfig(
                api_url=config_dict.pop('ollama_api_url', "http://localhost:11434/api/generate"),
                model=config_dict.pop('ollama_model', "")
            )
        elif provider_type == 'openrouter':
            if 'openrouter_api_key' not in config_dict:
                raise ValueError("Missing OpenRouter API key in configuration")
                
            provider_config = OpenRouterConfig(
                api_key=config_dict.pop('openrouter_api_key', ''),
                api_url=config_dict.pop('openrouter_api_url', "https://openrouter.ai/api/v1/chat/completions"),
                model=config_dict.pop('openrouter_model', "anthropic/claude-3-opus"),
                site_url=config_dict.pop('openrouter_site_url', "https://lightroom-ai-tool.example.com"),
                title=config_dict.pop('openrouter_title', "Lightroom AI Tool")
            )
        else:
            raise ValueError(f"Unsupported AI provider: {provider_type}")
        
        # Handle keyword_similarity_threshold if present (map to keyword_cluster_threshold)
        if 'keyword_similarity_threshold' in config_dict:
            config_dict['keyword_cluster_threshold'] = config_dict.pop('keyword_similarity_threshold')
        
        # Create main config with remaining fields
        app_config = AppConfig(provider=provider_config, **config_dict)
        return app_config
        
    except (json.JSONDecodeError, IOError) as e:
        raise RuntimeError(f"Failed to load configuration from {config_path}: {str(e)}")


def save_config(config: AppConfig, config_path: str) -> None:
    """
    Save configuration to JSON file.
    
    Args:
        config: AppConfig object
        config_path: Path to save the configuration
        
    Raises:
        RuntimeError: If the configuration cannot be saved
    """
    try:
        # Convert to dictionary
        config_dict = asdict(config)
        
        # Extract provider config
        provider_config = config_dict.pop('provider', {})
        provider_type = provider_config.pop('provider_type', 'claude')
        config_dict['provider'] = provider_type
        
        # Add provider-specific fields
        if provider_type == 'claude':
            config_dict['claude_api_key'] = provider_config.get('api_key', '')
            config_dict['claude_api_url'] = provider_config.get('api_url', '')
            config_dict['claude_model'] = provider_config.get('model', '')
            config_dict['use_batch_api'] = provider_config.get('use_batch_api', False)
        elif provider_type == 'ollama':
            config_dict['ollama_api_url'] = provider_config.get('api_url', '')
            config_dict['ollama_model'] = provider_config.get('model', '')
        elif provider_type == 'openrouter':
            config_dict['openrouter_api_key'] = provider_config.get('api_key', '')
            config_dict['openrouter_api_url'] = provider_config.get('api_url', '')
            config_dict['openrouter_model'] = provider_config.get('model', '')
            config_dict['openrouter_site_url'] = provider_config.get('site_url', '')
            config_dict['openrouter_title'] = provider_config.get('title', '')
        
        # Use keyword_similarity_threshold in the output for backward compatibility
        if 'keyword_cluster_threshold' in config_dict:
            config_dict['keyword_similarity_threshold'] = config_dict.pop('keyword_cluster_threshold')
        
        with open(config_path, 'w') as f:
            json.dump(config_dict, f, indent=2)
    except (IOError, TypeError) as e:
        raise RuntimeError(f"Failed to save configuration: {str(e)}")
