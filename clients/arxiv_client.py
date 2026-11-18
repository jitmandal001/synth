# Level 2: moved from services/arxiv.py. Talks to the arXiv API only;
# raises core.exceptions errors instead of fastapi.HTTPException.
#
# POST /extract path, step 8 of 10 (arXiv IDs only, and only if not already saved).
# Runs in a worker thread (asyncio.to_thread) because urlopen blocks.
from dataclasses import dataclass
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen
from xml.etree import ElementTree as ET

from core.config import get_settings
from core.exceptions import (
    ArxivPaperNotFoundError,
    ArxivUnavailableError,
    InvalidArxivIdError,
)


# Level 1 fix: title/category were never saved, so /documents?category= always
# returned []. arXiv already sends them, so return them with the abstract.
@dataclass
class ArxivPaper:
    abstract: str
    title: str | None
    category: str | None


def fetch_arxiv_paper(arxiv_id: str) -> ArxivPaper:
    params = urlencode({                          # build "id_list=1706.03762&max_results=1"
        "id_list": arxiv_id,
        "max_results": 1,
    })
    # Level 2: base URL comes from Settings instead of being hardcoded.
    url = f"{get_settings().arxiv_api_base_url}?{params}"   # full request URL

    try:
        with urlopen(url, timeout=15) as response:          # HTTP GET to arXiv (waits up to 15 s)
            xml_data = response.read()                      # raw Atom XML bytes

        root = ET.fromstring(xml_data)                      # parse XML into a tree
        ns = {                                              # short names for XML namespaces
            "atom": "http://www.w3.org/2005/Atom",
            # Level 1 fix: needed to read <arxiv:primary_category>.
            "arxiv": "http://arxiv.org/schemas/atom",
        }
        entry = root.find("atom:entry", ns)                 # the paper's <entry>

        if entry is None:                                   # no such paper
            raise ArxivPaperNotFoundError("No arXiv paper found for this ID.")   # → 404

        abstract = entry.findtext(                          # text of <summary> = the abstract
            "atom:summary",
            default="",
            namespaces=ns,
        )
        abstract = " ".join(abstract.split())               # collapse newlines/extra spaces

        if not abstract:                                    # paper exists but no abstract
            raise ArxivPaperNotFoundError("The paper has no abstract available.")  # → 404

        # Level 1 fix: read title (collapse arXiv's line breaks) and category.
        # Category is an attribute: <arxiv:primary_category term="cs.CL"/>
        title = " ".join(
            entry.findtext("atom:title", default="", namespaces=ns).split()
        )
        category_el = entry.find("arxiv:primary_category", ns)
        category = (
            category_el.get("term") if category_el is not None else None
        )

        return ArxivPaper(                                  # back to the service
            abstract=abstract,
            title=title or None,                            # "" → None
            category=category,
        )

    except ArxivPaperNotFoundError:
        raise  # our own error from above: pass it through unchanged
    except HTTPError as exc:                                # arXiv answered with an error status
        # arXiv rejects malformed IDs with a 400.
        if exc.code == 400:
            raise InvalidArxivIdError("Invalid arXiv ID format.") from exc               # → 400
        raise ArxivUnavailableError("Could not fetch the abstract from arXiv.") from exc  # → 502
    except Exception as exc:
        # Network errors, timeouts, broken XML, ...
        raise ArxivUnavailableError("Could not fetch the abstract from arXiv.") from exc  # → 502
