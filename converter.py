from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md

from constants import ARTICLE_NOT_FOUND_MSG, DATE_PATTERNS


@dataclass
class MediumToMarkdownConverter:
    """
    A tiny utility to convert public Medium articles to Markdown.
    """

    user_agent: str = (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/118.0 Safari/537.36"
    )
    session: requests.Session = requests.Session()

    def __post_init__(self) -> None:
        self.session.headers.update({"User-Agent": self.user_agent})

    def convert_from_url(self, url: str) -> Tuple[str, str]:
        html = self._download(url)
        soup = BeautifulSoup(html, "html.parser")

        article_tag = soup.find("article")
        if article_tag is None:
            raise RuntimeError(ARTICLE_NOT_FOUND_MSG)

        markdown = self._to_markdown(article_tag, base=url)
        title = self._extract_title(markdown)
        markdown = self._clean_markdown(markdown)

        return title, markdown

    def _download(self, url: str) -> str:
        resp = self.session.get(url, timeout=20)
        resp.raise_for_status()
        return resp.text

    def _to_markdown(self, tag, *, base: str) -> str:
        """HTML → Markdown via markdownify; make image/video URLs absolute."""
        for picture in tag.find_all("picture"):
            img = picture.find("img")
            source = picture.find("source", attrs={"srcset": True})

            if img and source and not img.has_attr("src"):
                img["src"] = source["srcset"].split(",")[0].split()[0]

        # First convert any <img src> / <a href> that are relative.
        for el in tag.find_all(["img", "a"]):
            attr = "src" if el.name == "img" else "href"
            if el.has_attr(attr):
                el[attr] = urljoin(base, el[attr])

        return md(str(tag), heading_style="ATX")

    @staticmethod
    def _extract_title(markdown: str) -> str:
        first_line = markdown.lstrip().splitlines()[0]
        return re.sub(r"^#+\s*", "", first_line).strip()

    @staticmethod
    def _clean_markdown(markdown: str) -> str:
        cleaned_lines: list[str] = []
        for line in markdown.splitlines():
            # Skip embedded sign-in / image proxies.

           # Remove Medium sign-in links
            if "medium.com/m/signin" in line:
                continue

# Remove plain Medium image URLs, but keep Markdown images
            if (
                "miro.medium.com" in line
                and not line.strip().startswith("![](")
                or "medium.com/m/signin" in line
            ):
                continue

            # if any(u in line for u in ("miro.medium.com", "medium.com/m/signin")):
            #     continue

            # Skip common Medium template phrases.
            if re.search(r"Published in|Listen|Share", line):
                continue

            # Skip blank reference links like "[ ]"
            if re.fullmatch(r"\[\s*]", line):
                continue

            # Remove read time
            if re.fullmatch(r"\d+\s+min read", line.strip()):
                continue

            # Remove published date like "1 day ago", "2 days ago", "5 hours ago"
            if any(pattern.fullmatch(line.strip()) for pattern in DATE_PATTERNS):
                continue

            # Remove separator lines
            if line.strip() in {"·", "--"}:
                continue

            if re.fullmatch(r"\[.*]\(https://medium\.com/@.*\)", line.strip()):
                continue


            cleaned_lines.append(line)

        return "\n".join(cleaned_lines).strip() + "\n"