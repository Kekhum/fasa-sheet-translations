# Roll20 Character Sheet Python Translator
This script was created exclusively for translating the [character sheet](https://github.com/Roll20/roll20-character-sheets/tree/master/Earthdawn%20(FASA%20Official)).
It has not been tested on other sheets, so it might not work.

## TODO
1. Find out if FASA find this script useful

## Info
Author: Marcin "Marenioo" Stefanko
License: GNU GPL
Version: 2.0 (2025-10-23)

## How Does It Work?
The script traverses the HTML tags and attempts to locate any meaningful text within them—even when scanning nested tags.
When it finds content suitable for translation, it simply adds the corresponding translation tags (without duplicates).

The script adds the following attributes:
- `data-i18n` – translation of the tag's content
- `data-i18n-title` – translation of the tag's title
- `data-i18n-placeholder` – translation of the tag's placeholder
- `data-i18n-alt` – translation of the tag's alt text
- `data-i18n-aria-label` – translation of ARIA labels
- `data-i18n-aria-description` – translation of ARIA descriptions
- `data-i18n-value` – translation of button/submit input values

### Key Features:
- **Smart tag handling**: Adds `data-i18n` directly to parent tags when possible, avoiding unnecessary nested spans
- **Preserves formatting**: Maintains original HTML structure, indentation, and multiple spaces
- **Skips single characters**: Ignores single-character text to avoid unnecessary translations
- **Template syntax detection**: Skips text containing template syntax ({{, @{, %{, ${, #{)
- **Boolean attributes**: Properly handles HTML boolean attributes (readonly, hidden, disabled, etc.)
- **Configurable**: Support for custom skipped tags and preserved formatting tags

As an output, the script generates a separate HTML file with the added translations.
It also creates a JSON translation file in the following format:

```json
{
    "key": "value",
    "key2": "value2"
}
```

Due to the complexity of the processed HTML, the script will **NOT** handle any data within `<script>`, `<style>`, `<br>`, `<hr>`, `<meta>`, or `<link>` elements.

## Installation

1. Install Python 3.7 or higher
2. Install the **beautifulsoup4** library:
   ```bash
   pip install beautifulsoup4
   ```
3. Download the [character sheet](https://github.com/Roll20/roll20-character-sheets/blob/master/Earthdawn%20(FASA%20Official)/Earthdawn.html)

## Usage

### Basic Usage
Run the script with default settings:
```bash
python translate.py
```
This will:
- Read from `Earthdawn.html`
- Output to `Earthdawn_translated.html`
- Create `translations.json`

### Command Line Options
```bash
python translate.py [input_file] [options]

Options:
  -o, --output FILE           Output HTML file (default: input_translated.html)
  -t, --translations FILE     Output translations JSON file (default: translations.json)
  --skip-tags TAG [TAG ...]   Additional tags to skip during processing
  --preserved-tags TAG [...]  Additional formatting tags to preserve
  --keep-original-attrs       Keep original attributes alongside i18n attributes
  -v, --verbose               Enable verbose logging
  -h, --help                  Show help message

Examples:
  # Process custom input file
  python translate.py MySheet.html -o MySheet_i18n.html -t my_translations.json

  # Skip additional tags
  python translate.py --skip-tags noscript iframe

  # Keep original attributes (not recommended)
  python translate.py --keep-original-attrs

  # Enable verbose mode for debugging
  python translate.py -v
```

## Workflow Example

### Step 1: Prepare HTML for Translation
```bash
python translate.py Earthdawn.html
```
Output:
- `Earthdawn_translated.html` - HTML with i18n tags added
- `translations.json` - JSON file with extracted text keys

### Step 2: Translate the JSON
Edit `translations.json` and replace English values with Polish translations:
```json
{
    "Damage": "Obrażenia",
    "Health Rating": "Ocena Zdrowia",
    "Wound Tr.": "Próg Ran",
    ...
}
```

### Step 3: Use in Roll20
Upload the translated HTML to Roll20 character sheet system. The i18n system will automatically use the translations from the JSON file.

## What's Changed in Version 2.0

### Fixes from FASA/Jiboux Feedback:
1. **No more unnecessary nested spans** - The script now adds `data-i18n` directly to parent tags when possible
2. **Proper attribute handling** - All translatable attributes (title, placeholder, alt, etc.) are correctly processed
3. **Boolean attributes preserved** - Attributes like `readonly`, `hidden` are kept as boolean without `=""`
4. **Multiple spaces preserved** - Formatting with multiple spaces is maintained
5. **Smart text detection** - Skip single characters and template syntax

### Before/After Example:
```html
<!-- Before (v1.0 output - problematic): -->
<span class="sheet-info" title="Instructions">
  <span data-i18n="i"></span>
</span>

<!-- After (v2.0 output - correct): -->
<span class="sheet-info" data-i18n-title="Instructions">i</span>
```

## Additional Info
Although the script generates a JSON translation file for the HTML character sheet, it does not translate the content in any way. This JSON file may later be used, for example, in [this service](https://roll20.crowdin.com/roll20-character-sheets).

While translating JSON Values try to use same number of characters as in original translation. Larger translations would need to be corrected in CSS file of that character sheet.

## Known Limitations
- Scripts and styles are not processed
- Single character texts are intentionally skipped
- Template syntax ({{, @{, %{) is preserved as-is
- The script does not perform actual translations - only prepares the structure

## Support
For issues or questions about the Earthdawn character sheet translation, contact the FASA/Topory Polish translation team or visit the Roll20 character sheets repository.

