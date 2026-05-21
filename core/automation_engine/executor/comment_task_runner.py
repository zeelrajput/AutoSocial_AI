# =========================================================
# COMMENT TASK RUNNER
# =========================================================

from core.automation_engine.platforms.linkedin.comments import (
    check_linkedin_comments,
    reply_linkedin_comment,
)


# =========================================================
# CHECK COMMENTS TASK
# =========================================================
def run_check_comments_task(
    driver,
    platform,
    post_url
):

    platform = platform.lower()

    if platform == "linkedin":

        return check_linkedin_comments(
            driver,
            post_url
        )

    return []


# =========================================================
# REPLY COMMENT TASK
# =========================================================
def run_reply_comment_task(
    driver,
    platform,
    post_url,
    reply_text=None,
    author=None,
    comment_text=None
):

    platform = platform.lower()

    if platform == "linkedin":

        return reply_linkedin_comment(
            driver=driver,
            post_url=post_url,
            reply_text=reply_text
        )

    return {
        "success": False,
        "message": "Unsupported platform"
    }