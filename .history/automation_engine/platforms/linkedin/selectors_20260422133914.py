START_POST_XPATHS = [
    "//button[contains(@aria-label,'Start a post')]",
    "//div[@role='button' and contains(@aria-label,'Start a post')]",
    "//span[normalize-space()='Start a post']/ancestor::*[@role='button'][1]",
    "//div[@role='button'][.//*[contains(normalize-space(),'Start a post')]]",
    "//button[.//*[contains(normalize-space(),'Start a post')]]",
]

TEXTBOX_XPATHS = [
    "//div[@role='dialog']//div[@role='textbox']",
    "//div[@role='dialog']//*[@contenteditable='true']",
    "//div[contains(@class,'ql-editor') and @contenteditable='true']",
    "//div[@role='textbox' and @contenteditable='true']",
]

POST_BUTTON_XPATHS = [
    "//div[@role='dialog']//button[contains(@aria-label,'Post')]",
    "//div[@role='dialog']//*[normalize-space()='Post']/ancestor::button[1]",
    "//div[@role='dialog']//*[normalize-space()='Post']/ancestor::*[@role='button'][1]",
    "//button[contains(@class,'share-actions__primary-action')]",
]

CLOSE_POPUP_XPATHS = [
    "//button[@aria-label='Dismiss']",
    "//button[@aria-label='Close']",
    "//span[normalize-space()='Not now']/ancestor::*[@role='button'][1]",
]

ADD_MEDIA_XPATHS = [
    "//div[@role='dialog']//button[contains(@aria-label,'Add media')]",
    "//div[@role='dialog']//*[contains(normalize-space(),'Add media')]/ancestor::button[1]",
    "//button[contains(@aria-label,'Photo')]",
]

FILE_INPUT_XPATHS = [
    "//input[@type='file' and contains(@accept,'image')]",
    "//input[@type='file' and contains(@accept,'image/')]",
    "//div[@role='dialog']//input[@type='file']",
]