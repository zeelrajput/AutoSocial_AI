from apps.posts.models import Post
from automation_engine.browser.browser_manager import BrowserManager
import time
from automation_engine.platforms.x.post import post_to_x
# Example platform import
# from automation_engine.platforms.x.post import post_to_x
# from automation_engine.platforms.linkedin.post import post_to_linkedin
# from automation_engine.platforms.instagram.post import post_to_instagram
# from automation_engine.platforms.facebook.post import post_to_facebook


def run_task(post_id):
    driver = None

    try:
        post = Post.objects.get(id=post_id)

        print(f"Running task for Post ID: {post.id}")
        print(f"Platform: {post.platform}")
        print(f"Caption: {post.caption}")

        manager = BrowserManager(
            user_data_dir="C:\Users\HP\AppData\Local\Google\Chrome\User Data"
            profile_directory="Default",
            detach=True,
            headless=False,
        )

        driver = manager.start_browser()
        # time.sleep(10)

        # Temporary routing logic
        if post.platform.lower() == "x":
            result = post_to_x(driver, post)

            if not result["success"]:
                raise Exception(result["message"])
                    # result = post_to_x(driver, post)

        elif post.platform.lower() == "linkedin":
            print("LinkedIn automation logic will run here")
            # result = post_to_linkedin(driver, post)

        elif post.platform.lower() == "instagram":
            driver.get("https://www.instagram.com")
            # result = post_to_instagram(driver, post)

        elif post.platform.lower() == "facebook":
            print("Facebook automation logic will run here")
            # result = post_to_facebook(driver, post)

        else:
            raise ValueError(f"Unsupported platform: {post.platform}")

        time.sleep(10)
        # Temporary success update
        post.status = "posted"
        post.error_message = None
        post.save()

        return {
            "success": True,
            "message": f"Post {post.id} processed successfully"
        }

    except Post.DoesNotExist:
        return {
            "success": False,
            "message": "Post not found"
        }

    except Exception as e:
        try:
            post = Post.objects.get(id=post_id)
            post.status = "failed"
            post.error_message = str(e)
            post.save()
        except Exception:
            pass

        return {
            "success": False,
            "message": str(e)
        }

    finally:
        if driver:
            BrowserManager.close_browser(driver)