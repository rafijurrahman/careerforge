# CareerForge System Architecture

CareerForge is designed as a modular, local-first engine composed of three core subsystems:
1. **The Ingestion & Normalization Layer:** Loads user profiles and scrapes public job boards.
2. **The Verification & Audit Layer:** Enforces 1-page document constraints and linguistic compliance.
3. **The Document Generation Layer:** Produces ATS-safe `.docx` and verified `.pdf` output.

---

## 🏛️ System Component Diagram

```mermaid
graph TD
    User([User CLI / forge]) --> CLI[careerforge/cli.py]
    
    subgraph Data & Storage
        Profile[(profile.yaml)]
        Skills[(careerforge/data/skills.yaml)]
        Rules[(careerforge/data/anti_ai_rules.yaml)]
    end

    subgraph Core Engine
        Loader[Profile Loader & Normalizer]
        Optimizer[1-Page Page Optimizer]
        CVBuilder[Universal docx Builder]
        Auditor[Anti-AI Linguistic Engine]
    end

    subgraph PDF Backends
        LibreOffice[LibreOffice Headless<br/>Cross-Platform Default]
        WordCOM[Microsoft Word COM<br/>Windows Fast-Path]
    end

    subgraph Scrapers Plugin Layer
        BaseScraper[BaseScraper ABC]
        GH[Greenhouse Scraper]
        Ashby[Ashby Scraper]
        Remotive[Remotive Scraper]
    end

    CLI --> Loader
    Loader --> Profile
    CLI --> Auditor
    Auditor --> Rules
    CLI --> Optimizer
    Optimizer --> CVBuilder
    Optimizer --> LibreOffice
    Optimizer --> WordCOM
    CLI --> BaseScraper
    BaseScraper --> GH
    BaseScraper --> Ashby
    BaseScraper --> Remotive
    
    CVBuilder --> OutputDocx[(output/Candidate_CV.docx)]
    Optimizer --> OutputPDF[(output/Candidate_CV.pdf)]
```

---

## 🔄 Execution Flow

### 1. The 1-Page Document Auto-Fitting Loop
```mermaid
sequenceDiagram
    participant User
    participant Optimizer as page_optimizer.py
    participant Builder as cv_builder.py
    participant Backend as PDF Engine (LibreOffice / Word COM)

    User->>Optimizer: forge apply --pages 1
    loop Grid Search (Font Scale 1.06 -> 0.92, Margins 0.30 -> 0.20)
        Optimizer->>Builder: build_universal_cv(font_scale, spacing_scale)
        Builder-->>Optimizer: output.docx written
        Optimizer->>Backend: convert_to_pdf_and_count_pages(docx)
        Backend-->>Optimizer: page_count
        alt page_count == 1
            Optimizer-->>User: 1-Page verified output!
        end
    end
```

### 2. The Anti-AI Linguistic Audit Pipeline
```mermaid
sequenceDiagram
    participant CLI as forge audit
    participant Engine as anti_ai_engine.py
    participant Rules as anti_ai_rules.yaml

    CLI->>Engine: audit_text(content)
    Engine->>Rules: Load rules (AI-001 to AI-005)
    Engine->>Engine: Regex pattern evaluation
    Engine->>Engine: Sentence cadence variance (burstiness)
    Engine-->>CLI: Findings report + Exit code (0=Pass, 1=Fail)
```
