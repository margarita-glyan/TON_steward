from __future__ import annotations


_MDV2_SPECIAL = r"_*[]()~`>#+-=|{}.!"


def escape_markdown_v2(text: str) -> str:
    """
    Minimal MarkdownV2 escaping for Telegram.
    """
    if text is None:
        return ""
    out = []
    for ch in str(text):
        if ch in _MDV2_SPECIAL:
            out.append("\\" + ch)
        else:
            out.append(ch)
    return "".join(out)


def truncate(text: str, max_len: int) -> str:
    t = text or ""
    if len(t) <= max_len:
        return t
    return t[: max(0, max_len - 1)] + "…"

