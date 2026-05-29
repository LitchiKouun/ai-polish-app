"""AI 文章润色助手 - Streamlit 主应用。"""

import html

import streamlit as st

from deepseek_client import polish_paragraphs
from logger import log_error, log_step
from prompts import (
    build_chat_assistant_message,
    build_chat_user_message,
    build_polish_messages,
)
from utils import ensure_list_length, merge_paragraphs, plain_text, split_paragraphs

# ---------------------------------------------------------------------------
# 页面配置与全局样式
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="AI 文章润色助手",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CUSTOM_CSS = """
<style>
    footer {visibility: hidden;}
    .block-container {padding-top: 1rem; padding-bottom: 0.5rem; max-width: 100%;}

    .app-title {
        font-size: 1.4rem;
        font-weight: 600;
        color: #1a1a2e;
        margin-bottom: 0.25rem;
    }
    .app-subtitle {
        font-size: 0.85rem;
        color: #6b7280;
        margin-bottom: 0.75rem;
    }
    .section-header {
        font-size: 0.9rem;
        font-weight: 600;
        color: #374151;
        margin: 0.25rem 0 0.5rem 0;
    }

    /* 左右栏等高容器 */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 10px !important;
    }

    /* 段落只读文本框 */
    div[data-testid="stTextArea"] textarea:disabled {
        color: #374151 !important;
        -webkit-text-fill-color: #374151 !important;
        opacity: 1 !important;
    }
    .text-box {
        border-radius: 6px;
        padding: 10px 12px;
        line-height: 1.7;
        font-size: 0.95rem;
        white-space: pre-wrap;
        word-break: break-word;
        margin-bottom: 0.5rem;
    }
    .text-box.orig {
        background: #f3f4f6;
        color: #374151;
    }
    .text-box.orig.dimmed {
        opacity: 0.45;
        color: #9ca3af;
        text-decoration: line-through;
    }
    .text-box.polished {
        background: #dbeafe;
        color: #1e3a5f;
    }
    .text-box.polished.dimmed {
        opacity: 0.45;
        text-decoration: line-through;
    }
    .reason-caption {
        font-size: 0.82rem;
        font-style: italic;
        color: #6b7280;
        margin-bottom: 0.75rem;
    }
    .reason-caption.dimmed {
        opacity: 0.45;
    }

    /* 右侧聊天 */
    .chat-header {
        font-weight: 600;
        color: #1f2937;
        font-size: 0.95rem;
        padding-bottom: 8px;
        margin-bottom: 4px;
        border-bottom: 1px solid #e5e7eb;
    }
    .chat-messages-wrap {
        min-height: 120px;
    }
    .chat-bubble {
        max-width: 88%;
        padding: 8px 12px;
        border-radius: 12px;
        margin-bottom: 10px;
        font-size: 0.9rem;
        line-height: 1.55;
        word-break: break-word;
        white-space: pre-wrap;
    }
    .chat-bubble.user {
        background: #3b82f6;
        color: #fff;
        margin-left: auto;
        border-bottom-right-radius: 4px;
    }
    .chat-bubble.assistant {
        background: #fff;
        color: #1f2937;
        border: 1px solid #e5e7eb;
        margin-right: auto;
        border-bottom-left-radius: 4px;
    }
    .chat-empty {
        color: #9ca3af;
        font-size: 0.88rem;
        text-align: center;
        padding: 32px 16px;
        line-height: 1.6;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session State
# ---------------------------------------------------------------------------

def init_session_state():
    defaults = {
        "original_paragraphs": [],
        "current_paragraphs": [],
        "polished_paragraphs": [],
        "reasons": [],
        "accepted": [],
        "rejected": [],
        "chat_history": [],
        "polish_active": False,
        "export_text": "",
        "_logger_initialized": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    if not st.session_state._logger_initialized:
        log_step("应用启动", "Session 状态初始化完成")
        st.session_state._logger_initialized = True


def run_polish(chat_user_msg: str | None = None):
    """触发润色 API 调用，更新 session state。"""
    trigger = "对话触发" if chat_user_msg else "开始润色"
    log_step(trigger, "开始执行润色流程...")

    paragraphs = st.session_state.current_paragraphs
    if not paragraphs:
        log_step(trigger, "失败：没有可润色的段落", level="warning")
        st.error("没有可润色的段落，请先输入文章并点击「开始润色」。")
        return

    if chat_user_msg:
        log_step(trigger, f"用户消息: {chat_user_msg}")
        st.session_state.chat_history.append(build_chat_user_message(chat_user_msg))

    try:
        with st.spinner("AI 正在润色，请稍候..."):
            messages = build_polish_messages(
                paragraphs, st.session_state.chat_history
            )
            result = polish_paragraphs(messages)

        count = len(paragraphs)
        polished = [plain_text(p) for p in ensure_list_length(result["polished"], count, "")]
        reasons = [plain_text(r) for r in ensure_list_length(result["reasons"], count, "")]

        st.session_state.polished_paragraphs = polished
        st.session_state.reasons = reasons
        st.session_state.accepted = ensure_list_length(st.session_state.accepted, count, False)
        st.session_state.rejected = ensure_list_length(
            st.session_state.get("rejected", []), count, False
        )

        auto_applied = 0
        for i in range(count):
            if st.session_state.accepted[i]:
                st.session_state.current_paragraphs[i] = polished[i]
                auto_applied += 1
            else:
                st.session_state.rejected[i] = False

        st.session_state.chat_history.append(
            build_chat_assistant_message(result.get("summary", ""), count)
        )
        st.session_state.polish_active = True

        log_step(
            trigger,
            f"润色完成 — 共 {count} 段，已自动应用到 {auto_applied} 个已接受段落",
        )

    except ValueError as e:
        if chat_user_msg:
            st.session_state.chat_history.pop()
        log_error(trigger, str(e), exc=e)
        st.error(str(e))
    except Exception as e:
        if chat_user_msg:
            st.session_state.chat_history.pop()
        log_error(trigger, f"润色失败: {e}", exc=e)
        st.error(f"润色失败：{e}")


def start_polish():
    """首次拆分段落并触发润色。"""
    log_step("开始润色", "用户点击「开始润色」按钮")
    text = st.session_state.get("raw_article_input", "")
    log_step("开始润色", f"输入文章长度: {len(text)} 字符")

    paragraphs = split_paragraphs(text)
    if not paragraphs:
        log_step("开始润色", "失败：文章内容为空", level="warning")
        st.error("请输入文章内容，段落之间请用空行分隔。")
        return

    st.session_state.original_paragraphs = paragraphs
    st.session_state.current_paragraphs = list(paragraphs)
    st.session_state.polished_paragraphs = [""] * len(paragraphs)
    st.session_state.reasons = [""] * len(paragraphs)
    st.session_state.accepted = [False] * len(paragraphs)
    st.session_state.rejected = [False] * len(paragraphs)
    log_step("开始润色", "段落状态已初始化，准备调用 API")
    run_polish()


def accept_paragraph(index: int):
    log_step("接受润色", f"段落 {index} 已接受润色")
    st.session_state.accepted[index] = True
    st.session_state.rejected[index] = False
    st.session_state.current_paragraphs[index] = st.session_state.polished_paragraphs[index]
    preview = st.session_state.current_paragraphs[index][:40]
    log_step("接受润色", f"  当前内容: {preview}{'...' if len(st.session_state.current_paragraphs[index]) > 40 else ''}")


def reject_paragraph(index: int):
    log_step("保留原文", f"段落 {index} 保留原文")
    st.session_state.accepted[index] = False
    st.session_state.rejected[index] = True
    st.session_state.current_paragraphs[index] = st.session_state.original_paragraphs[index]


def _esc(text: str) -> str:
    return html.escape(text or "")


def render_chat_messages() -> str:
    """返回聊天消息的 HTML 字符串。"""
    history = st.session_state.chat_history
    if not history:
        return (
            '<div class="chat-empty">'
            "在此输入润色要求，例如：<br>"
            "「请将文章改为更正式的学术风格」<br>"
            "「每段控制在 100 字以内」<br>"
            "「让语气更幽默一些」"
            "</div>"
        )

    bubbles = []
    for msg in history:
        role_class = "user" if msg["role"] == "user" else "assistant"
        bubbles.append(
            f'<div class="chat-bubble {role_class}">{_esc(msg["content"])}</div>'
        )
    return "".join(bubbles)


def _text_box(text: str, box_class: str) -> None:
    """用单块 HTML 展示纯文本（内容经转义，避免标签被渲染）。"""
    st.markdown(
        f'<div class="text-box {box_class}">{_esc(text)}</div>',
        unsafe_allow_html=True,
    )


def render_paragraph_card(index: int):
    original = plain_text(st.session_state.original_paragraphs[index])
    polished = plain_text(
        st.session_state.polished_paragraphs[index]
        if index < len(st.session_state.polished_paragraphs)
        else ""
    )
    reason = plain_text(
        st.session_state.reasons[index] if index < len(st.session_state.reasons) else ""
    )
    is_accepted = (
        st.session_state.accepted[index] if index < len(st.session_state.accepted) else False
    )
    is_rejected = (
        st.session_state.rejected[index] if index < len(st.session_state.rejected) else False
    )

    with st.container(border=True):
        header_l, header_r = st.columns([2, 1])
        with header_l:
            st.markdown(f"**段落 {index + 1}**")
        with header_r:
            if is_accepted:
                st.markdown(":green[**✅ 已接受**]")
            elif is_rejected and polished:
                st.markdown(":gray[**❌ 保留原文**]")
            elif polished:
                st.markdown(":orange[**⏳ 待确认**]")

        st.caption("原始段落")
        orig_class = "orig dimmed" if is_accepted else "orig"
        _text_box(original, orig_class)

        if polished:
            st.caption("AI 润色版本")
            polish_class = "polished dimmed" if is_rejected else "polished"
            _text_box(polished, polish_class)

            if reason:
                reason_class = "reason-caption dimmed" if is_rejected else "reason-caption"
                st.markdown(
                    f'<div class="{reason_class}">💡 {_esc(reason)}</div>',
                    unsafe_allow_html=True,
                )

            col1, col2, _ = st.columns([1, 1, 2])
            with col1:
                if st.button("✅ 接受润色", key=f"accept_{index}", use_container_width=True):
                    accept_paragraph(index)
                    st.rerun()
            with col2:
                if st.button("❌ 保留原文", key=f"reject_{index}", use_container_width=True):
                    reject_paragraph(index)
                    st.rerun()


# ---------------------------------------------------------------------------
# 主界面
# ---------------------------------------------------------------------------

init_session_state()

st.markdown('<div class="app-title">✨ AI 文章润色助手</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-subtitle">左侧编辑与润色 · 右侧对话调整风格 · 逐段确认后导出</div>',
    unsafe_allow_html=True,
)

left_col, right_col = st.columns([0.6, 0.4], gap="medium")

PANEL_HEIGHT = 720

# ---- 左侧：文章编辑与润色展示 ----
with left_col:
    with st.container(height=PANEL_HEIGHT, border=True):
        st.markdown('<div class="section-header">📝 原始文章</div>', unsafe_allow_html=True)
        input_height = 120 if st.session_state.polish_active else 200
        st.text_area(
            "原始文章输入",
            height=input_height,
            placeholder="请在此粘贴或输入文章内容，段落之间用空行分隔...",
            key="raw_article_input",
            label_visibility="collapsed",
        )

        if st.button("🚀 开始润色", type="primary", use_container_width=False):
            start_polish()
            st.rerun()

        if st.session_state.polish_active and st.session_state.original_paragraphs:
            st.markdown('<div class="section-header">📄 段落润色结果</div>', unsafe_allow_html=True)
            for i in range(len(st.session_state.original_paragraphs)):
                render_paragraph_card(i)

            st.divider()
            if st.button("📥 导出最终文章", type="secondary"):
                log_step("导出文章", "用户点击「导出最终文章」")
                final_text = merge_paragraphs(st.session_state.current_paragraphs)
                st.session_state.export_text = final_text
                accepted_count = sum(st.session_state.accepted)
                log_step(
                    "导出文章",
                    f"导出完成 — 共 {len(st.session_state.current_paragraphs)} 段，"
                    f"其中 {accepted_count} 段为润色版",
                )

            if st.session_state.export_text:
                st.markdown(
                    '<div class="section-header">📋 最终文章（可复制或下载）</div>',
                    unsafe_allow_html=True,
                )
                st.text_area(
                    "最终文章",
                    value=st.session_state.export_text,
                    height=120,
                    label_visibility="collapsed",
                )
                st.download_button(
                    label="⬇️ 下载 .txt 文件",
                    data=st.session_state.export_text,
                    file_name="polished_article.txt",
                    mime="text/plain",
                )

# ---- 右侧：AI 对话面板 ----
with right_col:
    with st.container(height=PANEL_HEIGHT, border=True):
        st.markdown('<div class="chat-header">💬 AI 润色助手</div>', unsafe_allow_html=True)

        chat_html = render_chat_messages()
        chat_area_height = 420 if st.session_state.polish_active else 480
        with st.container(height=chat_area_height):
            st.markdown(
                f'<div class="chat-messages-wrap">{chat_html}</div>',
                unsafe_allow_html=True,
            )

        with st.form("chat_form", clear_on_submit=True):
            chat_input = st.text_area(
                "对话输入",
                height=72,
                placeholder="输入润色要求，例如：请将文章改为更正式的学术风格",
                label_visibility="collapsed",
            )
            send_col, clear_col = st.columns([3, 1])
            with send_col:
                send_clicked = st.form_submit_button("发送", type="primary", use_container_width=True)
            with clear_col:
                clear_clicked = st.form_submit_button("清空", use_container_width=True)

    if clear_clicked:
        log_step("清空对话", "用户清空对话历史")
        st.session_state.chat_history = []
        st.rerun()

    if send_clicked:
        msg = (chat_input or "").strip()
        if not msg:
            log_step("对话触发", "失败：润色要求为空", level="warning")
            st.warning("请输入润色要求。")
        elif not st.session_state.polish_active:
            log_step("对话触发", "失败：尚未开始润色", level="warning")
            st.warning("请先在左侧输入文章并点击「开始润色」。")
        else:
            run_polish(chat_user_msg=msg)
            st.rerun()
