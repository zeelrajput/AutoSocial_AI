# open start-post model/button

START_POST_SELECTORS = [
        "button.share-box-feed-entry_trigger",
        "button[arial-label*='start a post']",
        "button[arial-label*='create a post']",
]

# text editor inside model
TEXTBOX_SELECTORS = [
    "div[role='textbox']",
    "div.ql-editor[contenteditable='true']",
    "div.editor-content[contenteditable='']"
]