import json
import logging
import argparse
import sys
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Comment
from bs4.element import Tag
import re
import html

# Global dictionary to store unique translation keys
translation_keys = {}

# Configuration
SKIPPED_TAGS = {'br', 'hr', 'script', 'style', 'meta', 'link'}
PRESERVED_FORMATTING_TAGS = {'b', 'i', 'strong', 'em', 'u', 'code', 'kbd', 'mark', 'small', 'sub', 'sup', 'p'}
TEMPLATE_PATTERNS = [r'{{', r'@{', r'%{', r'\${', r'#{']  # Common template syntax patterns
# REMOVED 'value' from translatable attributes - values should NOT be translated
TRANSLATABLE_ATTRIBUTES = {
    'title': 'data-i18n-title',
    'placeholder': 'data-i18n-placeholder',
    'alt': 'data-i18n-alt',
    'aria-label': 'data-i18n-aria-label',
    'aria-description': 'data-i18n-aria-description'
}

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def normalize_text(text):
    """
    Normalize input by preserving multiple spaces but trimming edges.
    Only collapse newlines and tabs to single space.
    """
    # Replace newlines and tabs with single space, but preserve multiple spaces
    text = re.sub(r'[\n\t\r]+', ' ', text)
    return text.strip()

def has_template_syntax(text):
    """
    Check if text contains template syntax that shouldn't be translated.
    """
    for pattern in TEMPLATE_PATTERNS:
        if re.search(pattern, text):
            return True
    return False

def should_translate(text):
    """
    Return True if text contains letters (including Polish) and no template syntax.
    Skip single characters to avoid unnecessary translations.
    """
    stripped = text.strip()
    # Skip single characters
    if len(stripped) <= 1:
        return False
    if has_template_syntax(text):
        return False
    return bool(re.search(r'[A-Za-zĄąĆćĘęŁłŃńÓóŚśŹźŻż]', stripped))

def add_translation_key(key):
    """
    Register a translation key if new.
    """
    norm = normalize_text(key)
    if norm not in translation_keys:
        logger.debug(f"Added translation key: {norm}")
        translation_keys[norm] = norm

def escape_attribute_value(value):
    """
    Properly escape attribute values for HTML.
    Converts quotes to HTML entities to avoid nesting issues.
    """
    # Escape quotes to avoid issues with nested quotes
    return html.escape(value, quote=True)


def wrap_text_with_whitespace(text, soup):
    """
    Given a text node string, split into leading ws, core, trailing ws,
    wrap core in <span data-i18n="..."></span>, and return list of nodes.
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
        span['data-i18n'] = norm
        # Don't include the original text in the span - it will be replaced by translation
        nodes.append(span)
    elif core:  # Only append if there's actual core content
        # no wrap if not translatable
        nodes.append(NavigableString(core))
    if trailing:
        nodes.append(NavigableString(trailing))
    return nodes


def process_tag(tag, soup, config=None):
    """
    Recursively wrap text nodes and attributes for translation.
    Skip configured tags, preserve formatting tags, and skip existing spans.
    """
    if config is None:
        config = {}

    skipped_tags = config.get('skipped_tags', SKIPPED_TAGS)
    preserved_tags = config.get('preserved_tags', PRESERVED_FORMATTING_TAGS)

    name = tag.name.lower()
    if name in skipped_tags:
        return

    # Process translatable attributes
    for attr_name, i18n_attr in TRANSLATABLE_ATTRIBUTES.items():
        if tag.has_attr(attr_name):
            attr_value = tag[attr_name]

            if attr_value and should_translate(attr_value):
                norm = normalize_text(attr_value)
                # Use escaped value for the attribute to avoid quote issues
                tag[i18n_attr] = escape_attribute_value(norm)
                # Remove the original attribute to avoid duplication
                if config.get('remove_original_attrs', True):
                    del tag[attr_name]
                add_translation_key(norm)
                logger.debug(f"Added {attr_name} attribute for translation: {norm}")

    # Gather all direct text content (excluding child tags)
    tag_text_content = ''.join([str(c) for c in tag.contents if isinstance(c, NavigableString) and not isinstance(c, Comment)])

    # Special handling for OPTION elements - NEVER translate their value attribute
    if name == 'option':
        # Only process the text content of option, never the value
        if tag_text_content and should_translate(tag_text_content):
            norm = normalize_text(tag_text_content)
            tag['data-i18n'] = escape_attribute_value(norm)
            tag.clear()  # Clear the content - it will be replaced by translation
            add_translation_key(norm)
        return  # Don't process children of option tags

    # Check if we can add data-i18n directly to this tag
    # This works for tags with only text content or tags where all text should be replaced
    if tag_text_content and should_translate(tag_text_content):
        has_only_text = all(isinstance(c, NavigableString) for c in tag.contents)
        child_tags = [c for c in tag.contents if isinstance(c, Tag)]

        # Special handling for tags with mixed content (text + input elements)
        # If tag has both text and child elements, wrap text in nested spans
        has_input_children = any(
            c.name.lower() in {'input', 'select', 'textarea', 'button'}
            for c in child_tags
        )

        if has_input_children and tag_text_content.strip():
            # Mixed content case - wrap text nodes in spans with data-i18n
            # Keep the parent structure intact
            for child in list(tag.contents):
                if isinstance(child, NavigableString) and not isinstance(child, Comment):
                    text = str(child)
                    if text.strip() and should_translate(text):
                        norm = normalize_text(text)
                        new_span = soup.new_tag('span')
                        new_span['data-i18n'] = escape_attribute_value(norm)
                        child.replace_with(new_span)
                        add_translation_key(norm)
            # Process child tags for their attributes
            for child in child_tags:
                if isinstance(child, Tag):
                    process_tag(child, soup, config)
            return

        # Simple text-only case - add data-i18n to the tag itself
        if has_only_text:
            norm = normalize_text(tag_text_content)
            tag['data-i18n'] = escape_attribute_value(norm)
            # Clear the content - it will be replaced by translation
            tag.clear()
            add_translation_key(norm)
            return  # Don't process children since we handled the whole tag

    # Process children normally if we couldn't add data-i18n to the parent
    for child in list(tag.contents):
        if isinstance(child, NavigableString) and not isinstance(child, Comment):
            text = str(child)
            if text.strip():
                parent = child.parent
                # skip if parent already has data-i18n
                if not (isinstance(parent, Tag) and parent.has_attr('data-i18n')):
                    new_nodes = wrap_text_with_whitespace(text, soup)
                    child.replace_with(*new_nodes)
                # else leave as-is
            else:
                # remove pure whitespace node? keep indentation though
                # to preserve formatting, we skip extraction
                continue
        elif isinstance(child, Tag):
            child_name = child.name.lower()
            # Skip if it's a skipped tag
            if child_name in skipped_tags:
                continue
            # Skip if it's already a translation span
            if child_name == 'span' and child.has_attr('data-i18n'):
                continue
            # For preserved formatting tags, process their content but don't skip them
            process_tag(child, soup, config)


def process_html(html_content, config=None):
    """
    Parse and process HTML content.
    """
    if config is None:
        config = {}

    logger.info("Starting HTML processing...")
    # Use html.parser with specific formatter to preserve original HTML structure
    soup = BeautifulSoup(html_content, 'html.parser')

    tags_processed = 0
    for tag in soup.find_all(True):
        process_tag(tag, soup, config)
        tags_processed += 1

    logger.info(f"Processed {tags_processed} tags")
    logger.info(f"Found {len(translation_keys)} unique translation keys")
    
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

    # Unescape HTML entities in data-i18n attributes back to their original form
    # This is needed because we escaped them earlier but want them readable in the output
    html_output = re.sub(r'data-i18n([^=]*)="([^"]*)"',
                        lambda m: f'data-i18n{m.group(1)}="{html.unescape(m.group(2))}"',
                        html_output)

    return html_output

def main():
    parser = argparse.ArgumentParser(description='Extract and prepare HTML content for translation')
    parser.add_argument('input', nargs='?', default='Earthdawn.html',
                        help='Input HTML file (default: Earthdawn.html)')
    parser.add_argument('-o', '--output', default=None,
                        help='Output HTML file (default: input_translated.html)')
    parser.add_argument('-t', '--translations', default='translations.json',
                        help='Output translations JSON file (default: translations.json)')
    parser.add_argument('--skip-tags', nargs='+', default=None,
                        help='Additional tags to skip during processing')
    parser.add_argument('--preserved-tags', nargs='+', default=None,
                        help='Additional formatting tags to preserve')
    parser.add_argument('--keep-original-attrs', action='store_true',
                        help='Keep original attributes alongside i18n attributes')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Setup configuration
    config = {
        'remove_original_attrs': not args.keep_original_attrs
    }
    if args.skip_tags:
        config['skipped_tags'] = SKIPPED_TAGS | set(args.skip_tags)
    if args.preserved_tags:
        config['preserved_tags'] = PRESERVED_FORMATTING_TAGS | set(args.preserved_tags)

    # Determine output filename
    if args.output is None:
        input_path = Path(args.input)
        output_file = input_path.stem + '_translated' + input_path.suffix
    else:
        output_file = args.output

    try:
        # Read input file
        logger.info(f"Reading input file: {args.input}")
        with open(args.input, 'r', encoding='utf-8') as f:
            html = f.read()

        # Process HTML
        processed = process_html(html, config)

        # Write output HTML
        logger.info(f"Writing processed HTML to: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(processed)

        # Write translations JSON
        logger.info(f"Writing translations to: {args.translations}")
        with open(args.translations, 'w', encoding='utf-8') as f:
            json.dump(translation_keys, f, ensure_ascii=False, indent=4, sort_keys=True)

        logger.info("Processing completed successfully!")
        logger.info(f"Extracted {len(translation_keys)} unique translation keys")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e.filename}")
        sys.exit(1)
    except PermissionError as e:
        logger.error(f"Permission denied: {e.filename}")
        sys.exit(1)
    except UnicodeDecodeError as e:
        logger.error(f"Encoding error: {e}. Try a different encoding.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
