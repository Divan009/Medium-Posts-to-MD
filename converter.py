from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md

from constants import ARTICLE_NOT_FOUND_MSG


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
            if any(u in line for u in ("miro.medium.com", "medium.com/m/signin")):
                continue

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
            if re.fullmatch(r"\d+\s+(day|days|hour|hours|week|weeks|month|months|year|years)\s+ago", line.strip()):
                continue

            # Remove separator lines
            if line.strip() in {"·", "--"}:
                continue

            if re.fullmatch(r"\[.*]\(https://medium\.com/@.*\)", line.strip()):
                continue


            cleaned_lines.append(line)

        return "\n".join(cleaned_lines).strip() + "\n"