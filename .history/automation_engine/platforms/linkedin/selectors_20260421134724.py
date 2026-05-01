PROFILE_URL = "https://www.linkedin.com/in/zeel-rajput-25010136b/"

ACTIVITY_SECTION_XPATHS = [
    "//section[.//*[contains(normalize-space(),'Activity')]]",
    "//section[contains(., 'Activity')]",
    "//*[contains(normalize-space(),'Activity')]/ancestor::section[1]",
]

CREATE_POST_BUTTON_XPATHS = [
    ".//button[contains(., 'Create a post')]",
    ".//a[contains(., 'Create a post')]",
    ".//*[@role='button' and contains(., 'Create a post')]",
    ".//button[contains(@aria-label, 'Create a post')]",
]

TEXTBOX_XPATHS = [
    "//div[@role='dialog']//div[@contenteditable='true']",
    "//div[@role='dialog']//div[@role='textbox']",
    "//div[@role='dialog']//textarea",

    "//div[contains(@class,'artdeco-modal')]//div[@contenteditable='true']",
    "//div[contains(@class,'artdeco-modal')]//div[@role='textbox']",
    "//div[contains(@class,'artdeco-modal')]//textarea",

    "//div[contains(@class,'ql-editor') and @contenteditable='true']",
    "//div[@role='textbox' and @contenteditable='true']",
    "//div[@contenteditable='true']",
    "//textarea",
]

POST_BUTTON_XPATHS = [
    "//button[contains(@class, 'share-actions__primary-action')]",
    "//div[contains(@class, 'share-box_actions')]//button[contains(., 'Post')]",
    "//button[contains(@class, 'share-actions__post-button')]",
    "//div[@role='dialog']//button[.//*[text()='Post']]",
    "//button[@aria-label='Post']"
]