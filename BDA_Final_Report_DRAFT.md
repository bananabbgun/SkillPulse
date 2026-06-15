# SkillPulse — A Labor-Market Intelligence System for Data/AI Training Providers

**Big Data Systems · Spring 2026 · National Taiwan University**

| | |
|---|---|
| **Author** | `蔡侑岑` |
| **Student ID** | `b12902026` |
| **GitHub repository** | `https://github.com/bananabbgun/SkillPulse` |
| **Live demo (bonus)** | `https://skillpulse-gslw7hdztc85xs3qp3qihn.streamlit.app` |
| **Date** | `2026-06-15` |

> **Reading guide.** §1–§4 cover the product thesis, target customer, scope, and demand evidence (Required Components 1 and 2). §5–§6 cover the technical system, the four-stage refinement pipeline, and the analytical results (Figures 3–5 produced from the live scrape; Figure 6 specified as method only). Figures 1 and 2 are the scope and architecture diagrams in §3 and §5. §7 (GTM) and §8 (scalability + cost) address the optional bonus components. §11 lists what this iteration ships vs what is deliberately deferred to a follow-up iteration.

---

## Abstract

Raw job postings are abundant and public, but for the people who must decide *what to teach next*, they are unusable in raw form. **SkillPulse** turns the live stream of Taiwan data/AI job postings into a refined, role-resolved picture of which skills the market actually demands right now — with a deliberate lens on how generative-AI skills are being absorbed into established roles. The customer is the **small-to-mid-size vocational training provider** (private bootcamps and government-subsidized course operators), whose revenue and subsidy eligibility depend on aligning curricula to current market demand. The system ingests postings, refines them through a skill-taxonomy extraction and normalization pipeline, and delivers role-level skill-demand analytics and an "AI-skill premium" comparison through a read-only Streamlit dashboard.

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

- The Ministry of Labor's development agency ran **~1,200 AI cross-domain training classes over two years with >80% post-training placement**, and the program explicitly invites trade associations and colleges to design courses that "respond to future industry and market demand." That instruction *is* a standing, recurring demand for exactly our data. (Ministry of Labor, 2025)
- Under the *Industry Elite Pioneer Program*, courses must conform to 5+2 industry priorities; training units include foundations, trade/industry associations, and colleges — i.e., many small operators without in-house data teams. (Industry Elite Pioneer Program, 2026)
- Private operators already market on skill demand (e.g., 聯成電腦 publishes "which jobs are short-staffed in 2026" recruitment content), proving they need ammunition our product supplies. (聯成電腦, 2026)

Together, these three signals — a government program with an active subsidy budget, a regulatory requirement that courses align to declared industry priorities, and incumbent operators already marketing on demand — establish that the buyer exists and has a recurring, money-backed reason to consume role-resolved skill-demand intelligence. The willingness-to-pay anchors in §4.3 then size what they would plausibly spend on it.

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

![Figure 1 — Scope diagram of the data/AI job cluster: roles arranged along the data → analysis → modeling → production value chain, the AI-era zone (Generative AI / LLM / MLOps) called out as a skill layer rather than a separate role, the Backend Engineer marked as a non-AI control group, and disjoint-vocabulary roles excluded with a single inclusion rule.](docs/figures/BDAfinal_scope-1.png)

**Figure 1.** Scope diagram showing the cluster boundary and the position of each role on the value chain. The AI-era band (Stages 3–4) is the analytical focus; the Backend Engineer is retained as a non-AI baseline; the bottom-right tile lists roles excluded by the disjoint-vocabulary rule.

---

## 4. Evidence of Demand and Willingness to Pay (Required Component 2 — highest-weighted)

This section documents the **full acquisition process**, not just conclusions.

### 4.1 The "data = evidence = product" argument

Our demand evidence is generated by the same scrape that feeds the product. We establish demand through two independent strands: (a) **third-party, citable signals** about the size and direction of the AI-talent shift (Cake's labour-market estimate, Business Next's coverage, the Institute for Information Industry's shortage figure), and (b) **our own role-resolved scrape**, which lets us reproduce the same headline at finer granularity directly from live job postings rather than from a quarterly survey. The two strands corroborate each other: when 562 directly-scraped postings yield the same "AI-is-baseline" gradient that the III and Business Next reports describe in aggregate, the demand signal is robust to source. Willingness-to-pay (§4.3) is anchored against analogous paid products and against the subsidy money at stake per training cohort.

### 4.2 Public-data evidence (scale + market signal)

Independent, citable signals that the underlying demand exists and is shifting:

- **Cake** estimates Taiwan's IT-services sector needs ~**4,500 new AI professionals per year**, with the fastest growth in five emerging roles: AI application engineer, domain-application engineer, data engineer, AI/data scientist, AI project manager. (Cake, 2025)
- **Business Next (數位時代):** software-engineering postings fell ~5% YoY, but **the share mentioning AI reached ~33% — now a baseline expectation**; data scientist median annual pay NT$1.112M and algorithm engineer NT$1.066M entered the "million-NT club." AI hiring has moved "from pilot to scale," with employers wanting people who connect models to business outcomes. (Business Next, 2026)
- **Institute for Information Industry**: the generative-AI wave could shift work content and required skills by up to **65%**, and unusually hits high-skill/high-education roles too; **56.1% of firms report a talent-supply shortfall**. (Institute for Information Industry, 2025)

**Our own scrape (the load-bearing evidence).** We collected **562 postings** from two job boards (**104: 382, Cake: 180**) across 25 keyword searches spanning the six cluster roles plus the backend control. After skill-fingerprint role classification, the dataset breaks down as follows:

| Role | Postings | AI-inflected | AI share |
|---|---:|---:|---:|
| Data Engineer (MVP focus) | 68 | 20 | **29 %** |
| Data Analyst | 118 | 8 | 7 % |
| Data Scientist | 83 | 30 | 36 % |
| ML Engineer | 89 | 52 | **58 %** |
| Algorithm Engineer | 21 | 3 | 14 % |
| AI Engineer | 69 | 69 | **100 %** |
| Backend Engineer (control) | 64 | 12 | **19 %** |
| Other (off-cluster) | 50 | 0 | 0 % |
| **Total cluster (six roles)** | **448** | **182** | **41 %** |

**Across the six-role data/AI cluster (n = 448 postings), 41 % are AI-inflected, compared with 19 % in the backend control (n = 64).** A direct headline-vs-headline comparison with Business Next's "~33 %" is not quite an apples-to-apples — their 33 % is over *all software-engineering postings*, a much broader denominator, whereas our 41 % is computed over the deliberately narrowed data/AI cluster (one would *expect* a more AI-skewed denominator to read higher than a general-software one). What our number adds, beyond confirming that AI is now a baseline expectation rather than a niche, is the **role-by-role gradient: penetration scales monotonically with proximity to model production**, exactly the structure a curriculum planner needs to act on. The full per-role breakdown sits inside the cluster, and is what §6 (Figure 3) plots in detail.

### 4.3 Willingness-to-pay anchors

We triangulate WTP from analogous paid products and from the money at stake per cohort:

| Anchor | Figure | What it tells us |
|---|---|---|
| 比薪水 (salary.tw) VIP | One-time paid unlock; credit packs ~NT$150 / 100 credits; analogous site 面試趣 VIP ~NT$690 | Individuals already pay for far thinner labor data → B2B value is higher |
| Lightcast (global analog) | Enterprise, quote-based subscription | A whole industry monetizes exactly this analytics category |
| Coding bootcamp tuition | < ~NT$40,000 per student (e.g., 聯成) | Revenue scale a single cohort represents |
| Gov subsidy per trainee (Elite Pioneer) | Up to **NT$100,000** training fee + up to **NT$96,000** stipend = up to **NT$196,000 per trainee** | The money a provider is fighting to qualify for — the decision SkillPulse de-risks |

**Derived WTP hypothesis (analog-based).** A provider running cohorts of ~20 trainees with up to ~NT$196k of subsidy flowing per trainee is making a six-to-seven-figure decision each cohort. Triangulating against the anchors above — individuals already pay NT$150–690 for thinner labour data, and a global analog (Lightcast) monetises exactly this analytics category as an enterprise subscription — a B2B report or subscription that materially improves course-market fit and subsidy-approval odds is plausibly worth on the order of **a few thousand NT$ per provider per month**.

The unit-economics implication is checked against the §8 cost sketch: at a single-customer monthly run-cost of ≈ NT$1,900 (MVP scale), break-even on a NT$3,000-per-month subscription occurs at customer #1, and the business scales on customer count rather than infrastructure depth.

### 4.4 Data-acquisition methodology (reproducible)

Reproducible steps (scripts in `repo/ingestion/`, see Section 9):
1. Enumerate cluster + control job categories on 104 / Cake.
2. Pull postings via the boards' JSON list endpoints (104 exposes an XHR `list` endpoint requiring a `Referer` header); Playwright fallback for JS-heavy pages.
3. Persist raw JSON to the document store; land normalized Parquet to the lake.
4. **This iteration produces a single cross-sectional snapshot** (562 unique postings collected during the project window). The collector is designed to be re-run on a cadence — every run appends to the JSONL event log, so accumulating a longitudinal record over multiple runs is a matter of scheduling, not architecture; we discuss the longitudinal value in §8 and do not claim it as a property of this iteration. (Reproduction script: `repo/ingestion/collect.py`.)

---

## 5. System Design

### 5.1 Data sources

Two job boards were used in this iteration. The "additional sources" row records boards that the architecture is ready for but that we did not crawl in this iteration; the syllabus source is the one Figure 6 (deferred bonus) would consume.

| Source | What we ingest | How | Used this iteration |
|---|---|---|---|
| 104 人力銀行 | Postings for cluster + control roles: title, company, JD text, required skills, salary (when numeric), location, posted date | XHR `list` endpoint with `Referer` warming; CDP attach to a user-launched Chrome when Cloudflare blocks the raw HTTP path | ✓ 382 postings |
| Cake (cake.me) | Same fields, especially AI-titled and startup roles | Playwright headless; lazy-scroll on the search page to expand the result set | ✓ 180 postings |
| 1111 / Yourator (additional Taiwan boards) | Same posting fields | Same Playwright pattern as Cake | Deferred — architecture-ready |
| Training-provider syllabi (public) | Course skill lists for gap analysis | Manual collection + skill-id mapping YAML | Deferred — feeds Figure 6 |

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

1. **Skill extraction + normalization.** For each JD, match against the taxonomy dictionary (Appendix A; bilingual synonyms), normalize to canonical skills tagged by facet (1–9). **Buzzword filter:** a facet-5 (GenAI) term counts only if it appears in a requirement/skill context, not merely in company boilerplate. Output: a skill vector + facet flags per posting. *(This step is the project's central "raw → refined" value.)*
2. **Role classification by skill fingerprint.** Assign each posting to one of the six cluster sub-roles using its skill vector (nearest-prototype / lightweight classifier). **Job titles are a weak prior only** — Taiwan titles are inconsistent (a posting titled "AI Engineer" may functionally be a data engineer).
3. **AI penetration.** Define a posting as *AI-inflected* if its skill vector contains at least one canonical skill whose `ai_era` flag is true. The `ai_era` set is **all Facet 5 skills (Generative AI / LLM: LLM, RAG, prompt engineering, vector DB, embeddings, fine-tuning, …)** plus a **deliberately restricted subset of Facet 6 (MLOps): MLflow, W&B, model serving, model monitoring, feature store, Kubeflow.** Generic infrastructure used by backend roles too — Docker, Kubernetes, FastAPI, CI/CD — sits under Facet 6 but has `ai_era: false`, so a posting that mentions only those is **not** AI-inflected. This is the design choice that keeps the Backend control group from being falsely tagged (and is also what makes the Backend 19 % floor in Figure 3 a real signal rather than an artefact). Compute the AI-inflected share per role and for the whole cluster.
4. **Cross-sectional AI premium.** Within each role, compare AI-inflected vs non-AI postings on salary and skill count. Use numeric salaries only (drop "面議"/negotiable). The **Backend control group** is the non-AI baseline against which the cluster premium is interpreted.
5. **Skill co-occurrence / bundles.** Compute co-occurrence of AI-era skills with foundational skills (e.g., LLM×SQL, RAG×Python) to show AI skills are *bundled into* roles, not optional add-ons. Single-snapshot; no time series needed.
6. **Curriculum-gap analysis.** Map a real public syllabus onto the taxonomy, overlay on market demand frequency, and surface "high-demand-but-not-taught" skills (especially AI-era).

### 5.4 Delivery

A read-only **Streamlit dashboard** is the live delivery surface in this iteration — role selector → headline metrics, AI vs non-AI salary premium callout, skill-demand bar chart with AI-era skills highlighted in red, sample postings table, and a cross-cluster AI-penetration chart for context. Deployed to Streamlit Community Cloud; URL on page 1.

A read-only **FastAPI** query API (e.g., `GET /skills?role=data_engineer` returning the same role-skill-demand mart in JSON) is documented as the second delivery surface, but it is **deferred to a follow-up iteration** (§11). The marts that would back it are already published as CSV / Parquet / DuckDB in the same shape the API would serve, so adding the FastAPI layer is purely a thin wrapper job rather than a structural change.

![Figure 2 — End-to-end SkillPulse architecture: Ingestion (104 / Cake scrapers writing to an event log) → Storage (Mongo / Parquet on object storage, with DuckDB + CSV marts in the MVP) → Processing (Apache Spark running the four-stage refinement: taxonomy match, salary parser, skill-fingerprint role classification, mart aggregation) → Delivery (Streamlit dashboard shipped today; FastAPI query API planned).](docs/figures/BDAfinal_arch-1.png)

**Figure 2.** End-to-end system architecture. Solid borders are components implemented in this iteration; dashed borders are roadmap (FastAPI query API, full Kafka stream). Apache Airflow is shown as the orchestrator; in the MVP its role is filled by `run_all.py` / Makefile, with the same DAG shape preserved for the productionised version. Italic annotations under Stage 1 ("postings modeled as a stream — velocity") and Stage 3 ("raw → refined") restate the load-bearing big-data argument in §5.2.

---

## 6. Analysis Method and Results

Figures 3, 4, and 5 are pipeline outputs (Figures 1 and 2 in §3 and §5 are the author-drawn scope and architecture diagrams). All three result figures are produced as static PNGs by `python -m skillpulse.run_all` (saved to `output/figures/figure{3,4,5}_*.png`). Figure 5 has a second, interactive rendering in the Streamlit dashboard so the user can switch the focus role; the static PNG in this report uses Data Engineer as the focus, matching the MVP scope. Figure 6 (curriculum-gap overlay) is the deferred bonus and is specified as method only.

### Figure 3 — AI Penetration by Role

![Figure 3 — AI-inflected share of postings per role, ranked. AI Engineer is 100% (partly definitional — see interpretation); ML Engineer 58%; Data Scientist 36%; the MVP focus role Data Engineer 29% (teal-highlighted); Backend control 19%; Algorithm Engineer 14%; Data Analyst 7%. n shown above each bar.](output/figures/figure3_ai_penetration.png)

**Figure 3.** AI-inflected share by role across 562 postings. The teal bar marks the MVP focus role (Data Engineer); all others are grey.

| Role | n | AI-inflected share |
|---|---:|---:|
| AI Engineer | 69 | **100 %** |
| ML Engineer | 89 | 58 % |
| Data Scientist | 83 | 36 % |
| Data Engineer | 68 | 29 % |
| Backend (control) | 64 | 19 % |
| Algorithm Engineer | 21 | 14 % |
| Data Analyst | 118 | 7 % |

**Interpretation.** AI penetration tracks the value-chain position of the role: penetration decays as the role moves upstream toward data engineering and analysis. **One caveat on the AI Engineer 100 % cell:** that row is partly definitional rather than discovered, because the AI Engineer role prototype in `roles_v1.yaml` is itself defined by AI-era skills (LLM, RAG, prompt engineering, vector DB), so a posting cannot be classified as AI Engineer without already containing at least one ai_era skill. The numbers worth reading are the roles whose prototypes are **not** defined by ai_era skills — ML Engineer (58 %), Data Scientist (36 %), Data Engineer (29 %), Algorithm Engineer (14 %), Data Analyst (7 %) — and the **Backend control at 19 %**. The Backend floor is a non-trivial signal that AI skills also leak into roles outside the data/AI cluster (most often as RAG / embedding services in product backends), and it confirms that our taxonomy is not labelling every posting with Docker / FastAPI as AI-inflected — those skills are explicitly excluded from the ai_era set (see §5.3). For our MVP focus role, **Data Engineer at 29 %**, AI is no longer a niche specialisation — roughly one in three openings already expects an LLM / vector-DB / MLOps competence.

### Figure 4 — AI Salary Premium vs Backend Control

![Figure 4 — Median monthly salary in NTD, paired non-AI vs AI-inflected per role. ML Engineer shows the clearest within-role premium (NT$52k vs NT$78k, +50%); Data Engineer +22%; Data Scientist −6% (inside noise). Backend control inverts to −27% (NT$86k vs NT$63k). n above each bar; cells with no opposite-side n leave that bar blank.](output/figures/figure4_ai_premium_vs_backend.png)

**Figure 4.** AI salary premium within each role. Medians use only salary-known postings ("面議" / negotiable dropped). n is shown for each cell. Sub-groups with n < 8 are not interpretable on their own and are called out individually in the text below.

| Role | non-AI median (n) | AI-inflected median (n) | Premium |
|---|---|---|---:|
| Data Engineer | NT$75,887 (17) | NT$92,500 (8) | **+22 %** |
| ML Engineer | NT$51,750 (10) | NT$77,500 (18) | **+50 %** |
| Data Scientist | NT$53,000 (14) | NT$50,000 (7) | −6 % |
| Data Analyst | NT$52,500 (40) | NT$85,000 (1) | (n = 1, not interpretable) |
| Algorithm Engineer | — (0) | NT$100,000 (2) | (no non-AI baseline) |
| AI Engineer | — (no non-AI) | NT$66,667 (21) | (no within-role contrast) |
| Backend (control) | NT$86,250 (26) | NT$62,750 (8) | **−27 %** |

**Interpretation.** Within the two cluster roles where both sides have n ≥ 8 — **Data Engineer (+22 %) and ML Engineer (+50 %)** — AI-inflected postings carry a clear, measurable monthly premium of NT$15k–25k. ML Engineer is the strongest signal in the dataset: 18 AI-inflected vs 10 non-AI salary-known rows, and a +50 % gap that is robust to either tail being trimmed. Data Scientist comes out slightly negative (−6 %, n = 7 vs 14) but the gap is inside noise. The most diagnostic row is the **Backend control: non-AI postings actually pay 27 % more than AI-inflected ones (NT$86k vs NT$63k)** — a reminder that within a *non-AI* role, "doing some LLM glue work" is currently a junior-skewed feature, not a premium one. The contrast between Backend (negative within-role) and ML Engineer (large positive within-role) is what makes the premium claim defensible: AI skills pay *inside the cluster*, not as a universal Pareto improvement.

### Figure 5 — Skill Demand for the Focus Role (Data Engineer)

![Figure 5 — Horizontal bar chart of skill demand for Data Engineer (n=68 postings). Top 10 foundational skills shown in teal: Python 81%, SQL 75%, ETL/ELT 72%, GCP 53%, AWS 41%, Spark 41%, ML general 34%, Azure 32%, Kubernetes 26%, Airflow 26%. Top 5 AI-era skills shown in red below: LLM 16%, RAG 9%, AI Agents 9%, Vector Database 6%, Model Serving 4%.](output/figures/figure5_skill_demand_data_engineer.png)

**Figure 5.** Skill demand for Data Engineer, split into the top 10 foundational skills (teal) and the top 5 AI-era skills (red). A pure top-15 ranking would not surface any red bar because foundational skills dominate the head of the distribution — splitting the legend this way exposes the AI signal that the curriculum-design argument depends on. Tables of the same numbers follow.

Top 10 foundational skills demanded across the 68 Data Engineer postings (% = share of postings mentioning each):

| Rank | Skill | Facet | AI-era | % of postings |
|---:|---|---:|:---:|---:|
| 1 | Python | 1 | | 81 % |
| 2 | SQL | 1 | | 75 % |
| 3 | ETL / ELT | 2 | | 72 % |
| 4 | GCP | 7 | | 53 % |
| 5 | AWS | 7 | | 41 % |
| 5 | Apache Spark | 2 | | 41 % |
| 7 | Machine Learning (general) | 3 | | 34 % |
| 8 | Azure | 7 | | 32 % |
| 9 | Airflow | 2 | | 26 % |
| 9 | Kubernetes | 6 | | 26 % |

The leading AI-era skills inside the same role (Facet 5/6) are:

| Skill | Facet | % of DE postings |
|---|---:|---:|
| Large Language Models | 5 ★ | 16 % |
| RAG | 5 ★ | 9 % |
| AI Agents | 5 ★ | 9 % |
| Vector Database | 5 ★ | 6 % |

**Interpretation.** The Data Engineer skill bundle is still anchored to the classic spine — Python · SQL · ETL · multi-cloud (GCP > AWS > Azure) · Spark / Airflow — and that core dominates the top of the chart. The AI layer has not yet displaced the spine, but it has clearly arrived: **roughly 1 in 6 Data Engineer JDs (16 %) explicitly require Large Language Models**, with RAG and AI Agents trailing in the high single digits. This is the curriculum signal a bootcamp can act on directly: keep the SQL/ETL/cloud backbone, and start adding an LLM / RAG / vector-store module before that 16 % grows into the 30–40 % band where ML Engineer already sits.

### Figure 6 — Curriculum-gap analysis (deferred)

**Method (specified, not executed in this iteration).** Take a public syllabus from a Taiwanese training provider (e.g. an Elite Pioneer programme or a private bootcamp), map each taught topic to a canonical skill_id in our taxonomy, then overlay the resulting "taught / not taught" flag onto Figure 5's role-skill demand bar. The "high-demand-but-not-taught" skills — especially AI-era ones — are the actionable gap the customer pays for. Implementation sketch: a YAML of taught skill_ids per syllabus, joined against `role_skill_demand.csv`, coloured by `taught ∈ {yes, no}`. This bonus is recorded in §11 as deferred.

---

**Sample-size and salary-sparsity reality check.** Of the full 562 postings, **186 (33 %) parsed to a numeric monthly salary** — the remainder list "面議" / "待遇面議" / "negotiable". Figure 4 itself plots only the seven analysis roles (six cluster roles plus the Backend control), excluding the 50 postings classified as `other` (14 of which were salary-known). The salary-known sample that actually feeds Figure 4 is therefore **172**, distributed across the seven roles per the n columns in the table above. This sparsity is the dominant constraint on Figure 4: a (role, AI-flag) cell survives only if it has enough numeric rows. Cake is the better salary signal (**38 % of Cake postings are numeric, vs 31 % of 104**), which is why expanding the Cake share from 21 % to 32 % of the corpus shifted Figure 4's Data Engineer cell from −25 % (n = 3 vs 5) to +22 % (n = 8 vs 17) — i.e. the headline number tracks sample maturity, and a longitudinal scrape (Section 8) is what stabilises it.

**Stated limitations.** Three limitations are kept explicit and report-level, not hidden:
- *Salary sparsity.* Many postings list salary as "negotiable," so Figure 4's medians are computed off the salary-known subset only; we report n alongside every cell, and treat sub-groups with n < 8 as not interpretable.
- *Seniority confound.* Senior roles tend to be both more AI-heavy and higher-paid; the report does not currently stratify by seniority, so a portion of the AI premium in Figure 4 is co-mingled with seniority effects.
- *Snapshot aging.* A single cross-sectional scrape dates quickly; longitudinal value is argued under scalability (§8) and is not claimed for this snapshot.

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

**Cost sketch.** Three scales — *demo (today)*, *production MVP (≈ 1 k new postings/day)*, and *10× / 100×*. Public list prices, USD; convert to TWD ≈ ×31.

| Item | Demo (562 total) | MVP (≈ 30 k / mo) | 100× (≈ 3 M / mo) | Source / assumption |
|---|---|---|---|---|
| Compute (1× small VM) | US$0 (local laptop) | **US$30 / mo** (AWS t3.medium or Hetzner CPX21) | US$300–600 / mo (small Spark cluster, autoscaled) | AWS / Hetzner public price list |
| Object storage (Parquet) | US$0 | **< US$1 / mo** (≈ 30 GB) | US$50 / mo (≈ 2 TB) | S3 Standard US$0.023 / GB / mo |
| Document store (Mongo / Postgres) | US$0 (DuckDB file) | US$15 / mo (managed small instance) | US$200 / mo (managed cluster) | MongoDB Atlas / Supabase tiers |
| **LLM normalization** (uncached) | US$2.5 one-off | **US$135 / mo** | US$13,500 / mo | ≈ US$0.0045 / posting on Claude Haiku 4.5 (≈ 2 k in + 500 out tokens × $1 / M in + $5 / M out) |
| LLM normalization (canonical-string cache, 90 % hit) | — | **≈ US$15 / mo** | ≈ US$1,400 / mo | Each unique skill string is canonicalised once and cached; long-run cache hit > 90 % once the taxonomy stabilises |
| **Monthly total (with cache)** | **≈ US$0** | **≈ US$60 / mo (≈ NT$1,900)** | **≈ US$2,000 / mo (≈ NT$62 k)** | |

**Per-1 k-postings normalization cost.** Uncached: **≈ US$4.5 / k postings (≈ NT$140)**. With a warm canonical-string cache: **≈ US$0.5 / k postings (≈ NT$15)** — i.e. the cache is what makes the LLM step economically viable at scale, and it is the single most important engineering investment as the corpus grows. Compute and storage are essentially noise at this scale; **LLM API is ~70–90 % of the marginal cost**.

**Unit-economics sanity check vs the WTP anchor (§4.3).** A single training-provider customer on a "few thousand NT$/month" subscription (say NT$3,000) covers the entire MVP monthly run-cost (~NT$1,900) on its own — i.e. gross margin is positive from customer #1, and the business scales on customer count rather than on infrastructure depth. At the 100× scale (≈ NT$62 k/mo), break-even is ~21 paying customers, which is well inside the addressable population of small/mid training providers identified in §2.

---

## 9. Deliverables and Repository

**Repository layout (actual).**

```
SkillPulse/
├── README.md                            # local run + deploy + reproduction
├── BDA_Final_Report_DRAFT.md            # this report
├── Makefile                             # `make sample / dashboard / test / ...`
├── requirements.txt                     # core deps (pydantic, pandas, streamlit, ...)
├── requirements-scraping.txt            # adds Playwright (live collection)
├── requirements-spark.txt               # adds PySpark (opt-in for local Spark mode)
├── docker-compose.yml                   # optional single-broker Redpanda for the Kafka demo
├── skillpulse/                          # core Python package
│   ├── schema.py                        # data contract + TW salary parser
│   ├── taxonomy.py                      # YAML loaders for skills_v1 / roles_v1
│   ├── extraction.py                    # taxonomy dictionary matcher
│   ├── classification.py                # role classifier by skill fingerprint
│   ├── aggregation.py                   # mart builders (CSV / Parquet / DuckDB)
│   ├── run_all.py                       # end-to-end pipeline entry point
│   ├── paths.py                         # canonical paths used by every module
│   ├── ingestion/
│   │   ├── collect.py                   # CLI: `python -m skillpulse.ingestion.collect ...`
│   │   ├── events.py                    # append-only JSONL event log (Kafka stand-in)
│   │   └── sources/{job104.py, cake.py} # the two scrapers
│   ├── processing/pipeline.py           # raw → normalized (Spark local / pandas fallback)
│   ├── analysis/figures.py              # matplotlib Figures 3, 4, 5
│   └── dashboard/app.py                 # Streamlit one-page brief
├── taxonomy/
│   ├── skills_v1.yaml                   # canonical skill dictionary (Appendix A)
│   └── roles_v1.yaml                    # role prototypes for the classifier
├── tests/                               # pytest — extractor + salary-parser invariants
├── data/sample/postings_sample.json     # 26 offline fixtures for `--sample`
├── docs/figures/                        # the two author-rendered diagrams
└── output/marts/, output/figures/       # snapshot of the published 562-posting run
```

**Reproducibility.** The README documents (a) `--sample` for an offline, zero-credential demo run, (b) the live `collect.py` invocation per source (including the 104 manual-URL fallback when Cloudflare blocks the JSON path), and (c) the dashboard launch. Repro was verified end-to-end from a fresh `git clone` against an empty Python environment: `pip install -r requirements.txt` → `python -m skillpulse.run_all --sample` produces all marts and Figures 3, 4, 5 in pandas-fallback mode, and `python -m pytest tests` passes (7 tests).

---

## 10. Limitations and Ethics

Scraped data is used for academic analysis with rate-limiting and respect for robots.txt; no personal data of individuals is collected (postings are company-published). Salary inference is associational, not causal — we never claim AI "destroyed" any role, only that AI skills *co-occur with* higher pay. Conclusions are bounded by the snapshot window and by salary sparsity.

---

## 11. What This Iteration Ships vs Next-Iteration Work

### Shipped in this iteration
- **Data contract.** `schema.py` (pydantic v2) plus a Taiwan-specific salary parser that covers 月薪 / 年薪 / 時薪, range / 以上 / 面議, and Cake-style `40,000+ TWD / 月` (§5.3, Appendix A).
- **Skill taxonomy v1.** 88 canonical skills across 9 facets, bilingual aliases, `ai_era` flag, `require_context` buzzword filter (Appendix A).
- **Live scrape, two sources.** 104 (Cloudflare-bypassed via a CDP attach to a user-launched Chrome) and Cake (Playwright headless). Total **562 unique postings** (104: 382, Cake: 180), reproducible from a clean clone via `python -m skillpulse.ingestion.collect`.
- **Processing pipeline.** Skill extraction → fingerprint role classification → AI-penetration + AI-premium aggregation, runnable via `python -m skillpulse.run_all` (PySpark local mode when installed, pandas fallback otherwise).
- **Figures 3, 4, 5.** AI penetration by role, within-role AI salary premium vs Backend control, and Data Engineer top-skill ranking with AI-era highlights (§6). Figures 1 and 2 are the scope diagram (§3) and end-to-end architecture diagram (§5).
- **Delivery.** Read-only Streamlit dashboard with role selector, AI-vs-non-AI premium callout, skill demand bar (AI-era highlighted), and cross-role context chart.
- **Reproducibility.** README documents `--sample` (offline demo), live collection, and the 104 manual-URL fallback. Verified end-to-end from a fresh `git clone`; `pytest` passes (7 tests).
- **Cost model.** Three-scale back-of-envelope (demo / MVP / 100×) tied to published AWS and Anthropic prices (§8).

### Deliberately deferred (acknowledged scope)
- **Figure 6 (curriculum-gap overlay).** Method is specified in §6; implementation requires picking one or two public syllabi to map onto the taxonomy, which we leave as a follow-up.
- **Productionised stream stack.** The architecture is mapped to Kafka / MinIO / MongoDB / Postgres / Airflow (§5), but the demo runs against an append-only JSONL event log + local Parquet + DuckDB; the migration path is what §8's 10× / 100× column describes.
- **FastAPI delivery surface.** Read-only Streamlit dashboard is shipped (URL on page 1); the documented `GET /skills?role=…` endpoint is on the roadmap.
- **Additional Taiwan job boards (1111 / Yourator).** The scraper architecture and storage layer are source-agnostic; adding them is a `sources/*.py` adapter plus an entry in `collect.py`. We did not crawl them in this iteration to keep the corpus interpretable across two sources first.

---

## Appendix A — Skill Taxonomy v1

Nine facets, 88 canonical skills. ★ marks the "AI-era signal" facets used to measure the AI shift. Facet 9 (web/backend) does not contribute to the cluster's value vocabulary; it exists specifically to help the role classifier discriminate the Backend Engineer control group from cluster roles. **This v1 is a hypothesis to validate against scraped JDs** (top-down seed, then bottom-up reconciliation: add missed skills, filter buzzwords, canonicalize synonyms).

| # | Facet | Example canonical skills |
|---|---|---|
| 1 | Languages | Python (spine), SQL (spine), R, Scala, Bash |
| 2 | Data processing / storage | pandas, Spark, ETL/ELT, Airflow, dbt, data warehouse (BigQuery/Snowflake), NoSQL |
| 3 | Classical ML | scikit-learn, XGBoost, statistics, feature engineering, A/B testing, experiment design |
| 4 | Deep-learning frameworks | PyTorch, TensorFlow, CNN/RNN/Transformer |
| 5 | ★ Generative AI / LLM | LLM, RAG, prompt engineering, fine-tuning/LoRA, vector DB (pgvector/Milvus), embeddings, LangChain/LlamaIndex, agents, model APIs (OpenAI/Claude/Gemini) |
| 6 | ★ MLOps / deployment | MLflow, Weights & Biases, model serving (Triton/BentoML), model monitoring, feature store, Kubeflow. Dual-use infra (Docker, Kubernetes, FastAPI, CI/CD) lives in this facet too but is `ai_era: false` so it does not by itself flag a posting as AI-inflected. |
| 7 | Cloud | AWS/GCP/Azure + ML services (SageMaker/Vertex/Azure ML) |
| 8 | BI / business | Tableau/Power BI/Looker, dashboards, domain knowledge, "connect model to business outcome" (qualitative theme) |
| 9 | Web / backend (control-group discriminators) | Node.js, Express, Django, Flask, Spring Boot, .NET, PHP, REST API, microservices. Not part of the cluster's value vocabulary; used by the classifier to recognise the Backend Engineer control group. |

*Canonicalization example:* `LLM`, `大型語言模型`, `GPT`, `生成式AI`, `genAI` → **`llm`** (facet 5).

---

## References

Citation style: APA 7, adapted for primarily web-based industry sources. In-text references in the main report appear as *(Author, Year)*; full entries below. All URLs accessed 2026-06-14.

1. **104 Corporation.** (2026). *104 人力銀行 — Job posting list and detail endpoints.* https://www.104.com.tw/ — primary data source for Section 4 / 6.
2. **Anthropic.** (2026). *Claude API pricing.* https://www.anthropic.com/pricing — basis for the LLM normalization cost estimate in Section 8.
3. **AWS.** (2026). *Amazon S3 pricing.* https://aws.amazon.com/s3/pricing/ — basis for object-storage cost estimate in Section 8.
4. **Business Next (數位時代).** (2026, February). *Taiwan tech jobs shift to chip design and AI: AI share of software postings reaches ~33 %; data scientist median annual pay NT$1.112 M; algorithm engineer NT$1.066 M.* https://www.bnext.com.tw/ — third-party headline figures cited in Section 4.2.
5. **Cake (cake.me).** (2025). *Taiwan AI talent campaign: ~4,500 new AI professionals/year, five fastest-growing roles.* https://www.cake.me/ — secondary data source plus market sizing figure cited in Section 4.2.
6. **Industry Elite Pioneer Program (產業新尖兵試辦計畫).** (2026). *Ministry of Labor — subsidy and trainee stipend amounts.* https://www.wda.gov.tw/ — basis for the WTP anchor (NT$196k per trainee) in Section 4.3.
7. **Institute for Information Industry / National Development Council.** (2025). *2025–2027 AI-talent demand report: 65 % skill-content shift, 56.1 % firm-side shortage.* https://www.ndc.gov.tw/ — third-party signal in Section 4.2 and contrast for Section 7.
8. **Lightcast.** (2025). *Labor-market intelligence platform (global analog).* https://lightcast.io/ — competitive benchmark cited in Sections 4.3 and 7.
9. **Ministry of Labor, Workforce Development Agency.** (2025). *AI cross-domain training programme: ~1,200 classes over two years with >80 % post-training placement.* https://www.wda.gov.tw/ — demand evidence cited in Section 2.4.
10. **聯成電腦 (Lianchen Computer).** (2026). *Career marketing materials — "which jobs are short-staffed in 2026."* https://www.lccnet.com.tw/ — competitor / customer proof cited in Section 2.4.
11. **比薪水 (salary.tw).** (2026). *VIP unlock and credit pricing.* https://salary.tw/ — WTP anchor for individual-user pricing cited in Section 4.3.
12. **Taiwan Copyright Act / Personal Data Protection Act (個人資料保護法).** Legal framework constraining the scrape-to-licensed-API migration discussed in Section 7.
