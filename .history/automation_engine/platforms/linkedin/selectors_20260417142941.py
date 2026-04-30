START_POST_SELECTORS = [
    "//button[contains(@class, 'share-box-feed-entry__trigger')]",
    "//button[.//*[contains(text(), 'Start a post')]]",
    "//div[contains(@class, 'share-box-feed-entry')]//button",
    "//button[@id='ember_start_post_trigger']", # Note: ember IDs change, but sometimes persist
    "//div[@role='button'][contains(., 'Start a post')]"
]

TEXTBOX_SELECTORS = [
    "div[role='dialog'] div.ql-editor",
    "div[role='dialog'] div[role='textbox']",
    "div[role='dialog'] div[contenteditable='true']",
    "div.ql-editor",
    "div[role='textbox']",
    "div[contenteditable='true']",
    "textarea",
    "p",
]

POST_BUTTON_SELECTORS = [
    "div[role='dialog'] button.share-actions__primary-action",
    "div[role='dialog'] button[aria-label='Post']",
    "div[role='dialog'] button[aria-label*='Post']",
    "button.share-actions__primary-action",
    "button[aria-label='Post']",
    "button[aria-label*='Post']",
    "button.artdeco-button--primary",
]