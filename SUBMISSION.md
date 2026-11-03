# Submission sheet — Engineering Degree OS

| Field | Entry |
|---|---|
| Team / Student | Atul — B.Tech CSE |
| GitHub repository URL | `https://github.com/<your-username>/engineering-degree-os` |
| Live Streamlit app URL | `https://<your-app>.streamlit.app` |
| Screenshot | `docs/dashboard.png` (Dashboard) + `docs/chatbot.png` (Ask Degree AI) — retake on the live URL after deploying |
| Failure / safety example | Q: *"What is my official university CGPA formula?"* → **"I cannot verify that from the current Degree OS data."** No official formula is loaded, so Degree AI refused to invent one and offered only the clearly-labelled prototype score percentage. |
| Improvement for next version | Upload the official syllabus PDF and academic regulations, extract course metadata automatically, and add the verified CGPA formula with its source — then add attendance tracking and deadline reminders. |

## Final launch checklist

- [x] App opens without an error
- [x] Dashboard shows meaningful degree metrics
- [x] All 8 semesters exist
- [x] Courses and syllabus filterable by semester
- [x] University Syllabus page includes a source/reference field
- [x] Academic / Leave Calendar works by year/semester
- [x] Internal assessments are visible and date-based
- [x] Status Tracker shows Not Started / In Progress / Completed
- [x] Scorecard calculates from the loaded score data
- [x] Plan & Checklist is editable and tracks completion
- [x] Chatbot answers at least 5 supported degree questions (9 tested)
- [x] Chatbot refuses an unsupported university-rule question
- [x] Data Admin can edit tables and save them
- [ ] GitHub repo is updated — *push using README Phase 8*
- [ ] Streamlit app URL works in a new browser window — *after deploy*

## Prompts used (Phases 3 & 6)

The app was generated from the assignment's **Master Build Prompt** (single-file `app.py`, CSV storage, 11 pages, friendly warnings for missing files) and the **Chatbot Upgrade Prompt** (context from the CSVs only, Gemini when `GEMINI_API_KEY` exists, the exact Degree AI system instruction, data-area labels, deterministic local fallback).
