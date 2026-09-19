from typing import AsyncGenerator
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionChunk

from .base import BaseProvider

# 内容安全相关的错误关键词
CONTENT_SAFETY_KEYWORDS = [
    "inappropriate content",
    "content policy violation",
    "ContentPolicyViolation",
    "sensitive",
    "安全",
    "违规",
    "不当内容",
    "内容审核",
]


def _is_content_safety_error(error: Exception) -> bool:
    """判断是否为内容安全相关的错误"""
    error_msg = str(error).lower()
    return any(keyword.lower() in error_msg for keyword in CONTENT_SAFETY_KEYWORDS)


def _get_friendly_error_message(error: Exception) -> str:
    """根据错误类型返回友好的错误信息"""
    if _is_content_safety_error(error):
        return (
            "内容审核未通过。这可能是由于输入或回复中包含敏感内容。\n"
            "建议：\n"
            "1. 检查并修改您的问题，避免敏感词汇\n"
            "2. 尝试重新表述问题\n"
            "3. 如果问题持续，可以尝试切换其他模型"
        )
    return str(error)


class OpenAICompatProvider(BaseProvider):
    def __init__(self, base_url: str, api_key: str):
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)

    async def chat(
        self,
        messages: list[dict],
        model: str,
        stream: bool = True,
    ) -> AsyncGenerator[str, None]:
        try:
            if stream:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    stream=True,
                )
                async for chunk in response:
                    if not chunk.choices:
                        continue
                    # 检查是否因内容安全被拒绝
                    finish_reason = chunk.choices[0].finish_reason
                    if finish_reason == "content_filter":
                        raise Exception(
                            "Output data may contain inappropriate content. "
                            "For details, see: https://help.aliyun.com/zh/model-studio/error-code#inappropriate-content"
                        )
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yield delta
            else:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    stream=False,
                )
                # 检查是否因内容安全被拒绝
                finish_reason = response.choices[0].finish_reason
                if finish_reason == "content_filter":
                    raise Exception(
                        "Output data may contain inappropriate content. "
                        "For details, see: https://help.aliyun.com/zh/model-studio/error-code#inappropriate-content"
                    )
                yield response.choices[0].message.content or ""
        except Exception as e:
            # 将原始错误转换为友好的错误信息
            raise Exception(_get_friendly_error_message(e)) from e
