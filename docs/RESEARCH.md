# Linguistic Research Foundations

CareerForge's Anti-AI engine is informed by computational linguistics research analyzing Large Language Model artifacts in human-facing text, combined with practical editorial cleanup heuristics.

---

## 📚 Key Research & Reference Papers

| Paper / Guide | Authors | Venue & Year | DOI / Link | Status |
|---|---|---|---|:---:|
| *"Delving into ChatGPT usage in academic writing through excess vocabulary"* | Dmitry Kobak, Rita González-Márquez, Emőke-Ágnes Horvát, Jan Lause | *Science Advances* / arXiv, 2024 | [arXiv:2406.07016](https://arxiv.org/abs/2406.07016) | **Verified** |
| *"Do LLMs write like humans? Variation in grammatical and rhetorical styles"* | Alex Reinhart, Ben Markey, Michael Laudenbach, Kachatad Pantusen, Ronald Yurko, Gordon Weinberg, David West Brown | *Proceedings of the National Academy of Sciences (PNAS)*, 2025 | [10.1073/pnas.2422455122](https://doi.org/10.1073/pnas.2422455122) | **Verified** |
| *"Why Does ChatGPT 'Delve' So Much? Exploring the Sources of Lexical Overrepresentation in Large Language Models"* / *"Word Overuse and Alignment in LLMs"* | Tom S. Juzek & Zina B. Ward | *ACL Anthology (COLING 2025)* / ECML-PKDD, 2024–2025 | [arXiv:2408.06730](https://arxiv.org/abs/2408.06730) | **Verified** |
| Copula Avoidance in LLM Sentence Generation (`AI-002`) | Mingmeng Geng & Roberto Trotta (Prior Attribution) | SISSA & Imperial College London | *Citation to be verified* | **UNVERIFIED (Heuristic)** |
| Wikipedia AI Cleanup Project (`WP:AIVOCAB`, `WP:AINOCOPULA`, `WP:SUPERFICIAL`, `WP:AIPARALLEL`) | Wikipedia Community Collaborators | Wikipedia Project Guidelines, 2023–2025 | [WP:AI Cleanup](https://en.wikipedia.org/wiki/Wikipedia:WikiProject_AI_Cleanup) | **Verified (Style Guide)** |

---

### 1. Excess Frequency Spikes in Post-2022 Text
* **Authors:** Dmitry Kobak, Rita González-Márquez, Emőke-Ágnes Horvát, Jan Lause
* **Publication:** *Science Advances* / arXiv:2406.07016 (2024)
* **Paper Title:** *"Delving into ChatGPT usage in academic writing through excess vocabulary"*
* **Finding:** Documented anomalous frequency spikes post-2022 across scientific writing for specific vocabulary words such as *delve*, *intricate*, *pivotal*, *realm*, *tapestry*, *bolster*, and *foster*.
* **Rule in CareerForge:** [`AI-001: AI Puffery & Synthetic Vocabulary`](../careerforge/data/anti_ai_rules.yaml)

### 2. Nominal Load & Present Participle Suffix Inflation
* **Authors:** Alex Reinhart, Ben Markey, Michael Laudenbach, Kachatad Pantusen, Ronald Yurko, Gordon Weinberg, David West Brown (Carnegie Mellon University)
* **Publication:** *Proceedings of the National Academy of Sciences (PNAS)*, Vol. 122, No. 8, e2422455122 (2025)
* **Paper Title:** *"Do LLMs write like humans? Variation in grammatical and rhetorical styles"*
* **Finding:** LLMs systematically exhibit higher nominalization rates and append superficial participial clauses (`", ensuring..."`, `", highlighting..."`) at sentence boundaries.
* **Rule in CareerForge:** [`AI-004: Superficial Present Participle Clause Endings`](../careerforge/data/anti_ai_rules.yaml)

### 3. Lexical Overrepresentation & Alignment
* **Authors:** Tom S. Juzek & Zina B. Ward
* **Publication:** *ACL Anthology (COLING 2025)* / ECML-PKDD (2024–2025)
* **Paper Title:** *"Why Does ChatGPT 'Delve' So Much? Exploring the Sources of Lexical Overrepresentation in Large Language Models"*
* **Finding:** Demonstrates how learning from human feedback (RLHF/DPO) and annotator stylistic preferences reinforce formal robotic vocabulary and signposting.
* **Rule in CareerForge:** [`AI-003: Robotic Transition Signposts`](../careerforge/data/anti_ai_rules.yaml)

### 4. Copula Avoidance (Heuristic / Editorial Guide)
* **Status:** **UNVERIFIED CITATION** (Earlier drafts attributed this claim to Geng & Trotta; their published work focuses on human-LLM coevolution and diffusion watermarking rather than copular verb ratios).
* **Finding:** Community editorial observation: substitution of direct copular verbs (*is*, *are*) with bloated multi-word phrases (*"serves as a"*, *"stands as a"*). Retained purely as a stylistic quality heuristic.
* **Rule in CareerForge:** [`AI-002: Copula Avoidance Inflation`](../careerforge/data/anti_ai_rules.yaml)

### 5. Wikipedia AI Cleanup Project
* **Guidelines:** `WP:AIVOCAB`, `WP:AINOCOPULA`, `WP:SUPERFICIAL`, `WP:AIPARALLEL`
* **Community Analysis:** Documented recurring pseudo-mythbusting contrast templates (*"not only X, but also Y"*, *"rather than X, Y"*) and uniform metronomic sentence cadences lacking burstiness.
* **Rule in CareerForge:** [`AI-005: Negative Parallelisms`](../careerforge/data/anti_ai_rules.yaml) and [`CADENCE-001: Sentence Cadence Variance`](../careerforge/data/anti_ai_rules.yaml)
