import logging
from api.core_config import app_configs

logger = logging.getLogger(__name__)

def get_code_review_service():
    """根据配置返回相应的审查服务"""
    use_qianwen = app_configs.get("USE_QIANWEN", False)
    
    if use_qianwen:
        logger.info("使用通义千问进行代码审查")
        from .qianwen_review_detailed_service import get_qianwen_code_review
        return get_qianwen_code_review
    else:
        logger.info("使用 OpenAI 进行代码审查")
        from .llm_review_detailed_service import get_openai_code_review
        return get_openai_code_review


def get_detailed_review_service():
    """根据配置返回相应的详细审查服务"""
    use_qianwen = app_configs.get("USE_QIANWEN", False)
    
    if use_qianwen:
        logger.info("使用通义千问进行详细审查")
        from .qianwen_review_detailed_service import get_qianwen_detailed_review_for_file
        return get_qianwen_detailed_review_for_file
    else:
        logger.info("使用 OpenAI 进行详细审查")
        from .llm_review_detailed_service import get_openai_detailed_review_for_file
        return get_openai_detailed_review_for_file


def get_general_review_service():
    """根据配置返回相应的通用审查服务"""
    use_qianwen = app_configs.get("USE_QIANWEN", False)
    
    if use_qianwen:
        logger.info("使用通义千问进行通用审查")
        from .qianwen_review_general_service import get_qianwen_code_review_general
        return get_qianwen_code_review_general
    else:
        logger.info("使用 OpenAI 进行通用审查")
        from .llm_review_general_service import get_openai_code_review_general
        return get_openai_code_review_general


def get_llm_client():
    """根据配置返回相应的 LLM 客户端"""
    use_qianwen = app_configs.get("USE_QIANWEN", False)
    
    if use_qianwen:
        logger.info("使用通义千问客户端")
        from .qianwen_client_manager import get_qianwen_client
        return get_qianwen_client
    else:
        logger.info("使用 OpenAI 客户端")
        from .llm_client_manager import get_openai_client
        return get_openai_client


def initialize_llm_client():
    """根据配置初始化相应的 LLM 客户端"""
    use_qianwen = app_configs.get("USE_QIANWEN", False)
    
    if use_qianwen:
        logger.info("初始化通义千问客户端")
        from .qianwen_client_manager import initialize_qianwen_client
        return initialize_qianwen_client()
    else:
        logger.info("初始化 OpenAI 客户端")
        from .llm_client_manager import initialize_openai_client
        return initialize_openai_client()