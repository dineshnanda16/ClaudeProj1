"""
Medication Reconciliation Agent - Level 3 Prototype

A healthcare prototype system for identifying potential medication discrepancies
across multiple medical documents. Level 3 includes LLM-powered medication extraction
with structured output.

Author: Built with Claude Code
Date: September 2026
"""

import streamlit as st
import pandas as pd
from components.file_uploader import file_uploader_section, get_upload_summary
from components.disclaimer import show_disclaimer, show_footer_disclaimer
from processors.document_processor import process_uploaded_documents, ProcessingStatus
from processors.medication_extractor import extract_medications_from_processed_documents, ExtractionStatus


# Page configuration
st.set_page_config(
    page_title="Medication Reconciliation Agent",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="collapsed"
)


def main():
    """Main application entry point."""

    # Application header
    st.title("💊 Medication Reconciliation Agent")
    st.markdown("""
    **A prototype system for identifying potential medication discrepancies across medical documents.**

    This tool compares medication information from multiple sources to flag potential differences
    that require healthcare professional review.
    """)

    # Display prominent disclaimer
    show_disclaimer()

    st.markdown("---")

    # Document Upload Section
    st.header("📤 Document Upload")
    st.markdown("""
    **Upload any available medical documents for medication reconciliation analysis.**

    You do not need to provide all document types. The system will analyze whatever information
    is available and identify any limitations.

    Accepted formats: **PDF, JPG, PNG** | Maximum size: **10 MB per file**
    """)

    # Create two columns for upload sections
    col1, col2 = st.columns(2)

    with col1:
        # Old Prescription upload
        old_prescription = file_uploader_section(
            label="Old Prescription",
            key="old_prescription",
            help_text="Previous prescription document"
        )

        st.markdown("")  # Spacing

        # Discharge Summary upload
        discharge_summary = file_uploader_section(
            label="Discharge Summary",
            key="discharge_summary",
            help_text="Hospital discharge summary with medication instructions"
        )

    with col2:
        # New Prescription upload
        new_prescription = file_uploader_section(
            label="New Prescription",
            key="new_prescription",
            help_text="Current prescription document"
        )

        st.markdown("")  # Spacing

        # Pharmacy Medication List upload
        pharmacy_list = file_uploader_section(
            label="Pharmacy Medication List",
            key="pharmacy_list",
            help_text="Current medication list from pharmacy"
        )

    # Upload summary
    st.markdown("---")
    uploaded_files = {
        'old_prescription': old_prescription,
        'new_prescription': new_prescription,
        'discharge_summary': discharge_summary,
        'pharmacy_list': pharmacy_list
    }

    summary = get_upload_summary(uploaded_files)

    # Display upload status summary
    col_summary1, col_summary2, col_summary3 = st.columns(3)
    with col_summary1:
        st.metric("Documents Uploaded", f"{summary['uploaded']}")
    with col_summary2:
        if summary['uploaded'] > 0:
            status = "✅ Ready to Process"
        else:
            status = "⏳ No Documents"
        st.metric("Upload Status", status)
    with col_summary3:
        st.metric("Available Document Types", summary['uploaded'])

    st.markdown("---")

    # Run Reconciliation Button
    st.header("🔍 Analysis")

    # Initialize session state for processed documents and medications
    if 'processed_documents' not in st.session_state:
        st.session_state.processed_documents = None
    if 'extracted_medications' not in st.session_state:
        st.session_state.extracted_medications = None

    if summary['uploaded'] > 0:
        if st.button("🚀 Process Documents & Extract Medications", type="primary", use_container_width=True):
            with st.spinner("Processing documents... This may take a moment."):
                # Step 1: Process all uploaded documents
                st.session_state.processed_documents = process_uploaded_documents(uploaded_files)
                st.success(f"✅ Document processing complete! {len(st.session_state.processed_documents)} document(s) processed.")

            # Step 2: Extract medications if documents were successfully processed
            if st.session_state.processed_documents and len(st.session_state.processed_documents) > 0:
                with st.spinner("Extracting medication information using LLM... This may take a minute."):
                    try:
                        st.session_state.extracted_medications = extract_medications_from_processed_documents(
                            st.session_state.processed_documents
                        )
                        total_meds = sum(doc.get_medication_count() for doc in st.session_state.extracted_medications)
                        st.success(f"✅ Medication extraction complete! {total_meds} medication(s) extracted from {len(st.session_state.extracted_medications)} document(s).")
                    except Exception as e:
                        st.error(f"❌ Medication extraction failed: {str(e)}")
                        st.info("💡 Please ensure your .env file is configured with LLM_PROVIDER and API keys.")
                        st.session_state.extracted_medications = None
    else:
        st.button(
            "🚀 Process Documents & Extract Medications",
            type="primary",
            use_container_width=True,
            disabled=True
        )
        st.info("📄 Upload at least one document to begin processing.")

    st.markdown("---")

    # Results section - only show if documents have been processed
    st.header("📊 Results")

    if st.session_state.processed_documents is not None:
        processed_docs = st.session_state.processed_documents

        # Document Processing Status
        with st.expander("📄 Document Processing Status", expanded=True):
            if len(processed_docs) == 0:
                st.warning("No documents were processed.")
            else:
                st.markdown(f"**Total documents processed:** {len(processed_docs)}")
                st.markdown("---")

                for doc in processed_docs:
                    # Create columns for each document
                    col_doc1, col_doc2, col_doc3 = st.columns([3, 1, 1])

                    with col_doc1:
                        st.markdown(f"**{doc.document_type.value}**")
                        st.caption(f"📎 {doc.filename}")

                    with col_doc2:
                        if doc.status == ProcessingStatus.SUCCESS:
                            st.success("✅ Success")
                        elif doc.status == ProcessingStatus.PARTIAL:
                            st.warning("⚠️ Partial")
                        else:
                            st.error("❌ Failed")

                    with col_doc3:
                        st.metric("Pages", f"{len(doc.pages)}/{doc.total_pages if doc.total_pages > 0 else len(doc.pages)}")

                    # Show details
                    if doc.error_message:
                        st.caption(f"ℹ️ {doc.error_message}")

                    # Show extraction methods used
                    if doc.pages:
                        methods = set(p.extraction_method for p in doc.pages)
                        method_text = ", ".join(methods)
                        st.caption(f"🔧 Extraction: {method_text}")

                    st.markdown("---")

        # Extracted Text Display
        with st.expander("📄 Extracted Document Text", expanded=False):
            if len(processed_docs) == 0:
                st.info("No documents to display.")
            else:
                # Create tabs for each document
                doc_tabs = st.tabs([f"{doc.document_type.value}" for doc in processed_docs])

                for idx, (tab, doc) in enumerate(zip(doc_tabs, processed_docs)):
                    with tab:
                        st.markdown(f"**Filename:** {doc.filename}")
                        st.markdown(f"**Status:** {doc.status.value}")
                        st.markdown(f"**Total Pages:** {doc.total_pages if doc.total_pages > 0 else len(doc.pages)}")

                        if doc.pages:
                            st.markdown("---")
                            for page in doc.pages:
                                st.markdown(f"### Page {page.page_number}")
                                st.caption(f"Extraction method: {page.extraction_method}")

                                # Display extracted text in a scrollable text area
                                if page.text:
                                    st.text_area(
                                        f"Page {page.page_number} Content",
                                        value=page.text,
                                        height=300,
                                        key=f"text_{idx}_page_{page.page_number}",
                                        disabled=True
                                    )
                                else:
                                    st.info("No text extracted from this page.")
                        else:
                            st.warning("No content could be extracted from this document.")
                            if doc.error_message:
                                st.error(f"Error: {doc.error_message}")

    else:
        # Show placeholder when no processing has occurred
        with st.expander("📄 Document Processing Status", expanded=False):
            st.info("🚧 Process documents to see extraction status.")

    # Extracted Medications Section
    with st.expander("💊 Extracted Medications", expanded=True):
        if st.session_state.extracted_medications is not None:
            extracted_meds = st.session_state.extracted_medications

            if len(extracted_meds) == 0:
                st.warning("No medications were extracted.")
            else:
                # Summary metrics
                total_meds = sum(doc.get_medication_count() for doc in extracted_meds)
                successful_extractions = sum(1 for doc in extracted_meds if doc.extraction_status == ExtractionStatus.SUCCESS)

                col_med1, col_med2, col_med3 = st.columns(3)
                with col_med1:
                    st.metric("Total Medications Extracted", total_meds)
                with col_med2:
                    st.metric("Documents with Medications", successful_extractions)
                with col_med3:
                    st.metric("Documents Processed", len(extracted_meds))

                st.markdown("---")

                # Display medications by document
                for doc_meds in extracted_meds:
                    st.markdown(f"### 📄 {doc_meds.document_type}")
                    st.caption(f"Source: {doc_meds.filename}")

                    # Show extraction status
                    if doc_meds.extraction_status == ExtractionStatus.SUCCESS:
                        st.success(f"✅ Successfully extracted {doc_meds.get_medication_count()} medication(s)")
                    elif doc_meds.extraction_status == ExtractionStatus.NO_MEDICATIONS:
                        st.info("ℹ️ No medications found in this document")
                    elif doc_meds.extraction_status == ExtractionStatus.FAILED:
                        st.error(f"❌ Extraction failed: {doc_meds.error_message}")
                    elif doc_meds.extraction_status == ExtractionStatus.PARTIAL:
                        st.warning(f"⚠️ Partial extraction: {doc_meds.error_message}")

                    # Display medications if any were extracted
                    if doc_meds.medications and len(doc_meds.medications) > 0:
                        # Create dataframe for table display
                        med_data = []
                        for idx, med in enumerate(doc_meds.medications):
                            med_data.append({
                                "#": idx + 1,
                                "Medication": med.medication_name,
                                "Strength": med.strength or "—",
                                "Dose": med.dose or "—",
                                "Route": med.route or "—",
                                "Frequency": med.frequency or "—",
                                "Instructions": med.instructions or "—",
                                "Page": med.source_page or "—"
                            })

                        df = pd.DataFrame(med_data)
                        st.dataframe(df, use_container_width=True, hide_index=True)

                        # Detailed view for each medication
                        st.markdown("#### Detailed Medication Information")
                        for idx, med in enumerate(doc_meds.medications):
                            with st.expander(f"Medication #{idx + 1}: {med.medication_name}", expanded=False):
                                col_detail1, col_detail2 = st.columns(2)

                                with col_detail1:
                                    st.markdown("**Basic Information:**")
                                    st.markdown(f"- **Medication Name:** {med.medication_name}")
                                    st.markdown(f"- **Generic Name:** {med.generic_name or 'Not specified'}")
                                    st.markdown(f"- **Brand Name:** {med.brand_name or 'Not specified'}")
                                    st.markdown(f"- **Strength:** {med.strength or 'Not specified'}")
                                    st.markdown(f"- **Dosage Form:** {med.dosage_form or 'Not specified'}")

                                with col_detail2:
                                    st.markdown("**Dosing Information:**")
                                    st.markdown(f"- **Dose:** {med.dose or 'Not specified'}")
                                    st.markdown(f"- **Route:** {med.route or 'Not specified'}")
                                    st.markdown(f"- **Frequency:** {med.frequency or 'Not specified'}")
                                    st.markdown(f"- **Duration:** {med.duration or 'Not specified'}")
                                    st.markdown(f"- **Instructions:** {med.instructions or 'Not specified'}")

                                st.markdown("**Additional Information:**")
                                st.markdown(f"- **Indication:** {med.indication or 'Not specified'}")
                                st.markdown(f"- **Status:** {med.status or 'Not specified'}")

                                st.markdown("**Source Information:**")
                                st.markdown(f"- **Document:** {med.source_document}")
                                st.markdown(f"- **Page:** {med.source_page or 'Unknown'}")

                                st.markdown("**Evidence Text:**")
                                st.text_area(
                                    "Original text from document",
                                    value=med.evidence_text,
                                    height=100,
                                    key=f"evidence_{doc_meds.filename}_{idx}",
                                    disabled=True
                                )

                    st.markdown("---")

        else:
            st.info("🚧 Process documents to extract medication information.")

    # Medication Comparison (placeholder)
    with st.expander("🔄 Medication Comparison", expanded=False):
        st.info("🚧 This section will show side-by-side medication comparisons in future versions.")

    # Possible Discrepancies (placeholder)
    with st.expander("⚠️ Possible Discrepancies", expanded=False):
        st.info("🚧 This section will list identified discrepancies with severity levels in future versions.")
        st.markdown("""
        **Future discrepancy categories will include:**
        - New medication added
        - Possible removed/stopped medication
        - Dose change detected
        - Frequency change detected
        - Duplicate medication identified
        """)

    # Source Evidence (placeholder)
    with st.expander("📋 Source Evidence", expanded=False):
        st.info("🚧 This section will show relevant excerpts from source documents supporting each finding.")

    # Footer disclaimer
    show_footer_disclaimer()

    # Sidebar (optional information)
    with st.sidebar:
        st.header("ℹ️ About")
        st.markdown("""
        **Version:** Level 3 Prototype

        **Current Features:**
        - Document upload interface
        - File validation
        - PDF text extraction
        - Image OCR processing
        - Page-by-page extraction
        - Multi-document support
        - **LLM-powered medication extraction**
        - **Structured medication data**
        - **Source tracking**

        **Coming Soon:**
        - Medication comparison logic
        - Discrepancy identification
        - Evidence linking
        - Medication normalization
        """)

        st.markdown("---")

        st.header("📚 Help")
        st.markdown("""
        **Supported File Types:**
        - PDF (.pdf)
        - Images (.jpg, .jpeg, .png)

        **Maximum File Size:**
        - 10 MB per file

        **Document Requirements:**
        - Upload any available medical documents
        - All document types are optional
        - System adapts to available information
        - At least one document needed for analysis

        **Processing:**
        - Text-based PDFs: Direct text extraction
        - Scanned PDFs/Images: OCR processing
        - Page-by-page content preservation
        - LLM extracts structured medication data

        **Configuration:**
        - Create `.env` file from `.env.example`
        - Set LLM_PROVIDER (openai or anthropic)
        - Add your API key
        - Choose model (gpt-4o or claude-3-5-sonnet)
        """)


if __name__ == "__main__":
    main()
