import logging
import openai
from api.core_config import app_configs

logger = logging.getLogger(__name__)

qianwen_client = None

def initialize_qianwen_client():
    """根据 app_configs 初始化或重新初始化全局通义千问客户端。"""
    global qianwen_client
    import os
    
    try:
        current_api_key = app_configs.get("QIANWEN_API_KEY")
        current_model = app_configs.get("QIANWEN_MODEL", "qwen-plus")
        current_base_url = app_configs.get("QIANWEN_API_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

        if not current_api_key or current_api_key == "xxxx-xxxx-xxxx-xxxx":
            logger.warning(
                "警告: 通义千问 API Key 未配置或为占位符。通义千问客户端将不会初始化。")
            qianwen_client = None
            return

        logger.info(f"初始化通义千问客户端，使用模型: {current_model}")
        logger.info(f"使用Base URL: {current_base_url}")
        
        # 检查环境变量
        dashscope_key = os.environ.get("DASHSCOPE_API_KEY")
        if dashscope_key:
            logger.info("检测到 DASHSCOPE_API_KEY 环境变量，将使用该值")
            # 设置环境变量，让 openai 客户端自动使用
            os.environ["OPENAI_API_KEY"] = dashscope_key
            current_api_key = dashscope_key
        else:
            # 使用配置中的 API Key
            os.environ["OPENAI_API_KEY"] = current_api_key
        
        # 设置 Base URL
        os.environ["OPENAI_BASE_URL"] = current_base_url
        
        # 使用官方推荐的初始化方式：通过环境变量
        client = openai.OpenAI(
        # 若没有配置环境变量，请用阿里云百炼API Key将下行替换为：api_key="sk-xxx",
        # 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
        api_key="sk-c7fc4081b2ad475eafbfa2e18bcf8b18",
        # 以下是北京地域base_url，如果使用新加坡地域的模型，需要将base_url替换为：https://dashscope-intl.aliyuncs.com/compatible-mode/v1
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
        # qianwen_client = openai.OpenAI()
        logger.info(f"通义千问客户端已初始化/重新初始化。将使用的模型: {current_model}")
        logger.info(f"API Key 来源: {'DASHSCOPE_API_KEY 环境变量' if dashscope_key else 'QIANWEN_API_KEY 配置'}")
        
    except Exception as e:
        logger.error(f"初始化通义千问客户端时出错: {e}")
        logger.error(f"错误类型: {type(e).__name__}")
        logger.error("请确保通过管理面板或环境变量设置了通义千问 API Key。")
        qianwen_client = None


def get_qianwen_client():
    """获取通义千问客户端实例，如果未初始化则尝试初始化。"""
    global qianwen_client
    if qianwen_client is None:
        logger.info("通义千问客户端为 None，尝试初始化...")
        initialize_qianwen_client()
    return qianwen_client


def execute_qianwen_chat_completion(client, model_name: str, system_prompt: str, user_prompt: str, context_description: str,
                                   response_format_type: str = None):
    """
    执行通义千问 LLM 请求。

    :param client: 通义千问客户端实例。
    :param model_name: 要使用的模型名称。
    :param system_prompt: 系统提示。
    :param user_prompt: 用户原始提示。
    :param context_description: 用于日志的上下文描述。
    :param response_format_type: 可选，响应格式类型 (例如 "json_object")。
    :return: LLM 的响应内容。
    """
    
    # 构建消息列表
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if user_prompt:
        messages.append({"role": "user", "content": user_prompt})

    completion_params = {
        "model": model_name,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 4000
    }
    
    if response_format_type == "json_object":
        completion_params["response_format"] = {"type": "json_object"}

    try:
        response = client.chat.completions.create(**completion_params)
        
        if response and response.choices:
            content = response.choices[0].message.content
            logger.info(f"通义千问响应成功 ({context_description})")
            
            # 如果需要 JSON 格式，尝试解析
            if response_format_type == "json_object":
                try:
                    return content
                except Exception as e:
                    logger.warning(f"通义千问响应不是有效的 JSON 格式 ({context_description}): {e}")
                    return content
            else:
                return content
        else:
            logger.error(f"通义千问 API 请求失败 ({context_description}): {response}")
            return f"Error: 通义千问 API 请求失败 ({context_description})"
            
    except Exception as e:
        logger.error(f"处理通义千问响应时发生错误 ({context_description}): {e}")
        return f"Error: 处理通义千问响应时发生错误 ({context_description}): {str(e)}"