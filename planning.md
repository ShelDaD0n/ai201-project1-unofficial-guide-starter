# Project 1 Planning: The Unofficial Guide - VT CS Professor Reviews

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---


## Domain

Virginia Tech Computer Science professor reviews, collected from Rate My Professors. This knowledge is valuable because official university channels (course catalogs, department websites) tell you nothing about how a professor actually teaches, grades, or treats students. Students rely on word-of-mouth and scattered forum posts to make registration decisions. This system makes that scattered knowledge searchable and answerable in plain language.

## Documents

10 plain-text files, one per professor, each containing 5 student reviews collected from Rate My Professors. All professors are in the VT Computer Science department.

| File | Professor |
|------|-----------|
| `AllysonSenger_back_reviews.txt` | Allyson Senger |
| `DavidMcPherson_back_reviews.txt` | David McPherson |
| `Eli_Tilevich_back_reviews.txt` | Eli Tilevich |
| `Godmar_Back_back_reviews.txt` | Godmar Back |
| `HeathHillman_back_reviews.txt` | Heath Hillman |
| `JohnLewis_back_reviews.txt` | John Lewis |
| `MargaretEllis_back_reviews.txt` | Margaret Ellis |
| `OsmanBalci_back_reviews.txt` | Osman Balci |
| `PatrickSullivan_back_reviews.txt` | Patrick Sullivan |
| `StephenEdwards_back_reviews.txt` | Stephen Edwards |

Sources cover a range of teaching styles, difficulty levels, and student sentiments — from widely praised (John Lewis) to widely criticized (Heath Hillman, Stephen Edwards) — giving the system varied signal to retrieve from.

## Chunking Strategy

**Strategy: one chunk per individual review.**

Each `-` bullet in the source files is a single student review, typically 3–6 sentences. These are already natural, self-contained units of meaning — a student's complete opinion about one professor. Splitting mid-review would destroy that coherence; bundling all 5 reviews for one professor into a single chunk would dilute retrieval precision (a query about "exam difficulty" could match a chunk that's mostly about office hours).

- **Chunk size:** one review per chunk (~100–250 characters each)
- **Overlap:** none — because chunk boundaries are natural (end of one review, start of another), overlap would just duplicate content without adding context
- **Expected chunk count:** ~50 (10 professors × 5 reviews each)
- **Metadata stored per chunk:** professor name, source filename, chunk index within that professor's file

**Why not fixed character splitting?** Fixed splits (e.g. every 500 characters) would routinely cut mid-sentence across two different students' opinions, producing chunks with no coherent meaning and poor retrieval signal.

## Retrieval Approach

**Embedding model:** `all-MiniLM-L6-v2` via `sentence-transformers`
- Runs fully locally — no API key, no rate limits, no cost
- Well-suited for short opinion text; 384-dimensional embeddings are compact and fast
- Context length (256 tokens) comfortably fits any single review in our corpus

**Top-k:** `k=4`
- With 50 total chunks, retrieving 4 gives the LLM enough student perspectives to synthesize a nuanced answer without flooding it with loosely related reviews
- Too few (k=1–2): risks missing the most relevant review if embedding similarity isn't perfect
- Too many (k=8+): pulls in off-topic reviews from other professors, diluting the answer

**Production tradeoffs (if cost weren't a constraint):**
- `text-embedding-3-large` (OpenAI) would offer higher accuracy on domain-specific nuance but adds per-token cost and API dependency
- `multilingual-e5-large` would matter if we expanded to international student reviews
- Local models win here on latency and privacy; API models win on accuracy at scale

**Vector store:** ChromaDB, running locally with no account required

## Evaluation Plan

| # | Question | Expected Answer |
|---|----------|-----------------|
| Q1 | What level of weekly time commitment do Godmar Back's reviewers say is needed to get an A? | 20+ hours per week |
| Q2 | What do David McPherson's reviewers warn happens with projects near the end of the semester? | They cram a lot of projects in toward the end |
| Q3 | Which professor do reviewers consistently praise for being active on class forums and Discord? | Godmar Back |
| Q4 | Which professor has reviews warning students they will have to self-study and that he caused some students to drop out of their major? | Heath Hillman |
| Q5 | What grading decision made John Lewis a student favorite? | He gave everyone a 100 on the final quiz because of a snow day instead of rescheduling it |

## Anticipated Challenges

**Risk 1 — Stale data for Tilevich:** One of Eli Tilevich's reviews explicitly mentions taking his class "around 2017." If a user asks about his current teaching style, the system may return that review as highly relevant and produce a summary that is 8+ years out of date, with no way to flag the staleness. This is a retrieval accuracy problem that metadata filtering (by date) could partially address, but our current documents don't include review dates.

**Risk 2 — Professor blending on course-level queries:** Allyson Senger and David McPherson both teach the same intro CS course (CS 2505). If a user asks "what is the intro CS course like?" without naming a professor, the retrieval may return reviews from both professors and the LLM may blend them into a single answer that doesn't accurately describe either one. The response could mislead a student trying to choose between the two.

## Architecture

```
┌─────────────────────┐
│   Raw .txt files    │  (10 files, 5 reviews each)
│   /docs/            │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Document Ingestion │  Python: load + parse by "-" bullet
│  ingest.py          │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Chunking           │  One chunk per review
│  ingest.py          │  + metadata: professor name, source file
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Embedding          │  sentence-transformers
│                     │  all-MiniLM-L6-v2 (local)
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Vector Store       │  ChromaDB (local)
│                     │  stores chunks + embeddings + metadata
└────────┬────────────┘
         │  (query time)
         ▼
┌─────────────────────┐
│  Retrieval          │  Semantic search, top-k=4
│  query.py           │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Generation         │  Groq: llama-3.3-70b-versatile
│  query.py           │  Grounded prompt — context only
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Query Interface    │  Gradio web UI
│  app.py             │  Input: question / Output: answer + sources
└─────────────────────┘
```

## AI Tool Plan

| Pipeline Stage | What I'll give the AI | What I expect it to produce |
|---------------|----------------------|----------------------------|
| Ingestion + chunking | This planning.md (Documents + Chunking sections) + sample .txt file | `ingest.py` that parses reviews by `-` bullet, attaches professor name metadata, outputs chunk list |
| Embedding + ChromaDB | Architecture diagram + Retrieval Approach section | Code to embed chunks with `all-MiniLM-L6-v2` and store in ChromaDB with metadata |
| Retrieval function | Retrieval Approach section (k=4, return source metadata) | `query.py` retrieval function returning top-4 chunks + source filenames |
| Grounded generation | Grounding requirement + example of good vs bad response | Prompt template enforcing context-only answers + source attribution |
| Gradio UI | Milestone 5 Gradio skeleton + my function signatures | `app.py` wiring input → retrieval → generation → output with sources displayed |

I will review all generated code before running it, verify it matches this spec, and ask the AI to explain any pattern I don't recognize.

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
