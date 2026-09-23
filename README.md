# 💊 Medication Reconciliation Agent

A prototype healthcare system for identifying potential medication discrepancies across multiple medical documents.

## ⚠️ IMPORTANT DISCLAIMER

**This is a research prototype for demonstration purposes only.**

- Does NOT provide medical advice, diagnosis, or treatment
- Does NOT prescribe, recommend, stop, or modify medications
- All findings MUST be verified by qualified healthcare professionals
- NOT approved for clinical use

## 📋 Overview

The Medication Reconciliation Agent is designed to help identify potential discrepancies when comparing medications across multiple medical documents:

- Old prescriptions
- New prescriptions
- Hospital discharge summaries
- Pharmacy medication lists

The system will eventually flag differences such as:
- New medications added
- Medications possibly removed or stopped
- Dose changes
- Frequency changes
- Duplicate medications

**All identified discrepancies require healthcare professional verification.**

## 🚀 Current Version: Level 1

### ✅ Implemented Features

- Clean, professional user interface
- File upload for 4 document types (PDF, JPG, PNG)
- File type and size validation
- Upload status tracking
- Placeholder sections for future features
- Prominent medical disclaimers

### 🚧 Not Yet Implemented

- Document content processing
- OCR/text extraction
- LLM-powered medication extraction
- Medication comparison logic
- Discrepancy identification
- Evidence linking

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup Steps

1. **Navigate to the project directory:**
   ```powershell
   cd D:\Claude\Test1
   ```

2. **Create a virtual environment (recommended):**
   ```powershell
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

   *Note: If you get an execution policy error, run:*
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

4. **Install required packages:**
   ```powershell
   pip install -r requirements.txt
   ```

## 🏃 Running the Application

### Start the Streamlit app:

```powershell
streamlit run app.py
```

The application will automatically open in your default web browser at `http://localhost:8501`

### Stop the application:

Press `Ctrl + C` in the terminal

## 📁 Project Structure

```
D:\Claude\Test1\
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── .gitignore                      # Git ignore rules
├── components/
│   ├── __init__.py
│   ├── file_uploader.py           # File upload component
│   └── disclaimer.py              # Medical disclaimer component
├── utils/
│   ├── __init__.py
│   └── validators.py              # File validation utilities
└── assets/
    └── styles.css                 # Custom CSS (for future use)
```

## 🎯 Usage

1. Launch the application using `streamlit run app.py`
2. Upload all four required documents:
   - Old Prescription
   - New Prescription
   - Discharge Summary
   - Pharmacy Medication List
3. Review upload status
4. Click "Run Medication Reconciliation" (currently displays placeholder message)

### Supported File Formats

- **PDF:** .pdf
- **Images:** .jpg, .jpeg, .png

### File Size Limits

- Maximum: 10 MB per file

## 🔮 Future Development Roadmap

### Level 2: Document Processing
- OCR implementation for image files
- PDF text extraction
- Document preprocessing

### Level 3: Medication Extraction
- LLM integration (e.g., OpenAI, Claude)
- Structured medication extraction
- Entity recognition and normalization

### Level 4: Comparison Logic
- Medication matching algorithm
- Discrepancy detection
- Severity classification

### Level 5: Evidence & Reporting
- Source document linking
- Evidence highlighting
- Exportable reports

## 🛠️ Technical Stack

- **Framework:** Streamlit
- **Language:** Python 3.8+
- **UI Components:** Custom Streamlit components
- **File Processing:** Pillow (for image handling)

## 👥 Contributing

This is a prototype project. Future enhancements will include:
- Unit tests
- Integration tests
- Documentation improvements
- Code quality tools

## 📄 License

This is a prototype educational project.

## 🆘 Support

For issues or questions about this prototype:
1. Check the in-app help section
2. Review this README
3. Contact the development team

## ⚕️ Medical Safety

**Remember:**
- This system is NOT a substitute for professional medical advice
- NEVER make medication changes without consulting a healthcare provider
- In emergencies, contact your doctor or emergency services immediately
- All system outputs require healthcare professional verification

---

**Built with Claude Code** | September 2026 | Version: Level 1 Prototype
