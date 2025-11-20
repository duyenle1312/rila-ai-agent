from datetime import datetime
from notion_client import Client
from app.config import settings
from bs4 import BeautifulSoup  # for parsing HTML

def html_to_notion_blocks(html: str):
    """
    Converts simple HTML content to Notion blocks.
    Currently supports: <p>, <h1>-<h3>, <ul>, <ol>, <li>, <strong>, <em>
    """
    soup = BeautifulSoup(html, "html.parser")
    blocks = []

    for element in soup.children:
        if element.name == "p":
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": element.get_text()}}]
                }
            })
        elif element.name in ["h1", "h2", "h3"]:
            blocks.append({
                "object": "block",
                "type": "heading_" + str(element.name[-1]),
                "heading_" + str(element.name[-1]): {
                    "rich_text": [{"type": "text", "text": {"content": element.get_text()}}]
                }
            })
        elif element.name in ["ul", "ol"]:
            for li in element.find_all("li"):
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item" if element.name == "ul" else "numbered_list_item",
                    element.name: {
                        "rich_text": [{"type": "text", "text": {"content": li.get_text()}}]
                    }
                })
    return blocks

async def create_notion_page(title: str, slug: str, seo_keywords: str, coverImg: str, ai_summary: str, html_content: str):
    print("Creating Notion page with title:", title)
    
    # Convert HTML to Notion blocks
    blocks = html_to_notion_blocks(html_content)

    print("Converted HTML to Notion blocks")

    notion = Client(auth=settings.NOTION_API_KEY)

    today = datetime.today().strftime('%Y-%m-%d')

    try:
        # Create the page first
        new_page = notion.pages.create(
            parent={"database_id": settings.NOTION_PARENT_PAGE},
            properties={
                "title": {"title": [{"text": {"content": title}}]},
                "date": {"date": {"start": today}},
                "lastEditedAt": {"date": {"start": today}},
                "slug": {"rich_text": [{"text": {"content": slug}}]},
                "keywords": {"rich_text": [{"text": {"content": seo_keywords}}]},
                "summary": {"rich_text": [{"text": {"content": ai_summary}}]},
            },
            cover={
                "type": "external",
                "external": {"url": coverImg} 
            }
        )

        print("Notion page created with ID:", new_page["id"])

        print("Appending blocks to Notion page...")

        # Append blocks to the page
        for block in blocks:
            notion.blocks.children.append(new_page["id"], children=[block])

        print("Notion page created successfully at:", new_page["url"])

        return {"status": "success", "url": new_page["url"]}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
    