from typing import cast

import markdown
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def markdown_to_html(value: str) -> str:
    """Render markdown text to HTML. Use with {{ content|markdown_to_html }} in templates."""
    if not value:
        return ""
    html = markdown.markdown(
        value,
        extensions=["extra", "nl2br", "sane_lists"],
    )
    return cast(str, mark_safe(html))
