
import requests
import pymupdf
import re

from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime, date


class ContentExtractor:

    def __init__(self):

        self.timeout = 20

        self.max_characters = 12000

        self.max_pdf_pages = 30

        self.headers = {
            "User-Agent": "Mozilla/5.0 QELVORIResearchAgent/3.0"
        }

    # --------------------------------------------------
    # DATE PARSING
    # --------------------------------------------------

    def parse_date(self, value):

        if not value:
            return None

        value = str(value).strip()

        # Handle PDF metadata dates:
        # D:20240621120000
        if value.startswith("D:"):

            value = value[2:]

            match = re.match(r"^(\d{8})", value)

            if match:

                try:
                    return datetime.strptime(
                        match.group(1),
                        "%Y%m%d"
                    ).date().isoformat()

                except ValueError:
                    return None

        # Handle ISO and common date formats
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%Y/%m/%d",
            "%B %d, %Y",
            "%b %d, %Y"
        ]

        for date_format in formats:

            try:

                parsed = datetime.strptime(
                    value,
                    date_format
                )

                return parsed.date().isoformat()

            except ValueError:
                continue

        # Handle ISO dates containing timezone information
        try:

            parsed = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )

            return parsed.date().isoformat()

        except ValueError:
            return None

    # --------------------------------------------------
    # PUBLICATION DATE VALIDATION
    # --------------------------------------------------

    def validate_publication_date(self, publication_date):

        if not publication_date:
            return "MISSING_PUBLICATION_DATE"

        try:

            parsed_date = date.fromisoformat(
                publication_date
            )

            if parsed_date > date.today():

                return "FUTURE_PUBLICATION_DATE"

            return "VALID_PUBLICATION_DATE"

        except (ValueError, TypeError):

            return "INVALID_PUBLICATION_DATE"

    # --------------------------------------------------
    # JSON-LD DATE EXTRACTION
    # --------------------------------------------------

    def extract_jsonld_dates(self, soup):

        publication_date = None
        modified_date = None

        scripts = soup.find_all(
            "script",
            type="application/ld+json"
        )

        def inspect_data(data):

            nonlocal publication_date
            nonlocal modified_date

            if isinstance(data, dict):

                if not publication_date:

                    publication_date = (
                        data.get("datePublished")
                        or data.get("dateCreated")
                    )

                if not modified_date:

                    modified_date = data.get(
                        "dateModified"
                    )

                for value in data.values():

                    if isinstance(value, (dict, list)):
                        inspect_data(value)

            elif isinstance(data, list):

                for item in data:
                    inspect_data(item)

        import json

        for script in scripts:

            try:

                data = json.loads(
                    script.string or script.get_text()
                )

                inspect_data(data)

            except (json.JSONDecodeError, TypeError):
                continue

        return {

            "publication_date": self.parse_date(
                publication_date
            ),

            "modified_date": self.parse_date(
                modified_date
            )

        }

    # --------------------------------------------------
    # HTML PUBLICATION DATE EXTRACTION
    # --------------------------------------------------

    def extract_html_dates(self, soup):

        publication_date = None
        modified_date = None
        date_source = None

        publication_selectors = [

            ("meta", {"property": "article:published_time"}),

            ("meta", {"name": "publication_date"}),

            ("meta", {"name": "datePublished"}),

            ("meta", {"itemprop": "datePublished"}),

            ("meta", {"name": "citation_publication_date"}),

            ("meta", {"name": "dc.date"}),

            ("meta", {"name": "dcterms.date"})

        ]

        modified_selectors = [

            ("meta", {"property": "article:modified_time"}),

            ("meta", {"name": "last-modified"}),

            ("meta", {"name": "dateModified"})

        ]

        # First check JSON-LD metadata
        jsonld_dates = self.extract_jsonld_dates(
            soup
        )

        publication_date = jsonld_dates.get(
            "publication_date"
        )

        modified_date = jsonld_dates.get(
            "modified_date"
        )

        if publication_date:

            date_source = "HTML JSON-LD metadata"

        # Check HTML publication metadata
        if not publication_date:

            for tag_name, attributes in publication_selectors:

                tag = soup.find(
                    tag_name,
                    attrs=attributes
                )

                if tag:

                    value = (
                        tag.get("content")
                        or tag.get("datetime")
                        or tag.get_text(strip=True)
                    )

                    parsed = self.parse_date(value)

                    if parsed:

                        publication_date = parsed

                        date_source = (
                            "HTML publication metadata"
                        )

                        break

        # Check modified date metadata
        if not modified_date:

            for tag_name, attributes in modified_selectors:

                tag = soup.find(
                    tag_name,
                    attrs=attributes
                )

                if tag:

                    value = (
                        tag.get("content")
                        or tag.get("datetime")
                        or tag.get_text(strip=True)
                    )

                    modified_date = self.parse_date(
                        value
                    )

                    if modified_date:
                        break

        return {

            "publication_date": publication_date,

            "document_creation_date": None,

            "modified_date": modified_date,

            "date_source": date_source

        }

    # --------------------------------------------------
    # PDF CONTENT AND METADATA EXTRACTION
    # --------------------------------------------------

    def extract_pdf_details(self, response):

        try:

            document = pymupdf.open(
                stream=response.content,
                filetype="pdf"
            )

            if document.page_count == 0:

                document.close()

                return None, {}

            metadata = document.metadata or {}

            content = []

            total_pages = min(
                document.page_count,
                self.max_pdf_pages
            )

            for page_number in range(total_pages):

                page = document.load_page(
                    page_number
                )

                text = page.get_text("text")

                if text.strip():
                    content.append(text)

            document.close()

            extracted_text = self.clean_text(
                "\n".join(content)
            )

            creation_date = self.parse_date(
                metadata.get("creationDate")
            )

            modified_date = self.parse_date(
                metadata.get("modDate")
            )

            date_information = {

                # PDF creation metadata is NOT proof
                # of the actual publication date.

                "publication_date": None,

                "document_creation_date": creation_date,

                "modified_date": modified_date,

                "date_source": (
                    "PDF creation metadata "
                    "(not verified publication date)"
                    if creation_date
                    else None
                )

            }

            return extracted_text, date_information

        except Exception as error:

            print(
                "PDF extraction failed:",
                error
            )

            return None, {}

    # --------------------------------------------------
    # HTML CONTENT EXTRACTION
    # --------------------------------------------------

    def extract_html(self, response):

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        for element in soup([

            "script",
            "style",
            "nav",
            "footer",
            "header",
            "noscript",
            "aside"

        ]):

            element.decompose()

        main_content = (

            soup.find("main")
            or soup.find("article")
            or soup.body

        )

        if not main_content:
            return None

        return self.clean_text(
            main_content.get_text(
                separator=" ",
                strip=True
            )
        )

    # --------------------------------------------------
    # TEXT CLEANING
    # --------------------------------------------------

    def clean_text(self, text):

        if not text:
            return None

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        text = text.strip()

        return text[:self.max_characters]

    # --------------------------------------------------
    # MAIN METADATA-AWARE EXTRACTION
    # --------------------------------------------------

    def extract_with_metadata(self, url):

        if not url.startswith(
            ("http://", "https://")
        ):

            return None

        print(
            f"\nExtracting: {url}"
        )

        try:

            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.timeout,
                allow_redirects=True
            )

            response.raise_for_status()

            content_type = response.headers.get(
                "Content-Type",
                ""
            ).lower()

            is_pdf = (

                "application/pdf" in content_type

                or urlparse(
                    response.url
                ).path.lower().endswith(".pdf")

            )

            if is_pdf:

                print("PDF detected.")

                content, date_information = (
                    self.extract_pdf_details(response)
                )

            else:

                print("Webpage detected.")

                soup = BeautifulSoup(
                    response.text,
                    "html.parser"
                )

                date_information = (
                    self.extract_html_dates(soup)
                )

                content = self.extract_html(
                    response
                )

            if not content:
                return None

            publication_date = date_information.get(
                "publication_date"
            )

            date_status = (
                self.validate_publication_date(
                    publication_date
                )
            )

            return {

                "content": content,

                "publication_date": publication_date,

                "document_creation_date": (
                    date_information.get(
                        "document_creation_date"
                    )
                ),

                "modified_date": (
                    date_information.get(
                        "modified_date"
                    )
                ),

                "date_source": (
                    date_information.get(
                        "date_source"
                    )
                ),

                "date_status": date_status

            }

        except requests.Timeout:

            print(
                "Website timed out:",
                url
            )

            return None

        except requests.RequestException as error:

            print(
                "Website extraction error:",
                error
            )

            return None

        except Exception as error:

            print(
                "Unexpected extraction error:",
                error
            )

            return None

    # --------------------------------------------------
    # BACKWARD COMPATIBILITY
    # --------------------------------------------------

    def extract(self, url):

        result = self.extract_with_metadata(
            url
        )

        if result:

            return result["content"]

        return None


# ------------------------------------------------------
# DIRECT TEST
# ------------------------------------------------------

if __name__ == "__main__":

    extractor = ContentExtractor()

    test_url = input(
        "Enter webpage or PDF URL: "
    )

    result = extractor.extract_with_metadata(
        test_url
    )

    if result:

        print(
            "\n===== EXTRACTED CONTENT =====\n"
        )

        print(
            result["content"][:3000]
        )

        print(
            "\n===== DATE METADATA ====="
        )

        print(
            "Publication Date:",
            result["publication_date"]
        )

        print(
            "Document Creation Date:",
            result["document_creation_date"]
        )

        print(
            "Modified Date:",
            result["modified_date"]
        )

        print(
            "Date Source:",
            result["date_source"]
        )

        print(
            "Date Status:",
            result["date_status"]
        )

        print(
            "\nTotal extracted characters:",
            len(result["content"])
        )

    else:

        print(
            "\nCould not extract content."
        )

