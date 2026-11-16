
from urllib.request import urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError
from xml.etree import ElementTree as ET

from dataclasses import dataclass

from fastapi import HTTPException

from core.config import get_settings


# Level 1 fix: title/category were never saved, so /documents?category= always
# returned []. arXiv already sends them, so return them with the abstract.
@dataclass
class ArxivPaper:
    abstract: str
    title: str | None
    category: str | None


def fetch_arxiv_paper(arxiv_id: str) -> ArxivPaper:
    params = urlencode({
        "id_list": arxiv_id,
        "max_results": 1,
    })
    # Level 2: base URL comes from Settings instead of being hardcoded.
    url = f"{get_settings().arxiv_api_base_url}?{params}"

    try:
        with urlopen(url, timeout=15) as response:
            xml_data = response.read()

        root = ET.fromstring(xml_data)
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            # Level 1 fix: needed to read <arxiv:primary_category>.
            "arxiv": "http://arxiv.org/schemas/atom",
        }
        entry = root.find("atom:entry", ns)

        if entry is None:
            raise HTTPException(
                status_code=404,
                detail="No arXiv paper found for this ID.",
            )

        abstract = entry.findtext(
            "atom:summary",
            default="",
            namespaces=ns,
        )
        abstract = " ".join(abstract.split())

        if not abstract:
            raise HTTPException(
                status_code=404,
                detail="The paper has no abstract available.",
            )

        # Level 1 fix: read title (collapse arXiv's line breaks) and category.
        # Category is an attribute: <arxiv:primary_category term="cs.CL"/>
        title = " ".join(
            entry.findtext("atom:title", default="", namespaces=ns).split()
        )
        category_el = entry.find("arxiv:primary_category", ns)
        category = (
            category_el.get("term") if category_el is not None else None
        )

        return ArxivPaper(
            abstract=abstract,
            title=title or None,
            category=category,
        )

    except HTTPException:
        raise
    except HTTPError as exc:
        # arXiv rejects malformed IDs with a 400.
        if exc.code == 400:
            raise HTTPException(
                status_code=400,
                detail="Invalid arXiv ID format.",
            ) from exc
        raise HTTPException(
            status_code=502,
            detail="Could not fetch the abstract from arXiv.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Could not fetch the abstract from arXiv.",
        ) from exc
