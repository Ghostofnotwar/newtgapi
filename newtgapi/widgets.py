"""HTML widget construction helpers (Bot API 10.4).

Widgets are small HTML documents rendered natively inside a message.
This module provides a tiny, dependency-free builder so bots do not
have to hand-concatenate strings (and forget to escape user input).

Example::

    from newtgapi.widgets import HtmlWidget

    html = (
        HtmlWidget(title="Магазин")
        .text("Выберите товар")
        .button("Купить", data="buy:1")
        .button("TON 💎", data="ton:sign", query_type="sign")
        .render()
    )
    bot.send_widget(chat_id, html, width=320, height=240)

The builder emits a self-contained document with inline CSS and a
small JS bridge stub (``window.tgWidget``) that posts interactions
back to the bot as ``WidgetQuery`` updates.  The exact JS bridge
name follows the Bot API docs; the stub is intentionally minimal
and easy to replace via :meth:`HtmlWidget.raw`.
"""

from __future__ import annotations

import html as _html
import json
from dataclasses import dataclass, field

from .exceptions import ValidationError

# Bot API limits (documented defaults; kept as constants so tests and
# callers can reference them instead of magic numbers).
MAX_WIDGET_HTML_SIZE = 64 * 1024  # 64 KiB
MAX_WIDGET_WIDTH = 4096
MAX_WIDGET_HEIGHT = 4096
MAX_WIDGET_DATA_SIZE = 4096  # widget query / edit data payload
DEFAULT_WIDGET_WIDTH = 320
DEFAULT_WIDGET_HEIGHT = 240


def escape(text: str) -> str:
    """Escape text for safe inclusion in widget HTML."""
    return _html.escape(str(text), quote=True)


def validate_widget_html(html: str) -> str:
    if not isinstance(html, str) or not html.strip():
        raise ValidationError("widget html must be a non-empty string")
    if len(html.encode("utf-8")) > MAX_WIDGET_HTML_SIZE:
        raise ValidationError(
            f"widget html exceeds {MAX_WIDGET_HTML_SIZE} bytes "
            f"({len(html.encode('utf-8'))} bytes)"
        )
    return html


def validate_widget_size(width: int | None, height: int | None) -> tuple[int | None, int | None]:
    for name, value in (("width", width), ("height", height)):
        if value is None:
            continue
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValidationError(f"widget {name} must be an int")
        if not (1 <= value <= MAX_WIDGET_WIDTH):
            raise ValidationError(f"widget {name} must be between 1 and {MAX_WIDGET_WIDTH}")
    return width, height


def validate_widget_data(data: str | dict) -> str:
    """Normalize widget ``data`` (str or JSON-serializable) to a string."""
    if isinstance(data, dict):
        data = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    if not isinstance(data, str):
        raise ValidationError("widget data must be str or dict")
    if len(data.encode("utf-8")) > MAX_WIDGET_DATA_SIZE:
        raise ValidationError(f"widget data exceeds {MAX_WIDGET_DATA_SIZE} bytes")
    return data


@dataclass
class WidgetButton:
    label: str
    data: str = ""
    query_type: str | None = None  # "sign" | "transaction" | None
    style: str | None = None

    def render(self) -> str:
        attrs = [f'data-query="{escape(self.data)}"']
        if self.query_type:
            attrs.append(f'data-query-type="{escape(self.query_type)}"')
        if self.style:
            attrs.append(f'style="{escape(self.style)}"')
        return f'<button {" ".join(attrs)}>{escape(self.label)}</button>'


@dataclass
class HtmlWidget:
    """Fluent builder for a widget HTML document."""

    title: str = ""
    theme: str = "light"
    _parts: list[str] = field(default_factory=list)

    # -- content -------------------------------------------------------
    def text(self, text: str) -> "HtmlWidget":
        self._parts.append(f"<p>{escape(text)}</p>")
        return self

    def html(self, raw: str) -> "HtmlWidget":
        """Append trusted raw HTML (caller is responsible for escaping)."""
        self._parts.append(raw)
        return self

    def raw(self, raw: str) -> "HtmlWidget":
        return self.html(raw)

    def heading(self, text: str, level: int = 2) -> "HtmlWidget":
        level = max(1, min(6, level))
        self._parts.append(f"<h{level}>{escape(text)}</h{level}>")
        return self

    def button(
        self,
        label: str,
        data: str = "",
        *,
        query_type: str | None = None,
        style: str | None = None,
    ) -> "HtmlWidget":
        self._parts.append(
            WidgetButton(label=label, data=data, query_type=query_type, style=style).render()
        )
        return self

    def ton_sign_button(self, label: str = "Подписать в TON Wallet", data: str = "ton:sign") -> "HtmlWidget":
        return self.button(label, data=data, query_type="sign")

    def ton_transaction_button(
        self, label: str = "Подтвердить транзакцию", data: str = "ton:tx"
    ) -> "HtmlWidget":
        return self.button(label, data=data, query_type="transaction")

    def input(self, name: str, placeholder: str = "", value: str = "") -> "HtmlWidget":
        self._parts.append(
            f'<input name="{escape(name)}" placeholder="{escape(placeholder)}" '
            f'value="{escape(value)}" />'
        )
        return self

    def image(self, url: str, alt: str = "") -> "HtmlWidget":
        self._parts.append(f'<img src="{escape(url)}" alt="{escape(alt)}" />')
        return self

    def divider(self) -> "HtmlWidget":
        self._parts.append("<hr />")
        return self

    # -- rendering -----------------------------------------------------
    def render(self) -> str:
        validate_widget_html("x")  # title/body validated below as a whole
        body = "\n".join(self._parts)
        title = escape(self.title or "Widget")
        doc = (
            "<!DOCTYPE html><html><head><meta charset=\"utf-8\" />"
            f"<title>{title}</title>"
            "<style>body{font-family:system-ui,sans-serif;margin:16px;"
            "color:#222}button{margin:4px;padding:8px 14px;border-radius:8px;"
            "border:1px solid #ccc;cursor:pointer}</style></head>"
            f"<body><h1>{title}</h1>{body}"
            "<script>(function(){document.querySelectorAll('button').forEach(function(b){"
            "b.addEventListener('click',function(){"
            "window.tgWidget&&window.tgWidget.sendQuery({"
            "data:b.getAttribute('data-query')||'',"
            "queryType:b.getAttribute('data-query-type')||'interaction'});});});})();</script>"
            "</body></html>"
        )
        return validate_widget_html(doc)

    __str__ = render


def widget_data_to_json(data: str | dict) -> str:
    """Serialize widget data payload (used by edit*WidgetData)."""
    return validate_widget_data(data)


def parse_widget_query_data(data: str | None) -> dict | str | None:
    """Best-effort parse of ``WidgetQuery.data`` — JSON dict or raw string."""
    if data is None:
        return None
    try:
        parsed = json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return data
    return parsed if isinstance(parsed, dict) else data


__all__ = [
    "DEFAULT_WIDGET_HEIGHT",
    "DEFAULT_WIDGET_WIDTH",
    "MAX_WIDGET_DATA_SIZE",
    "MAX_WIDGET_HEIGHT",
    "MAX_WIDGET_HTML_SIZE",
    "MAX_WIDGET_WIDTH",
    "HtmlWidget",
    "WidgetButton",
    "escape",
    "parse_widget_query_data",
    "validate_widget_data",
    "validate_widget_html",
    "validate_widget_size",
    "widget_data_to_json",
]
