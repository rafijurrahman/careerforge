# cv/ — Your Base CV Goes Here

This folder holds your personal CV file. CareerForge reads it as a reference when tailoring applications.

---

## Step 1 — Build Your Base CV (Free Tools)

Pick any free CV builder below and export a clean, ATS-safe PDF:

| Tool | URL | Notes |
|------|-----|-------|
| **FlowCV** | [flowcv.com](https://flowcv.com) | Clean templates, free PDF export |
| **Resume.io** | [resume.io](https://resume.io) | Professional layouts, free tier |
| **Canva** | [canva.com/resumes](https://www.canva.com/resumes) | Design-friendly, free export |
| **Reactive Resume** | [rxresu.me](https://rxresu.me) | 100% free, open-source |
| **CV.co** | [cv.co](https://cv.co) | Simple and fast, free PDF |
| **OpenResume** | [open-resume.com](https://www.open-resume.com) | Open-source, ATS optimized |

> **Recommended:** FlowCV or Reactive Resume. Both export clean, ATS-readable PDFs at no cost.

---

## Step 2 — Export and Save Here

After building your CV, export it as PDF and save it in this folder:

```
CareerForge/
└── cv/
    └── my_base_cv.pdf    ← your file goes here
```

**Naming convention:** `my_base_cv.pdf` (CareerForge looks for this filename by default).
You can use a different name — just update `profile.yaml`:

```yaml
base_cv_path: cv/my_base_cv.pdf
```

---

## Step 3 — What CareerForge Does With It

CareerForge reads your base CV to:
- Extract your existing bullet points as a starting reference
- Understand your formatting preferences
- Compare your content against the job description
- Build a tailored 1-page `.docx` output in `output/`

Your base CV is **never modified**. CareerForge only reads it.

---

## Privacy

This folder is in `.gitignore`. Your CV will **never** be pushed to GitHub.

```
cv/
cv/*.pdf
cv/*.docx
```

---

## Checklist Before Running `python cli.py apply`

- [ ] Base CV PDF is saved as `cv/my_base_cv.pdf`
- [ ] `profile.yaml` is filled out (run `python cli.py setup` if not done)
- [ ] Job description text is ready to paste when prompted
