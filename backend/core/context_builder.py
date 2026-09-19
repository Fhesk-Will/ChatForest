def build_messages(canvas: dict, target_card_id: str) -> list[dict]:
    """从目标卡片向上回溯，构建完整的对话历史 messages 列表。
    遇到 is_summary=true 的卡片时停止向上追溯，将其 ai_message 作为 system 消息注入。
    """
    cards = {c["id"]: c for c in canvas.get("cards", [])}
    edges = canvas.get("edges", [])

    parent_map: dict[str, str] = {}
    for e in edges:
        if e["target"] not in parent_map:
            parent_map[e["target"]] = e["source"]

    chain = []
    current = target_card_id
    while current and current in cards:
        card = cards[current]
        chain.append(card)
        if card.get("is_summary"):
            break
        current = parent_map.get(current)

    chain.reverse()

    messages = []
    for card in chain:
        if card.get("is_summary"):
            if card.get("ai_message"):
                messages.append({
                    "role": "system",
                    "content": f"[Earlier conversation summary]\n{card['ai_message']}"
                })
        else:
            if card.get("user_message"):
                messages.append({"role": "user", "content": card["user_message"]})
            if card.get("ai_message"):
                messages.append({"role": "assistant", "content": card["ai_message"]})

    return messages


def build_messages_for_ids(canvas: dict, card_ids: list[str]) -> list[dict]:
    """为指定有序 ID 列表构建消息（不做摘要感知，用于生成摘要时的原始内容）。"""
    cards_map = {c["id"]: c for c in canvas.get("cards", [])}
    messages = []
    for cid in card_ids:
        card = cards_map.get(cid, {})
        if card.get("user_message"):
            messages.append({"role": "user", "content": card["user_message"]})
        if card.get("ai_message"):
            messages.append({"role": "assistant", "content": card["ai_message"]})
    return messages


def estimate_tokens(messages: list[dict]) -> int:
    """粗估 token 数（字符数 / 4）。"""
    return sum(len(m.get("content", "")) for m in messages) // 4


def find_summary_split(
    canvas: dict, target_card_id: str, keep_recent: int
) -> tuple[list[str], list[str]]:
    """
    返回 (to_summarize_ids, to_keep_ids)。
    to_summarize_ids: 应被压缩的卡片 ID（较早部分）。
    to_keep_ids: 保留的最近 keep_recent 条卡片 ID。
    遇到 is_summary 节点时停止向上追溯。
    """
    cards = {c["id"]: c for c in canvas.get("cards", [])}
    edges = canvas.get("edges", [])

    parent_map: dict[str, str] = {}
    for e in edges:
        if e["target"] not in parent_map:
            parent_map[e["target"]] = e["source"]

    chain_ids: list[str] = []
    current = target_card_id
    while current and current in cards:
        chain_ids.append(current)
        if cards[current].get("is_summary"):
            break
        current = parent_map.get(current)

    chain_ids.reverse()

    if len(chain_ids) <= keep_recent:
        return [], chain_ids

    split = len(chain_ids) - keep_recent
    return chain_ids[:split], chain_ids[split:]
