import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from storage import JsonStorage
from config import DATA_DIR
from core import get_provider, build_messages, build_messages_for_ids, estimate_tokens, find_summary_split

router = APIRouter()
storage = JsonStorage(DATA_DIR)


class ChatRequest(BaseModel):
    canvas_id: str
    parent_card_id: str | None = None
    user_message: str
    provider_id: str | None = None
    model: str | None = None


class SummarizeRequest(BaseModel):
    canvas_id: str
    up_to_card_id: str
    provider_id: str | None = None
    model: str | None = None


DEFAULT_SUMMARY_PROMPT = (
    "请对以上对话内容进行简洁的摘要，保留关键事实、决策和继续对话所需的上下文。"
    "用第三人称、过去时态书写，不超过500字。"
)


async def generate_summary(models_config: dict, messages: list[dict]) -> str:
    """调用摘要模型（或回退到默认模型）生成摘要文本。"""
    summary_model_cfg = models_config.get("summary_model") or models_config["default_model"]
    provider_id = summary_model_cfg["provider_id"]
    model = summary_model_cfg["model"]

    provider_config = next(
        (p for p in models_config["providers"] if p["id"] == provider_id), None
    )
    if not provider_config or not provider_config.get("api_key"):
        raise ValueError(f"摘要模型 provider '{provider_id}' 未配置或缺少 API Key")

    custom_prompt = models_config.get("summary_prompt", "").strip()
    prompt_text = custom_prompt if custom_prompt else DEFAULT_SUMMARY_PROMPT

    summary_prompt = messages + [{
        "role": "user",
        "content": prompt_text,
    }]

    provider = get_provider(provider_config)
    result = ""
    async for chunk in provider.chat(summary_prompt, model, stream=False):
        result += chunk
    return result


@router.post("/stream")
async def chat_stream(req: ChatRequest):
    models_config = await storage.get_models_config()

    provider_id = req.provider_id or models_config["default_model"]["provider_id"]
    model = req.model or models_config["default_model"]["model"]

    provider_config = next(
        (p for p in models_config["providers"] if p["id"] == provider_id), None
    )
    if provider_config is None:
        raise HTTPException(status_code=400, detail=f"Provider '{provider_id}' not found")
    if not provider_config.get("api_key"):
        raise HTTPException(status_code=400, detail="API key not configured")

    canvas = await storage.get_canvas(req.canvas_id)
    if canvas is None:
        raise HTTPException(status_code=404, detail="Canvas not found")

    messages = []
    if req.parent_card_id:
        messages = build_messages(canvas, req.parent_card_id)
    messages.append({"role": "user", "content": req.user_message})

    # --- 自动摘要检测 ---
    summary_event_payload: dict | None = None
    context_limit = provider_config.get("context_limit")
    threshold = float(models_config.get("auto_summary_threshold", 0.8))
    keep_recent = int(models_config.get("auto_summary_keep_recent", 4))

    if context_limit and req.parent_card_id:
        token_estimate = estimate_tokens(messages)
        if token_estimate > threshold * context_limit:
            to_summarize_ids, to_keep_ids = find_summary_split(
                canvas, req.parent_card_id, keep_recent
            )
            if to_summarize_ids:
                cards_map = {c["id"]: c for c in canvas.get("cards", [])}

                # 检查是否可以复用已有摘要节点
                existing_summary = next(
                    (cards_map[cid] for cid in to_summarize_ids
                     if cards_map.get(cid, {}).get("is_summary")),
                    None
                )

                if existing_summary:
                    summary_text = existing_summary["ai_message"]
                    summarized_ids = existing_summary.get("summarized_card_ids", to_summarize_ids)
                else:
                    summary_messages = build_messages_for_ids(canvas, to_summarize_ids)
                    try:
                        summary_text = await generate_summary(models_config, summary_messages)
                        summarized_ids = to_summarize_ids
                    except Exception as e:
                        # 摘要失败时静默降级，继续使用完整上下文
                        summary_text = None
                        summarized_ids = []

                if summary_text:
                    summary_event_payload = {
                        "summary": summary_text,
                        "summarized_card_ids": summarized_ids,
                    }

                    # 用压缩后的上下文替换完整上下文
                    compressed = [
                        {
                            "role": "system",
                            "content": f"[Earlier conversation summary]\n{summary_text}"
                        }
                    ]
                    for cid in to_keep_ids:
                        card = cards_map.get(cid, {})
                        if card.get("user_message"):
                            compressed.append({"role": "user", "content": card["user_message"]})
                        if card.get("ai_message"):
                            compressed.append({"role": "assistant", "content": card["ai_message"]})
                    compressed.append({"role": "user", "content": req.user_message})
                    messages = compressed

    provider = get_provider(provider_config)

    async def event_stream():
        # 先发送摘要事件（若有）
        if summary_event_payload:
            encoded_payload = json.dumps(summary_event_payload, ensure_ascii=False)
            yield f"data: [SUMMARY] {encoded_payload}\n\n"
        try:
            async for token in provider.chat(messages, model, stream=True):
                encoded = token.replace("\\", "\\\\").replace("\n", "\\n")
                yield f"data: {encoded}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/summarize")
async def summarize_conversation(req: SummarizeRequest):
    """手动摘要端点：对指定卡片之前的对话链生成摘要。"""
    models_config = await storage.get_models_config()
    canvas = await storage.get_canvas(req.canvas_id)
    if canvas is None:
        raise HTTPException(status_code=404, detail="Canvas not found")

    messages = build_messages(canvas, req.up_to_card_id)
    if not messages:
        raise HTTPException(status_code=400, detail="No messages to summarize")

    # 收集链上的卡片 ID
    cards_map = {c["id"]: c for c in canvas.get("cards", [])}
    edges = canvas.get("edges", [])
    parent_map: dict[str, str] = {}
    for e in edges:
        if e["target"] not in parent_map:
            parent_map[e["target"]] = e["source"]

    chain_ids: list[str] = []
    current = req.up_to_card_id
    while current and current in cards_map:
        chain_ids.append(current)
        if cards_map[current].get("is_summary"):
            break
        current = parent_map.get(current)
    chain_ids.reverse()

    # 若请求中指定了模型，临时覆盖 summary_model
    if req.provider_id or req.model:
        override_config = dict(models_config)
        override_config["summary_model"] = {
            "provider_id": req.provider_id or models_config["default_model"]["provider_id"],
            "model": req.model or models_config["default_model"]["model"],
        }
        summary_text = await generate_summary(override_config, messages)
    else:
        summary_text = await generate_summary(models_config, messages)

    return {"summary": summary_text, "summarized_card_ids": chain_ids}
