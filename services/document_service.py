from core.exceptions import DocumentNotFoundError
from repositories import DocumentRepository
from schemas import DocumentResponse


class DocumentService:
    """Reading stored documents and their extractions."""

    def __init__(self, repository: DocumentRepository):
        self.repository = repository

    async def list_documents(self, category: str | None = None) -> list[DocumentResponse]:
        documents = await self.repository.list_documents(category)
        # Level 2: from_attributes in DocumentResponse replaces format_document().
        return [DocumentResponse.model_validate(document) for document in documents]

    async def get_document(self, document_id: int) -> DocumentResponse:
        document = await self.repository.get_document(document_id)
        if document is None:
            # Business rule: a missing id is an error. The web layer maps it to 404.
            raise DocumentNotFoundError("Document not found")
        return DocumentResponse.model_validate(document)
