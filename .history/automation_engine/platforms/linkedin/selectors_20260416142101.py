# automation_engine/platforms/linkedin/selectors.py

# ─── Start/Create Post Button ────────────────────────────────────────────────

START_POST_SELECTORS = [
    "button[aria-label*='Create a post']",
    "button[aria-label*='Start a post']",
    "button.share-box-feed-entry__trigger",
    "div.share-box-feed-entry__top-bar button",
    "a[href*='/post/new/']",
    "a[href*='create-post']",
]

START_POST_XPATHS = [
    "//button[contains(., 'Create a post')]",
    "//button[contains(., 'Start a post')]",
    "//button[contains(@aria-label, 'Create a post')]",
    "//button[contains(@aria-label, 'Start a post')]",
    "//span[contains(., 'Create a post')]/ancestor::button[1]",
    "//span[contains(., 'Start a post')]/ancestor::button[1]",
    "//a[contains(@href, '/post/new/')]",
]


# ─── Textbox inside the post composer modal ──────────────────────────────────

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


# ─── Post / Submit button ────────────────────────────────────────────────────

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