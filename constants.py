import re

ARTICLE_NOT_FOUND_MSG = "Unable to locate <article> section on the page."

DATE_PATTERNS = [
    re.compile(r"\d+\s+(day|days|hour|hours|week|weeks|month|months|year|years)\s+ago"),
    re.compile(
        r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|"
        r"January|February|March|April|June|July|August|September|October|November|December)"
        r"\s+\d{1,2},\s+\d{4}"
    ),
]