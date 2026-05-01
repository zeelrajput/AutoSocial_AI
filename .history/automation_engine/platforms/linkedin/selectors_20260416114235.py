# automation_engine/platforms/linkedin/selectors.py

# Step 1: "Create a post" / "Start a post" trigger
START_POST_SELECTORS = [
    "button[aria-label*='Create a post']",
    "button[aria-label*='Start a post']",
    "button.share-box-feed-entry__trigger",
    "button.artdeco-button",
]

START_POST_XPATHS = [
    "//button[contains(., 'Create a post')]",
    "//button[contains(., 'Start a post')]",
    "//button[contains(@aria-label, 'Create a post')]",
    "//button[contains(@aria-label, 'Start a post')]",
    "//span[contains(., 'Create a post')]/ancestor::button[1]",
    "//span[contains(., 'Start a post')]/ancestor::button[1]",
]

# Step 2: Post text editor
TEXTBOX_SELECTORS = [
    "div[role='textbox']",
    "div.ql-editor[contenteditable='true']",
    "div.editor-content[contenteditable='true']",
]

TEXTBOX_XPATHS = [
    "//div[@role='textbox']",
    "//div[@contenteditable='true']",
]

# Step 3: Final Post button
POST_BUTTON_SELECTORS = [
    "button[aria-label='Post']",
    "button.share-actions__primary-action",
    "button.artdeco-button--primary",
]

POST_BUTTON_XPATHS = [
    "//button[@aria-label='Post']",
    "//button[contains(., 'Post')]",
    "//span[contains(., 'Post')]/ancestor::button[1]",
]