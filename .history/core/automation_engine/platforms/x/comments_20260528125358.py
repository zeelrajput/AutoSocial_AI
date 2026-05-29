import time
import re

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from apps.comments.ai_reply import generate_ai_reply

SILENT = False


def log(msg):
    if not SILENT:
        print(msg, flush=True)


def normalize(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.lower()).strip()


def clean_text(text):
    return "".join(c for c in text if ord(c) <= 0xFFFF)


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

            if username and username not in ["home", "explore", "notifications", "messages"]:
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
        articles = driver.find_elements(By.XPATH, "//article[@data-testid='tweet']")
        return articles
    except Exception:
        return []


def check_x_comments(driver, post_url):
    try:
        log("📩 Checking X replies...")

        driver.get(post_url)

        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        time.sleep(4)

        load_x_replies(driver)

        articles = get_x_reply_articles(driver)

        comments = []

        for index, article in enumerate(articles):
            try:
                text = extract_x_reply_text(article)

                if not text:
                    continue

                # First article is usually the original post.
                if index == 0:
                    continue

                author = extract_x_author(article)

                comments.append({
                    "author": author,
                    "text": text,
                })

                log(f"💬 X reply found: {author} - {text}")

            except Exception as e:
                print("X COMMENT PARSE ERROR:", e)

        log(f"✅ Total X replies extracted: {len(comments)}")
        return comments

    except Exception as e:
        print("❌ X CHECK COMMENT ERROR:", e)
        return []


def find_target_x_reply(driver, comment_text):
    target = normalize(comment_text)

    articles = get_x_reply_articles(driver)

    for index, article in enumerate(articles):
        if index == 0:
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
    try:
        log("📩 X reply task received")

        driver.get(post_url)

        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        time.sleep(4)
        load_x_replies(driver)

        comment_element = find_target_x_reply(driver, comment_text)

        if not comment_element:
            return {
                "success": False,
                "message": "Target X reply not found",
            }

        if not reply_text:
            ai_data = generate_ai_reply(
                comment_text=comment_text,
                author=author or "user",
                post_caption="",
                previous_comments=[],
                platform="twitter",
            )

            reply_text = ai_data.get("reply") or "Thank you!"

        log(f"🤖 Reply text: {reply_text}")

        if not click_x_reply_button(comment_element):
            return {
                "success": False,
                "message": "X reply button not found",
            }

        textbox = type_x_reply(driver, reply_text)

        if not textbox:
            return {
                "success": False,
                "message": "X reply textbox not found",
            }

        if not submit_x_reply(driver):
            return {
                "success": False,
                "message": "X reply submit failed",
            }

        log("✅ X reply sent")

        return {
            "success": True,
            "comment": comment_text,
            "reply": reply_text,
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e),
        }
    