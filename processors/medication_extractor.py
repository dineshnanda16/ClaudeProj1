"""
Medication extraction module for Medication Reconciliation Agent.
Uses LLM to extract structured medication information from document text.
"""

import os
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")


class ExtractionStatus(Enum):
    """Extraction status enumeration."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    NO_MEDICATIONS = "no_medications"


class MedicationSchema(BaseModel):
    """Pydantic schema for medication extraction."""
    medication_name: str = Field(description="The medication name as written in the document")
    generic_name: Optional[str] = Field(default=None, description="Generic name if explicitly mentioned")
    brand_name: Optional[str] = Field(default=None, description="Brand name if explicitly mentioned")
    strength: Optional[str] = Field(default=None, description="Medication strength (e.g., '500 mg', '10 mg/mL')")
    dose: Optional[str] = Field(default=None, description="Dose per administration (e.g., '1 tablet', '500 mg')")
    dosage_form: Optional[str] = Field(default=None, description="Form of medication (e.g., 'tablet', 'capsule', 'solution')")
    route: Optional[str] = Field(default=None, description="Route of administration (e.g., 'oral', 'IV', 'topical')")
    frequency: Optional[str] = Field(default=None, description="How often to take (e.g., 'twice daily', 'every 6 hours')")
    duration: Optional[str] = Field(default=None, description="How long to take (e.g., '7 days', '3 months')")
    instructions: Optional[str] = Field(default=None, description="Special instructions (e.g., 'with food', 'before bedtime')")
    indication: Optional[str] = Field(default=None, description="Reason for medication if explicitly stated")
    status: Optional[str] = Field(default=None, description="Medication status if explicitly stated (e.g., 'discontinued', 'new')")
    evidence_text: str = Field(description="Original text excerpt from document that mentions this medication")


class MedicationListSchema(BaseModel):
    """Schema for list of medications extracted from a document."""
    medications: List[MedicationSchema] = Field(default_factory=list)


@dataclass
class ExtractedMedication:
    """Represents a single extracted medication with source information."""
    medication_name: str
    generic_name: Optional[str] = None
    brand_name: Optional[str] = None
    strength: Optional[str] = None
    dose: Optional[str] = None
    dosage_form: Optional[str] = None
    route: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    instructions: Optional[str] = None
    indication: Optional[str] = None
    status: Optional[str] = None
    source_document: str = ""
    source_page: Optional[int] = None
    evidence_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class DocumentMedications:
    """Represents all medications extracted from a single document."""
    filename: str
    document_type: str
    extraction_status: ExtractionStatus
    medications: List[ExtractedMedication] = field(default_factory=list)
    error_message: Optional[str] = None

    def get_medication_count(self) -> int:
        """Get number of medications extracted."""
        return len(self.medications)


class MedicationExtractor:
    """Extracts medication information from document text using LLM."""

    def __init__(self):
        """Initialize medication extractor with LLM client."""
        self.provider = os.getenv("LLM_PROVIDER", "").strip().lower()
        if not self.provider:
            configured = [provider for provider, env_name in (
                ("cohere", "COHERE_API_KEY"),
                ("openai", "OPENAI_API_KEY"),
                ("anthropic", "ANTHROPIC_API_KEY"),
            ) if os.getenv(env_name, "").strip()]
            if len(configured) != 1:
                raise ValueError(
                    "Set LLM_PROVIDER=cohere and COHERE_API_KEY in the project-root .env file "
                    "(or choose one configured provider)."
                )
            self.provider = configured[0]
        default_models = {
            "cohere": "command-a-03-2025",
            "openai": "gpt-4o",
            "anthropic": "claude-3-5-sonnet-20241022",
        }
        self.model = os.getenv("LLM_MODEL", "").strip() or default_models.get(self.provider, "")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.0"))

        # Initialize LLM client based on provider
        if self.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "LLM_PROVIDER is set to openai but OPENAI_API_KEY is missing. "
                    "If you use Cohere, set LLM_PROVIDER=cohere and COHERE_API_KEY in the project-root .env file."
                )
            import openai
            self.client = openai.OpenAI(api_key=api_key)
        elif self.provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment. Please configure .env file.")
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
        elif self.provider == "cohere":
            api_key = os.getenv("COHERE_API_KEY")
            if not api_key or api_key.strip() in {"<api key>", "your-api-key", "your_cohere_api_key"}:
                raise ValueError("COHERE_API_KEY is missing or still a placeholder. Set it in the project-root .env file.")
            # Use the documented V2 HTTPS endpoint directly. A broken Cohere SDK
            # installation should not prevent extraction from starting.
            self.cohere_api_key = api_key.strip()
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}. Supported providers: openai, anthropic, cohere")

    def extract_medications_from_document(
        self,
        document_text: str,
        filename: str,
        document_type: str,
        page_info: List[tuple]  # [(page_num, page_text), ...]
    ) -> DocumentMedications:
        """
        Extract medications from a processed document.

        Args:
            document_text: Full text content of the document
            filename: Document filename
            document_type: Type of document (e.g., "Old Prescription")
            page_info: List of (page_number, page_text) tuples

        Returns:
            DocumentMedications object with extracted medications
        """
        try:
            # Build extraction prompt
            extraction_prompt = self._build_extraction_prompt(document_text)

            # Call LLM for extraction
            if self.provider == "openai":
                medications_data = self._extract_with_openai(extraction_prompt)
            elif self.provider == "anthropic":
                medications_data = self._extract_with_anthropic(extraction_prompt)
            elif self.provider == "cohere":
                medications_data = self._extract_with_cohere(extraction_prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

            # Process extracted medications and add source information
            extracted_meds = []
            for med_data in medications_data.get("medications", []):
                # Find which page contains this medication
                page_num = self._find_source_page(med_data.get("evidence_text", ""), page_info)

                extracted_med = ExtractedMedication(
                    medication_name=med_data.get("medication_name", "Unknown"),
                    generic_name=med_data.get("generic_name"),
                    brand_name=med_data.get("brand_name"),
                    strength=med_data.get("strength"),
                    dose=med_data.get("dose"),
                    dosage_form=med_data.get("dosage_form"),
                    route=med_data.get("route"),
                    frequency=med_data.get("frequency"),
                    duration=med_data.get("duration"),
                    instructions=med_data.get("instructions"),
                    indication=med_data.get("indication"),
                    status=med_data.get("status"),
                    source_document=filename,
                    source_page=page_num,
                    evidence_text=med_data.get("evidence_text", "")
                )
                extracted_meds.append(extracted_med)

            # Determine extraction status
            if len(extracted_meds) == 0:
                status = ExtractionStatus.NO_MEDICATIONS
            else:
                status = ExtractionStatus.SUCCESS

            return DocumentMedications(
                filename=filename,
                document_type=document_type,
                extraction_status=status,
                medications=extracted_meds
            )

        except Exception as e:
            return DocumentMedications(
                filename=filename,
                document_type=document_type,
                extraction_status=ExtractionStatus.FAILED,
                medications=[],
                error_message=f"Extraction error: {str(e)}"
            )

    def _build_extraction_prompt(self, document_text: str) -> str:
        """Build the extraction prompt for the LLM."""
        return f"""You are a medical information extraction system. Your task is to extract medication information from medical documents.

**CRITICAL SAFETY RULES:**
1. Extract ONLY what is explicitly written in the document
2. DO NOT infer or guess missing information
3. If a field is not mentioned, return null/None
4. DO NOT make clinical decisions (e.g., don't label medications as "discontinued" unless explicitly stated)
5. Preserve the exact wording from the document in evidence_text

**DOCUMENT TEXT:**
{document_text}

**YOUR TASK:**
Extract all medications mentioned in this document. For each medication, provide:

- medication_name: The medication name as written in the document (REQUIRED)
- generic_name: Generic name if explicitly mentioned (null if not stated)
- brand_name: Brand name if explicitly mentioned (null if not stated)
- strength: Medication strength (e.g., "500 mg", "10 mg/mL") (null if not stated)
- dose: Dose per administration (e.g., "1 tablet", "500 mg") (null if not stated)
- dosage_form: Form of medication (e.g., "tablet", "capsule", "solution") (null if not stated)
- route: Route of administration (e.g., "oral", "IV", "topical") (null if not stated)
- frequency: How often to take (e.g., "twice daily", "every 6 hours") (null if not stated)
- duration: How long to take (e.g., "7 days", "3 months") (null if not stated)
- instructions: Special instructions (e.g., "with food", "before bedtime") (null if not stated)
- indication: Reason for medication if explicitly stated (null if not stated)
- status: Medication status ONLY if explicitly stated (e.g., "discontinued", "new") (null otherwise)
- evidence_text: The exact excerpt from the document that mentions this medication (REQUIRED)

Return your response as a JSON object with this structure:
{{
  "medications": [
    {{
      "medication_name": "...",
      "generic_name": null,
      "brand_name": null,
      "strength": "...",
      "dose": "...",
      "dosage_form": "...",
      "route": "...",
      "frequency": "...",
      "duration": null,
      "instructions": "...",
      "indication": null,
      "status": null,
      "evidence_text": "..."
    }}
  ]
}}

If no medications are found in the document, return: {{"medications": []}}

Extract medications now:"""

    def _extract_with_openai(self, prompt: str) -> Dict[str, Any]:
        """Extract medications using OpenAI API with structured outputs."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a medical information extraction system. Extract medication information accurately and return valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )

            # Parse JSON response
            content = response.choices[0].message.content
            return json.loads(content)

        except Exception as e:
            raise Exception(f"OpenAI extraction failed: {str(e)}")

    def _extract_with_anthropic(self, prompt: str) -> Dict[str, Any]:
        """Extract medications using Anthropic Claude API."""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Extract text content
            content = response.content[0].text

            # Parse JSON from response
            # Claude may include markdown code blocks, so extract JSON
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()

            return json.loads(content)

        except Exception as e:
            raise Exception(f"Anthropic extraction failed: {str(e)}")

    def _extract_with_cohere(self, prompt: str) -> Dict[str, Any]:
        """Extract JSON with Cohere V2 Chat using Python's standard library."""
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "response_format": {"type": "json_object"},
        }
        request = Request(
            "https://api.cohere.com/v2/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": "Bearer {}".format(self.cohere_api_key),
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=90) as response:
                body = json.load(response)
        except HTTPError as error:
            if error.code in (401, 403):
                reason = "Check the Cohere API key and account permissions."
            elif error.code == 429:
                reason = "Rate limit reached; try again later."
            elif error.code == 400:
                reason = "Check LLM_MODEL and the request configuration."
            else:
                reason = "Check the Cohere service status and retry."
            raise RuntimeError("Cohere API returned HTTP {}. {}".format(error.code, reason)) from error
        except URLError as error:
            raise RuntimeError("Could not reach Cohere's API. Check network access and retry.") from error

        try:
            if body.get("finish_reason") not in (None, "COMPLETE"):
                raise ValueError("Cohere response was incomplete")
            content = "".join(part["text"] for part in body["message"]["content"] if part.get("type") == "text")
            medications_data = json.loads(content)
            if not isinstance(medications_data, dict) or not isinstance(medications_data.get("medications"), list):
                raise ValueError("Response is missing a medications list")
            return medications_data
        except (KeyError, TypeError, ValueError) as error:
            raise RuntimeError("Cohere returned an invalid medication JSON response.") from error

    def _find_source_page(self, evidence_text: str, page_info: List[tuple]) -> Optional[int]:
        """
        Find which page contains the evidence text.

        Args:
            evidence_text: The evidence text to search for
            page_info: List of (page_number, page_text) tuples

        Returns:
            Page number or None if not found
        """
        if not evidence_text:
            return None

        # Search for evidence text in pages
        evidence_lower = evidence_text.lower()
        for page_num, page_text in page_info:
            if evidence_lower in page_text.lower():
                return page_num

        # If exact match not found, return first page as fallback
        return page_info[0][0] if page_info else None


def extract_medications_from_processed_documents(
    processed_documents: List[Any]
) -> List[DocumentMedications]:
    """
    Extract medications from all processed documents.

    Args:
        processed_documents: List of ProcessedDocument objects from Level 2

    Returns:
        List of DocumentMedications objects
    """
    extractor = MedicationExtractor()
    all_extracted = []

    for doc in processed_documents:
        # Skip documents that failed processing
        if not doc.pages or len(doc.pages) == 0:
            all_extracted.append(DocumentMedications(
                filename=doc.filename,
                document_type=doc.document_type.value,
                extraction_status=ExtractionStatus.FAILED,
                medications=[],
                error_message="No text available from document processing"
            ))
            continue

        # Get full text and page information
        full_text = doc.get_full_text()
        page_info = [(page.page_number, page.text) for page in doc.pages]

        # Extract medications
        extracted = extractor.extract_medications_from_document(
            document_text=full_text,
            filename=doc.filename,
            document_type=doc.document_type.value,
            page_info=page_info
        )

        all_extracted.append(extracted)

    return all_extracted
