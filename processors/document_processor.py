"""
Document processing module for Medication Reconciliation Agent.
Extracts text from PDF and image files with OCR support.
"""

import io
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

import pypdf
from PIL import Image
import pytesseract


class DocumentType(Enum):
    """Document type enumeration."""
    OLD_PRESCRIPTION = "Old Prescription"
    NEW_PRESCRIPTION = "New Prescription"
    DISCHARGE_SUMMARY = "Discharge Summary"
    PHARMACY_LIST = "Pharmacy Medication List"
    UNKNOWN = "Unknown Document"


class ProcessingStatus(Enum):
    """Processing status enumeration."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    PENDING = "pending"


@dataclass
class PageContent:
    """Represents content from a single page."""
    page_number: int
    text: str
    extraction_method: str  # 'pdf_text', 'ocr', 'hybrid'
    confidence: Optional[float] = None  # OCR confidence if applicable


@dataclass
class ProcessedDocument:
    """Represents a processed document with extracted content."""
    filename: str
    document_type: DocumentType
    status: ProcessingStatus
    pages: List[PageContent] = field(default_factory=list)
    total_pages: int = 0
    error_message: Optional[str] = None

    def get_full_text(self) -> str:
        """Get all extracted text concatenated."""
        return "\n\n".join([f"[Page {p.page_number}]\n{p.text}" for p in self.pages])

    def get_page_text(self, page_number: int) -> Optional[str]:
        """Get text from a specific page."""
        for page in self.pages:
            if page.page_number == page_number:
                return page.text
        return None


class DocumentProcessor:
    """Processes medical documents and extracts text content."""

    def __init__(self, enable_ocr: bool = True):
        """
        Initialize document processor.

        Args:
            enable_ocr: Whether to enable OCR for scanned documents
        """
        self.enable_ocr = enable_ocr

    def process_document(
        self,
        file_bytes: bytes,
        filename: str,
        document_type: DocumentType
    ) -> ProcessedDocument:
        """
        Process a document and extract text.

        Args:
            file_bytes: Raw file bytes
            filename: Original filename
            document_type: Type of medical document

        Returns:
            ProcessedDocument with extracted content
        """
        # Determine file type
        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''

        try:
            if file_ext == 'pdf':
                return self._process_pdf(file_bytes, filename, document_type)
            elif file_ext in ['jpg', 'jpeg', 'png']:
                return self._process_image(file_bytes, filename, document_type)
            else:
                return ProcessedDocument(
                    filename=filename,
                    document_type=document_type,
                    status=ProcessingStatus.FAILED,
                    error_message=f"Unsupported file type: {file_ext}"
                )
        except Exception as e:
            return ProcessedDocument(
                filename=filename,
                document_type=document_type,
                status=ProcessingStatus.FAILED,
                error_message=f"Processing error: {str(e)}"
            )

    def _process_pdf(
        self,
        file_bytes: bytes,
        filename: str,
        document_type: DocumentType
    ) -> ProcessedDocument:
        """
        Extract text from PDF file.
        Falls back to OCR if text extraction yields minimal content.
        """
        doc = ProcessedDocument(
            filename=filename,
            document_type=document_type,
            status=ProcessingStatus.PENDING
        )

        try:
            # Try text extraction first
            pdf_file = io.BytesIO(file_bytes)
            pdf_reader = pypdf.PdfReader(pdf_file)
            doc.total_pages = len(pdf_reader.pages)

            pages_with_text = 0

            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()

                # Check if meaningful text was extracted
                if text and len(text.strip()) > 50:
                    doc.pages.append(PageContent(
                        page_number=page_num + 1,
                        text=text.strip(),
                        extraction_method='pdf_text'
                    ))
                    pages_with_text += 1
                else:
                    # Minimal or no text - likely scanned
                    if self.enable_ocr:
                        ocr_result = self._ocr_pdf_page(file_bytes, page_num)
                        if ocr_result:
                            doc.pages.append(ocr_result)
                    else:
                        doc.pages.append(PageContent(
                            page_number=page_num + 1,
                            text=f"[Page {page_num + 1} contains minimal extractable text. OCR may be needed.]",
                            extraction_method='pdf_text'
                        ))

            # Determine status
            if len(doc.pages) == doc.total_pages and pages_with_text > 0:
                doc.status = ProcessingStatus.SUCCESS
            elif len(doc.pages) > 0:
                doc.status = ProcessingStatus.PARTIAL
                doc.error_message = f"Some pages had minimal text. Extracted {pages_with_text}/{doc.total_pages} pages successfully."
            else:
                doc.status = ProcessingStatus.FAILED
                doc.error_message = "No text could be extracted from PDF"

        except Exception as e:
            doc.status = ProcessingStatus.FAILED
            doc.error_message = f"PDF processing error: {str(e)}"

        return doc

    def _process_image(
        self,
        file_bytes: bytes,
        filename: str,
        document_type: DocumentType
    ) -> ProcessedDocument:
        """Extract text from image file using OCR."""
        doc = ProcessedDocument(
            filename=filename,
            document_type=document_type,
            status=ProcessingStatus.PENDING,
            total_pages=1
        )

        try:
            if not self.enable_ocr:
                doc.status = ProcessingStatus.FAILED
                doc.error_message = "OCR is disabled. Cannot process image files."
                return doc

            # Open image
            image = Image.open(io.BytesIO(file_bytes))

            # Perform OCR
            text = pytesseract.image_to_string(image)

            if text and len(text.strip()) > 20:
                doc.pages.append(PageContent(
                    page_number=1,
                    text=text.strip(),
                    extraction_method='ocr'
                ))
                doc.status = ProcessingStatus.SUCCESS
            else:
                doc.status = ProcessingStatus.PARTIAL
                doc.error_message = "OCR completed but extracted minimal text"
                doc.pages.append(PageContent(
                    page_number=1,
                    text=text.strip() if text else "[No text detected]",
                    extraction_method='ocr'
                ))

        except Exception as e:
            doc.status = ProcessingStatus.FAILED
            doc.error_message = f"Image OCR error: {str(e)}"

        return doc

    def _ocr_pdf_page(self, file_bytes: bytes, page_num: int) -> Optional[PageContent]:
        """
        Perform OCR on a specific PDF page.
        Note: This is a placeholder for pdf2image integration.
        """
        # This would require pdf2image and poppler installation
        # For Level 2, we'll note that this page needs OCR
        return PageContent(
            page_number=page_num + 1,
            text=f"[Page {page_num + 1} appears to be scanned. Advanced OCR required.]",
            extraction_method='ocr_needed'
        )


def process_uploaded_documents(uploaded_files: Dict[str, any]) -> List[ProcessedDocument]:
    """
    Process all uploaded documents.

    Args:
        uploaded_files: Dictionary mapping document type key to uploaded file object

    Returns:
        List of ProcessedDocument objects (only for successfully uploaded files)
    """
    processor = DocumentProcessor(enable_ocr=True)
    processed_docs = []

    # Document type mapping
    doc_type_map = {
        'old_prescription': DocumentType.OLD_PRESCRIPTION,
        'new_prescription': DocumentType.NEW_PRESCRIPTION,
        'discharge_summary': DocumentType.DISCHARGE_SUMMARY,
        'pharmacy_list': DocumentType.PHARMACY_LIST
    }

    for doc_key, uploaded_file in uploaded_files.items():
        if uploaded_file is not None:
            # Get document type
            doc_type = doc_type_map.get(doc_key, DocumentType.UNKNOWN)

            # Read file bytes
            file_bytes = uploaded_file.getvalue()

            # Process document
            processed_doc = processor.process_document(
                file_bytes=file_bytes,
                filename=uploaded_file.name,
                document_type=doc_type
            )

            processed_docs.append(processed_doc)

    return processed_docs
