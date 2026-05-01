START_POST_SELECTORS = [
    "button[aria-label='Start a post']",
    "div.share-box-feed-entry__trigger",
    "button.share-box-feed-entry__trigger",
    "div[role='button'][aria-label*='post']",
]

TEXTBOX_SELECTORS = [
    "div[role='dialog'] div[role='textbox'][contenteditable='true']",
    "div[role='dialog'] div.ql-editor[contenteditable='true']",
    "div.ql-editor[contenteditable='true']",
    "div[contenteditable='true'][role='textbox']",
    "div[contenteditable='true']",
]

POST_BUTTON_SELECTORS = [
    "div[role='dialog'] button[aria-label='Post']",
    "div[role='dialog'] button.share-actions__primary-action",
    "button.share-actions__primary-action",
    "button[aria-label*='Post']",
]