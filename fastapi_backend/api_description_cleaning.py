"""
This is meant to clean RemoteOK's messy description data from their API.
"""

import html
import re

from bs4 import BeautifulSoup
from ftfy import fix_text


def clean_description(description: str) -> str:
    """Clean an API job-description string."""

    if not description:
        return ""

    # Fix text such as â, â, and other encoding problems.
    description = fix_text(description)

    # Convert HTML entities such as &amp; into &.
    description = html.unescape(description)

    # Convert useful HTML elements into line breaks before removing tags.
    soup = BeautifulSoup(description, "html.parser")

    for tag in soup.find_all(["br", "p", "div"]):
        tag.replace_with("\n")

    for item in soup.find_all("li"):
        item.insert_before("\n- ")
        item.append("\n")

    # Remove the remaining HTML tags.
    cleaned = soup.get_text()

    # Normalize whitespace.
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r" *\n *", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()
