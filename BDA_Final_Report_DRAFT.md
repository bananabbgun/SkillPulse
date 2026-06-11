# SkillPulse — A Labor-Market Intelligence System for Data/AI Training Providers

**Big Data Systems · Spring 2026 · National Taiwan University**

| | |
|---|---|
| **Author** | `[TODO: your name]` |
| **Student ID** | `[TODO: b1290xxxx]` |
| **GitHub repository** | `[TODO: https://github.com/<you>/skillpulse]` — *must appear on page 1* |
| **Live demo (bonus)** | `[TODO: https://skillpulse.<host>.app]` — *add here if deployed* |
| **Date** | `[TODO]` |

> **How to read this draft.** Everything not marked `[TODO]` is final prose you can keep. Every `[TODO]` block is either (a) a number/figure that only appears after the pipeline runs or interviews happen, or (b) a decision left to you. Section 11 ("Execution Checklist") consolidates *what is left and how to do it*. The report must finally be exported as a single **PDF named `<student_id>.pdf`, in English**, with the GitHub URL on page 1.

---

## Abstract

Raw job postings are abundant and public, but for the people who must decide *what to teach next*, they are unusable in raw form. **SkillPulse** turns the live stream of Taiwan data/AI job postings into a refined, role-resolved picture of which skills the market actually demands right now — with a deliberate lens on how generative-AI skills are being absorbed into established roles. The customer is the **small-to-mid-size vocational training provider** (private bootcamps and government-subsidized course operators), whose revenue and subsidy eligibility depend on aligning curricula to current market demand. The system ingests postings as a stream, refines them through a skill-taxonomy extraction and normalization pipeline, and delivers role-level skill-demand analytics, an "AI-skill premium" comparison, and a curriculum-gap report through a dashboard and API.

---

## 1. Overview and Product Thesis

Data is only valuable once refined into something a specific buyer will pay for. A single job posting is nearly worthless to a curriculum planner; one hundred thousand postings, *cleaned, de-duplicated, mapped to a canonical skill vocabulary, resolved to roles, and differenced against what a course currently teaches*, is decision-grade intelligence.

SkillPulse refines public postings into three answers a training provider needs every cohort:

1. **What skills does the market demand for the roles I train people for, right now?**
2. **How much is the generative-AI shift reshaping those roles** — is "AI" a buzzword or a paid requirement?
3. **Where is the gap between my current curriculum and that demand?**

The unifying technical claim of the project is that the *same* corpus we scrape to **prove demand exists** (Section 4) is the *product's raw material* (Sections 5–6). The data-acquisition work and the system are one effort, not two.

---

## 2. Target Customer (Required Component 1)

### 2.1 The segment

**Primary customer: small-to-mid-size vocational training providers in Taiwan that train people for data/AI roles** — private coding/AI bootcamps and operators of government-subsidized vocational courses (e.g., units running classes under the Ministry of Labor's *Industry Elite Pioneer Program*, 產業新尖兵計畫).

This is deliberately **not** "schools." Public universities are slow-moving and their funding is not tied to placement outcomes, so their willingness to continuously re-tune curricula to the market is structurally low. The right wedge is the operator **whose money depends on placement rate and on justifying course design to a subsidy reviewer**.

### 2.2 The job they are trying to do today, and their workaround

Every cohort, a training provider must decide which skills to teach and must justify that choice in three places: the **subsidy application** (course must align with national 5+2 industry priorities and market demand), the **marketing page** ("learn the most in-demand skills"), and the **curriculum design meeting**. Today they do this with: ad-hoc manual browsing of job boards, periodic but lagging survey reports (e.g., the Institute for Information Industry's AI-talent surveys, built from ~146 questionnaires and 8 interviews — slow, coarse, and already dated on release), and gut feel from instructors.

### 2.3 Why SkillPulse beats the status quo

| Dimension | Status quo (manual / survey reports) | SkillPulse |
|---|---|---|
| Freshness | Quarterly/annual, lagging | Continuously updated from live postings |
| Granularity | Occupation-level | Individual skill-level, role-resolved |
| AI-shift visibility | Narrative ("AI is important") | Quantified penetration + salary premium |
| Actionability | None tied to *their* curriculum | Direct curriculum-gap map |

### 2.4 Evidence this customer is real and active

- The Ministry of Labor's development agency ran **~1,200 AI cross-domain training classes over two years with >80% post-training placement**, and the program explicitly invites trade associations and colleges to design courses that "respond to future industry and market demand." That instruction *is* a standing, recurring demand for exactly our data. (Source: wda.gov.tw)
- Under the *Industry Elite Pioneer Program*, courses must conform to 5+2 industry priorities; training units include foundations, trade/industry associations, and colleges — i.e., many small operators without in-house data teams. (Source: wda.gov.tw / mol.gov.tw)
- Private operators already market on skill demand (e.g., 聯成電腦 publishes "which jobs are short-staffed in 2026" recruitment content), proving they need ammunition our product supplies. (Source: lccnet.com.tw)

`[TODO — STRENGTHENS COMPONENT 1: add 3–5 sentences from your own interviews (Section 4.4) naming a real operator and the exact decision they struggle with.]`

---

## 3. Scope: The Data/AI Job Cluster

We do not analyze "all jobs." We analyze one coherent **job cluster** defined as a value chain whose roles share a single skill vocabulary (Python · SQL · data · ML), so that **one taxonomy serves all of them**. The boundary is the point at which the vocabulary stops overlapping.

**Core cluster (analysis target), placed along the data → analysis → modeling → production chain:**

| Value-chain stage | Roles in cluster |
|---|---|
| Data engineering | Data Engineer |
| Analysis & insight | Data Analyst (technical), Data Scientist |
| Modeling | ML Engineer, Algorithm Engineer |
| Production & application | AI Engineer / AI Application Engineer |
| *(cross-cutting skill layer, stages 3–4)* | **MLOps** — treated as a skill layer, not a separate title bucket |

**Control group (scraped, but NOT a cluster member): Backend Engineer.** Backend shares infrastructure vocabulary with Data Engineering but its core (web frameworks, microservices) diverges from the ML spine. We keep it as a deliberate **non-AI baseline** for the cross-sectional AI-premium comparison in Section 6.

**Excluded (disjoint vocabulary):** Frontend, Mobile (iOS/Android), MIS/IT-support, Hardware/Firmware, IC Design, Security. (IC design leads Taiwan salary tables in 2026, but its vocabulary — Verilog, EDA — is disjoint; including it would dilute the AI signal.)

> **Figure 1 — Scope diagram (cluster boundary).** `[TODO: insert the scope figure you are generating in Claude Design. This is the boundary/value-chain figure, distinct from the system architecture figure in Section 5.]`

---

## 4. Evidence of Demand and Willingness to Pay (Required Component 2 — highest-weighted)

This section documents the **full acquisition process**, not just conclusions.

### 4.1 The "data = evidence = product" argument

Our demand evidence is generated by the same scrape that feeds the product. We establish demand through (a) public-posting-scale evidence, (b) competitor pricing anchors, and (c) targeted customer interviews. (a) is the load-bearing evidence; (c) corroborates it.

### 4.2 Public-data evidence (scale + market signal)

Independent, citable signals that the underlying demand exists and is shifting:

- **Cake** estimates Taiwan's IT-services sector needs ~**4,500 new AI professionals per year**, with the fastest growth in five emerging roles: AI application engineer, domain-application engineer, data engineer, AI/data scientist, AI project manager. (Source: cake.me)
- **Business Next (數位時代), 2026:** software-engineering postings fell ~5% YoY, but **the share mentioning AI reached ~33% — now a baseline expectation**; data scientist median annual pay NT$1.112M and algorithm engineer NT$1.066M entered the "million-NT club." AI hiring has moved "from pilot to scale," with employers wanting people who connect models to business outcomes. (Source: bnext.com.tw)
- **Institute for Information Industry, 2025–2027 AI-talent report:** the generative-AI wave could shift work content and required skills by up to **65%**, and unusually hits high-skill/high-education roles too; **56.1% of firms report a talent-supply shortfall**. (Source: ndc.gov.tw / iii)

`[TODO — CORE DELIVERABLE: replace this line with YOUR scraped figures once the pipeline runs: total postings collected, postings per cluster role, and the AI-penetration rate you measure (your own role-resolved version of the "33%" headline). These charts (Section 6) ARE your strongest demand evidence.]`

### 4.3 Willingness-to-pay anchors

We triangulate WTP from analogous paid products and from the money at stake per cohort:

| Anchor | Figure | What it tells us |
|---|---|---|
| 比薪水 (salary.tw) VIP | One-time paid unlock; credit packs ~NT$150 / 100 credits; analogous site 面試趣 VIP ~NT$690 | Individuals already pay for far thinner labor data → B2B value is higher |
| Lightcast (global analog) | Enterprise, quote-based subscription | A whole industry monetizes exactly this analytics category |
| Coding bootcamp tuition | < ~NT$40,000 per student (e.g., 聯成) | Revenue scale a single cohort represents |
| Gov subsidy per trainee (Elite Pioneer) | Up to **NT$100,000** training fee + up to **NT$96,000** stipend = up to **NT$196,000 per trainee** | The money a provider is fighting to qualify for — the decision SkillPulse de-risks |

**Derived WTP hypothesis:** A provider running cohorts of ~20 trainees with up to ~NT$196k of subsidy flowing per trainee is making a six-to-seven-figure decision each cohort. A report/subscription that materially improves course-market fit and subsidy-approval odds is plausibly worth a **few thousand NT$/month** (per-report or subscription). `[TODO: tighten this number with interview data in 4.4 — ask directly what they'd pay.]`

### 4.4 Customer interviews (process + instrument)

We interview 5–8 course planners / subsidy-application owners at small-mid training providers. The instrument is in **Appendix B**. `[TODO — ONLY YOU CAN DO THIS: conduct the interviews and paste a response summary here: how they decide what to teach, what they use today, the worst part of the process, and a concrete WTP figure. This is the part graders most reward and that cannot be fabricated.]`

### 4.5 Data-acquisition methodology (reproducible)

Reproducible steps (scripts in `repo/ingestion/`, see Section 9):
1. Enumerate cluster + control job categories on 104 / Cake.
2. Pull postings via the boards' JSON list endpoints (104 exposes an XHR `list` endpoint requiring a `Referer` header); Playwright fallback for JS-heavy pages.
3. Persist raw JSON to the document store; land normalized Parquet to the lake.
4. Re-run nightly to accumulate a longitudinal record. (Reproduction script: `repo/ingestion/collect.py`.)

---

## 5. System Design

### 5.1 Data sources

| Source | What we ingest | How |
|---|---|---|
| 104 人力銀行 | Postings for cluster + control roles: title, company, JD text, required skills, salary (when numeric), location, posted date | JSON `list` XHR endpoint (+ `Referer`); detail fetch per job |
| Cake (cake.me) | Same fields, especially AI-titled roles | Playwright (JS-rendered) |
| 1111 / Yourator *(optional, breadth)* | Same | Scraper |
| Gov salary reference (DGBAS 薪情平臺) | Authoritative salary distributions for sanity-checking | Public download |
| Training-provider syllabi (public) | Course skill lists for gap analysis | Manual + `web_fetch` |

### 5.2 Technology stack and why (mapped to course paradigms)

The honest fact first: this corpus is **hundreds of thousands of postings, not petabytes** — it is not "big" by volume. We therefore justify each big-data component by **velocity (a continuous posting stream), variety (heterogeneous multi-source JSON/HTML), and forward scalability**, and we make the 10×/100× argument explicit in Section 8. The architecture is the smallest design that is *genuinely* a streaming-plus-batch big-data pipeline rather than a single script.

| Layer | Choice | Why this, why appropriate |
|---|---|---|
| Orchestration | **Apache Airflow** | DAG scheduling of scrape→land→process→publish; canonical batch-orchestration paradigm |
| Ingestion / streaming | **Apache Kafka** (topic `raw-postings`) | New postings modeled as events → legitimate message-queue + stream-processing paradigm; decouples scrapers from processing. (Single-broker / Redpanda is fine for the demo.) |
| Raw landing / data lake | **Parquet on MinIO** (S3-compatible) | Distributed-file-system lineage; columnar storage for analytics |
| Document store (NoSQL) | **MongoDB** | Schema-flexible raw posting JSON across heterogeneous sources |
| Batch processing | **Apache Spark (PySpark)** | De-dup, skill extraction, aggregation; the canonical distributed batch engine; horizontally scalable for the 100× case |
| Stream processing | **Spark Structured Streaming** consuming Kafka | Incremental processing of incoming postings |
| Skill normalization | Taxonomy dictionary match **+ LLM canonicalization pass** | Maps `LLM`/`大型語言模型`/`GPT`/`生成式AI` → one canonical skill; the core "refinement" step |
| Serving store (SQL/OLAP) | **PostgreSQL** (or DuckDB) | Aggregated "marts" feeding dashboard/API; OLAP-style queries |
| Delivery | **FastAPI** (query API) + **Streamlit** (read-only dashboard) | API and dashboard delivery channels |
| Repro / deploy | **Docker Compose**; deploy dashboard to Streamlit Cloud / Render / Fly.io | One-command reproduction; bonus deployment |

### 5.3 Processing pipeline (the refinement logic)

1. **Skill extraction + normalization.** For each JD, match against the taxonomy dictionary (Appendix A; bilingual synonyms), normalize to canonical skills tagged by facet (1–8). **Buzzword filter:** a facet-5 (GenAI) term counts only if it appears in a requirement/skill context, not merely in company boilerplate. Output: a skill vector + facet flags per posting. *(This step is the project's central "raw → refined" value.)*
2. **Role classification by skill fingerprint.** Assign each posting to one of the six cluster sub-roles using its skill vector (nearest-prototype / lightweight classifier). **Job titles are a weak prior only** — Taiwan titles are inconsistent (a posting titled "AI Engineer" may functionally be a data engineer).
3. **AI penetration.** Define a posting as *AI-inflected* if it contains ≥1 facet-5 or facet-6 skill. Compute the AI-inflected share per role and for the whole cluster.
4. **Cross-sectional AI premium.** Within each role, compare AI-inflected vs non-AI postings on salary and skill count. Use numeric salaries only (drop "面議"/negotiable). The **Backend control group** is the non-AI baseline against which the cluster premium is interpreted.
5. **Skill co-occurrence / bundles.** Compute co-occurrence of AI-era skills with foundational skills (e.g., LLM×SQL, RAG×Python) to show AI skills are *bundled into* roles, not optional add-ons. Single-snapshot; no time series needed.
6. **Curriculum-gap analysis.** Map a real public syllabus onto the taxonomy, overlay on market demand frequency, and surface "high-demand-but-not-taught" skills (especially AI-era).

### 5.4 Delivery

A read-only **Streamlit dashboard** (role selector → demand charts, AI-premium, gap map) plus a **FastAPI** endpoint (e.g., `GET /skills?role=data_engineer` returns ranked skills with demand and AI-flag) for the "API delivery" requirement.

> **Figure 2 — End-to-end system architecture.** `[TODO: insert the SYSTEM architecture figure (ingestion→storage→processing→delivery). This is a SECOND, different diagram from Figure 1. A ready-to-paste Claude Design prompt is in Appendix C.]`

---

## 6. Analysis Method and Results

Method is specified; figures populate once the pipeline runs. Each figure doubles as product output and as demand evidence (Section 4).

| # | Figure | Claim it earns |
|---|---|---|
| 1 | AI-penetration rate per role (bar/heatmap) | "AI is now baseline across the whole cluster" — cross-sectional proof of the demand shift |
| 2 | AI-premium: AI vs non-AI salary & skill count per role, with Backend as a control lane | "AI skills carry a measurable premium" — the money chart |
| 3 | Top-skill ranking / co-occurrence network for the focus role (AI-era skills highlighted) | "AI skills are bundled into the role, not optional" |
| 4 | Curriculum-gap map (x = market demand frequency, y/color = taught or not) | The actionable gap — justifies WTP |

`[TODO — CORE DELIVERABLE: generate Figures 1–4 from your scraped data and write 1–2 sentences of interpretation under each. Until then these are method-only.]`

**Honesty notes to keep in the report (do not hide):**
- *Salary sparsity:* many postings list salary as "negotiable," shrinking Figure 2's sample — report n and confidence intervals, and use *skill count* as a robustness proxy.
- *Seniority confound:* senior roles tend to be both more AI-heavy and higher-paid; stratify by seniority where the JD allows, otherwise state the limitation explicitly.
- *Snapshot aging:* a snapshot dates quickly — a feature for a subscription product, immaterial for the demo; the longitudinal value is argued under scalability (Section 8).

---

## 7. Go-to-Market Difficulties (Bonus Component 3)

- **Data-acquisition legality / ToS.** Scraping job boards engages Taiwan's Copyright Act, Personal Data Protection Act, and each board's terms; community tutorials explicitly restrict scraped data to *non-commercial learning use*. As an academic project this is defensible; **as a business, SkillPulse must migrate from scraping to licensed API / data partnership** (104 offers API access). We treat this scrape→license path as the central operational risk, not an afterthought.
- **Trust vs incumbents.** 104 runs an AI-career platform, Cake has AI sections, and III publishes AI-talent reports. We cannot out-scale them; we differentiate on *continuous + skill-granular + tied to the training-provider curriculum-gap use case + localized*. The III survey method (146 questionnaires) is our foil: we are posting-based, always-fresh, and skill-level.
- **Moat / who else could do this.** The biggest threat is the boards themselves (they own the data). Our defensibility is vertical depth, taxonomy quality, and freshness — the same moat Lightcast relies on. Large training units (III, ITRI, iSpan) have in-house capability; our wedge is explicitly the **small-mid operator without a data team**.
- **Cold start.** Offer free first reports in exchange for case studies to seed credibility.
- **Unit economics.** Scraping + processing are low marginal cost; main costs are LLM normalization calls and maintenance. See Section 8.

---

## 8. Scalability and Cost (Bonus)

**At 10×/100×** (more sources, regions, longer history, more verticals): Kafka partitions and Spark executors scale horizontally; the data lake (Parquet/object storage) is natively scalable; the serving store moves Postgres → ClickHouse/BigQuery; LLM normalization is the cost driver and is mitigated by caching canonicalizations (each skill string is normalized once, then cached). The **longitudinal value compounds**: with a year of accumulated snapshots, the system delivers true skill-trend tracking that a one-semester scrape cannot — this is where the cross-sectional product becomes a time-series product.

**Cost sketch (demo scale):** `[TODO: fill rough monthly figures — VM/compute, object storage, LLM-call cost for normalization. Provide a back-of-envelope per-1k-postings normalization cost.]`

---

## 9. Deliverables and Repository

**Repository layout (proposed):**
```
skillpulse/
├── README.md                  # run locally + access deployed demo
├── docker-compose.yml         # Kafka, MinIO, MongoDB, Postgres, Airflow, app
├── ingestion/                 # scrapers + repro data-collection scripts
│   ├── collect.py
│   └── sources/{job104.py,cake.py}
├── taxonomy/skills_v1.yaml    # canonical skill dictionary (Appendix A)
├── processing/                # PySpark jobs: extract, classify, aggregate
├── analysis/                  # figure-generation notebooks/scripts
├── api/                       # FastAPI service
├── dashboard/                 # Streamlit app
└── data/sample/               # small sample dataset for graders
```
**README must include:** one-command local run, deployed URL, and reproduction of the data-collection step. `[TODO — repro is explicitly graded: ensure collect.py runs end-to-end from a clean clone.]`

---

## 10. Limitations and Ethics

Scraped data is used for academic analysis with rate-limiting and respect for robots.txt; no personal data of individuals is collected (postings are company-published). Salary inference is associational, not causal — we never claim AI "destroyed" any role, only that AI skills *co-occur with* higher pay. Conclusions are bounded by the snapshot window and by salary sparsity.

---

## 11. Execution Checklist — What Is Left and How To Do It

**Legend:** 🟢 already done (design) · 🔵 I (assistant) can produce · 🟡 only you can do · ⬜ decision.

### A. Decisions to lock (⬜ — unblock everything else)
- ⬜ **Final scope cut:** minimum-viable deliverable vs. bonus features (recommended MVP below).
- ⬜ **Focus role for the demo** (recommend: *Data Engineer* or *ML Engineer* — densest, cleanest signal). I can recommend; you confirm.

### B. Only you can do (🟡 — not transferable)
- 🟡 **Run the scrapers against the live sites.** I cannot reach 104/Cake from my environment. I write the code; you run it and paste back errors for me to fix. You also judge scrape-rate/ToS risk.
- 🟡 **Conduct the 5–8 interviews** (instrument in Appendix B). Paste a response summary into §4.4 and a concrete WTP number into §4.3.
- 🟡 **Deploy** the dashboard to your account (Streamlit Cloud/Render/Fly.io).
- 🟡 **Identity/logistics:** create the GitHub repo, put its URL on page 1, name the final PDF `<student_id>.pdf`, submit.

### C. I can produce next (🔵 — you review)
- 🔵 **Taxonomy dictionary file** `skills_v1.yaml` (8 facets, bilingual synonyms, facet tags) — *ready to generate now*.
- 🔵 **Scraper code** for 104 + Cake (best-effort; you run it).
- 🔵 **PySpark processing pipeline** (extract → normalize → classify → aggregate, all 6 steps).
- 🔵 **Figure-generation scripts** for Figures 1–4.
- 🔵 **FastAPI + Streamlit** delivery apps.
- 🔵 **docker-compose.yml + README** (reproducibility).
- 🔵 **Appendix C system-architecture diagram prompt** for Claude Design (already drafted below).
- 🔵 **Fetch a public syllabus** (Elite Pioneer / bootcamp) for the Figure-4 gap analysis.
- 🔵 **Finalize all English prose** once real numbers land.

### Dependency note
Most 🔵 items I can *scaffold* immediately with placeholders, but their *content quality* depends on 🟡 items B1 (real scraped data) and B2 (real interviews). The efficient path: I build the entire pipeline/dashboard/report skeleton; you spend your effort only on the two irreplaceable tasks (scraping + interviews).

### Recommended Minimum-Viable Deliverable (defensible on its own)
Scrape one cluster + the backend control → extract & normalize skills → **Figure 1 (AI penetration)** + **Figure 2 (AI premium)** → a working dashboard → README that reproduces collection. This alone carries the 40% (system) + 25% (evidence) core. Everything else (Figures 3–4, full GTM, 10×/100×, larger interview set, deployment) is additive bonus.

---

## Appendix A — Skill Taxonomy v1

Eight facets; ★ marks the "AI-era signal" layer used to measure the AI shift. **This v1 is a hypothesis to validate against scraped JDs** (top-down seed, then bottom-up reconciliation: add missed skills, filter buzzwords, canonicalize synonyms).

| # | Facet | Example canonical skills |
|---|---|---|
| 1 | Languages | Python (spine), SQL (spine), R, Scala, Bash |
| 2 | Data processing / storage | pandas, Spark, ETL/ELT, Airflow, dbt, data warehouse (BigQuery/Snowflake), NoSQL |
| 3 | Classical ML | scikit-learn, XGBoost, statistics, feature engineering, A/B testing, experiment design |
| 4 | Deep-learning frameworks | PyTorch, TensorFlow, CNN/RNN/Transformer |
| 5 | ★ Generative AI / LLM | LLM, RAG, prompt engineering, fine-tuning/LoRA, vector DB (pgvector/Milvus), embeddings, LangChain/LlamaIndex, agents, model APIs (OpenAI/Claude/Gemini) |
| 6 | ★ MLOps / deployment | Docker, Kubernetes, model serving (FastAPI/Triton/BentoML), MLflow/W&B, CI/CD, model monitoring, feature store |
| 7 | Cloud | AWS/GCP/Azure + ML services (SageMaker/Vertex/Azure ML) |
| 8 | BI / business | Tableau/Power BI/Looker, dashboards, domain knowledge, "connect model to business outcome" (qualitative theme) |

*Canonicalization example:* `LLM`, `大型語言模型`, `GPT`, `生成式AI`, `genAI` → **`llm`** (facet 5).

---

## Appendix B — Interview / Survey Instrument

**Target respondent:** course planner or subsidy-application owner at a small/mid training provider.

**Screening:** Do you decide or influence which skills a course teaches? Do you prepare subsidy applications?

**Core questions:**
1. Walk me through how you decided the curriculum for your most recent data/AI course. Who decided, based on what?
2. What sources did you use to judge "what the market wants"? How fresh were they?
3. When you apply for subsidy, how do you demonstrate the course matches market demand?
4. What's the most painful/uncertain part of getting curriculum-market fit right?
5. Have you ever taught something that turned out to be off-market, or missed something hot? What did it cost you (enrollment, placement, subsidy)?
6. If a tool gave you a fresh, role-level skill-demand list plus a gap analysis against your syllabus, where would it fit your workflow?
7. What would you pay for that — per report, or monthly subscription? At what price would it be a clear yes? A clear no?
8. What would make you *not* trust it?

**Capture:** for §4.3, record at least one explicit price point per respondent.

---

## Appendix C — Claude Design Prompt for the SYSTEM ARCHITECTURE Diagram (Figure 2)

> Note: this is the **second** diagram (data flow), different from the scope diagram (Figure 1).

```text
Create a clean, professional end-to-end SYSTEM ARCHITECTURE diagram for an academic
Big Data Systems final-project report. English labels. Left-to-right data flow,
landscape, export-ready for a PDF report. Group nodes into four labeled stages.

TITLE: "SkillPulse — End-to-End Architecture"

STAGE 1 — INGESTION
- "Scrapers (104 / Cake)" → emits events to
- "Apache Kafka — topic: raw-postings"
- Orchestrated by "Apache Airflow" (show as a scheduler controlling the flow)

STAGE 2 — STORAGE
- "MongoDB (raw JSON, NoSQL)"
- "Data Lake — Parquet on MinIO"

STAGE 3 — PROCESSING (Apache Spark)
- "Spark Structured Streaming (incremental)"
- "Skill Extraction + Taxonomy match"
- "LLM Normalization (canonical skills)"
- "Role Classification (skill fingerprint)"
- "Aggregation → marts"
- output to "PostgreSQL (serving / OLAP)"

STAGE 4 — DELIVERY
- "FastAPI (query API)"
- "Streamlit Dashboard (read-only)"
- end node: "Customer: training provider"

ANNOTATIONS
- Small italic note under Stage 1: "new postings modeled as a stream (velocity)"
- Small italic note under Stage 3: "the 'raw → refined' core"
- Show all containers wrapped by a thin dashed box labeled "Docker Compose"

STYLE: modern, restrained, academic. One accent color for the processing stage
(the core value), neutral elsewhere. Clear arrows, generous whitespace, legible
sans-serif, no decorative icons. Must read clearly at half-page landscape scale.
```

---

## References (to format properly in the final PDF)

- Business Next (數位時代), 2026 — Taiwan tech jobs shift to chip design & AI; AI share of software postings, salary medians.
- Cake (cake.me) — AI jobs campaign; ~4,500 new AI professionals/yr; five emerging roles.
- Institute for Information Industry / National Development Council — 2025–2027 AI-talent demand report (65% skill-shift; 56.1% shortage).
- Ministry of Labor, Workforce Development Agency — Industry Elite Pioneer Program; ~1,200 AI classes, >80% placement; subsidy amounts.
- salary.tw (比薪水) — VIP/credit pricing; product model.
- Lightcast — labor-market intelligence (global analog; AI-skill premium reporting).
- 104 / community sources — posting JSON endpoints; scraping legal considerations (Copyright Act, PDPA, ToS).

`[TODO: convert to a consistent citation style and add access dates for the final PDF.]`
