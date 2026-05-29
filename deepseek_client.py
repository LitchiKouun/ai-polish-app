"""DeepSeek API 调用封装。"""

import json
import os
import re
import time

from logger import log_error, log_step
from openai import OpenAI
from utils import plain_text


def get_client() -> OpenAI:
    log_step("API 客户端", "正在初始化 DeepSeek 客户端...")
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        log_error("API 客户端", "未设置环境变量 DEEPSEEK_API_KEY")
        raise ValueError("未设置环境变量 DEEPSEEK_API_KEY，请先配置 API Key。")
    log_step("API 客户端", "客户端初始化成功（API Key 已读取）")
    return OpenAI(api_key=api_key, base_url="https://api.deepseek.com")


def _extract_json(text: str) -> dict:
    """从模型返回文本中提取 JSON 对象。"""
    log_step("JSON 解析", "开始解析模型返回内容...")
    text = text.strip()
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence_match:
        text = fence_match.group(1).strip()
        log_step("JSON 解析", "检测到 markdown 代码块，已提取内部 JSON")
    try:
        data = json.loads(text)
        log_step("JSON 解析", f"解析成功，包含 {len(data.get('paragraphs', []))} 个段落结果")
        return data
    except json.JSONDecodeError as e:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                data = json.loads(text[start : end + 1])
                log_step("JSON 解析", "通过截取 JSON 片段解析成功")
                return data
            except json.JSONDecodeError:
                pass
        log_error("JSON 解析", f"解析失败: {e}")
        raise ValueError(f"无法解析模型返回的 JSON：{text[:200]}...") from e


def polish_paragraphs(messages: list[dict], model: str = "deepseek-chat") -> dict:
    """
    调用 DeepSeek 润色段落。

    返回:
        {
            "polished": list[str],
            "reasons": list[str],
            "summary": str,
        }
    """
    log_step("API 调用", f"开始调用 DeepSeek 模型: {model}")
    client = get_client()

    start_time = time.time()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
        )
        elapsed = time.time() - start_time
        log_step("API 调用", f"请求成功，耗时 {elapsed:.2f}s")

        usage = getattr(response, "usage", None)
        if usage:
            log_step(
                "API 调用",
                f"Token 用量 — 输入: {usage.prompt_tokens}, "
                f"输出: {usage.completion_tokens}, 合计: {usage.total_tokens}",
            )
    except Exception as e:
        elapsed = time.time() - start_time
        log_error("API 调用", f"请求失败，耗时 {elapsed:.2f}s", exc=e)
        raise

    content = response.choices[0].message.content or ""
    log_step("API 调用", f"收到响应，内容长度: {len(content)} 字符")

    data = _extract_json(content)

    paragraphs_data = data.get("paragraphs", [])
    paragraphs_data.sort(key=lambda x: x.get("index", 0))

    polished = [plain_text(item.get("polished", "")) for item in paragraphs_data]
    reasons = [plain_text(item.get("reason", "")) for item in paragraphs_data]
    summary = plain_text(data.get("summary", ""))

    log_step("润色结果", f"共生成 {len(polished)} 个润色段落")
    for i, (p, r) in enumerate(zip(polished, reasons)):
        preview = p[:40].replace("\n", " ")
        log_step("润色结果", f"  段落 {i}: {preview}{'...' if len(p) > 40 else ''} | 理由: {r[:30]}{'...' if len(r) > 30 else ''}")

    if summary:
        log_step("润色结果", f"摘要: {summary}")

    return {
        "polished": polished,
        "reasons": reasons,
        "summary": summary,
    }
