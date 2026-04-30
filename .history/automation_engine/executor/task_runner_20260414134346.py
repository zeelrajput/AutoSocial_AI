from apps.posts.models import Post

# platform imports (future)
# from automation_engine.platforms.instagram.post import post_to_instagram

def run_task(post_id):
    try:
        post = Post.objects.get(id=post_id)

        print(f"running task for {post.platform}")
        
    except Exception as e:
        print("heelo")