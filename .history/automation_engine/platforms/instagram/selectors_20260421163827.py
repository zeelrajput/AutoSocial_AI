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

FILE_INPUT_XPATHS = [
    "//input[@type='file']",
    "//input[contains(@accept,'image')]",
    "//input[contains(@accept,'video')]",
    "//input[contains(@accept,'image') and @type='file']",
]

SELECT_FROM_COMPUTER_XPATHS = [
    "//div[text()='Select from computer']",
    "//button[text()='Select from computer']",
    "//span[text()='Select from computer']/ancestor::button[1]",
    "//span[text()='Select from computer']/ancestor::div[@role='button'][1]",
]

CREATE_BUTTON_XPATHS = [
    "//a[contains(@href,'/create/select')]",
    "//div[@role='button'][.//*[name()='svg']]",
    "//span[text()='Create']/ancestor::*[@role='button'][1]",
    "//a[.//span[text()='Create']]",
]

NEW_POST_XPATHS = [
    "//span[text()='Post']/ancestor::*[@role='button'][1]",
    "//span[text()='Post']/ancestor::div[@role='button'][1]",
    "//div[@role='button'][.//span[text()='Post']]",
    "//span[text()='New post']/ancestor::*[@role='button'][1]",
]

FILE_INPUT_XPATHS = [
    "//input[@type='file']",
    "//input[contains(@accept,'image')]",
    "//input[contains(@accept,'video')]",
    "//input[contains(@accept,'image') and @type='file']",
]

SELECT_FROM_COMPUTER_XPATHS = [
    "//div[text()='Select from computer']",
    "//button[text()='Select from computer']",
    "//span[text()='Select from computer']/ancestor::button[1]",
    "//span[text()='Select from computer']/ancestor::*[@role='button'][1]",
]