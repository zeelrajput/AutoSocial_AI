# PROFILE_URL = "https://www.linkedin.com/in/zeel-rajput-25010136b/"

ACTIVITY_SECTION_XPATHS = [
    "//section[.//*[contains(normalize-space(),'Activity')]]",
    "//section[contains(., 'Activity')]",
    "//*[contains(normalize-space(),'Activity')]/ancestor::section[1]",
]

CREATE_POST_BUTTON_XPATHS = [
    ".//button[contains(normalize-space(), 'Create a post')]",
    ".//a[contains(normalize-space(), 'Create a post')]",
    ".//*[@role='button' and contains(normalize-space(), 'Create a post')]",
    ".//button[contains(@aria-label, 'Create a post')]",
    ".//a[contains(@href, '/preload/sharebox')]",
]

TEXTBOX_XPATHS = [
    # Dialog/modal based
    "//div[@role='dialog']//div[@contenteditable='true']",
    "//div[@role='dialog']//div[@role='textbox']",
    "//div[@role='dialog']//textarea",

    "//div[contains(@class,'artdeco-modal')]//div[@contenteditable='true']",
    "//div[contains(@class,'artdeco-modal')]//div[@role='textbox']",
    "//div[contains(@class,'artdeco-modal')]//textarea",

    # Sharebox / page based
    "//main//div[@contenteditable='true']",
    "//main//div[@role='textbox']",
    "//main//textarea",
    "//form//div[@contenteditable='true']",
    "//form//div[@role='textbox']",
    "//form//textarea",
    "//section//div[@contenteditable='true']",
    "//section//div[@role='textbox']",

    # Generic fallbacks
    "//div[contains(@class,'ql-editor') and @contenteditable='true']",
    "//div[@role='textbox' and @contenteditable='true']",
    "//div[@contenteditable='true']",
    "//textarea",
]

POST_BUTTON_XPATHS = [
    # Dialog scoped
    "//div[@role='dialog']//button[@type='submit']",
    "//div[@role='dialog']//button[contains(normalize-space(), 'Post')]",
    "//div[@role='dialog']//button[.//span[contains(normalize-space(), 'Post')]]",
    "//div[@role='dialog']//button[contains(@aria-label, 'Post')]",
    "//div[@role='dialog']//footer//button[not(@disabled)]",

    # Modal scoped
    "//div[contains(@class,'artdeco-modal')]//button[@type='submit']",
    "//div[contains(@class,'artdeco-modal')]//button[contains(normalize-space(), 'Post')]",
    "//div[contains(@class,'artdeco-modal')]//button[.//span[contains(normalize-space(), 'Post')]]",
    "//div[contains(@class,'artdeco-modal')]//button[contains(@aria-label, 'Post')]",
    "//div[contains(@class,'artdeco-modal')]//footer//button[not(@disabled)]",

    # Page/sharebox scoped
    "//main//button[@type='submit']",
    "//main//button[contains(normalize-space(), 'Post')]",
    "//main//button[.//span[contains(normalize-space(), 'Post')]]",
    "//main//button[contains(@aria-label, 'Post')]",
    "//form//button[@type='submit']",
    "//form//button[contains(normalize-space(), 'Post')]",
    "//form//button[.//span[contains(normalize-space(), 'Post')]]",
    "//form//button[contains(@aria-label, 'Post')]",

    # Generic LinkedIn post button fallbacks
    "//button[contains(@class, 'share-actions__primary-action')]",
    "//button[contains(@class, 'share-actions__post-button')]",
    "//button[contains(@data-control-name, 'share.post')]",
    "//button[contains(@data-control-name, 'post_share')]",
    "//button[@aria-label='Post']",
    "//button[contains(@aria-label, 'Post')]",
    "//button[normalize-space()='Post']",
    "//button[.//span[normalize-space()='Post']]",
]