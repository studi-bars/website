import xml.etree.ElementTree as etree

from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from markdown import markdown
from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor
from markdown.treeprocessors import Treeprocessor

register = template.Library()

# bare urls; trailing punctuation is left out so "see https://x.de." does not swallow the dot
BARE_URL_RE = r'https?://[^\s<>]*[^\s<>.,;:!?)\]\'"]'


class BareUrlProcessor(InlineProcessor):
    def handleMatch(self, m, data):
        el = etree.Element('a', href=m.group(0))
        el.text = m.group(0)
        return el, m.start(0), m.end(0)


class NewTabTreeprocessor(Treeprocessor):
    def run(self, root):
        for a in root.iter('a'):
            a.set('target', '_blank')
            a.set('rel', 'noopener noreferrer')


class LinkExtension(Extension):
    def extendMarkdown(self, md):
        # below 'link' (160) and 'autolink' (120), so urls inside [text](url) and <url>
        # have already been consumed and are not linked twice; code spans (190) are skipped too
        md.inlinePatterns.register(BareUrlProcessor(BARE_URL_RE, md), 'bare_url', 115)
        # after 'inline' (20), which is the step that turns the inline patterns into <a> elements
        md.treeprocessors.register(NewTabTreeprocessor(md), 'new_tab_links', 5)


@register.filter(name='markdown')
@stringfilter
def markdown_filter(value: str):
    # nl2br: always render new lines as new lines, even without two ending spaces
    return mark_safe(markdown(value, extensions=['nl2br', LinkExtension()]))
