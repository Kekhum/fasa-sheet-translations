import json
from bs4 import BeautifulSoup, NavigableString, Comment
from bs4.element import Tag
import re

# Global dictionary to store unique translation keys
translation_keys = {}

def normalize_text(text):
    """
    Normalize input by collapsing whitespace within the core text.
    """
    return re.sub(r'\s+', ' ', text).strip()

def should_translate(text):
    """
    Return True if text contains letters (including Polish).
    """
    if re.search(r'{{', text):
        return False
    return bool(re.search(r'[A-Za-zĄąĆćĘęŁłŃńÓóŚśŹźŻż]', text.strip()))

def add_translation_key(key):
    """
    Register a translation key if new.
    """
    norm = normalize_text(key)
    translation_keys.setdefault(norm, norm)


def wrap_text_with_whitespace(text, soup):
    """
    Given a text node string, split into leading ws, core, trailing ws,
    wrap core in <span i18n="...">core</span>, and return list of nodes.
    """
    # Separate leading/trailing whitespace
    m = re.match(r'^(\s*)(.*?)(\s*)$', text, re.DOTALL)
    leading, core, trailing = m.groups()
    nodes = []
    if leading:
        nodes.append(NavigableString(leading))
    if core and should_translate(core):
        norm = normalize_text(core)
        add_translation_key(norm)
        span = soup.new_tag('span')
        span['i18n'] = norm
        span.string = core
        nodes.append(span)
    else:
        # no wrap if no core or not translatable
        nodes.append(NavigableString(core))
    if trailing:
        nodes.append(NavigableString(trailing))
    return nodes


def process_tag(tag, soup):
    """
    Recursively wrap text nodes and attributes for translation.
    Skip <script>, preserve <br>, <hr>, and skip existing spans.
    """
    name = tag.name.lower()
    if name == 'script':
        return

    # Attributes
    if tag.has_attr('title'):
        txt = tag['title']
        if txt and should_translate(txt) and '@{' not in txt and '%{' not in txt:
            norm = normalize_text(txt)
            tag['data-i18n-title'] = norm
            add_translation_key(norm)
    if tag.has_attr('placeholder'):
        ph = tag['placeholder']
        if ph and should_translate(ph):
            norm = normalize_text(ph)
            tag['data-i18n-placeholder'] = norm
            add_translation_key(norm)

    # Process children
    for child in list(tag.contents):
        if isinstance(child, NavigableString) and not isinstance(child, Comment):
            text = str(child)
            if text.strip():
                parent = child.parent
                # skip if already wrapped
                if not (isinstance(parent, Tag) and parent.has_attr('i18n')):
                    new_nodes = wrap_text_with_whitespace(text, soup)
                    child.replace_with(*new_nodes)
                # else leave as-is
            else:
                # remove pure whitespace node? keep indentation though
                # to preserve formatting, we skip extraction
                continue
        elif isinstance(child, Tag):
            if child.name.lower() in ('br', 'hr'):
                continue
            if child.name.lower() == 'span' and child.has_attr('i18n'):
                continue
            process_tag(child, soup)


def process_html(html_content):
    """
    Parse and process HTML content.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    for tag in soup.find_all(True):
        process_tag(tag, soup)
    return str(soup)

if __name__ == '__main__':
    with open('Earthdawn.html', 'r', encoding='utf-8') as f:
        html = f.read()
    processed = process_html(html)
    with open('Earthdawn_translated.html', 'w', encoding='utf-8') as f:
        f.write(processed)
    with open('translations.json', 'w', encoding='utf-8') as f:
        json.dump(translation_keys, f, ensure_ascii=False, indent=4)
