"""
File uploader component for Medication Reconciliation Agent.
Provides reusable upload interface with validation and status display.
"""

import streamlit as st
from utils.validators import validate_upload


def file_uploader_section(
    label: str,
    key: str,
    help_text: str = "Upload PDF or image file (JPG, PNG) - Optional"
):
    """
    Create a file upload section with validation and status display.

    Args:
        label: Display label for the upload section
        key: Unique key for the Streamlit file_uploader widget
        help_text: Help text to display below the uploader

    Returns:
        Uploaded file object or None
    """
    st.subheader(f"{label} (Optional)")

    # File uploader widget
    uploaded_file = st.file_uploader(
        f"Choose {label}",
        type=['pdf', 'jpg', 'jpeg', 'png'],
        key=key,
        help=help_text,
        label_visibility="collapsed"
    )

    # Display upload status
    if uploaded_file is not None:
        # Validate the uploaded file
        is_valid, message = validate_upload(
            uploaded_file.name,
            uploaded_file.size
        )

        if is_valid:
            # Show success status
            st.success(f"✅ **{uploaded_file.name}** uploaded successfully")

            # Display file details
            file_size_kb = uploaded_file.size / 1024
            file_type = uploaded_file.name.split('.')[-1].upper()

            col1, col2 = st.columns(2)
            with col1:
                st.caption(f"**Type:** {file_type}")
            with col2:
                st.caption(f"**Size:** {file_size_kb:.1f} KB")

        else:
            # Show error status
            st.error(f"❌ {message}")
            return None

    else:
        # Show waiting status
        st.info("📄 No file uploaded yet")

    return uploaded_file


def get_upload_summary(uploaded_files: dict) -> dict:
    """
    Generate a summary of all uploaded files.

    Args:
        uploaded_files: Dictionary mapping document type to uploaded file object

    Returns:
        Dictionary with upload status summary
    """
    summary = {
        'total': len(uploaded_files),
        'uploaded': sum(1 for f in uploaded_files.values() if f is not None),
        'missing': sum(1 for f in uploaded_files.values() if f is None),
        'complete': all(f is not None for f in uploaded_files.values())
    }

    return summary
