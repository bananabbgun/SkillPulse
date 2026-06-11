# SkillPulse — Seed Pack

High-quality foundation files for the coding agent to build on. Drop these into your
repo root; they match the layout in the report (`BDA_Final_Report_DRAFT.md` §9).

```
skillpulse_seed/
├── taxonomy/
│   ├── skills_v1.yaml     # 88 canonical skills, 9 facets, bilingual aliases
│   └── roles_v1.yaml      # role prototypes for skill-fingerprint classification
├── skillpulse/
│   └── schema.py          # pydantic v2 data contract + reference TW salary parser
└── data/sample/
    └── postings_sample.json   # 26 realistic fixtures (all roles + backend control)
```

## What each file is

- **`taxonomy/skills_v1.yaml`** — the core "refinement" asset. Canonical skill → bilingual
  aliases, facet (1–9), `ai_era` flag. Facets 5 (GenAI) and 6 (MLOps) are the AI-era signal.
  Generic infra (docker/k8s/ci-cd/fastapi) is deliberately `ai_era: false` so it doesn't
  falsely flag backend postings as AI. `require_context: true` skills should only count
  inside a requirements/skills context (buzzword filter).
- **`taxonomy/roles_v1.yaml`** — prototype skill sets + weak title hints for each of the 6
  cluster roles + `backend` (CONTROL) + `other`. The classifier assigns by skill-vector
  similarity; title is a tie-breaker only.
- **`skillpulse/schema.py`** — the data contract every module imports. `RawPosting` (scraper
  output, fixtures conform to it) → `NormalizedPosting` (refined) → serving marts
  (`RoleAIPenetration`=Fig1, `AIPremiumRow`=Fig2, `RoleSkillDemand`=Fig3). Ships a reference
  `parse_salary()` for messy TW strings ("面議", "月薪 60,000~85,000 元", "年薪 …", "時薪 …").
- **`data/sample/postings_sample.json`** — 26 fixtures so the whole pipeline runs with no
  network. Mix of AI-inflected and non-AI within roles (so Figure 2 has signal), messy
  salaries (some negotiable), and a clean backend control group.

## Verified behavior (smoke-tested)

A minimal extract→classify→salary pass over the fixtures yields: all 7 roles present,
14/26 postings AI-inflected, backend control never falsely flagged, salaries parsed
correctly. The agent's real implementation should reproduce/extend this.

## Known nuance to keep (not a bug)

Two fixtures titled "Data Scientist" classify as `ai_engineer` / `algorithm_engineer`
because their **skill fingerprint** is LLM/DL-heavy. This is the intended behavior
("classify by skills, not title") — Taiwan titles are inconsistent. Surface it in the
report as evidence of why fingerprint classification matters.

## How the agent should use these

1. Treat `schema.py` as the immutable data contract.
2. Build the extractor to read `skills_v1.yaml` (lowercase EN, keep ZH, honor
   `require_context` and per-skill `ai_era` override).
3. Build the classifier to read `roles_v1.yaml`.
4. Develop the entire pipeline against `data/sample/postings_sample.json` first; wire the
   live scraper in later. The `--sample` MVP run must work with zero network / zero API key.
