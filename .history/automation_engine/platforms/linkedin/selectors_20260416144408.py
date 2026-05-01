# LinkedIn Selectors for Post Automation

# -------------------------------
# 1. START POST BUTTON
# -------------------------------
COMPOSE_SELECTORS = [
    # Primary (most stable)
    "button.share-box-feed-entry__trigger",

    # Aria-based (dynamic but reliable)
    "button[aria-label*='Start a post']",
    "button[aria-label*='post']",

    # Structure-based fallback
    "div.share-box-feed-entry__top-bar button",

    # XPath fallback
    "//button[contains(@class,'share-box-feed-entry__trigger')]",
    "//button[contains(@aria-label,'Start')]",
    "//span[text()='Start a post']/ancestor::button",
]


# -------------------------------
# 2. TEXTBOX (POST COMPOSER)
# -------------------------------
TEXTBOX_SELECTORS = [
    # Inside modal (best)
    "div[role='dialog'] div.ql-editor[contenteditable='true']",
    "div[role='dialog'] div[role='textbox'][contenteditable='true']",

    # General LinkedIn editor
    "div.ql-editor[contenteditable='true']",
    "div[role='textbox'][contenteditable='true']",

    # Fallback
    "div[contenteditable='true'][aria-multiline='true']",

    # XPath fallback
    "//div[@role='dialog']//div[@contenteditable='true']",
]


# -------------------------------
# 3. POST BUTTON
# -------------------------------
POST_BUTTON_SELECTORS = [
    # Primary
    "button.share-actions__primary-action",

    # Aria-based
    "button[aria-label='Post']",
    "button[aria-label*='post']",

    # Text-based
    "//button[.//span[text()='Post']]",

    # Generic fallback
    "button[type='submit']",
]