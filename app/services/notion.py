from datetime import datetime
from notion_client import Client
from app.config import settings
from bs4 import BeautifulSoup  # for parsing HTML
import copy


def rich_text_from_html(element):
    """Recursively convert inline HTML tags into Notion rich text list."""
    fragments = []

    for node in element.children:
        if node.name is None:
            # plain text
            # [{"type": "text", "text": {"content": element.get_text()}}]
            text = (node.string or "")
            if text:
                fragments.append({
                    "type": "text",
                    "text": {"content": text}
                })

        elif node.name in ["strong", "b"]:
            fragments.append({
                "type": "text",
                "text": {"content": node.get_text()},
                "annotations": {"bold": True}
            })

        elif node.name in ["em", "i"]:
            fragments.append({
                "type": "text",
                "text": {"content": node.get_text()},
                "annotations": {"italic": True}
            })

        elif node.name == "code":
            fragments.append({
                "type": "text",
                "text": {"content": node.get_text()},
                "annotations": {"code": True}
            })

        elif node.name == "a":
            fragments.append({
                "type": "text",
                "text": {
                    "content": node.get_text(),
                    "link": {"url": node.get("href")}
                }
            })

        else:
            # handle nested inline elements recursively
            fragments.extend(rich_text_from_html(node))

    return fragments

def build_list_block(li, block_type):
    """
    Build a Notion list item block, supporting nested lists without duplicating nested text.
    Only the direct text/inline children of <li> are used in rich_text.
    """
    # Extract only direct content of <li> excluding nested <ul>/<ol>
    li_content = copy.deepcopy(li)
    
    # Remove nested lists from this copy
    for child_list in li_content.find_all(["ul", "ol"], recursive=False):
        child_list.decompose()  # remove nested lists from rich_text

    # Build base block
    block = {
        "object": "block",
        "type": block_type,
        block_type: {
            "rich_text": rich_text_from_html(li_content)
        }
    }

    # Handle nested lists
    children = []
    for nested_list in li.find_all(["ul", "ol"], recursive=False):
        nested_type = "bulleted_list_item" if nested_list.name == "ul" else "numbered_list_item"
        for nested_li in nested_list.find_all("li", recursive=False):
            children.append(build_list_block(nested_li, nested_type))

    if children:
        block[block_type]["children"] = children

    return block


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
                    "rich_text": rich_text_from_html(element)
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

            list_block_type = "bulleted_list_item" if element.name == "ul" else "numbered_list_item"

            for li in element.find_all("li", recursive=False):
                blocks.append(build_list_block(li, list_block_type))

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
    