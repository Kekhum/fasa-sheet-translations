import json
from bs4 import BeautifulSoup, NavigableString, Comment
import re

# Global dictionary to store unique translation keys
translation_keys = {}

def normalize_text(text):
    """
    Normalize the input text by removing excess whitespace.
    
    - Replaces any sequence of whitespace characters (spaces, tabs, newlines)
      with a single space.
    - Trims the text to remove leading and trailing whitespace.
    
    Args:
        text (str): The text to be normalized.
        
    Returns:
        str: The normalized text.
    """
    return re.sub(r'\s+', ' ', text).strip()

def should_translate(text):
    """
    Determine if the given text should be considered for translation.
    
    The function checks if the text contains at least one letter (including 
    Polish characters), which indicates that it is meaningful text for translation.
    
    Args:
        text (str): The text to check.
        
    Returns:
        bool: True if the text contains at least one letter, False otherwise.
    """
    text = text.strip()
    return bool(re.search(r'[A-Za-zĄąĆćĘęŁłŃńÓóŚśŹźŻż]', text))

def add_translation_key(key):
    """
    Add a translation key to the global dictionary if it is not already present.
    
    The key is normalized to remove any excess whitespace before being stored.
    
    Args:
        key (str): The translation key to add.
    """
    normalized_key = normalize_text(key)
    if normalized_key not in translation_keys:
        translation_keys[normalized_key] = normalized_key

def process_tag(tag):
    """
    Process an individual HTML tag to add translatable attributes.
    
    This function performs the following steps:
    
    1. Skips processing for <script> tags (and potentially others that should be ignored).
    2. Extracts the first non-empty direct text node (ignoring comments and nested texts).
       If the text is deemed translatable, a 'data-i18n' attribute is added to the tag
       with the normalized text, and the translation key is recorded.
    3. If the tag has a 'title' attribute, and the text does not contain template 
       placeholders (e.g., "@{" or "%{"), it adds a 'data-i18n-title' attribute with 
       the normalized text and records the key.
    4. Processes the 'placeholder' attribute in a similar manner.
    
    Args:
        tag (bs4.element.Tag): The HTML tag to process.
    """
    # Skip <script> tags (or any tags we do not wish to process)
    if tag.name.lower() == "script":
        return

    # Retrieve only direct text nodes (ignoring comments and empty nodes)
    direct_texts = [
        node.strip() for node in tag.contents
        if isinstance(node, NavigableString) and not isinstance(node, Comment) and node.strip()
    ]
    if direct_texts:
        text_to_use = direct_texts[0]
        if should_translate(text_to_use):
            normalized_text = normalize_text(text_to_use)
            tag['data-i18n'] = normalized_text
            add_translation_key(normalized_text)

    # Process the 'title' attribute if it exists
    if tag.has_attr('title'):
        title_text = tag['title'].strip()
        if title_text and should_translate(title_text) and "@{" not in title_text and "%{" not in title_text:
            normalized_title = normalize_text(title_text)
            tag['data-i18n-title'] = normalized_title
            add_translation_key(normalized_title)

    # Process the 'placeholder' attribute if it exists
    if tag.has_attr('placeholder'):
        placeholder_text = tag['placeholder'].strip()
        if placeholder_text and should_translate(placeholder_text):
            normalized_placeholder = normalize_text(placeholder_text)
            tag['data-i18n-placeholder'] = normalized_placeholder
            add_translation_key(normalized_placeholder)

def process_html(html_content):
    """
    Parse and process the HTML content.
    
    This function uses BeautifulSoup to parse the input HTML, iterates over every tag,
    and processes each tag to add translation-related attributes where applicable.
    
    Args:
        html_content (str): The HTML content to process.
        
    Returns:
        str: The modified HTML content as a string.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    for tag in soup.find_all(True):
        process_tag(tag)
    return str(soup)

if __name__ == "__main__":
    # Load the original HTML file
    with open("Earthdawn.html", "r", encoding="utf-8") as f:
        html_content = f.read()

    # Process the HTML to add translation attributes and collect translation keys
    processed_html = process_html(html_content)

    # Save the modified HTML to a new file
    with open("Earthdawn_translated.html", "w", encoding="utf-8") as f:
        f.write(processed_html)

    # Save the unique translation keys to a JSON file
    # The keys and values are identical and normalized (free of excess whitespace)
    with open("translations.json", "w", encoding="utf-8") as f:
        json.dump(translation_keys, f, ensure_ascii=False, indent=4)
