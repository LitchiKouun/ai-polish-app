"""文本分段、合并等工具函数。"""

import html
import re

from logger import log_step


def split_paragraphs(text: str) -> list[str]:
    """按空行或换行符将文章拆分为自然段，过滤空白段。"""
    log_step("段落拆分", "开始拆分文章...")
    if not text or not text.strip():
        log_step("段落拆分", "输入为空，未拆分到任何段落", level="warning")
        return []

    stripped = text.strip()
    parts = re.split(r"\n\s*\n", stripped)

    if len(parts) == 1 and "\n" in parts[0]:
        paragraphs = [line.strip() for line in parts[0].split("\n") if line.strip()]
    else:
        paragraphs = []
        for part in parts:
            lines = [line.strip() for line in part.split("\n") if line.strip()]
            if lines:
                paragraphs.append("\n".join(lines))

    log_step("段落拆分", f"拆分完成，共 {len(paragraphs)} 个段落")
    for i, para in enumerate(paragraphs):
        preview = para[:50].replace("\n", " ")
        suffix = "..." if len(para) > 50 else ""
        log_step("段落拆分", f"  段落 {i}: {preview}{suffix}")
    return paragraphs


def merge_paragraphs(paragraphs: list[str]) -> str:
    """将段落列表合并为完整文章，段落之间以空行分隔。"""
    log_step("文章合并", f"开始合并 {len(paragraphs)} 个段落...")
    result = "\n\n".join(p for p in paragraphs if p and p.strip())
    log_step("文章合并", f"合并完成，总字符数: {len(result)}")
    return result


def ensure_list_length(lst: list, length: int, fill_value="") -> list:
    """确保列表长度与段落数一致。"""
    result = list(lst) if lst else []
    while len(result) < length:
        result.append(fill_value if isinstance(fill_value, str) else fill_value)
    return result[:length]


def strip_html(text: str) -> str:
    """去除 HTML 标签并还原实体，确保内容为纯文本。"""
    if not text:
        return ""
    cleaned = re.sub(r"<[^>]+>", "", text)
    return html.unescape(cleaned).strip()


def plain_text(text: str) -> str:
    """展示/API 入库前的纯文本清洗。"""
    return strip_html(text or "")


def create_polish_snapshot(
    *,
    label: str,
    round_num: int,
    current_paragraphs: list[str],
    polished_paragraphs: list[str],
    reasons: list[str],
    accepted: list[bool],
    rejected: list[bool],
    chat_history: list[dict],
) -> dict:
    """创建润色历史快照（深拷贝段落与对话状态）。"""
    return {
        "label": label,
        "round": round_num,
        "current_paragraphs": list(current_paragraphs),
        "polished_paragraphs": list(polished_paragraphs),
        "reasons": list(reasons),
        "accepted": list(accepted),
        "rejected": list(rejected),
        "chat_history": [dict(msg) for msg in chat_history],
    }


def apply_polish_snapshot(snapshot: dict) -> dict:
    """从快照提取可写回 session state 的字段。"""
    return {
        "current_paragraphs": list(snapshot["current_paragraphs"]),
        "polished_paragraphs": list(snapshot["polished_paragraphs"]),
        "reasons": list(snapshot["reasons"]),
        "accepted": list(snapshot["accepted"]),
        "rejected": list(snapshot["rejected"]),
        "chat_history": [dict(msg) for msg in snapshot["chat_history"]],
        "polish_round": snapshot["round"],
    }
