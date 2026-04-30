START_POST_XPATHS = [
    "//button[contains(@class, 'share-box-feed-entry__trigger')]",
    "//button[.//*[contains(text(), 'Start a post')]]",
    "//div[contains(@class, 'share-box-feed-entry')]//button",
    "//button[@id='ember_start_post_trigger']",
    "//div[@role='button'][contains(., 'Start a post')]",
    "//button[@aria-label='Start a post']",
    "//button[contains(@aria-label,'Start a post')]",
    "//div[@role='button' and contains(@aria-label,'Start a post')]",
    "//span[contains(normalize-space(),'Start a post')]/ancestor::*[@role='button' or self::button][1]",
    "//div[contains(normalize-space(),'Start a post')]/ancestor::*[@role='button' or self::button][1]",
]

TEXTBOX_SELECTORS = [
    "div[role='dialog'] div.ql-editor[contenteditable='true']",
    "div[role='dialog'] div[role='textbox'][contenteditable='true']",
    "div[role='dialog'] div[contenteditable='true']",
    "div[role='dialog'] textarea",

    "div.artdeco-modal div.ql-editor[contenteditable='true']",
    "div.artdeco-modal div[role='textbox'][contenteditable='true']",
    "div.artdeco-modal div[contenteditable='true']",
    "div.artdeco-modal textarea",

    ".share-box div.ql-editor[contenteditable='true']",
    ".share-box div[role='textbox']",
    ".share-box div[contenteditable='true']",

    ".share-creation-state div.ql-editor[contenteditable='true']",
    ".share-creation-state div[role='textbox']",
    ".share-creation-state div[contenteditable='true']",
]

POST_BUTTON_SELECTORS = [
    "div[role='dialog'] button.share-actions__primary-action",
    "div[role='dialog'] button[aria-label='Post']",
    "div[role='dialog'] button[aria-label*='Post']",
    "div[role='dialog'] button.artdeco-button--primary",

    "div.artdeco-modal button.share-actions__primary-action",
    "div.artdeco-modal button[aria-label='Post']",
    "div.artdeco-modal button[aria-label*='Post']",

    "button.share-actions__primary-action",
    "button[aria-label='Post']",
    "button[aria-label*='Post']",
    "button.artdeco-button--primary",
]