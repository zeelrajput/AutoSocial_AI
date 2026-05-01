START_POST_XPATHS = [
    "//button[contains(@aria-label,'Start a post')]",
    "//div[@role='button'][.//*[contains(normalize-space(),'Start a post')]]",
    "//span[contains(normalize-space(),'Start a post')]/ancestor::*[@role='button'][1]",
    "//*[@aria-label='Start a post']/ancestor::*[@role='button' or self::button][1]",
]

TEXTBOX_XPATHS = [
    # modal scoped
    "//div[@role='dialog']//div[@contenteditable='true']",
    "//div[@role='dialog']//div[@role='textbox']",
    "//div[@role='dialog']//*[@contenteditable='true' and @role='textbox']",
    "//div[@role='dialog']//div[contains(@class,'ql-editor')]",
    "//div[@role='dialog']//*[@data-placeholder]",

    # global fallbacks
    "//div[@contenteditable='true' and @role='textbox']",
    "//div[@role='textbox' and @contenteditable='true']",
    "//div[contains(@class,'ql-editor') and @contenteditable='true']",
    "//*[@contenteditable='true' and contains(@aria-label,'text')]",
    "//*[@contenteditable='true' and contains(@data-placeholder,'talk about')]",
    "//*[@contenteditable='true']",
]


PHOTO_BUTTON_XPATHS = [
    "//button[.//span[normalize-space()='Add media']]",
    "//button[.//span[normalize-space()='Photo']]",
    "//button[contains(@aria-label,'Add media')]",
    "//button[contains(@aria-label,'Photo')]",
    "//div[@role='button'][.//span[normalize-space()='Photo']]",
    "//div[@role='button'][.//span[normalize-space()='Add media']]",
    "//span[normalize-space()='Photo']/ancestor::button[1]",
    "//span[normalize-space()='Add media']/ancestor::button[1]",
]

CLOSE_POPUP_XPATHS = [
    "//button[@aria-label='Dismiss']",
    "//button[@aria-label='Close']",
    "//span[normalize-space()='Not now']/ancestor::*[@role='button'][1]",
]