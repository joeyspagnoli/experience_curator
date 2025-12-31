# Product Spec — ExperienceCurator.ai (Single-Tenant “Career Memory”)

**Product name:** ExperienceCurator.ai  
**Doc owner:** Joey  
**Status:** Draft v0.1.3  
**Last updated:** 2025-12-26  
**Target user:** Single power user (personal use, demo-able publicly)  
**North star:** “Ask anything about my experience and get a trustworthy, cited answer—then tailor my resume to a job posting with zero fabrication.”

---

## 1) One-paragraph summary

ExperienceCurator.ai is a local-first “career memory” platform (NotebookLM-like) that stores my academic, personal, and work artifacts (docs + code projects). It ingests uploads into a searchable **Evidence Library** with stable, verifiable citations. It powers (1) evidence-grounded Q&A, (2) a constrained resume-bullet tailoring workflow against a job posting with strict no-hallucination rules, and (3) a lightweight **Experience Map** (Folder Summaries + Skill Tags + Evidence Links) generated from evidence.

---

## 2) Problem statement

I have lots of scattered experience (classes, projects, internships) and I need a system that helps me:

- quickly confirm whether I’ve used a skill/technology (Linux, CI/CD, MLOps, etc.)
- frame that experience clearly for interviews (technical explanations + STAR stories)
- tailor resume bullet points to a job posting without exaggeration or invented metrics
- identify real gaps and what to learn next, based on what I’ve actually done

---

## 3) Goals and non-goals

### 3.1 Goals (must-have for MVP)

1. **Experience Library + Folders:** Organize artifacts into categories (Academics / Personal Projects / Work / Misc).
2. **Ingestion for docs + code projects:**
   - Docs: `.md`, `.docx`, `.txt` (MVP)
   - Code projects: upload repo **ZIP** (preferred) or **local path indexing** (fallback)
3. **Evidence-grounded Q&A (Citations ON by default):**
   - Every claim must be backed by one or more evidence chunk citations.
   - “No evidence → no claim” behavior is enforced.
4. **Resume Tailor (bullet-level only, interactive approval):**
   - Paste job posting + choose resume
   - Suggest **bullet point edits/variants only** from evidence
   - If metrics aren’t present, ask user for them and provide non-numeric boilerplate alternatives
   - Show diff + user approves changes
5. **Experience Map (thin structured memory):**
   - One card per top-level folder item (project / role / course)
   - Generated: Folder Summary + Skill Tags + Evidence Links (no auto-merge/dedupe)
   - Optional manual pin/edit of summary and tags
6. **Repo Map (for code projects):**
   - Generate a short “repo map” summary per project, grounded in file structure + README + key files
   - Used to improve retrieval/navigation for code Q&A
7. **Eval harness:** basic regression tests for groundedness, citation correctness, and injection resistance.
8. **Debug UI:** show retrieved chunks, scores, scope, citations, and trace IDs.

### 3.2 Non-goals (out of scope for MVP)

- Multi-user accounts, billing, team workspaces
- Job board crawling, auto-applying
- GitHub OAuth sync
- Full resume document rewriting/export (DOCX rewrite)
- Fancy knowledge graphs, ontology building, auto-dedupe/auto-merge
- Advanced retrieval (hybrid search, rerankers) unless needed after MVP
- PDF ingestion (defer; support later if needed)

---

## 4) Target user persona

### Persona: “The Builder Interviewing Soon”

- CS major or early-career engineer
- Has many artifacts but struggles to recall details quickly
- Wants **trustworthy** and **interview-ready** framing
- Prefers an app that feels like: “file library + chat + resume bullet tailoring workspace”
- Is okay with local-first (personal) deployment and CLI/dev workflows

---

## 5) Product principles (hard rules)

### 5.1 Trust and grounding (non-negotiable)

- **Citations ON is default.**
- **No evidence → no claim.**
- **Citation integrity:** each citation must reference a stable `chunk_id` tied to an artifact path and snippet.
- **Metrics policy:** never invent numbers. If metrics are missing: 
  - explicitly flag missing metrics
  - ask the user for real numbers
  - provide non-numeric boilerplate alternatives

### 5.2 “Agent-ness” (workflow, not magic)

The system behaves like an agent by executing an explicit, tool-like workflow:

- Interpret intent → Retrieve → Draft → Verify → Respond  
  Verification blocks unsupported claims. Prefer a deterministic pipeline over multi-agent orchestration.

### 5.3 User control

- Resume bullet modifications require explicit user approval (diff-based).
- Citation toggle is visible: 
  - **Citations ON** (trust mode, default)
  - **Brainstorm mode** (citations OFF) with warning
- **Brainstorm mode is never allowed for Resume Tailor outputs.**

### 5.4 Privacy-first defaults (even for solo)

- Treat uploads as sensitive
- Safe file handling + deletion flows
- Secrets stay server-side only
- Local-first by default; optionally dockerized for portability

---

## 6) Core user journeys

### 6.1 Onboarding (“Initial Experience Dump”)

1. Optional questionnaire:
   - years of experience
   - target CS field (SWE/ML/Systems/etc.)
   - goals (interview prep / resume / learning roadmap)
2. Upload current resume + initial docs + (optionally) a code project ZIP
3. System ingests:
   - searchable evidence index
   - initial Experience Map cards (thin)

**Success:** user can ask “Have I used X?” and get cited evidence immediately.

---

### 6.2 Evidence Q&A (“Do I have experience with X?”)

1. Ask: “Have I used CI/CD? Where?”
2. System retrieves evidence from selected folders/projects
3. System answers with:
   - “Yes, here’s where” + citations
   - or “No evidence found” + suggested next action (“upload notes” / “add project_description.md” / “add README”)

**Success:** answer is trustworthy and points to sources.

---

### 6.3 Code Q&A (“Where is X implemented?”)

1. Upload a repo ZIP (or index local path)
2. Ask: “Where is the training loop?” / “Where do I configure CI?”
3. System uses Repo Map + retrieval to answer with:
   - file paths + snippet citations

**Success:** answers cite file paths and include the relevant snippet chunk(s).

---

### 6.4 Resume Tailor (job posting → approved bullet edits)

1. Paste job posting text
2. Select a resume version (upload `.docx` or `.md`)
3. System:
   - extracts requirements + keywords
   - matches to evidence/cards
   - proposes bullet edits/variants grounded in evidence
   - flags missing metrics and asks user
4. UI shows diff + evidence links
5. User approves/rejects edits
6. Export revised bullets (copy to clipboard; optional plain text download)

**Success:** improved keyword alignment + stronger bullets without fabrication.

---

### 6.5 Skill gap analysis + learning roadmap

1. Paste job posting or select saved “target role”
2. System categorizes requirements:
   - Covered (strong evidence)
   - Partial (thin evidence)
   - Missing (no evidence)
3. System recommends:
   - small project ideas for missing skills
   - learning sequence based on current strengths

**Success:** actionable plan tailored to real gaps.

---

## 7) Information architecture (folders + structure)

### 7.1 Root directories (left sidebar)

- **Academics**
  - Course directories 
    - Course Info (optional)
    - Projects (optional nested)
- **Personal Projects**
  - Project directories (each may include docs + code)
- **Work Experience**
  - One directory per role
- **Misc**
  - Resumes, cover letters, random docs

### 7.2 Recommended “truth anchor” files (high-signal)

- In every project directory: `project_description.md` (recommended)
- In every work role directory: `work_experience.md` (recommended)
- For code projects: `README.md` (recommended)

These should act as high-quality grounding anchors and dramatically improve retrieval quality.

---

## 8) UI/UX spec (layout + screens)

### 8.1 Layout (MVP-friendly)

**Three-pane layout**

- **Left:** Folder tree + search + filters
- **Center:** Main workspace (Ask / Resume Tailor)
- **Right:** Context panel (collapsible) 
  - Evidence (retrieved snippets + citations)
  - Repo Map (for code projects)
  - Experience Map (cards + skill tags)
  - Debug (trace/run details)

### 8.2 Primary screens (MVP)

1. **Home / Onboarding**
2. **Library**
   - folder tree
   - artifact list
   - upload controls (docs + repo ZIP)
   - artifact detail: extracted text preview + ingestion status
3. **Ask**
   - chat input + citations toggle + scope selection
   - evidence panel (retrieved chunks, scores, file path)
4. **Resume Tailor**
   - job posting input
   - resume selection
   - bullet suggestions with approve/reject + evidence links
   - missing metrics loop
5. **Experience Map**
   - generated cards list (one per top-level folder item)
   - skill tags view
6. **Debug Run View**
   - traceId, retrieved chunks, prompt context (sanitized), verification results
7. **Settings**
   - default citation behavior
   - delete/export data
   - model settings (advanced; optional)

---

## 9) Functional requirements

### 9.1 Upload + storage

- Supported uploads (MVP): 
  - docs: `.md`, `.docx`, `.txt`
  - code projects: `.zip` (repo ZIP)
- Optional fallback (MVP if ZIP is painful): **local path indexing** (user selects a local directory; backend indexes files)
- Validate file types + enforce size limits
- Store: 
  - raw files (filesystem or local storage volume)
  - metadata + derived text/chunks in Postgres
- Deletion removes raw + derived (chunks/embeddings/cards/repo map)

### 9.2 Ingestion pipeline

**Docs ingestion**

- Extract text safely
- Chunk with stable chunk IDs for citations
- Compute embeddings and store in vector DB (pgvector)
- Maintain mapping: chunk → artifact → folder/path

**Repo ZIP ingestion**

- Safe extraction requirements: 
  - prevent zip-slip path traversal
  - enforce max file count and max total extracted size
  - ignore common heavy dirs/files: `node_modules/`, `dist/`, `build/`, `.venv/`, `__pycache__/`, binaries
- Index allowed file extensions (configurable allowlist)
- Chunk code per file (MVP): fixed-size chunks with overlap
- Store file path in metadata; citations must include path

### 9.3 Repo Map (MVP)

- For each code project folder, generate a **Repo Map artifact** (stored as a derived markdown/text record): 
  - languages detected
  - key entry points (best-effort)
  - notable directories/files
  - high-level architecture summary
- Repo Map must be **cited** to source files (README, config files, etc.) where possible.

### 9.4 Retrieval

- Folder/project scoped retrieval (default: all)
- Filters (MVP): 
  - folder scope
  - artifact type (doc vs code)
- Retrieval returns: 
  - chunk_id
  - artifact path/name
  - snippet text
  - similarity score
  - optional locator (heading; later line range)

### 9.5 Ask (Q&A workflow) — “Agent” pipeline

**Fixed pipeline (deterministic):**

1. Interpret intent (Ask vs ResumeTailor vs MapBuild)
2. Retrieve relevant chunks (and repo map chunks if code project scope)
3. Draft answer using only retrieved context
4. Verify:
   - block/strip claims not supported by citations
   - if insufficient evidence: return “no evidence found” with next-action suggestions
5. Respond with:
   - answer
   - citations (chunk_id, snippet/quote, artifact filename/path, optional locator)
   - trace_id

### 9.6 Experience Map (thin, generated)

**Definition:** A generated view over folders/projects/roles/courses that provides:

- Folder Summary (1–3 sentences, cited)
- Skill/Tech tags (each tag must have at least 1 evidence chunk)
- Evidence links (top chunks) **No auto-merge/dedupe in MVP.** Optional user actions:
- Pin/edit folder summary (user-authored anchor)
- Add/remove skill tags manually

### 9.7 Resume Tailor (interactive, no fabrication)

- Inputs: job posting text + resume (docx/md) + scope
- Steps: 
  1. extract requirements/keywords
  2. match to evidence/cards
  3. generate bullet variants grounded in evidence
  4. detect missing metrics; ask user
  5. show diff and gather approvals
- Output: 
  - approved bullet edits
  - missing requirements list
  - keyword coverage summary **Hard rule:** Brainstorm mode cannot be used for Resume Tailor.

### 9.8 Skill gaps + learning recommendations

- For a job posting: 
  - Covered / Partial / Missing
- Recommendations (MVP): 
  - 3–5 project ideas for missing skills
  - suggested order based on current strengths

### 9.9 Observability / tracing

- Trace ID per Ask/Tailor run
- Log for each run: 
  - retrieved chunk IDs + similarity scores
  - scope filters
  - model versions
  - verification outcomes (blocked claims count)

### 9.10 Eval harness (minimum viable)

- Groundedness test: answer must cite appropriate chunks or refuse
- Citation correctness test: expected chunk IDs for a subset of questions
- Missing evidence test: must return “no evidence found”
- Prompt injection test: docs containing instructions must not override system rules

---

## 10) Non-functional requirements

### 10.1 Performance (MVP targets)

- Ingestion completes in reasonable time for typical docs and a medium repo
- Q&A returns in interactive time

### 10.2 Security + privacy

- Single-user access control (even if simple token-based or local-only)
- Safe uploads and extraction (ZIP safety rules)
- Server-only secrets
- Data deletion removes raw + derived

### 10.3 Portability

- Postgres is source of truth for metadata/chunks/embeddings/cards/repo maps
- Can run fully local; docker-compose supported for easy setup

---

## 11) Conceptual data model (entities)

- Folder
- Artifact (doc file OR code file OR derived repo map)
- Chunk (extracted text segment)
- Embedding (vector for chunk; stored in pgvector)
- ExperienceCard (thin: folder summary + tags + evidence)
- SkillTag (normalized tag linked to evidence)
- ResumeVersion (stored resume artifact)
- JobPosting (optional persisted)
- RunTrace (ask/tailor runs, retrieval logs, verification report)

Relationships:

- Folder → Artifacts → Chunks → Embeddings
- ExperienceCard → EvidenceChunks
- SkillTag → EvidenceChunks and SkillTag → ExperienceCards
- RunTrace → RetrievedChunks → OutputCitations

---

## 12) Roadmap alignment (Week plan)

### Week 1 — Foundations + doc ingestion + cited Ask

- folder + doc upload (`.md`, `.docx`, `.txt`)
- extraction + chunking + embeddings + retrieval
- Ask with citations ON + verification gate
- debug UI (retrieved chunks + traceId)

### Week 2 — Code projects + Repo Map

- repo ZIP upload (or local path indexing fallback)
- safe extraction + ignore rules
- code chunking + retrieval + code Q&A citations (file path)
- repo map generation per project

### Week 3 — Resume Tailor + thin Experience Map

- resume upload/select
- job posting parsing + requirements extraction
- bullet suggestions grounded in evidence + approvals + missing metrics loop
- thin Experience Map (folder summary + skill tags + evidence)

### Week 4 — Reliability + deploy + demo polish

- eval harness regression tests
- logging/trace IDs hardened
- docker-compose “one command run”
- demo script

---

## 13) MVP acceptance criteria (demo-ready)

- Upload 3–5 docs → Ask “What’s my Linux experience?” → cited answer with clickable sources
- Ask about something not present → “no evidence found” (no invention) + suggested next actions
- Upload a code project ZIP → Ask “Where is the training loop?” → file path + snippet citations
- Paste job posting + select resume → bullet suggestions grounded in evidence; missing metrics flagged (no invented numbers)
- Debug view shows: scope + retrieved chunks + scores + traceId + verification result

---

## 14) Open questions (intentionally deferred)

- Exact frontend stack/component library (but UI spec assumes a modern SPA/Next-like app)
- Background job runner choice (in-process vs queue) for ingestion
- Advanced code chunking (function/class boundary + line numbers)
- Hybrid search/reranking if retrieval quality isn’t sufficient
- PDF ingestion (only if needed later)

---