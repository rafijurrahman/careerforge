# Linguistic Research Foundations

CareerForge's Anti-AI engine is grounded in empirical computational linguistics and peer-reviewed research analyzing Large Language Model artifacts in human-facing text.

---

## 📚 Key Research Papers

### 1. Excess Frequency Spikes in Post-2022 Academic & Professional Writing
* **Authors:** Dmitry Kobak, Rita González-Márquez, et al.
* **Publication:** *Science Advances*, 2024
* **Paper Title:** *"Delving into ChatGPT usage: A statistical analysis of excess vocabulary in scientific writing"*
* **Key Finding:** Proved statistical frequency spikes between 300% and 1,000% in post-2022 corpora for words like *delve*, *intricate*, *pivotal*, *realm*, *tapestry*, *bolster*, and *foster*.
* **Rule Enforcement in CareerForge:** [`AI-001: AI Puffery & Synthetic Vocabulary`](careerforge/data/anti_ai_rules.yaml)

### 2. Nominal Load & Present Participle Suffix Inflation
* **Authors:** Alex Reinhart, Ben Markey, Ronald Yurko, et al.
* **Institution:** Carnegie Mellon University & NJIT
* **Publication:** *Proceedings of the National Academy of Sciences (PNAS)*, 2025
* **Key Finding:** Proved LLMs exhibit heavy nominal load (converting active verbs into Latinate abstract nouns with `-tion`, `-ment`, `-ance`) and append superficial participial clauses (`", ensuring..."`, `", highlighting..."`) at sentence boundaries at rates dramatically exceeding human writing.
* **Rule Enforcement in CareerForge:** [`AI-004: Superficial Present Participle Clause Endings`](careerforge/data/anti_ai_rules.yaml)

### 3. RLHF-Induced Artificial Academic Formality
* **Authors:** Tom S. Juzek & Zina B. Ward
* **Publication:** *Association for Computational Linguistics (ACL)*, 2025
* **Key Finding:** Reinforcement Learning from Human Feedback (RLHF) forces language models into predictable polite formality, characterized by mechanical signposts (*furthermore*, *moreover*, *consequently*, *it is worth noting that*).
* **Rule Enforcement in CareerForge:** [`AI-003: Robotic Transition Signposts`](careerforge/data/anti_ai_rules.yaml)

### 4. Copula Avoidance in LLM Sentence Generation
* **Authors:** Mingmeng Geng & Roberto Trotta
* **Institution:** SISSA & Imperial College London, 2024
* **Key Finding:** Simple copular verbs (*is*, *are*) dropped by over 10% in synthetic text as models artificially inflate sentences using bloated substitutes (*"serves as a"*, *"stands as a"*, *"functions as a"*).
* **Rule Enforcement in CareerForge:** [`AI-002: Copula Avoidance Inflation`](careerforge/data/anti_ai_rules.yaml)

### 5. Wikipedia AI Cleanup Project
* **Guidelines:** `WP:AIVOCAB`, `WP:AINOCOPULA`, `WP:SUPERFICIAL`, `WP:AIPARALLEL`
* **Community Analysis:** Documented recurring pseudo-mythbusting contrast templates (*"not only X, but also Y"*, *"rather than X, Y"*) and uniform metronomic sentence cadences lacking burstiness.
* **Rule Enforcement in CareerForge:** [`AI-005: Negative Parallelisms`](careerforge/data/anti_ai_rules.yaml) and [`CADENCE-001: Sentence Cadence Variance`](careerforge/data/anti_ai_rules.yaml)
