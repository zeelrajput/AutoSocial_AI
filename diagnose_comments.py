import os
import sys
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# Setup paths
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Use the exact profile from the config
CONFIG_FILE = Path(os.environ.get("LOCALAPPDATA", "")) / "AutoSocialAI" / "agent_config.json"
if not CONFIG_FILE.exists():
    # Fallback to local_agent config
    CONFIG_FILE = BASE_DIR / "agent_config.json"

import json
if CONFIG_FILE.exists():
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
    user_data_dir = config.get("user_data_dir")
    profile_directory = config.get("profile_directory", "Default")
else:
    user_data_dir = str(Path(os.environ.get("LOCALAPPDATA", "")) / "AutoSocialAI" / "chrome_profile")
    profile_directory = "Default"

print(f"Profile Path: {user_data_dir}")
print(f"Profile Directory: {profile_directory}")

options = Options()
options.add_argument(f"--user-data-dir={user_data_dir}")
options.add_argument(f"--profile-directory={profile_directory}")
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# Run headless so it doesn't disturb the user
options.add_argument("--headless=new")

driver = webdriver.Chrome(options=options)

try:
    post_url = "https://www.linkedin.com/feed/update/urn:li:share:7462433823159504896/"
    print(f"Opening URL: {post_url}")
    driver.get(post_url)
    time.sleep(8)
    
    # Scroll to load comments
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
    time.sleep(3)
    
    comments_els = driver.find_elements(
        By.XPATH,
        "//article[(contains(@class,'comments-comment-item') or contains(@class,'comment')) and not(ancestor::article)]"
    )
    
    print(f"Total top-level comments found: {len(comments_els)}")
    
    for idx, c in enumerate(comments_els):
        print(f"\n--- Comment #{idx + 1} ---")
        try:
            # Print first 2 lines of text
            text_lines = c.text.split("\n")
            print(f"First 2 lines of text: {text_lines[:2]}")
            
            # Print full text briefly
            full_text_preview = " | ".join(line.strip() for line in text_lines if line.strip())[:150]
            print(f"Full text preview: {full_text_preview}")
            
            # Extract author
            author = text_lines[0].strip().lower() if text_lines else "unknown"
            print(f"Extracted Author (legacy): {author}")
            
            # Try specific selectors
            specific_author = "not found"
            for xpath in [
                ".//span[contains(@class, 'comments-post-meta__name-text')]",
                ".//a[contains(@class, 'comments-post-meta__name-link')]",
                ".//span[contains(@class, 'comments-comment-meta__description-title')]"
            ]:
                try:
                    el = c.find_element(By.XPATH, xpath)
                    specific_author = el.text.strip().lower()
                    break
                except:
                    continue
            print(f"Extracted Author (specific): {specific_author}")
            
            # Find nested articles
            nested_articles = c.find_elements(By.XPATH, ".//article")
            print(f"Nested articles found (including possible self): {len(nested_articles)}")
            
            for jdx, r in enumerate(nested_articles):
                is_self = (r.id == c.id)
                r_text_lines = r.text.split("\n")
                r_author = r_text_lines[0].strip().lower() if r_text_lines else "unknown"
                print(f"  -> Nested #{jdx + 1}: is_self={is_self}, ID={r.id}")
                print(f"     First line: {r_text_lines[:1]}")
                print(f"     Author: {r_author}")
                
        except Exception as ex:
            print(f"Error parsing comment #{idx + 1}: {ex}")

finally:
    driver.quit()
