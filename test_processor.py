"""
Test script for document processor - Level 2
Creates sample test documents and verifies processing works.
"""

from processors.document_processor import DocumentProcessor, DocumentType
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io
from PIL import Image, ImageDraw, ImageFont

def create_test_pdf_with_text():
    """Create a simple PDF with text content."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    # Page 1
    c.drawString(100, 750, "Medical Prescription")
    c.drawString(100, 730, "Patient: John Doe")
    c.drawString(100, 710, "Date: 2026-09-22")
    c.drawString(100, 680, "Medications:")
    c.drawString(120, 660, "1. Lisinopril 10mg - Take once daily")
    c.drawString(120, 640, "2. Metformin 500mg - Take twice daily with meals")
    c.drawString(120, 620, "3. Atorvastatin 20mg - Take once daily at bedtime")
    c.showPage()

    # Page 2
    c.drawString(100, 750, "Additional Instructions")
    c.drawString(100, 730, "Follow up in 30 days")
    c.drawString(100, 710, "Monitor blood pressure regularly")
    c.showPage()

    c.save()
    buffer.seek(0)
    return buffer.getvalue()

def create_test_image_with_text():
    """Create a simple image with text content."""
    # Create a white image
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)

    # Add text (using default font)
    draw.text((50, 50), "PHARMACY MEDICATION LIST", fill='black')
    draw.text((50, 100), "Patient: Jane Smith", fill='black')
    draw.text((50, 130), "Date: 2026-09-22", fill='black')
    draw.text((50, 170), "Current Medications:", fill='black')
    draw.text((70, 200), "1. Aspirin 81mg daily", fill='black')
    draw.text((70, 230), "2. Lisinopril 10mg daily", fill='black')
    draw.text((70, 260), "3. Metformin 500mg twice daily", fill='black')

    # Convert to bytes
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer.getvalue()

def test_document_processing():
    """Test document processing functionality."""
    processor = DocumentProcessor(enable_ocr=True)

    print("=" * 60)
    print("Testing Document Processor - Level 2")
    print("=" * 60)

    # Test 1: PDF with text
    print("\n[Test 1] Processing PDF with text...")
    pdf_bytes = create_test_pdf_with_text()
    pdf_doc = processor.process_document(
        file_bytes=pdf_bytes,
        filename="test_prescription.pdf",
        document_type=DocumentType.NEW_PRESCRIPTION
    )

    print(f"  Status: {pdf_doc.status.value}")
    print(f"  Pages processed: {len(pdf_doc.pages)}/{pdf_doc.total_pages}")
    print(f"  Document type: {pdf_doc.document_type.value}")
    if pdf_doc.error_message:
        print(f"  Message: {pdf_doc.error_message}")

    if pdf_doc.pages:
        print(f"  Sample text from Page 1:")
        sample_text = pdf_doc.pages[0].text[:200]
        print(f"    {sample_text}...")

    # Test 2: Image with text (requires Tesseract)
    print("\n[Test 2] Processing image with text...")
    try:
        img_bytes = create_test_image_with_text()
        img_doc = processor.process_document(
            file_bytes=img_bytes,
            filename="test_pharmacy_list.png",
            document_type=DocumentType.PHARMACY_LIST
        )

        print(f"  Status: {img_doc.status.value}")
        print(f"  Pages processed: {len(img_doc.pages)}")
        print(f"  Document type: {img_doc.document_type.value}")
        if img_doc.error_message:
            print(f"  Message: {img_doc.error_message}")

        if img_doc.pages:
            print(f"  Sample text from image:")
            sample_text = img_doc.pages[0].text[:200] if img_doc.pages[0].text else "[No text]"
            print(f"    {sample_text}")
    except Exception as e:
        print(f"  ⚠️ Image processing error: {str(e)}")
        print(f"  Note: Image OCR requires Tesseract to be installed on the system")

    # Test 3: Empty/invalid file
    print("\n[Test 3] Processing invalid file...")
    invalid_doc = processor.process_document(
        file_bytes=b"invalid content",
        filename="test.txt",
        document_type=DocumentType.UNKNOWN
    )

    print(f"  Status: {invalid_doc.status.value}")
    print(f"  Error message: {invalid_doc.error_message}")

    print("\n" + "=" * 60)
    print("✅ Document processor testing complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run: streamlit run app.py")
    print("2. Upload test documents (PDF or images)")
    print("3. Click 'Process Documents' button")
    print("4. Review extracted text in the UI")
    print("\nNote: For image OCR to work, Tesseract must be installed:")
    print("  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
    print("  After install, add to PATH or set TESSDATA_PREFIX environment variable")

if __name__ == "__main__":
    test_document_processing()
