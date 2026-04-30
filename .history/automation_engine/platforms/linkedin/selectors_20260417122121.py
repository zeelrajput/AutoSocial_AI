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
    # First search inside dialog/composer
    "div[role='dialog'] div.ql-editor[contenteditable='true']",
    "div[role='dialog'] div[role='textbox'][contenteditable='true']",
    "div[role='dialog'] div[contenteditable='true'][role='textbox']",
    "div[role='dialog'] div[contenteditable='true'][data-placeholder]",
    "div[role='dialog'] div[contenteditable='true'][aria-multiline='true']",
    "div[role='dialog'] div[contenteditable='true']",

    # General fallbacks
    "div.ql-editor[contenteditable='true']",
    "div[role='textbox'][contenteditable='true']",
    "div[contenteditable='true'][role='textbox']",
    "div[contenteditable='true'][data-placeholder]",
    "div[contenteditable='true'][aria-multiline='true']",
    "div[contenteditable='true']",
    "textarea",
]

POST_BUTTON_SELECTORS = [
    "div[role='dialog'] button.share-actions__primary-action",
    "div[role='dialog'] button[aria-label='Post']",
    "div[role='dialog'] button[aria-label*='Post']",
    "div[role='dialog'] button.share-box_actions__primary-action",
    "button.share-actions__primary-action",
    "button[aria-label='Post']",
    "button[aria-label*='Post']",
]