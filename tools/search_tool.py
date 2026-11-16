import html
import re
import time
from urllib.parse import quote, urlparse, urlunparse

import requests

try:
    from ddgs import DDGS
except ImportError:
    DDGS = None


class SearchTool:

    def __init__(self):

        self.max_results = 10
        self.final_results = 5
        self.timeout = 20

        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": (
                "QELVORIResearchAgent/3.1 "
                "(educational research tool)"
            ),
            "Accept": "application/json, text/html;q=0.9, */*;q=0.8"
        })

        # Source domain indicators.
        # These do not prove source credibility.

        self.academic_domains = [
            ".edu",
            ".ac.uk",
            ".edu.in"
        ]

        self.government_domains = [
            ".gov",
            ".gov.in"
        ]

        self.research_domains = [
            "ieee.org",
            "acm.org",
            "nature.com",
            "sciencedirect.com",
            "springer.com",
            "wiley.com",
            "elsevier.com",
            "cell.com",
            "pnas.org",
            "aps.org",
            "aip.org",
            "tandfonline.com",
            "frontiersin.org",
            "mdpi.com"
        ]

        self.preprint_domains = [
            "arxiv.org"
        ]

        self.journal_domains = [
            "ijert.org",
            "ijtsrd.com"
        ]

        self.research_sharing_domains = [
            "researchgate.net"
        ]

        self.research_index_domains = [
            "pubmed.ncbi.nlm.nih.gov",
            "openalex.org",
            "crossref.org",
            "semanticscholar.org"
        ]

        self.international_domains = [
            "who.int",
            "nasa.gov"
        ]

    # ==========================================
    # DOMAIN UTILITIES
    # ==========================================

    def domain_matches(self, hostname, domain):

        hostname = (hostname or "").lower().strip(".")
        domain = (domain or "").lower().strip(".")

        return (
            hostname == domain
            or hostname.endswith("." + domain)
        )

    def get_hostname(self, url):

        try:

            parsed = urlparse(url or "")

            if parsed.scheme not in ("http", "https"):
                return ""

            if not parsed.hostname:
                return ""

            return parsed.hostname.lower()

        except (TypeError, ValueError):

            return ""

    # ==========================================
    # SOURCE CLASSIFICATION
    # ==========================================

    def classify_source(self, url):

        hostname = self.get_hostname(url)

        if not hostname:
            return "Unknown"

        if any(
            self.domain_matches(hostname, domain)
            for domain in self.government_domains
        ):
            return "Government"

        if any(
            self.domain_matches(hostname, domain)
            for domain in self.academic_domains
        ):
            return "Academic Institution"

        if any(
            self.domain_matches(hostname, domain)
            for domain in self.research_domains
        ):
            return "Scholarly Publisher or Platform"

        if any(
            self.domain_matches(hostname, domain)
            for domain in self.journal_domains
        ):
            return "Journal Website"

        if any(
            self.domain_matches(hostname, domain)
            for domain in self.research_sharing_domains
        ):
            return "Research Sharing Platform"

        if any(
            self.domain_matches(hostname, domain)
            for domain in self.preprint_domains
        ):
            return "Preprint Repository"

        if any(
            self.domain_matches(hostname, domain)
            for domain in self.research_index_domains
        ):
            return "Research Index"

        if any(
            self.domain_matches(hostname, domain)
            for domain in self.international_domains
        ):
            return "International or Scientific Organization"

        return "General Web"

    # ==========================================
    # TEXT UTILITIES
    # ==========================================

    @staticmethod
    def clean_text(value):

        if not value:
            return ""

        value = re.sub(r"<[^>]+>", " ", str(value))

        value = html.unescape(value)

        return re.sub(r"\s+", " ", value).strip()

    @staticmethod
    def reconstruct_abstract(inverted_index):

        if not isinstance(inverted_index, dict):
            return ""

        positioned_words = []

        for word, positions in inverted_index.items():

            if not isinstance(positions, list):
                continue

            for position in positions:

                if isinstance(position, int) and position >= 0:

                    positioned_words.append(
                        (position, word)
                    )

        positioned_words.sort(
            key=lambda item: item[0]
        )

        return " ".join(
            word for _, word in positioned_words
        )

    def clean_url(self, url):

        try:

            parsed = urlparse(url)

            clean = parsed._replace(
                query="",
                fragment=""
            )

            return urlunparse(clean).rstrip("/").lower()

        except (TypeError, ValueError):

            return (url or "").lower()

    # ==========================================
    # SOURCE QUALITY SCORING
    # ==========================================

    def calculate_score(self, result, query):

        title = str(
            result.get("title") or ""
        ).lower()

        snippet = str(
            result.get("snippet") or ""
        ).lower()

        url = str(
            result.get("url") or ""
        )

        hostname = self.get_hostname(url)

        source_type = self.classify_source(url)

        score = 0

        reasons = []

        if source_type in [
            "Government",
            "Academic Institution",
            "Scholarly Publisher or Platform",
            "International or Scientific Organization"
        ]:

            score += 5

            reasons.append(
                "Institutional or scholarly domain indicator"
            )

        elif source_type in [
            "Journal Website",
            "Preprint Repository",
            "Research Index"
        ]:

            score += 3

            reasons.append(
                "Journal, preprint, or research-index domain indicator"
            )

        elif source_type == "Research Sharing Platform":

            score += 1

            reasons.append(
                "Research-sharing platform; verify original publication"
            )

        else:

            reasons.append(
                "General web source"
            )

        # Topic relevance

        keywords = set(
            re.findall(
                r"\b[a-z0-9]+\b",
                query.lower()
            )
        )

        ignored = {
            "the",
            "and",
            "for",
            "with",
            "from",
            "into",
            "about",
            "latest",
            "future",
            "trends",
            "applications",
            "recent"
        }

        matched_title = []

        matched_snippet = []

        for keyword in keywords:

            if len(keyword) < 3 or keyword in ignored:
                continue

            if keyword in title:

                score += 3

                matched_title.append(keyword)

            if keyword in snippet:

                score += 1

                matched_snippet.append(keyword)

        if matched_title:

            reasons.append(
                "Topic terms in title: "
                + ", ".join(sorted(matched_title))
            )

        if matched_snippet:

            reasons.append(
                "Topic terms in summary: "
                + ", ".join(sorted(matched_snippet))
            )

        # Descriptive title

        if len(title) > 15:

            score += 1

            reasons.append(
                "Descriptive title"
            )

        # HTTPS check

        if url.startswith("https://"):

            score += 1

            reasons.append(
                "Uses HTTPS"
            )

        else:

            score -= 2

            reasons.append(
                "Does not use HTTPS"
            )

        # Missing information

        if not title:

            score -= 10

            reasons.append(
                "Missing title"
            )

        if not hostname:

            score -= 10

            reasons.append(
                "Invalid or unsupported URL"
            )

        breakdown = {

            "source_type": source_type,

            "hostname": hostname,

            "matched_title_keywords": sorted(matched_title),

            "matched_snippet_keywords": sorted(matched_snippet),

            "reasons": reasons
        }

        return score, breakdown

    # ==========================================
    # REMOVE DUPLICATE RESULTS
    # ==========================================

    def remove_duplicates(self, results):

        unique_results = []

        seen_urls = set()

        for result in results:

            url = result.get("url", "")

            if not url:
                continue

            cleaned = self.clean_url(url)

            if cleaned in seen_urls:
                continue

            seen_urls.add(cleaned)

            unique_results.append(result)

        return unique_results

    # ==========================================
    # OPENALEX SEARCH
    # ==========================================

    def openalex_search(self, query):

        print("Searching OpenAlex...")

        response = self.session.get(

            "https://api.openalex.org/works",

            params={

                "search": query,

                "per-page": self.max_results,

                "select": (
                    "id,doi,title,publication_year,"
                    "primary_location,best_oa_location,"
                    "open_access,abstract_inverted_index"
                )
            },

            timeout=self.timeout
        )

        response.raise_for_status()

        payload = response.json()

        formatted = []

        for item in payload.get("results", []):

            title = self.clean_text(
                item.get("title")
            )

            if not title:
                continue

            best_location = item.get(
                "best_oa_location"
            ) or {}

            primary_location = item.get(
                "primary_location"
            ) or {}

            landing_url = (

                best_location.get("landing_page_url")

                or best_location.get("pdf_url")

                or primary_location.get("landing_page_url")

                or item.get("doi")

                or item.get("id")
            )

            if landing_url and landing_url.startswith("http"):

                url = landing_url

            elif item.get("doi"):

                url = item["doi"]

            else:

                url = item.get("id", "")

            abstract = self.reconstruct_abstract(
                item.get("abstract_inverted_index")
            )

            year = item.get("publication_year")

            snippet = abstract[:1200]

            if year:

                snippet = (
                    f"Publication year: {year}. "
                    + snippet
                )

            if not snippet:

                snippet = (
                    "Scholarly work indexed by OpenAlex."
                )

            formatted.append({

                "id": len(formatted) + 1,

                "title": title,

                "url": url,

                "snippet": snippet
            })

        print(
            f"OpenAlex returned {len(formatted)} results."
        )

        return formatted

    # ==========================================
    # CROSSREF SEARCH
    # ==========================================

    def crossref_search(self, query):

        print("Searching Crossref...")

        response = self.session.get(

            "https://api.crossref.org/works",

            params={

                "query.bibliographic": query,

                "rows": self.max_results,

                "select": (
                    "DOI,title,URL,abstract,published,"
                    "published-print,published-online"
                )
            },

            timeout=self.timeout
        )

        response.raise_for_status()

        items = response.json().get(
            "message", {}
        ).get("items", [])

        formatted = []

        for item in items:

            titles = item.get("title") or []

            title = self.clean_text(
                titles[0] if titles else ""
            )

            url = item.get("URL") or (

                "https://doi.org/" + item["DOI"]

                if item.get("DOI")

                else ""
            )

            if not title or not url:
                continue

            abstract = self.clean_text(
                item.get("abstract", "")
            )

            date_info = (

                item.get("published")

                or item.get("published-print")

                or item.get("published-online")

                or {}
            )

            date_parts = date_info.get(
                "date-parts", []
            )

            year = (
                date_parts[0][0]
                if date_parts and date_parts[0]
                else None
            )

            snippet = abstract[:1200]

            if year:

                snippet = (
                    f"Publication year: {year}. "
                    + snippet
                )

            if not snippet:

                snippet = (
                    "Publication metadata indexed by Crossref."
                )

            formatted.append({

                "id": len(formatted) + 1,

                "title": title,

                "url": url,

                "snippet": snippet
            })

        print(
            f"Crossref returned {len(formatted)} results."
        )

        return formatted

    # ==========================================
    # WIKIPEDIA SEARCH
    # ==========================================

    def wikipedia_search(self, query):

        print("Searching Wikipedia...")

        response = self.session.get(

            "https://en.wikipedia.org/w/api.php",

            params={

                "action": "query",

                "list": "search",

                "srsearch": query,

                "format": "json",

                "srlimit": self.max_results
            },

            timeout=self.timeout
        )

        response.raise_for_status()

        results = response.json().get(
            "query", {}
        ).get("search", [])

        formatted = []

        for item in results:

            title = self.clean_text(
                item.get("title")
            )

            if not title:
                continue

            formatted.append({

                "id": len(formatted) + 1,

                "title": title,

                "url": (
                    "https://en.wikipedia.org/wiki/"
                    + quote(title.replace(" ", "_"))
                ),

                "snippet": self.clean_text(
                    item.get("snippet", "")
                )
            })

        print(
            f"Wikipedia returned {len(formatted)} results."
        )

        return formatted

    # ==========================================
    # DUCKDUCKGO SEARCH
    # ==========================================

    def duckduckgo_search(self, query):

        if DDGS is None:

            print(
                "DuckDuckGo unavailable: ddgs package not installed."
            )

            return []

        print("Searching DuckDuckGo...")

        with DDGS(timeout=self.timeout) as ddgs:

            raw_results = list(
                ddgs.text(
                    query,
                    max_results=self.max_results
                )
            )

        formatted = []

        for item in raw_results:

            formatted.append({

                "id": len(formatted) + 1,

                "title": item.get("title") or "Untitled",

                "url": item.get("href") or "",

                "snippet": item.get("body") or ""
            })

        print(
            f"DuckDuckGo returned {len(formatted)} results."
        )

        return formatted

    # ==========================================
    # MAIN SEARCH ENGINE
    # ==========================================

    def search(self, query):

        query = (
            (query or "")
            .strip()
            .strip('"')
            .strip()
        )

        if not query:

            print("Search query is empty.")

            return []

        print(
            f"\nQELVORI searching for: {query}"
        )

        all_results = []

        providers = [

            ("OpenAlex", self.openalex_search),

            ("Crossref", self.crossref_search),

            ("Wikipedia", self.wikipedia_search),

            ("DuckDuckGo", self.duckduckgo_search)
        ]

        # Each provider is independent.

        for provider_name, provider in providers:

            try:

                provider_results = provider(query)

                all_results.extend(
                    provider_results
                )

            except requests.RequestException as error:

                print(
                    f"{provider_name} network error: {error}"
                )

            except (
                ValueError,
                KeyError,
                TypeError
            ) as error:

                print(
                    f"{provider_name} response error: {error}"
                )

            except Exception as error:

                print(
                    f"{provider_name} search error: "
                    f"{type(error).__name__}: {error}"
                )

            time.sleep(0.25)

        # Remove duplicates.

        results = self.remove_duplicates(
            all_results
        )

        if not results:

            print(
                "No search results available from any provider."
            )

            return []

        # Calculate scores.

        for result in results:

            score, breakdown = self.calculate_score(
                result,
                query
            )

            result["quality_score"] = score

            result["source_type"] = breakdown[
                "source_type"
            ]

            result["score_breakdown"] = breakdown

        # Rank results.

        results.sort(

            key=lambda item: item["quality_score"],

            reverse=True
        )

        selected = results[:self.final_results]

        # Assign IDs.

        for index, result in enumerate(
            selected,
            1
        ):

            result["id"] = index

        print(
            "\nQELVORI selected search candidates:"
        )

        for result in selected:

            print(
                f"\n{result['id']}. {result['title']}"
            )

            print(
                "URL:",
                result["url"]
            )

            print(
                "Score:",
                result["quality_score"]
            )

            print(
                "Source Type:",
                result["source_type"]
            )

            print(
                "Assessment:",
                "; ".join(
                    result["score_breakdown"]["reasons"]
                )
            )

        print(
            "\nNote: Scores are heuristic ranking indicators, "
            "not proof of source credibility. "
            "Original publications must be checked."
        )

        return selected


# ==========================================
# STANDALONE TEST
# ==========================================

if __name__ == "__main__":

    search_tool = SearchTool()

    query = input(
        "\nEnter a research topic: "
    ).strip()

    results = search_tool.search(query)

    print(
        "\n===== QELVORI SEARCH RESULTS ====="
    )

    for result in results:

        print(
            f"\n{result['id']}. {result['title']}"
        )

        print(
            "URL:",
            result["url"]
        )

        print(
            "Score:",
            result["quality_score"]
        )

        print(
            "Source Type:",
            result["source_type"]
        )

        print(
            "Summary:",
            result["snippet"][:500]
        )
