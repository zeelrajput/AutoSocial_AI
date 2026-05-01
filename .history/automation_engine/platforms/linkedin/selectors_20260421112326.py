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
    "//div[@role='dialog']//button[@aria-label='Post']",
    "//div[@role='dialog']//button[contains(@aria-label,'Post')]",
    "//div[@role='dialog']//span[normalize-space()='Post']/ancestor::button[1]",
    "//div[@role='dialog']//button[.//span[normalize-space()='Post']]",
    "//div[@role='dialog']//button[contains(., 'Post')]",

    "//div[contains(@class,'artdeco-modal')]//button[@aria-label='Post']",
    "//div[contains(@class,'artdeco-modal')]//button[contains(@aria-label,'Post')]",
    "//div[contains(@class,'artdeco-modal')]//span[normalize-space()='Post']/ancestor::button[1]",
    "//div[contains(@class,'artdeco-modal')]//button[.//span[normalize-space()='Post']]",
    "//div[contains(@class,'artdeco-modal')]//button[contains(., 'Post')]",

    "//button[@aria-label='Post']",
    "//button[contains(@aria-label,'Post')]",
    "//span[normalize-space()='Post']/ancestor::button[1]",
    "//button[.//span[normalize-space()='Post']]",
    "//button[contains(., 'Post')]",
]