from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from markdown import markdown

register = template.Library()


@register.filter(name='markdown')
@stringfilter
def markdown_filter(value: str):
    # always render new lines as new lines, even without two ending spaces
    return mark_safe(markdown(value).replace("\r\n", "  \r\n"), )
