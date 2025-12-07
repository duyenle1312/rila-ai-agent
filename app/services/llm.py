import json
import re
from google import genai
from google.genai import types
from app.config import settings


async def summarize_text(title, html_content: str) -> str:
    print("Summarizing text with Gemini for title:", title)

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    response = client.models.generate_content(
        model=settings.GEMINI_AI_MODEL,
        config=types.GenerateContentConfig(
            system_instruction="Give me some high ranking SEO keywords separated by comma for this article in HTML format, a slug from the title provided below, also an image URL for the cover image of this article, and add an interesting, thought-provoking, informative one paragraph summary at the beginning of the HTML content using HTML tags <h2>Summary</h2> and <p> for the summary content, then also add this summary paragraph as plain text to the final json. Response as a json with this structure: { title: "", slug: "", seo_keywords: "" , cover_imgUrl: "", plain_text_summary: "", html_content: "" }:",),
        contents="Title {title}\n\nArticle Content in HTML format:\n{html_content}".format(
            title=title, html_content=html_content)
    )

    cleaned_output = re.sub(r"^```json\s*|\s*```$", "", response.text, flags=re.MULTILINE)

    # Parse as JSON
    data = json.loads(cleaned_output)

    response_in_json = {
        "title": data.get("title", ""),
        "slug": data.get("slug", ""),
        "seo_keywords": data.get("seo_keywords", ""),
        "cover_imgUrl": data.get("cover_imgUrl", ""),
        "ai_summary": data.get("plain_text_summary", ""),
        "html_content": data.get("html_content", "")
    }

    return response_in_json
