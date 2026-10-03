"""Lazy loader for optional RAG dependencies."""

import os
from functools import lru_cache


@lru_cache(maxsize=1)
def get_rag_service():
    if not os.environ.get('DEEPSEEK_API_KEY'):
        return None

    try:
        from .services_deepseek import DeepSeekRAGService
    except ImportError:
        return None

    return DeepSeekRAGService()
