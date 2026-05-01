# automation_engine/platforms/linkedin/selectors.py

START_POST_SELECTORS = [
    # The actual "Start a post" placeholder text area
    "div.share-box-feed-entry__top-bar",
    "div.share-box-feed-entry__trigger-container",
    "button.share-box-feed-entry__trigger",
    "[placeholder='Start a post']",
    "div[aria-placeholder='Start a post']",
]

START_POST_XPATHS = [
    "//div[contains(text(), 'Start a post')]",
    "//span[contains(text(), 'Start a post')]",
    "//button[contains(text(), 'Start a post')]",
    "//*[contains(@placeholder, 'Start a post')]",
    "//*[contains(@aria-placeholder, 'Start a post')]",
    "//div[contains(@class, 'share-box-feed-entry')]//button",
    "//div[contains(@class, 'share-box')]",
]

TEXTBOX_SELECTORS = [
    "div[role='textbox']",
    "div.ql-editor[contenteditable='true']",
    "div.editor-content[contenteditable='true']",
]

TEXTBOX_XPATHS = [
    "//div[@role='textbox']",
    "//div[@contenteditable='true']",
]

POST_BUTTON_SELECTORS = [
    "button[aria-label='Post']",
    "button.share-actions__primary-action",
    # removed: "button.artdeco-button--primary"  ← too broad
]

POST_BUTTON_XPATHS = [
    "//button[@aria-label='Post']",
    "//button[normalize-space(.)='Post']",  # exact text match
    "//span[normalize-space(.)='Post']/ancestor::button[1]",
]