

def find_create_button(driver):
    for xpath in CREATE_BUTTON_XPATHS:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for el in elements:
                if el.is_displayed():
                    return el
        except:
            continue
    return None


def click_next(driver):
    for _ in range(5):
        for xpath in NEXT_BUTTON_XPATHS:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                for el in elements:
                    if el.is_displayed():
                        el.click()
                        time.sleep(2)
                        print("✅ Next clicked")
                        return True
            except:
                continue
        time.sleep(1)
    return False


def find_caption_box(driver):
    for xpath in CAPTION_XPATHS:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for el in elements:
                if el.is_displayed():
                    return el
        except:
            continue
    return None


def find_share_button(driver):
    for _ in range(5):
        for xpath in SHARE_BUTTON_XPATHS:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                for el in elements:
                    if el.is_displayed():
                        return el
            except:
                continue
        time.sleep(1)
    return None