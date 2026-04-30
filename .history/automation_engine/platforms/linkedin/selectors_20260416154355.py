START_POST_SELECTORS = [
    "button[aria-label='Start a post']",
    "button[aria-label*='Start a post']",
    "div[role='button'][aria-label*='Start a post']",
    "button.share-box-feed-entry__trigger",
    "div.share-box-feed-entry__trigger",
    "div.share-box-feed-entry--closed",
    ".share-box-feed-entry__top-bar",
]

TEXTBOX_SELECTORS = [
    # inside modal/editor
    "div[role='dialog'] div.ql-editor[contenteditable='true']",
    "div[role='dialog'] div[role='textbox'][contenteditable='true']",
    "div[role='dialog'] div[contenteditable='true']",

    # LinkedIn editor variants
    "div.ql-editor[contenteditable='true']",
    "div.editor-content div[contenteditable='true']",
    "div.share-box__content div[contenteditable='true']",
    "div[role='textbox'][contenteditable='true']",
    "div[contenteditable='true']",
]

POST_BUTTON_SELECTORS = [
    "button[aria-label='Post']",
    "button.share-actions__primary-action",
    "button[aria-label*='Post']",
]