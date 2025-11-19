import json
import logging
from api.core_config import app_configs
from .qianwen_client_manager import get_qianwen_client, execute_qianwen_chat_completion
from api.prompt.prompt_loader import get_prompt

logger = logging.getLogger(__name__)

def get_qianwen_code_review(structured_file_changes):
    """使用通义千问 API 对结构化的代码变更进行 review"""
    client = get_qianwen_client()
    if not client:
        logger.warning("通义千问客户端不可用 (未初始化或初始化失败)。跳过审查。")
        return "[]"
    if not structured_file_changes:
        logger.info("未提供结构化变更以供审查。")
        return "[]"

    all_reviews = []
    current_model = app_configs.get("QIANWEN_MODEL", "qwen-turbo")

    for file_path, file_data in structured_file_changes.items():
        input_data = {
            "file_meta": {
                "path": file_data["path"],
                "old_path": file_data.get("old_path"),
                "lines_changed": file_data.get("lines_changed", len(file_data["changes"])),
                "context": file_data["context"]
            },
            "changes": file_data["changes"]
        }
        try:
            input_json_string = json.dumps(input_data, indent=2, ensure_ascii=False)
        except TypeError as te:
            logger.error(f"序列化文件 {file_path} 的输入数据时出错: {te}")
            logger.error(f"有问题的据结构: {input_data}")
            continue

        user_prompt_for_llm = f"\n\n```json\n{input_json_string}\n```\n"

        try:
            logger.info(f"正在发送文件审查请求: {file_path}...")
            client = get_qianwen_client()
            if not client:
                logger.warning(f"在审查 {file_path} 前通义千问客户端变得不可用。将跳过此文件并继续处理其他文件。")
                continue
            
            detailed_review_system_prompt = get_prompt('detailed_review')
            if "Error: Prompt" in detailed_review_system_prompt:
                logger.error(f"无法加载详细审查的 System Prompt。跳过文件 {file_path}。错误: {detailed_review_system_prompt}")
                continue

            review_json_str = execute_qianwen_chat_completion(
                client,
                current_model,
                detailed_review_system_prompt,
                user_prompt_for_llm,
                "细粒度审查",
                response_format_type="json_object"
            )

            logger.info(f"-------------通义千问输出-----------")
            logger.info(f"文件 {file_path} 的通义千问原始输出:")
            logger.info(f"{review_json_str}")
            logger.info(f"-------------通义千问输出-----------")

            try:
                parsed_output = json.loads(review_json_str)
                reviews_for_file = []
                if isinstance(parsed_output, list):
                    reviews_for_file = parsed_output
                elif isinstance(parsed_output, dict):
                    found_list = False
                    for key, value in parsed_output.items():
                        if isinstance(value, list):
                            reviews_for_file = value
                            found_list = True
                            logger.info(f"在通义千问输出的键 '{key}' 下找到审查列表。")
                            break
                    if not found_list:
                        logger.warning(
                            f"警告: 文件 {file_path} 的通义千问输出是一个字典，但未找到列表值。输出: {review_json_str}")
                        reviews_for_file = [parsed_output]
                else:
                    logger.warning(
                        f"警告: 文件 {file_path} 的通义千问输出不是 JSON 列表或预期的字典。输出: {review_json_str}")

                valid_reviews_for_file = []
                for review in reviews_for_file:
                    if isinstance(review, dict) and all(
                            k in review for k in ["file", "lines", "category", "severity", "analysis", "suggestion"]):
                        if review.get("file") != file_path:
                            logger.warning(f"警告: 修正审查中的文件路径从 '{review.get('file')}' 为 '{file_path}'")
                            review["file"] = file_path
                        valid_reviews_for_file.append(review)
                    else:
                        logger.warning(f"警告: 跳过文件 {file_path} 的无效审查项结构: {review}")
                all_reviews.extend(valid_reviews_for_file)

            except json.JSONDecodeError as json_e:
                logger.error(f"错误: 解析来自通义千问的文件 {file_path} 的 JSON 响应失败: {json_e}")
                logger.error(f"通义千问原始输出为: {review_json_str}")
        except Exception as e:
            logger.exception(f"从通义千问获取文件 {file_path} 的代码审查时出错:")

    try:
        final_json_output = json.dumps(all_reviews, ensure_ascii=False, indent=2)
    except TypeError as te:
        logger.error(f"序列化最终审查列表时出错: {te}")
        logger.error(f"有问题的列表结构: {all_reviews}")
        final_json_output = "[]"

    return final_json_output


def get_qianwen_detailed_review_for_file(file_path: str, file_data: dict, client, model_name: str):
    """
    使用通义千问 API 对单个文件的结构化代码变更进行详细审查。
    返回一个 Python 列表，其中包含该文件的审查意见字典。
    如果文件没有问题或发生错误，则返回空列表。
    """
    if not client:
        logger.warning(f"通义千问客户端不可用 (传递给 get_qianwen_detailed_review_for_file 时)。跳过文件 {file_path} 的审查。")
        return []
    if not file_data:
        logger.info(f"未提供文件 {file_path} 的数据以供详细审查。")
        return []

    input_data = {
        "file_meta": {
            "path": file_data.get("path", file_path),
            "old_path": file_data.get("old_path"),
            "lines_changed": file_data.get("lines_changed", len(file_data.get("changes", []))),
            "context": file_data.get("context", {})
        },
        "changes": file_data.get("changes", [])
    }
    try:
        input_json_string = json.dumps(input_data, indent=2, ensure_ascii=False)
    except TypeError as te:
        logger.error(f"序列化文件 {file_path} 的输入数据时出错: {te}")
        logger.error(f"有问题的输入结构: {input_data}")
        return []

    user_prompt_for_llm = f"\n\n```json\n{input_json_string}\n```\n"

    try:
        logger.info(f"正在发送文件审查请求 (详细): {file_path} 给模型 {model_name}...")
        
        detailed_review_system_prompt = get_prompt('detailed_review')
        if "Error: Prompt" in detailed_review_system_prompt:
            logger.error(f"无法加载详细审查的 System Prompt。跳过文件 {file_path}。错误: {detailed_review_system_prompt}")
            return []

        review_json_str = execute_qianwen_chat_completion(
            client,
            model_name,
            detailed_review_system_prompt,
            user_prompt_for_llm,
            f"文件 {file_path} 的细粒度审查",
            response_format_type="json_object"
        )

        logger.info(f"-------------通义千问输出 (文件: {file_path})-----------")
        logger.info(f"{review_json_str}")
        logger.info(f"-------------通义千问输出结束 (文件: {file_path})-----------")

        try:
            parsed_output = json.loads(review_json_str)
            reviews_for_this_file = []
            if isinstance(parsed_output, list):
                reviews_for_this_file = parsed_output
            elif isinstance(parsed_output, dict):
                found_list = False
                for key, value in parsed_output.items():
                    if isinstance(value, list):
                        reviews_for_this_file = value
                        found_list = True
                        logger.info(f"在通义千问输出的键 '{key}' 下找到文件 {file_path} 的审查列表。")
                        break
                if not found_list:
                    logger.warning(
                        f"警告: 文件 {file_path} 的通义千问输出是一个字典，但未找到列表值。输出: {review_json_str}")
                    reviews_for_this_file = [parsed_output]
            else:
                logger.warning(
                    f"警告: 文件 {file_path} 的通义千问输出不是 JSON 列表或预期的字典。输出: {review_json_str}")
                return []

            valid_reviews = []
            for review in reviews_for_this_file:
                if isinstance(review, dict) and all(
                        k in review for k in ["file", "lines", "category", "severity", "analysis", "suggestion"]):
                    if review.get("file") != file_path:
                        logger.warning(f"警告: 修正审查中的文件路径从 '{review.get('file')}' 为 '{file_path}' (针对文件 {file_path})")
                        review["file"] = file_path
                    valid_reviews.append(review)
                else:
                    logger.warning(f"警告: 跳过文件 {file_path} 的无效审查项结构: {review}")
            return valid_reviews

        except json.JSONDecodeError as json_e:
            logger.error(f"错误: 解析来自通义千问的文件 {file_path} 的 JSON 响应失败: {json_e}")
            logger.error(f"通义千问原始输出为: {review_json_str}")
            return []
    except Exception as e:
        logger.exception(f"从通义千问获取文件 {file_path} 的详细代码审查时出错:")
        return []