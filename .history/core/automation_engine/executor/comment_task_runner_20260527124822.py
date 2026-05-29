import time
from core.automation_engine.platforms.instagram.comments import (
    check_instagram_comments,
    reply_instagram_comment,
)

from core.automation_engine.platforms.facebook.comments import (
    check_facebook_comments,
    reply_facebook_comment,
)

from core.automation_engine.platforms.linkedin.comments import (
    check_linkedin_comments,
    reply_linkedin_comment,
)

from core.automation_engine.platforms.x.comments import (
    check_x_comments,
    reply_x_comment,
)


def run_check_comments_task(driver, platform, post_url):

    platform = platform.lower()
    

    if platform == "instagram":
        return check_instagram_comments(driver, post_url)

    elif platform == "facebook":
        return check_facebook_comments(driver, post_url)

    elif platform == "linkedin":
        return check_linkedin_comments(driver, post_url)

    elif platform == "x":
        return check_x_comments(driver, post_url)

    return []


def run_reply_comment_task(
    driver,
    platform,
    post_url,
    reply_text,
    author=None,
    comment_text=None
):

    platform = platform.lower()

    if platform == "instagram":
        return reply_instagram_comment(
            driver,
            post_url,
            reply_text,
            author,
            comment_text
        )

    elif platform == "facebook":
        return reply_facebook_comment(
            driver,
            post_url,
            reply_text
        )

    elif platform == "linkedin":
        return reply_linkedin_comment(
            driver,
            post_url,
            reply_text
        )

    elif platform == "x":
        return reply_x_comment(
            driver,
            post_url,
            reply_text
        )

    return {
        "success": False,
        "message": "Unsupported platform"
    }