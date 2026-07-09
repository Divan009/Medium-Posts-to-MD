import argparse
import pathlib

from converter import MediumToMarkdownConverter
from utils import slugify


def main():
    parser = argparse.ArgumentParser(
        description="Download a Medium article and save as Markdown."
    )
    parser.add_argument("url", help="Medium article URL")
    parser.add_argument(
        "-o",
        "--out",
        default="md_files",
        help="Output directory (default: md_files)"
    )
    args = parser.parse_args()

    converter = MediumToMarkdownConverter()
    title, markdown_text = converter.convert_from_url(args.url)

    out_dir = pathlib.Path(args.out).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    safe_name = slugify(title) + ".md"
    outfile = out_dir / safe_name
    outfile.write_text(markdown_text, encoding="utf-8")

    print(f"  Saved '{title}' → {outfile}")


if __name__ == "__main__":
    main()