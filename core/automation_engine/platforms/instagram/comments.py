from selenium.webdriver.common.keys import Keys
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random

# =========================
# DRIVER CHECK
# =========================
def is_driver_alive(driver):
    try:
        driver.execute_script("return 1")
        return True
    except:
        return False


# =========================
# WAIT INSTAGRAM LOAD
# =========================
def wait_for_instagram(driver):
    try:
        WebDriverWait(driver, 25).until(
            lambda d: d.execute_script(
                "return document.querySelector('main') !== null"
            )
        )
        time.sleep(5)
        return True
    except:
        return False


# =========================
# OPEN POST
# =========================
def open_post(driver, url):
    try:
        driver.get(url)

        if not wait_for_instagram(driver):
            return False

        if "login" in driver.current_url.lower():
            return False

        print("🌍 URL:", driver.current_url)
        print("📄 TITLE:", driver.title)

        return True

    except Exception as e:
        print("❌ open_post error:", str(e))
        return False


# =========================
# FORCE LOAD COMMENTS
# =========================
def trigger_comment_load(driver):
    try:
        # Scroll the main window
        driver.execute_script("window.scrollBy(0, 300)")
        time.sleep(1)

        # Force scroll ANY scrollable container found on the page
        # This is crucial for the Instagram sidebar which has its own scrollbar
        driver.execute_script("""
            var scrolled = false;
            document.querySelectorAll('div').forEach(div => {
                if (div.scrollHeight > div.clientHeight) {
                    var style = window.getComputedStyle(div);
                    if (style.overflowY === 'auto' || style.overflowY === 'scroll') {
                        div.scrollTop = div.scrollHeight;
                        scrolled = true;
                    }
                }
            });
            return scrolled;
        """)
        time.sleep(2)
        
        # Scroll up slightly to ensure elements are in view
        driver.execute_script("window.scrollBy(0, -100)")
        time.sleep(1)
    except:
        pass


# =========================
# GET COMMENTS (CLEAN FORMAT)
# =========================
def check_instagram_comments(driver, post_url):
    comments = []

    try:
        if not is_driver_alive(driver):
            return []

        if not open_post(driver, post_url):
            return []

        print("✅ Post loaded")

        # Robust Bot Detection
        bot_username = "unknown_bot"
        try:
            bot_username = driver.execute_script("""
                var links = document.querySelectorAll('a[href^="/"]');
                for (var link of links) {
                    var href = link.getAttribute('href').replace(/\\//g, '');
                    if (link.innerText.toLowerCase().includes('profile') || 
                        link.getAttribute('aria-label')?.toLowerCase().includes('profile') ||
                        (link.querySelector('img') && link.querySelector('img').getAttribute('alt')?.toLowerCase().includes('profile'))) {
                        return href;
                    }
                }
                return null;
            """)
            if bot_username:
                print(f"🤖 Bot identified as: {bot_username}")
        except:
            pass

        trigger_comment_load(driver)
        time.sleep(6) # Increased wait for lazy loading

        # UNIVERSAL CRAWLER (Anchored on 'Reply' buttons)
        js_crawl_script = """
        var results = [];
        var timeRegex = /^(\\d+\\s*(s|m|h|d|w|sec|min|hour|day|week|ago|seconds|minutes|hours|days|weeks).*)$|^(\\d+[smhdw])$/i;

        // Find all "Reply" or "Like" buttons which are always present in comments
        var anchors = Array.from(document.querySelectorAll('div[role="button"], button')).filter(b => {
            var t = b.innerText.toLowerCase();
            return t === 'reply' || t === 'like';
        });
        
        var containers = new Set();
        anchors.forEach(a => {
            var c = a.closest('li, [role="menuitem"], [style*="flex-direction: column"]');
            if (c) containers.add(c);
        });
        
        // If no structured containers, try the parent of the anchors
        if (containers.size === 0) {
            anchors.forEach(a => {
                var p = a.parentElement;
                for(var i=0; i<5 && p; i++) {
                    if (p.innerText.length > 10 && p.querySelector('a[href^="/"]')) {
                        containers.add(p);
                        break;
                    }
                    p = p.parentElement;
                }
            });
        }

        containers.forEach(item => {
            var links = item.querySelectorAll('a[href^="/"]');
            var author = null;
            var text = "";
            
            for (var link of links) {
                var val = link.innerText.trim();
                if (val && !timeRegex.test(val) && val.length >= 2 && !val.includes(' ') && !val.includes('\\n')) {
                    author = val;
                    break;
                }
            }
            
            if (!author) return;
            
            var candidates = item.querySelectorAll('span, div');
            for (var cand of candidates) {
                if (cand.children.length > 2 && cand.tagName === 'DIV') continue; 
                
                var content = cand.innerText.trim();
                if (!content || content.length < 1) continue;
                if (content === author) continue;
                if (timeRegex.test(content)) continue;
                
                var lower = content.toLowerCase();
                if (['reply', 'see translation', 'view replies', 'hide replies', 'send', 'like', 'post'].includes(lower)) continue;
                
                if (content.startsWith(author)) {
                   content = content.substring(author.length).trim();
                }
                
                // Aggressive cleaning of timestamps and leading line breaks
                content = content.replace(/^\\d+[smhdw]\\s*/, '').replace(/^\\d+\\s*(m|h|d|w|min|hour|day|week|ago).*?\\n/, '').trim();
                content = content.replace(/^[\\n\\r\\s]+/, '');

                if (content.length > 0 && !timeRegex.test(content) && content.length < 500) {
                    text = content;
                    break;
                }
            }
            
            var blacklist = ['privacy', 'terms', 'locations', 'popular', 'about', 'help', 'api', 'jobs', 'meta', 'instagram', 'facebook', 'threads', 'contact', 'log in', 'sign up'];
            if (author && text) {
                if (!blacklist.includes(author.toLowerCase())) {
                    results.push({author: author, text: text});
                }
            }
        });
        
        return results;
        """
        
        raw_comments = driver.execute_script(js_crawl_script)
        
        print(f"🔍 DEBUG: Raw detected items: {len(raw_comments)}") 
        
        seen_hashes = set()
        for c in raw_comments:
            author = c['author']
            text = c['text']
            
            if not author or not text: continue
            
            # Skip if it's the bot itself
            if bot_username and author.lower() == bot_username.lower(): 
                continue
            
            c_hash = f"{author}:{text}"
            if c_hash not in seen_hashes:
                seen_hashes.add(c_hash)
                comments.append(c)
                print(f"✅ Detected comment: [{author}] - {text[:40]}...")

        print(f"📥 Found {len(comments)} valid comments after filtering")
        return comments[:30]

    except Exception as e:
        print("❌ Comment error:", str(e))
        return []


# =========================
# REPLY COMMENT (FIXED SIGNATURE + SAFE)
# =========================
def reply_instagram_comment(driver, post_url, reply_text, author=None, comment_text=None, comment_id=None, *args, **kwargs):
    try:
        print(f"🤖 Preparing to reply to [{author}]: '{reply_text}'")
        if not is_driver_alive(driver):
            print("❌ Driver dead")
            return {"success": False, "message": "Driver dead"}

        try:
            if not open_post(driver, post_url):
                print("❌ Post failed to load")
                return {"success": False, "message": "Post failed"}
        except Exception as e:
            print(f"❌ open_post error: {e}")
            return {"success": False, "message": f"Browser connection error: {e}"}

        trigger_comment_load(driver)
        time.sleep(3)
        # Incremental search and expansion
        reply_clicked = False
        if author and comment_text:
            print(f"🔍 Searching for specific comment by {author}...")
            
            for scroll_attempt in range(6):
                # 1. Expand any "View replies" buttons
                driver.execute_script("""
                    var buttons = document.querySelectorAll('button, span[role="button"]');
                    for (var i = 0; i < buttons.length; i++) {
                        var t = buttons[i].innerText.toLowerCase();
                        if (t.includes('view') && (t.includes('reply') || t.includes('replies'))) {
                            buttons[i].click();
                        }
                    }
                """)
                if scroll_attempt > 0: time.sleep(2)

                # 2. Search for the specific comment
                reply_clicked = driver.execute_script("""
                    var author = arguments[0].toLowerCase();
                    var text = arguments[1].toLowerCase();
                    var authorNoUnderscore = author.replace(/_/g, '');
                    var textClean = text.replace(/^@\\w+\\s+/, '').trim(); 
                    var textShort = textClean.substring(0, Math.min(textClean.length, 15));
                    
                    function matchComment(containerText) {
                        var ct = containerText.toLowerCase();
                        var authorMatch = ct.includes(author) || ct.includes(authorNoUnderscore);
                        var textMatch = ct.includes(text) || ct.includes(textClean) || (textShort.length > 5 && ct.includes(textShort));
                        return authorMatch && textMatch;
                    }

                    // Use "Reply" buttons as anchors (same as crawler)
                    var anchors = document.querySelectorAll('div[role="button"], button, span[role="button"]');
                    for (var i = 0; i < anchors.length; i++) {
                        var a = anchors[i];
                        if (a.innerText.toLowerCase().trim() === 'reply') {
                            // Find the closest container that holds the comment content
                            var container = a.closest('li, [role="menuitem"], [style*="flex-direction: column"]');
                            if (!container) {
                                // Fallback to a reasonably sized parent div
                                var p = a.parentElement;
                                for(var j=0; j<5 && p; j++) {
                                    if (p.innerText.length > 10 && p.innerText.length < 1000) {
                                        container = p;
                                        break;
                                    }
                                    p = p.parentElement;
                                }
                            }
                            
                            if (container && matchComment(container.innerText)) {
                                a.scrollIntoView({block: 'center'});
                                a.click();
                                return true;
                            }
                        }
                    }
                    return false;
                """, author, comment_text)

                if reply_clicked:
                    break
                
                # 3. Scroll down slightly if not found
                print(f"   (Attempt {scroll_attempt+1}) Not found, scrolling...")
                driver.execute_script("window.scrollBy(0, 500)")
                driver.execute_script("""
                    document.querySelectorAll('div').forEach(div => {
                        if (div.scrollHeight > div.clientHeight) {
                            var style = window.getComputedStyle(div);
                            if (style.overflowY === 'auto' || style.overflowY === 'scroll') {
                                div.scrollTop += 500;
                            }
                        }
                    });
                """)
                time.sleep(2)

        if reply_clicked:
            print("✅ Clicked 'Reply' on specific comment")
            time.sleep(2)
        else:
            print("❌ 'Reply' button not found for this specific comment. Skipping to avoid non-threaded response.")
            return {"success": False, "message": "Threaded 'Reply' button not found"}

        # 3. Wait until reply input box becomes active
        print("⏳ Step 3: Waiting for reply box to activate...")
        time.sleep(3)
        
        box = None
        print("🔍 Searching for specific threaded comment box...")
        
        # Priority 1: Search for a box inside the comment list (threaded)
        try:
            box = driver.execute_script("""
                var threadContainer = document.querySelector('ul[class*="X67o1"], div[role="button"] + ul, article ul');
                if (threadContainer) {
                    var innerBox = threadContainer.querySelector('div[contenteditable="true"], textarea');
                    if (innerBox && innerBox.offsetWidth > 0) return innerBox;
                }
                // Look for any box that is NOT the main fixed bottom box
                var allBoxes = document.querySelectorAll('div[contenteditable="true"], textarea');
                for (var i = 0; i < allBoxes.length; i++) {
                    var b = allBoxes[i];
                    if (b.offsetWidth > 0 && !b.closest('section')) return b; // main box is usually inside a section
                }
                return null;
            """)
        except:
            pass

        if not box:
            print("⚠️ Threaded box not found, searching for any active box...")
            xpaths = ["//textarea", "//div[@role='textbox']", "//div[contains(@aria-label, 'Add a comment')]"]
            for xp in xpaths:
                els = driver.find_elements(By.XPATH, xp)
                for el in els:
                    if el.is_displayed() and el.is_enabled():
                        box = el
                        break
                if box: break

        if not box:
            print("❌ Comment box not found")
            return {"success": False, "message": "Comment box not found"}

        # --- 10-Step Human Simulation Process ---
        
        # 1. Detect & Locate (Already done in previous steps)
        print(f"🤖 Step 1-3: Initiating human-like reply for {author}")
        
        # 4. Focus on the textarea/input
        try:
            box.click()
        except:
            driver.execute_script("arguments[0].click(); arguments[0].focus();", box)
        time.sleep(1)
        
        # 5. Type response slowly like a human
        print("⌨️ Step 5: Typing response slowly...")
        # Prepend a space if needed
        val = driver.execute_script("return arguments[0].innerText || arguments[0].value || '';", box)
        if val.strip() and not val.endswith(' '):
            driver.execute_script("arguments[0].innerText += ' '; arguments[0].dispatchEvent(new Event('input', {bubbles:true}));", box)
        
        for char in reply_text:
            # Use JS to append character (more robust than send_keys)
            driver.execute_script("""
                var el = arguments[0];
                var char = arguments[1];
                if (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT') {
                    el.value += char;
                } else {
                    el.innerText += char;
                }
                el.dispatchEvent(new Event('input', { bubbles: true }));
            """, box, char)
            time.sleep(random.uniform(0.05, 0.15)) # Human-like speed
            
        # 6. Wait 1–2 seconds
        time.sleep(random.uniform(1, 2))
        
        # 7. Verify text exists in input field
        print("🔍 Step 7: Verifying text in input...")
        final_val = driver.execute_script("return arguments[0].innerText || arguments[0].value || '';", box)
        if reply_text not in final_val:
            print("⚠️ Text missing! Retrying with direct injection...")
            driver.execute_script("arguments[0].innerText += arguments[1];", box, " " + reply_text)
            
        # 8. Click Post button
        print("📤 Step 8: Clicking Post button...")
        submit_success = driver.execute_script("""
            var buttons = document.querySelectorAll('button, div[role="button"], span[role="button"]');
            var postBtn = null;
            for (var i = 0; i < buttons.length; i++) {
                var t = buttons[i].innerText.toLowerCase().trim();
                if (t === 'post' || t === 'send') {
                    if (buttons[i].disabled) continue;
                    postBtn = buttons[i];
                    break;
                }
            }
            if (postBtn) {
                postBtn.scrollIntoView({block: 'center'});
                var events = ['mousedown', 'mouseup', 'click'];
                events.forEach(function(evtName) {
                    var evt = new MouseEvent(evtName, {bubbles: true, cancelable: true, view: window, buttons: 1});
                    postBtn.dispatchEvent(evt);
                });
                return true;
            }
            return false;
        """)
        
        if not submit_success:
            box.send_keys(Keys.ENTER)
            
        # 9. Wait for success confirmation
        print("⏳ Step 9: Waiting for submission to clear...")
        # Increase wait time for slow Instagram servers
        for _ in range(10):
            time.sleep(1)
            box_still_there = driver.execute_script("return arguments[0].offsetWidth > 0 && arguments[0].offsetHeight > 0;", box)
            if not box_still_there:
                break
        
        if box_still_there:
            # Check if it actually posted anyway (sometimes the box hangs but comment goes through)
            print("⚠️ Box still visible, checking DOM for comment...")
            
        # 10. Verify comment appears in DOM
        print("✅ Step 10: Verifying comment in DOM...")
        time.sleep(2)
        found_in_dom = driver.execute_script("""
            var comments = document.querySelectorAll('span');
            var target = arguments[0].toLowerCase();
            for (var i = 0; i < comments.length; i++) {
                if (comments[i].innerText.toLowerCase().includes(target)) return true;
            }
            return false;
        """, reply_text[:20]) # Check for first 20 chars
        
        if found_in_dom:
            print("🎉 Comment verified in DOM!")
            print("✅ Threaded reply successful")
            return {"success": True, "message": "Threaded reply successful"}
        elif box_still_there:
            print("❌ Submission failed (Instagram block)")
            return {"success": False, "message": "Submission failed (Instagram block)"}
        else:
            print("⚠️ Comment not found in DOM yet (might be slow loading)")
            return {"success": True, "message": "Reply sent (DOM verification pending)"}

    except Exception as e:
        print(f"❌ Reply Exception: {e}")
        return {"success": False, "message": str(e)}