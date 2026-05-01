import time
from types import SimpleNamespace

from automation_engine.browser.browser_manager import BrowserManager

from automation_engine.platforms.x.post import post_to_x
from automation_engine.platforms.linkedin.post import post_to_linkedin
from automation_engine.platforms.instagram.post import post_to_instagram
from automation_engine.platforms.facebook.post import post_to_facebook


def run_task(post_id, platform=None, caption=None, media=None, driver=None):
    try:
        print("🚀 Running task from local agent")
        print("Post ID:", post_id)
        print("Platform:", platform)
        print("Caption:", caption)
        print("Media:", media)

        post = SimpleNamespace(
            id=post_id,
            platform=platform,
            caption=caption,
            media=media
        )

        if driver is None:
            manager = BrowserManager(detach=True, headless=False)
            print("🌐 Starting Chrome browser...")
            driver = manager.start_browser()
            print("✅ Chrome opened successfully")
        else:
            print("✅ Using existing Chrome browser")

        platform_name = str(platform).lower()

        if platform_name == "x":
            result = post_to_x(driver, post)

        elif platform_name == "linkedin":
            print("Calling LinkedIn automation...")
            result = post_to_linkedin(driver, post)

        elif platform_name == "instagram":
            print("Calling Instagram automation...")
            result = post_to_instagram(driver, post)

        elif platform_name == "facebook":
            print("Calling Facebook automation...")
            result = post_to_facebook(driver, post)

        else:
            return {
                "success": False,
                "message": f"Unsupported platform: {platform}"
            }

        print("Automation result:", result)

        if not result or not result.get("success"):
            return {
                "success": False,
                "message": result.get("message", "Automation failed") if result else "Automation failed"
            }

        time.sleep(3)

        return {
            "success": True,
            "message": f"Post {post_id} processed successfully"
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }