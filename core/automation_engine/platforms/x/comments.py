import time
import re

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from apps.comments.ai_reply import generate_ai_reply
from core.automation_engine.common.logger import clean_log as log, get_platform_logger

# SILENT = False


# def log(msg):
#     if not SILENT:
#         print(msg, flush=True)


def normalize(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.lower()).strip()


def clean_text(text):
    return "".join(c for c in text if ord(c) <= 0xFFFF)


def extract_status_id(url):
    if not url:
        return None

    match = re.search(r"/status/(\d+)", url)
    return match.group(1) if match else None


def get_article_status_id(article):
    try:
        links = article.find_elements(By.XPATH, ".//a[contains(@href, '/status/')]")

        for link in links:
            href = link.get_attribute("href") or ""
            match = re.search(r"/status/(\d+)", href)

            if match:
                return match.group(1)

    except Exception:
        pass

    return None


def click_show_more_replies(driver):
    try:
        buttons = driver.find_elements(By.XPATH, "//button | //div[@role='button']")

        for btn in buttons:
            text = normalize(btn.text)

            if (
                "show more replies" in text or
                "show replies" in text or
                "show additional replies" in text
            ):
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(2)

    except Exception:
        pass


def click_probable_spam(driver):
    try:
        elements = driver.find_elements(
            By.XPATH,
            "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'show probable spam')]"
        )

        for el in elements:
            if el.is_displayed():
                driver.execute_script("arguments[0].click();", el)
                time.sleep(3)
                return True

    except Exception:
        pass

    return False


def load_x_replies(driver):
    for i in range(8):
        driver.execute_script(f"window.scrollTo(0, {(i + 1) * 700});")
        time.sleep(0.7)


def extract_x_author(article):
    try:
        links = article.find_elements(By.XPATH, ".//a[contains(@href, '/')]")

        for link in links:
            href = link.get_attribute("href")

            if not href:
                continue

            if "/status/" in href:
                continue

            parts = href.strip("/").split("/")
            username = parts[-1]

            if username and username not in [
                "home",
                "explore",
                "notifications",
                "messages",
                "compose",
                "search",
            ]:
                return username

    except Exception:
        pass

    return "unknown"


def extract_x_reply_text(article):
    try:
        text_nodes = article.find_elements(By.XPATH, ".//div[@data-testid='tweetText']")

        for node in text_nodes:
            txt = node.text.strip()

            if txt:
                return txt

    except Exception:
        pass

    return ""


def get_x_reply_articles(driver):
    try:
        return driver.find_elements(By.XPATH, "//article[@data-testid='tweet']")
    except Exception:
        return []


def prepare_x_replies(driver):
    click_show_more_replies(driver)
    click_probable_spam(driver)
    load_x_replies(driver)
    click_show_more_replies(driver)
    click_probable_spam(driver)
    time.sleep(2)


def check_x_comments(driver, post_url):
    error_log = get_platform_logger("x")

    try:
        log("Checking X replies...")

        main_status_id = extract_status_id(post_url)

        driver.get(post_url)

        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        time.sleep(5)

        prepare_x_replies(driver)

        articles = get_x_reply_articles(driver)
        comments = []

        log(f"Found {len(articles)} X tweet articles")

        for article in articles:
            article_status_id = get_article_status_id(article)

            if article_status_id and article_status_id == main_status_id:
                continue

            text = extract_x_reply_text(article)

            if not text:
                continue

            author = extract_x_author(article)

            comments.append({
                "author": author,
                "text": text,
            })

            log(f"X reply found: {author} - {text}")

        log(f"Total X replies extracted: {len(comments)}")

        error_log.info("No error generated during X comment detection")
        return comments

    except Exception as exc:
        error_log.exception("X comment detection failed")
        clean_message = _clean_error_message(exc)

        log(f"X comment detection failed: {clean_message}")
        return []


def find_target_x_reply(driver, comment_text, post_url=None):
    target = normalize(comment_text)
    main_status_id = extract_status_id(post_url)

    articles = get_x_reply_articles(driver)

    for article in articles:
        article_status_id = get_article_status_id(article)

        if article_status_id and article_status_id == main_status_id:
            continue

        text = normalize(extract_x_reply_text(article))

        if target and target in text:
            return article

    return None


def click_x_reply_button(article):
    try:
        buttons = article.find_elements(By.XPATH, ".//*[@data-testid='reply']")

        for btn in buttons:
            if btn.is_displayed():
                btn.click()
                time.sleep(2)
                return True

    except Exception:
        pass

    return False


def type_x_reply(driver, reply_text):
    try:
        textbox = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((
                By.XPATH,
                "//div[@role='textbox' and @contenteditable='true']"
            ))
        )

        textbox.click()
        time.sleep(1)

        reply_text = clean_text(reply_text)
        textbox.send_keys(reply_text)

        time.sleep(1)

        return textbox

    except Exception as e:
        print("X TYPE REPLY ERROR:", e)
        return None


def submit_x_reply(driver):
    try:
        btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//*[@data-testid='tweetButton' or @data-testid='tweetButtonInline']"
            ))
        )

        btn.click()
        time.sleep(4)

        return True

    except Exception as e:
        print("X SUBMIT REPLY ERROR:", e)

        try:
            active = driver.switch_to.active_element
            active.send_keys(Keys.CONTROL, Keys.ENTER)
            time.sleep(4)
            return True
        except Exception:
            return False


def reply_x_comment(driver, post_url, reply_text=None, author=None, comment_text=None):
    error_log = get_platform_logger("x")

    try:
        log("X reply task received")

        driver.get(post_url)

        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        time.sleep(4)

        prepare_x_replies(driver)

        comment_element = find_target_x_reply(driver, comment_text, post_url)

        if not comment_element:
            raise RuntimeError("Target X reply not found")

        if not reply_text:
            ai_data = generate_ai_reply(
                comment_text=comment_text,
                author=author or "user",
                post_caption="",
                previous_comments=[],
                platform="twitter",
            )

            reply_text = ai_data.get("reply") or "Thank you!"

        log(f"Reply text: {reply_text}")

        if not click_x_reply_button(comment_element):
            raise RuntimeError("X reply button not found")

        textbox = type_x_reply(driver, reply_text)

        if not textbox:
            raise RuntimeError("X reply textbox not found")

        if not submit_x_reply(driver):
            raise RuntimeError("X reply submit failed")

        log("X reply sent")

        error_log.info("No error generated during X comment reply")

        return {
            "success": True,
            "comment": comment_text,
            "reply": reply_text,
        }

    except Exception as exc:
        error_log.exception("X comment reply failed")
        clean_message = _clean_error_message(exc)

        log(f"X comment reply failed: {clean_message}")

        return {
            "success": False,
            "message": clean_message,
        }
    
def _clean_error_message(exc: Exception) -> str:
    message = str(exc).strip()

    if message:
        return message.split("Stacktrace:")[0].strip()

    return exc.__class__.__name__