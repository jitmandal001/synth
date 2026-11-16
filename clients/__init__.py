# Level 2: clients talk to outside services (arXiv API, OpenRouter LLM).
# They know nothing about FastAPI or HTTP status codes: on failure they raise
# the errors in core/exceptions.py, and the web layer decides the status code.
from clients.arxiv_client import ArxivPaper, fetch_arxiv_paper
from clients.llm_client import extract_research

__all__ = ["ArxivPaper", "fetch_arxiv_paper", "extract_research"]
