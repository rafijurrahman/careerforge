# CareerForge Setup Guide

This guide walks you through setting up **CareerForge** on your local machine.

---

## Platform Support

| Operating System | Support Level | PDF Backend Engine | Requirements |
|---|:---:|:---:|---|
| **Windows 10 / 11** | **Officially Supported** | Word COM (fast-path) + LibreOffice | Python 3.10+, Microsoft Word (optional) or LibreOffice |
| **macOS 12+ (Monterey+)** | **Officially Supported** | LibreOffice Headless | Python 3.10+, `brew install --cask libreoffice` |
| **Linux (Ubuntu, etc.)** | **Community-Supported** | LibreOffice Headless | Python 3.10+, unit tests pass (page-fit untested) |

---

## Prerequisites & Installation

### 1. Document / PDF Engine Setup

* **Windows:**
  * Option A (Fastest): If you have Microsoft Office / Word installed, install the Windows extra:
    ```powershell
    pip install "careerforge[windows]"
    ```
  * Option B (Open Source): Install LibreOffice via winget:
    ```powershell
    winget install TheDocumentFoundation.LibreOffice
    ```

* **macOS:**
  * Install LibreOffice via Homebrew:
    ```bash
    brew install --cask libreoffice
    ```

* **Linux (Community-Supported):**
  * Install LibreOffice Writer:
    ```bash
    sudo apt-get update && sudo apt-get install -y libreoffice-writer
    ```

---

## 1. Clone the Repository

To use CareerForge for your personal job search, clone your own copy:

```bash
git clone https://github.com/your-username/careerforge.git
cd careerforge
```

---

## 2. Set Up Python Virtual Environment

It is recommended to run CareerForge inside an isolated virtual environment:

### On Windows:
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### On macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 3. Initialize Your Profile

Run the interactive setup wizard to initialize your personal `profile.yaml`:

```bash
python cli.py setup
```

The wizard will prompt you for:
* Full Name and professional header
* Contact email, phone, and location
* LinkedIn, GitHub, and portfolio URLs

Your personal data is saved to `profile.yaml`.

> [!IMPORTANT]
> `profile.yaml` is automatically excluded by `.gitignore`. Your personal phone number, home location, and contact information will **never** be committed or exposed to GitHub.

---

## 4. Customize Your Experience & Skills

Open `profile.yaml` in your favorite code editor (VS Code, Cursor, PyCharm, etc.) and customize:
* **`target_preferences`**: Your target job titles and location preferences.
* **`professional_summary`**: Your general career overview.
* **`technical_skills`**: Categorized lists of your core skills and tools.
* **`work_experience`**: Your employment history with quantifiable achievements.
* **`featured_projects`**: Real projects with tech stacks and live repository links.
* **`academic_background`**: Degrees, universities, and graduation years.
* **`certifications`**: Professional credentials with optional verification URLs.

---

## 5. Verify Your Setup

Test the installation by generating your first single-page ATS CV:

```bash
python cli.py apply
```

You should see:
```text
✅ SUCCESS: 1-Page ATS CV generated and verified!
   DOCX: output\Your_Name_Tailored_CV.docx
   PDF:  output\Your_Name_Tailored_CV.pdf
   Pages: 1 | Font Scale: 1.05
```

Open the generated PDF to confirm that your layout, fonts, and hyperlinks render cleanly.

---

## Troubleshooting

### Word COM API on Windows
If you receive a `win32com.client` error when running `apply`:
1. Ensure Microsoft Word is installed and activated.
2. Close any hanging Word background processes via Task Manager (`WINWORD.EXE`).
3. Re-run `pip install --upgrade pywin32`.

### Non-Windows Platforms (macOS / Linux)
On macOS and Linux, CareerForge generates the `.docx` document and falls back to LibreOffice headless conversion:
```bash
libreoffice --headless --convert-to pdf output/Your_Name_CV.docx --outdir output/
```
