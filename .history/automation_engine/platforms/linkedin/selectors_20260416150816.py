# selector.py (LinkedIn)

# 1. Start Post Button (main trigger)
START_POST_SELECTORS = [
    "button[aria-label='Start a post']",
    "div.share-box-feed-entry__trigger",
    "button.share-box-feed-entry__trigger",
    "div[role='button'][aria-label*='post']",
]

# 2. Textbox inside modal
TEXTBOX_SELECTORS = [
    # Inside modal (most reliable)
    "div[role='dialog'] div[role='textbox'][contenteditable='true']",
    "div[role='dialog'] div.ql-editor[contenteditable='true']",

    # Quill editor (LinkedIn uses this)
    "div.ql-editor[contenteditable='true']",

    # Generic fallback
    "div[contenteditable='true'][role='textbox']",
    "div[contenteditable='true']",
]

# 3. Post Button
POST_BUTTON_SELECTORS = [
    "div[role='dialog'] button[aria-label='Post']",
    "div[role='dialog'] button.share-actions__primary-action",
    "button.share-actions__primary-action",
    "button[aria-label*='Post']",
]