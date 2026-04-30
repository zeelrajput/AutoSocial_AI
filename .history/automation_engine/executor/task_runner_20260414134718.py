from apps.posts.models import Post

# platform imports (future)
# from automation_engine.platforms.instagram.post import post_to_instagram

def run_task(post_id):
    try:
        post = Post.objects.get(id=post_id)

        print(f"running task for {post.platform}")

        if post.platform == "instagram":
            print("instagram logic here")

        elif post.platform == "facebook":
            print("facebook logic here")

        elif post.platform == "linkedin":
            print("linkedIn logic here")

        elif post.platform == "x":
            print("x logic here")

        post.status = "posted"
        post.save()

        return {"success"}
    except Exception as e:
        print("heelo")