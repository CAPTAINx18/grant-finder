import logging
from typing import Any, Dict, Type

from app.crawlers.base import BaseCrawler

logger = logging.getLogger(__name__)

# Global registry dict mapping crawler names to their classes
_CRAWLER_REGISTRY: Dict[str, Type[BaseCrawler]] = {}


def register_crawler(name: str):
    """Decorator to register a BaseCrawler implementation."""
    def decorator(cls: Type[BaseCrawler]):
        if name in _CRAWLER_REGISTRY:
            logger.warning(f"Overwriting already registered crawler name: '{name}'")
        _CRAWLER_REGISTRY[name] = cls
        logger.info(f"Registered crawler: '{name}' -> {cls.__name__}")
        return cls
    return decorator


def get_crawler(name: str, source_name: str, config: Dict[str, Any]) -> BaseCrawler:
    """Instantiate a registered crawler by name."""
    if name not in _CRAWLER_REGISTRY:
        raise ValueError(f"Crawler with name '{name}' is not registered.")
    
    crawler_cls = _CRAWLER_REGISTRY[name]
    return crawler_cls(source_name=source_name, config=config)


def list_registered_crawlers() -> Dict[str, str]:
    """List all registered crawler names and their class names."""
    return {name: cls.__name__ for name, cls in _CRAWLER_REGISTRY.items()}
