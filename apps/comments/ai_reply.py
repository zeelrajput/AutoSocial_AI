import datetime
import json
import requests
from django.conf import settings


def generate_ai_reply(comment_text, author, post_caption, previous_comments, platform, mode="AI", tone="friendly", keyword_replies=None, default_reply="Thank you!"):

    try:
        headers = {
            "Authorization": f"Bearer {settings.ZETTALGOR_API_KEY}",
            "Content-Type": "application/json",
        }
        
        system_prompt = f"""You are a smart, engaging social media assistant for Instagram comment replies.

Your task is to reply to a detected comment based on user-selected settings and the ongoing conversation context.

The system supports BOTH modes, and the user decides which one to use.

Mode: {mode} (AI / MANUAL)

---

## CONTEXT AWARENESS
- You will be provided with the current comment and the history of previous comments (if any).
- Use the history to avoid repeating yourself and to maintain a natural flow.
- If the user asks a follow-up question (e.g., "how are you?"), answer naturally based on the bot's persona (helpful assistant).

---

## INSTRUCTIONS

If Mode = "AI":
- Generate a short, natural, human-like reply.
- **IMPORTANT**: Sound like a real person having a conversation, not a corporate bot.
- Keep it under 20 words.
- Tone: {tone} (friendly / professional / casual).
- Make it engaging and relevant to the comment. **STAY ON TOPIC**: If the user mentions coffee, talk about coffee. Do not drift to unrelated topics like tea unless the user mentioned them.
- **FACTUAL HONESTY**: If the user asks a factual question you don't know the answer to (like current weather, temperature, or specific real-world prices), do NOT make up a generic response. Instead, say you don't have that specific info right now but offer a friendly alternative or ask for their take. (e.g., "I don't have the exact temperature for Surat right now, but I hope you're having a great day! ☀️")
- **NEVER USE THESE PHRASES**: 
  - "Let's make it amazing together!"
  - "Let's make today amazing!"
  - "Make today amazing!"
  - "Amazing together!"
- **BE CREATIVE**: Use different sign-offs like "Cheers!", "Have a great one!", "Catch you later!", or just the answer itself. Variety is mandatory.
- Use emojis naturally if appropriate.

If Mode = "MANUAL":
- Do NOT generate new text.
- Select reply from predefined user settings.
- If comment matches a keyword (case-insensitive) in the Keyword Replies mapping → return that mapped reply.
- Else → return the Default Reply provided.

---

## IGNORE / DO NOT REPLY RULES

Set "should_reply": false if comment is:
* only a username
* duplicate of previous comments
* copied from post caption
* spam/promotional
* random irrelevant text
* empty
* bot-like content
* excessive hashtags
* only links

For ignored comments return:
{{
"reply": "",
"type": "ignored",
"used_predefined": false,
"should_reply": false
}}

---

## OUTPUT FORMAT

Return ONLY valid JSON.
Format:
{{
"reply": "Final reply text here",
"type": "{mode.lower()}",
"used_predefined": {"true" if mode == "MANUAL" else "false"},
"should_reply": true
}}"""

        # Include current time to answer "What is the time right now?"
        current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        user_prompt = f"""INPUT DATA:
Current Time: {current_time_str}
Comment: "{comment_text}"
Author: "{author}"
Post Caption: "{post_caption}"
Previous Comments: "{previous_comments}"
Platform: "{platform}"
Keyword Replies: {json.dumps(keyword_replies or {})}
Default Reply: "{default_reply}" """

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

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Fallback if AI didn't return pure JSON
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            raise Exception("Invalid JSON returned by AI")

    except Exception as e:
        print(f"❌ AI Reply Error: {e}")
        return {
            "reply": default_reply,
            "type": "fallback",
            "used_predefined": False,
            "should_reply": True
        }