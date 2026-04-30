START_POST_SELECTORS = [
    "button[aria-label='Start a post']",
    "button[aria-label*='Start a post']",
    "div[role='button'][aria-label='Start a post']",
    "div[role='button'][aria-label*='Start a post']",
    "button.share-box-feed-entry__trigger",
    "div.share-box-feed-entry__trigger",
    "div.share-box-feed-entry--closed",
]
TEXTBOX_SELECTORS = [
    "div.ql-editor[contenteditable='true']",
    "div[role='textbox'][contenteditable='true']",
    "div[contenteditable='true'][role='textbox']",
    "div[contenteditable='true']",
]

POST_BUTTON_SELECTORS = [
    "button.share-actions__primary-action",
    "button[aria-label='Post']",
    "button[aria-label*='Post']",
]