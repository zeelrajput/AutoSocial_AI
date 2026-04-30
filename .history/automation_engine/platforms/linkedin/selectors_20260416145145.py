# Open start-post modal/button
START_POST_SELECTORS = [
    "button.share-box-feed-entry__trigger",
    "button[aria-label*='Start a post']",
    "button[aria-label*='Create a post']",
    "div.share-box-feed-entry__top-bar button",
    "div.share-box-feed-entry button",
    "button.artdeco-button[aria-label*='post']",
]

# Text editor inside modal
TEXTBOX_SELECTORS = [
    "div[role='textbox']",
    "div.ql-editor[contenteditable='true']",
    "div.editor-content[contenteditable='true']",
]

# Post button inside modal
POST_BUTTON_SELECTORS = [
    "button.share-actions__primary-action",
    "button[aria-label='Post']",
    "button.share-box_actions__primary-action",
]