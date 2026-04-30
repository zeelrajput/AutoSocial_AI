# automation_engine/platforms/linkedin/selectors.py

# ─── Start / Create Post Button ───────────────────────────────────────────────

START_POST_SELECTORS = [
    "button[aria-label*='Start a post']",
    "button.share-box-feed-entry__trigger",
    "div.share-box-feed-entry__top-bar button",
    "a[href*='/post/new/']",
]

START_POST_XPATHS = [
    "//button[contains(., 'Start a post')]",
    "//button[contains(@aria-label, 'Create a post')]",
    "//button[contains(@aria-label, 'Start a post')]",
    "//span[contains(., 'Start a post')]/ancestor::button[1]",
    "//a[contains(@href, '/post/new/')]",
]


# ─── Textbox inside the post composer modal ───────────────────────────────────

TEXTBOX_SELECTORS = [
    "div[role='textbox']",
    "[contenteditable='true']",
    "div[aria-multiline='true']",
    "div.ql-editor",
    "p[data-placeholder]",
]

TEXTBOX_XPATHS = [
    ".//*[@role='textbox']",
    ".//*[@contenteditable='true']",
    ".//*[@aria-multiline='true']",
    ".//*[contains(@class,'ql-editor')]",
    ".//p[@data-placeholder]",
]


# ─── Post / Submit Button ─────────────────────────────────────────────────────

POST_BUTTON_SELECTORS = [
    "button[aria-label='Post']",
    "button.share-actions__primary-action",
    ".share-actions__primary-action",
    "div.share-actions button[type='submit']",
    "footer button[aria-label='Post']",
]

POST_BUTTON_XPATHS = [
    "//button[@aria-label='Post']",
    "//button[normalize-space(.)='Post']",
    "//span[normalize-space(.)='Post']/ancestor::button[1]",
    "//button[contains(@class,'share-actions__primary-action')]",
]


# ─── Image / Media Upload ─────────────────────────────────────────────────────

MEDIA_UPLOAD_SELECTORS = [
    "button[aria-label*='Add a photo']",
    "button[aria-label*='Add media']",
    "input[type='file'][accept*='image']",
    ".share-creation-state__additional-toolbar button[aria-label*='photo']",
]

MEDIA_UPLOAD_XPATHS = [
    "//button[contains(@aria-label,'Add a photo')]",
    "//button[contains(@aria-label,'Add media')]",
    "//label[contains(@aria-label,'photo')]",
]