CREATE_BUTTON_XPATHS = [
    "//div[@role='button']//*[name()='svg']/ancestor::div[@role='button']",
    "//div[@role='button'][.//svg]",
]

FILE_INPUT = "//input[@type='file']"

NEXT_BUTTON_XPATHS = [
    "//button[text()='Next']",
    "//div[text()='Next']/ancestor::button",
]

SHARE_BUTTON_XPATHS = [
    "//button[text()='Share']",
    "//div[text()='Share']/ancestor::button",
]

CAPTION_XPATHS = [
    "//textarea",
    "//div[@contenteditable='true']",
]