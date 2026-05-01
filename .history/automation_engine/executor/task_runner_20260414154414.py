import time
from apps.posts.models import Post
from automation_engine.browser.browser_manager import BrowserManager


def run_task(post_id):
    driver = None

    try:
        post = Post.objects.get(id=post_id)

        manager = BrowserManager(
            user_data_dir=None,
            profile_directory="Default",
            detach=True,
            headless=False,
        )

        driver = manager.start_browser()

        if post.platform.lower() == "instagram":
            driver.get("https://www.instagram.com")
        elif post.platform.lower() == "x":
            driver.get("https://x.com")
        elif post.platform.lower() == "linkedin":
            driver.get("https://www.linkedin.com")
        elif post.platform.lower() == "facebook":
            driver.get("https://www.facebook.com")
        else:
            raise ValueError(f"Unsupported platform: {post.platform}")

        time.sleep(10)

        post.status = "posted"
        post.error_message = None
        post.save()

        return {"success": True, "message": "Task completed successfully"}

    except Exception as e:
        try:
            post = Post.objects.get(id=post_id)
            post.status = "failed"
            post.error_message = str(e)
            post.save()
        except Exception:
            pass

        return {"success": False, "message": str(e)}

    finally:
        pass