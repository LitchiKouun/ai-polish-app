"""System prompt 及消息构建。"""

from logger import log_step

SYSTEM_PROMPT = """你是一位专业的中文文章润色助手。用户会提供若干段落及润色要求，你需要对每一段分别进行润色。

## 输出要求
你必须且只能返回一段合法的 JSON，不要包含任何其他文字、markdown 代码块标记或解释。JSON 结构严格如下：

{
  "paragraphs": [
    {
      "index": 0,
      "polished": "润色后的段落文本",
      "reason": "此处给出中文润色理由，简要说明修改思路"
    }
  ],
  "summary": "用一两句话概括本次润色的整体说明（用于对话回复）"
}

## 润色原则
1. 保持原意，提升表达质量、流畅度与可读性。
2. 遵循用户在对话中提出的风格、语气、字数等全部要求。
3. 为每个段落都返回润色结果，index 从 0 开始连续编号，数量必须与输入段落数一致。
4. polished 字段只包含润色后的段落正文，必须是纯文本，禁止包含 HTML 标签、markdown 或 JSON。
5. reason 字段用中文简要说明修改原因，必须是纯文本，禁止包含 HTML 标签。"""


def build_polish_messages(
    paragraphs: list[str],
    chat_history: list[dict],
) -> list[dict]:
    """构建发送给 DeepSeek 的 messages 列表。"""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for msg in chat_history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    paragraph_block = "\n\n".join(
        f"【段落 {i}】\n{text}" for i, text in enumerate(paragraphs)
    )
    user_content = (
        f"请对以下 {len(paragraphs)} 个段落进行润色。"
        f"请严格按 JSON 格式返回结果。\n\n{paragraph_block}"
    )
    messages.append({"role": "user", "content": user_content})

    log_step(
        "消息构建",
        f"已构建 {len(messages)} 条消息（含 system），待润色段落数: {len(paragraphs)}，"
        f"对话历史: {len(chat_history)} 条",
    )
    return messages


def build_chat_user_message(content: str) -> dict:
    return {"role": "user", "content": content}


def build_chat_assistant_message(summary: str, paragraph_count: int) -> dict:
    text = summary or f"已完成 {paragraph_count} 个段落的润色建议，请在左侧查看并选择接受或保留原文。"
    return {"role": "assistant", "content": text}
