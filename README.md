# Roll20 Character Sheet Python Translator
This script was created exclusively for translating the [character sheet](https://github.com/Roll20/roll20-character-sheets/tree/master/Earthdawn%20(FASA%20Official)).  
It has not been tested on other sheets, so it might not work.

## TODO
1. Find out if FASA find this script usefull

## Info
Author: Marcin "Marenioo" Stefanko  
License: GNU GPL

## How Does It Work?
The script traverses the HTML tags and attempts to locate any meaningful text within them—even when scanning nested tags.
When it finds content suitable for translation, it simply adds the corresponding translation tags (without duplicates).

The script adds the following attributes:  
- `data-i18n` – translation of the tag's content  
- `data-i18n-title` – translation of the tag's title  
- `data-i18n-placeholder` – translation of the tag's placeholder  

As an output, the script generates a separate HTML file with the added translations.  
It also creates a JSON translation file in the following format:

```
{
    "key": "value",
    "key2": "value2"
}
```


Due to the complexity of the processed HTML, the script will **NOT** handle any data within `<script>` elements, nor will it process titles or placeholders whose values use macros such as `@{}` or `%{}`.

## Usage

1. Install the **beautifulsoup4** library using: `pip install beautifulsoup4`
2. Download the [character sheet](https://github.com/Roll20/roll20-character-sheets/blob/master/Earthdawn%20(FASA%20Official)/Earthdawn.html).
3. Run the script (don't forget to adjust the settings at the bottom).

## Additional Info
Although the script generates a JSON translation file for the HTML character sheet, it does not translate the content in any way. This JSON file may later be used, for example, in [this service](https://roll20.crowdin.com/roll20-character-sheets).  
While translating JSON Values try to use same number of characters as in original translation. 
Larger translations would need to be corrected in css file of that character sheet.


