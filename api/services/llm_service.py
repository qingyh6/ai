import logging

# 从 llm_client_manager 导入
from .llm_client_manager import (
    openai_client,
    initialize_openai_client,
    get_openai_client
)

# 从 qianwen_client_manager 导入
from .qianwen_client_manager import (
    qianwen_client,
    initialize_qianwen_client,
    get_qianwen_client
)

# 从 llm_review_detailed_service 导入
from .llm_review_detailed_service import get_openai_code_review, get_openai_detailed_review_for_file

# 从 llm_review_general_service 导入
from .llm_review_general_service import get_openai_code_review_general

logger = logging.getLogger(__name__)

# 使它们可以从此模块导入
__all__ = [
    # OpenAI 相关
    "openai_client",
    "initialize_openai_client",
    "get_openai_client",
    "get_openai_code_review",
    "get_openai_detailed_review_for_file",
    "get_openai_code_review_general",
    
    # 通义千问相关
    "qianwen_client",
    "initialize_qianwen_client",
    "get_qianwen_client",
]

logger.info("LLM 服务已初始化，支持 OpenAI 和通义千问。")
