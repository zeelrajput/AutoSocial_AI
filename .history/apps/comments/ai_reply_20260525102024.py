import datetime
import json
import requests
from django.conf import settings


def generate_ai_reply(
    comment_text,
    author,
    post_caption,
    previous_comments,
    platform,
    mode="AI",
    tone="friendly",
    keyword_replies=None,
    default_reply="Thank you!"
):
    try:
        mode = mode.upper()

        headers = {
            "Authorization": f"Bearer {settings.ZETTALGOR_API_KEY}",
            "Content-Type": "application/json",
        }

        system_prompt = f"""
You are a smart, engaging social media assistant for social media comment replies.

Your task is to reply to a detected comment based on user-selected settings and previous conversation.

Mode: {mode}

If mode = AI:
- Generate short human-like reply
- Max 20 words
- Tone: {tone}
- Stay relevant to comment
- Use emoji only when needed
- Return JSON only

If mode = MANUAL:
- Use predefined reply only
- If keyword match exists, use keyword reply
- else use default reply

IGNORE comments if:
- spam
- duplicate
- only links
- empty
- bot-like

Output format:
{{
 "reply": "",
 "type": "{mode.lower()}",
 "used_predefined": false,
 "should_reply": true
}}
"""

        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        user_prompt = f"""
Current Time: {current_time}
Comment: {comment_text}
Author: {author}
Post Caption: {post_caption}
Previous Comments: {previous_comments}
Platform: {platform}
Keyword Replies: {json.dumps(keyword_replies or {})}
Default Reply: {default_reply}
"""

        payload = {
            "model": settings.ZETTALGOR_MODEL,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        }

        response = requests.post(
            settings.ZETTALGOR_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        content = data["choices"][0]["message"]["content"]

        return json.loads(content)

    except Exception as e:
        print("❌ AI Reply Error:", e)

        return {
            "reply": default_reply,
            "type": "fallback",
            "used_predefined": False,
            "should_reply": True
        }