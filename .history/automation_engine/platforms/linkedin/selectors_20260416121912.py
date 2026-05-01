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
    "//button[contains(., 'Create a post')]",
    "//button[contains(., 'Start a post')]",
    "//button[contains(@aria-label, 'Create a post')]",
    "//button[contains(@aria-label, 'Start a post')]",
    "//a[contains(., 'Create a post')]",
    "//a[contains(@href, '/post/new/')]",
    "//span[contains(., 'Create a post')]/ancestor::a[1]",
    "//span[contains(., 'Create a post')]/ancestor::button[1]",
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