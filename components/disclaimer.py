"""
Medical disclaimer component for Medication Reconciliation Agent.
Displays prominent safety and liability disclaimers.
"""

import streamlit as st


def show_disclaimer():
    """
    Display a prominent medical disclaimer warning.
    This ensures users understand the prototype limitations.
    """
    st.markdown("""
    <div style="
        background-color: #fff3cd;
        border: 2px solid #ffc107;
        border-radius: 8px;
        padding: 20px;
        margin: 20px 0;
    ">
        <h3 style="color: #856404; margin-top: 0;">
            ⚠️ IMPORTANT MEDICAL DISCLAIMER
        </h3>
        <p style="color: #856404; margin-bottom: 0;">
            <strong>This is a prototype system for research and demonstration purposes only.</strong>
        </p>
        <ul style="color: #856404;">
            <li>This system does NOT provide medical advice, diagnosis, or treatment recommendations</li>
            <li>It does NOT prescribe, recommend, stop, or modify any medications</li>
            <li>All identified discrepancies MUST be reviewed and verified by a qualified healthcare professional</li>
            <li>Do NOT make any medication changes based solely on this system's output</li>
            <li>In case of medical emergency, contact your healthcare provider or emergency services immediately</li>
        </ul>
        <p style="color: #856404; margin-bottom: 0;">
            <strong>By using this system, you acknowledge that you understand these limitations and will seek
            professional medical guidance for all medication-related decisions.</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)


def show_footer_disclaimer():
    """
    Display a compact footer disclaimer.
    """
    st.markdown("---")
    st.caption(
        "⚠️ **Prototype System** - Not for clinical use. "
        "All findings require healthcare professional verification. "
        "This system does not provide medical advice."
    )
