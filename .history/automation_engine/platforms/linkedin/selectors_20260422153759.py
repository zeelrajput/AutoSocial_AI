START_POST_XPATHS = [
    "//button[contains(@aria-label,'Start a post')]",
    "//div[@role='button'][.//*[contains(normalize-space(),'Start a post')]]",
    "//span[contains(normalize-space(),'Start a post')]/ancestor::*[@role='button'][1]",
]

POST_BUTTON_XPATHS = [
    "//div[@role='dialog']//*[@aria-label='Post']",
    "//div[@role='dialog']//*[normalize-space()='Post']/ancestor::*[@role='button'][1]",
    "//button[contains(@aria-label,'Post')]",
]

CLOSE_POPUP_XPATHS = [
    "//button[@aria-label='Dismiss']",
    "//button[@aria-label='Close']",
    "//span[normalize-space()='Not now']/ancestor::*[@role='button'][1]",
]