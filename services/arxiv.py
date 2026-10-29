
from urllib.request import urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError
from xml.etree import ElementTree as ET

from fastapi import HTTPException


def fetch_arxiv_abstract(arxiv_id: str) -> str:
    params = urlencode({
        "id_list": arxiv_id,
        "max_results": 1,
    })
    url = f"https://export.arxiv.org/api/query?{params}"

    try:
        with urlopen(url, timeout=15) as response:
            xml_data = response.read()

        root = ET.fromstring(xml_data)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
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

        return abstract

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
