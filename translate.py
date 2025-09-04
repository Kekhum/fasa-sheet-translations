import json
from bs4 import BeautifulSoup, NavigableString, Comment
from bs4.element import Tag
import re

# Global dictionary to store unique translation keys
translation_keys = {}

def normalize_text(text):
    """
    Normalize input by preserving multiple spaces but trimming edges.
    Only collapse newlines and tabs to single space.
    """
    # Replace newlines and tabs with single space, but preserve multiple spaces
    text = re.sub(r'[\n\t\r]+', ' ', text)
    return text.strip()

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
            if child.name.lower() in ('br', 'hr', 'b', 'p'):
                continue
            if child.name.lower() == 'span' and child.has_attr('i18n'):
                continue
            process_tag(child, soup)


def process_html(html_content):
    """
    Parse and process HTML content.
    """
    # Use html.parser with specific formatter to preserve original HTML structure
    soup = BeautifulSoup(html_content, 'html.parser')
    for tag in soup.find_all(True):
        process_tag(tag, soup)
    
    # Convert back to string with custom formatting
    html_output = str(soup)
    
    # Fix boolean attributes that BeautifulSoup converts
    # Replace readonly="readonly" with readonly, hidden="hidden" with hidden, etc.
    # Also handle empty string versions
    boolean_attrs = ['readonly', 'hidden', 'disabled', 'checked', 'selected', 'multiple', 'required']
    for attr in boolean_attrs:
        # Handle both attr="attr" and attr="" patterns
        html_output = re.sub(f'{attr}="{attr}"', attr, html_output)
        html_output = re.sub(f'{attr}=""', attr, html_output)
    
    # Preserve original input tag closing style (remove self-closing /)
    # Only for input tags, keep /> for other self-closing tags
    html_output = re.sub(r'<input([^>]*)/>', r'<input\1>', html_output)
    
    return html_output

if __name__ == '__main__':
    with open('Earthdawn.html', 'r', encoding='utf-8') as f:
        html = f.read()
    processed = process_html(html)
    with open('Earthdawn_translated.html', 'w', encoding='utf-8') as f:
        f.write(processed)
    with open('translations.json', 'w', encoding='utf-8') as f:
        json.dump(translation_keys, f, ensure_ascii=False, indent=4)
