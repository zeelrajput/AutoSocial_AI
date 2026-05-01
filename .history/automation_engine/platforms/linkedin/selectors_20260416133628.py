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
    # Text-based — most reliable across LinkedIn UI changes
    "//button[contains(normalize-space(.), 'Start a post')]",
    "//span[contains(normalize-space(.), 'Start a post')]/ancestor::button[1]",
    "//div[contains(normalize-space(.), 'Start a post') and (@role='button' or @tabindex)]",

    # Share-box class patterns
    "//div[contains(@class,'share-box')]//button",
    "//div[contains(@class,'share-box-feed-entry')]//button[1]",
    "//div[contains(@class,'share')]//button[contains(@class,'trigger')]",

    # Placeholder-based
    "//*[@placeholder='Start a post']",
    "//*[contains(@aria-placeholder, 'Start a post')]",

    # Textbox-style div at top of feed (some LinkedIn layouts)
    "//div[@role='textbox' and contains(@aria-placeholder, 'post')]",

    # Last resort: any visible element with exact or partial text
    "//*[text()='Start a post']",
    "//*[contains(text(),'Start a post')]",
]


# ─── Textbox inside the post composer modal ───────────────────────────────────

TEXTBOX_SELECTORS = [
    # Inside modal — scoped to dialog container first
    "div[role='dialog'] div.ql-editor[contenteditable='true']",
    "div[role='dialog'] div[role='textbox'][contenteditable='true']",
    "div[role='dialog'] div[contenteditable='true']",

    # Quill editor (LinkedIn's rich text engine)
    "div.ql-editor[contenteditable='true']",

    # Role + contenteditable (most robust)
    "div[role='textbox'][contenteditable='true']",
    "div[contenteditable='true'][role='textbox']",
    "div[contenteditable='true'][aria-multiline='true']",

    # Share creation state editor
    "div.share-creation-state__main-editor div[role='textbox']",
    "div.share-creation-state__main-editor div[contenteditable='true']",
    "div.share-box-v2__content div[role='textbox']",
    "div.share-editor div[role='textbox']",

    # Broad fallback — any contenteditable div
    "div[contenteditable='true']",
]

TEXTBOX_XPATHS = [
    # Scoped inside modal dialog — most reliable
    "//div[@role='dialog']//div[@role='textbox' and @contenteditable='true']",
    "//div[@role='dialog']//div[@contenteditable='true']",
    "//div[@aria-modal='true']//div[@contenteditable='true']",

    # Quill editor
    "//div[contains(@class,'ql-editor') and @contenteditable='true']",
    "//div[contains(@class,'ql-editor')]",

    # Role + contenteditable
    "//div[@role='textbox' and @contenteditable='true']",
    "//div[@contenteditable='true' and @role='textbox']",

    # Editor class patterns
    "//div[contains(@class,'editor')][@contenteditable='true']",
    "//div[contains(@class,'share-creation')]//div[@contenteditable='true']",

    # Aria multiline (LinkedIn composer)
    "//div[@aria-multiline='true' and @contenteditable='true']",

    # Broad fallback
    "//div[@contenteditable='true']",
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