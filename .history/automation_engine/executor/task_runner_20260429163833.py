import time
from types import SimpleNamespace

from automation_engine.browser.browser_manager import BrowserManager

from automation_engine.platforms.x.post import post_to_x
from automation_engine.platforms.linkedin.post import post_to_linkedin
from automation_engine.platforms.instagram.post import post_to_instagram
from automation_engine.platforms.facebook.post import post_to_facebook


def run_task(post_id, platform=None, caption=None, media=None, browser_manager=None):
    driver = None

    try:
        print("🚀 Running task from local agent")

        post = SimpleNamespace(
            id=post_id,
            platform=platform,
            caption=caption,
            media=media
        )

        manager = browser_manager or BrowserManager(
            detach=True,
            headless=False,
        )

        driver = manager.start_browser()
        print("✅ Chrome opened")

        platform_name = str(platform).lower()

        time.sleep(2)

        if platform_name == "x":
            result = post_to_x(driver, post)

        elif platform_name == "linkedin":
            result = post_to_linkedin(driver, post)

        elif platform_name == "instagram":
            result = post_to_instagram(driver, post)

        elif platform_name == "facebook":
            result = post_to_facebook(driver, post)

        else:
            return {"success": False, "message": f"Unsupported platform: {platform}"}

        print("Result:", result)

        if not result.get("success"):
            print("❌ Error:", result.get("message"))
            return result

        return {
            "success": True,
            "message": f"Post {post_id} processed successfully"
        }

    except Exception as e:
        return {"success": False, "message": str(e)}

    finally:
        pass   # 🔥 IMPORTANT: keep browser open