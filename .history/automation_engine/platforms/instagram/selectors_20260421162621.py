FILE_INPUT_XPATHS = [
    "//input[@type='file']",
    "//input[contains(@accept,'image')]",
    "//input[contains(@accept,'video')]",
    "//input[contains(@accept,'image') and @type='file']",
]

SELECT_FROM_COMPUTER_XPATHS = [
    "//div[text()='Select from computer']",
    "//button[text()='Select from computer']",
    "//span[text()='Select from computer']/ancestor::button[1]",
    "//span[text()='Select from computer']/ancestor::div[@role='button'][1]",
]