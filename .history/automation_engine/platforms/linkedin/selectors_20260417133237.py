START_POST_SELECTORS = [
    "button[aria-label='Start a post']",
    "button[aria-label*='Start a post']",
    "div[role='button'][aria-label='Start a post']",
    "div[role='button'][aria-label*='Start a post']",
    "button.share-box-feed-entry__trigger",
    "div.share-box-feed-entry__trigger",
    "div.share-box-feed-entry--closed",
    "div.feed-share-box button",
    "div.feed-share-box div[role='button']",
    "button.artdeco-button",
    "div[role='button']",
]

TEXTBOX_SELECTORS = [
    "div[role='dialog'] div.ql-editor",
    "div[role='dialog'] div[role='textbox']",
    "div[role='dialog'] div[contenteditable='true']",
    "div.ql-editor",
    "div[role='textbox']",
    "div[contenteditable='true']",
    "textarea",
    "p",
]

POST_BUTTON_SELECTORS = [
    "div[role='dialog'] button.share-actions__primary-action",
    "div[role='dialog'] button[aria-label='Post']",
    "div[role='dialog'] button[aria-label*='Post']",
    "button.share-actions__primary-action",
    "button[aria-label='Post']",
    "button[aria-label*='Post']",
    "button.artdeco-button--primary",
]