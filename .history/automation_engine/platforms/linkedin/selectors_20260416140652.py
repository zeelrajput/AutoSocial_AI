# automation_engine/platforms/linkedin/selectors.py

START_POST_SELECTORS = [
    "button[aria-label*='Create a post']",
    "button[aria-label*='Start a post']",
    "a[href*='/post/new/']",
    "a[href*='create-post']",
    "button.share-box-feed-entry__trigger",
    "button.artdeco-button",
]

START_POST_XPATHS = [
    "//button[contains(., 'Create a post')]",
    "//button[contains(., 'Start a post')]",
    "//button[contains(@aria-label, 'Create a post')]",
    "//button[contains(@aria-label, 'Start a post')]",
    "//a[contains(., 'Create a post')]",
    "//a[contains(@href, '/post/new/')]",
    "//span[contains(., 'Create a post')]/ancestor::a[1]",
    "//span[contains(., 'Create a post')]/ancestor::button[1]",
]


# ─── Textbox inside the post composer modal ───────────────────────────────────

TEXTBOX_SELECTORS = [
    "div[role='textbox']",
    "div[contenteditable='true']",
    "[contenteditable='true']",
    "div[aria-multiline='true']",
    "p[data-placeholder]",
    "div.ql-editor",
]

TEXTBOX_XPATHS = [
    ".//*[@role='textbox']",
    ".//*[@contenteditable='true']",
    ".//*[@aria-multiline='true']",
    ".//p[@data-placeholder]",
    ".//*[contains(@class,'ql-editor')]",
]


# ─── Post / Submit button ─────────────────────────────────────────────────────

POST_BUTTON_SELECTORS = [
    # Aria-label based (most stable)
    "button[aria-label='Post']",

    # Class-based
    "button.share-actions__primary-action",
    ".share-actions__primary-action",

    # Inside modal footer
    "div[role='dialog'] button.share-actions__primary-action",
    "div.share-actions button[type='submit']",
]

POST_BUTTON_XPATHS = [
    # Aria-label (most stable)
    "//button[@aria-label='Post']",

    # Exact text
    "//button[normalize-space(.)='Post']",
    "//span[normalize-space(.)='Post']/ancestor::button[1]",

    # Inside modal dialog
    "//div[@role='dialog']//button[normalize-space(.)='Post']",
    "//div[@role='dialog']//button[@aria-label='Post']",

    # Primary action class
    "//button[contains(@class,'primary') and contains(normalize-space(.), 'Post')]",
    "//button[contains(@class,'share-actions__primary-action')]",
]