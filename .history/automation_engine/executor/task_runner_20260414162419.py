from apps.posts.models import Post
from automation_engine.browser.browser_manager import BrowserManager
from automation_engine.platforms.x.post import post_to_x


def run_task(post_id):
    driver = None

    try:
        post = Post.objects.get(id=post_id)

        print(f"Running task for Post ID: {post.id}")
        print(f"Platform: {post.platform}")
        print(f"Caption: {post.caption}")

        manager = BrowserManager(
            user_data_dir=r"C:\Users\HP\AppData\Local\Google\Chrome\User Data",
            profile_directory="Default",
            detach=True,
            headless=False,
        )

        print("Starting browser...")
        driver = manager.start_browser()
        print("Browser started")

        if post.platform.lower() == "x":
            print("Calling X automation...")
            result = post_to_x(driver, post)
            print("X result:", result)
        else:
            raise ValueError(f"Unsupported platform: {post.platform}")

        if not result["success"]:
            raise Exception(result["message"])

        post.status = "posted"
        post.error_message = None
        post.save()

        return {"success": True, "message": "Task completed successfully"}

    except Exception as e:
        print("TASK RUNNER ERROR:", str(e))
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