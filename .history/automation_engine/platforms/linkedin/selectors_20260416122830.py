# automation_engine/platforms/linkedin/selectors.py

START_POST_SELECTORS = [
    # Direct placeholder/trigger button
    "button.share-box-feed-entry__trigger",
    "div.share-box-feed-entry__trigger-container button",
    "div.share-box-feed-entry__top-bar button",

    # Generic placeholder-style inputs
    "[placeholder='Start a post']",
    "[placeholder*='post']",
    "div[aria-placeholder*='Start a post']",

    # Data attributes LinkedIn sometimes uses
    "[data-control-name='share.sharebox_focus']",
    "[data-control-name*='share']",
]

START_POST_XPATHS = [
    # Text-based - most reliable
    "//div[contains(@class,'share-box')]//button",
    "//button[contains(normalize-space(.), 'Start a post')]",
    "//span[contains(normalize-space(.), 'Start a post')]/ancestor::button[1]",
    "//div[contains(normalize-space(.), 'Start a post') and (@role='button' or @tabindex)]",

    # Placeholder-based
    "//*[@placeholder='Start a post']",
    "//*[contains(@aria-placeholder, 'Start a post')]",

    # The input-like div at the top of the feed
    "//div[@role='textbox' and contains(@aria-placeholder, 'post')]",

    # Any clickable element near the post icon (Z avatar area)
    "//div[contains(@class,'share-box-feed-entry')]//button[1]",
    "//div[contains(@class,'share')]//button[contains(@class,'trigger')]",

    # Last resort: find by visible text in any element
    "//*[text()='Start a post']",
    "//*[contains(text(),'Start a post')]",
]

TEXTBOX_SELECTORS = [
    "div[role='textbox']",
    "div.ql-editor[contenteditable='true']",
    "div.editor-content[contenteditable='true']",
    "div[contenteditable='true']",
    ".share-creation-state__main-editor div[role='textbox']",
    ".share-editor div[role='textbox']",
]

TEXTBOX_XPATHS = [
    "//div[@role='textbox' and @contenteditable='true']",
    "//div[@contenteditable='true' and @role='textbox']",
    "//div[@contenteditable='true']",
    "//div[contains(@class,'editor')][@contenteditable='true']",
    "//div[contains(@class,'ql-editor')]",
]

POST_BUTTON_SELECTORS = [
    "button[aria-label='Post']",
    "button.share-actions__primary-action",
    ".share-actions__primary-action",
]

POST_BUTTON_XPATHS = [
    "//button[@aria-label='Post']",
    "//button[normalize-space(.)='Post']",
    "//span[normalize-space(.)='Post']/ancestor::button[1]",
    "//button[contains(@class,'primary') and contains(normalize-space(.), 'Post')]",
]