CREATE_POST_XPATHS = [
    "//div[@aria-label='Create a post']",
    "//span[contains(normalize-space(),\"What's on your mind\")]/ancestor::*[@role='button'][1]",
    "//div[@role='button'][.//span[contains(normalize-space(),\"What's on your mind\")]]",
    "//span[normalize-space()='Photo/video']/ancestor::*[@role='button'][1]",
]

TEXTBOX_XPATHS = [
    "//div[@role='dialog']//div[@role='textbox']",
    "//div[@role='textbox']",
    "//div[contains(@aria-label,'on your mind')]",
    "//div[contains(@aria-label,'Write something')]",
]

PHOTO_VIDEO_XPATHS = [
    "//div[@role='dialog']//*[normalize-space()='Photo/video']/ancestor::*[@role='button'][1]",
    "//span[normalize-space()='Photo/video']/ancestor::*[@role='button'][1]",
    "//div[@aria-label='Photo/video']",
]

FILE_INPUT_XPATHS = [
    "//input[@type='file']",
    "//input[contains(@accept,'image')]",
    "//input[contains(@accept,'video')]",
]

POST_BUTTON_XPATHS = [
    "//div[@role='dialog']//*[@aria-label='Post']",
    "//div[@role='dialog']//*[normalize-space()='Post']/ancestor::*[@role='button'][1]",
    "//span[normalize-space()='Post']/ancestor::*[@role='button'][1]",
    "//div[@aria-label='Post']",
]