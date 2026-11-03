# 🎓 My Engineering Degree OS

A self-managed **Semester 1 → Semester 8** command center for a B.Tech student: schedules, syllabus, assessments, progress, scorecard, plan/checklist and a grounded AI chatbot — all driven by simple CSV files.

Built with **Python + Streamlit + Pandas**, optional **Gemini (google-genai)** for the chatbot, deployable free on **Streamlit Community Cloud**.

![Dashboard](docs/dashboard.png)

---

## What's inside (11 pages)

| # | Page | What it does |
|---|------|--------------|
| 01 | **Dashboard** | Hero with degree-completion ring, 8-semester journey track, current semester, completion %, next assessment, next holiday, prototype score, plan health, credits chart, next-14-days feed |
| 02 | **Semesters 1-8** | Eight "module" cards (course count, credits, status, progress ring) + inspector with courses / assessments / calendar tabs |
| 03 | **Courses & Syllabus** | Semester switcher, status filter, search, table + syllabus topic cards |
| 04 | **University Syllabus** | Programme overview, every field with a **source/reference**, editable syllabus link, structure computed from courses |
| 05 | **Academic / Leave Calendar** | Filter by academic year, semester, event type; timeline; month-grouped list |
| 06 | **Internal Assessments** | IA1, IA2, assignments, lab evaluations, project reviews, mid/end-sem — timeline + days-left |
| 07 | **Status Tracker** | Not Started / In Progress / Completed counts, progress bar, kanban board, whole-degree charts |
| 08 | **Scorecard** | Semester % and cumulative % (clearly labelled **prototype score percentage**, not CGPA), grade distribution, course detail |
| 09 | **Plan & Checklist** | This Week · Semester Milestones · Degree Milestones, Done / Due Soon / Overdue health, editable with `st.data_editor` |
| 10 | **Ask Degree AI** | Grounded chatbot: Gemini when a key exists, deterministic local engine otherwise, safety layer for university rules, shows data area used |
| 11 | **Data Admin** | Edit any CSV in a grid, validation, save with automatic backup, download, upload-replace, credit sync |

The sidebar **System clock** lets you preview the OS on any date (handy for demos and testing).

---

## Phase 1 — Set up (local)

```bash
cd engineering-degree-os
python -m pip install -r requirements.txt
python -m streamlit hello          # optional environment check
python -m streamlit run app.py
```

**Browser-only alternative:** push this folder to GitHub → *Code → Codespaces → Create codespace* → run the same commands in the Codespaces terminal.

## Phase 2 — Data model (`data/`)

| File | Purpose |
|------|---------|
| `semesters.csv` | Semester 1–8 status and credits |
| `courses.csv` | Code, name, short name, credits, faculty, syllabus topics (`;`-separated), status |
| `academic_calendar.csv` | Academic / Exam / Holiday / Leave events with academic_year + semester |
| `assessments.csv` | IA1, IA2, Assignment, Lab Evaluation, Project Review, Mid/End Semester |
| `scores.csv` | Marks and grades (4 completed semesters + Sem 5 mid-sems) |
| `plan_checklist.csv` | category, item, target_date, status, notes, scope (Semester / Degree) |
| `university_syllabus.csv` | Programme fields + source/reference. Official CGPA formula and regulations are intentionally blank. |

All dates are `YYYY-MM-DD`. Calendar dates and syllabus topics are **sample data** — replace them with your official university documents.

## Phase 6 — Gemini (optional)

1. Create a free key in Google AI Studio.
2. Local: copy `.streamlit/secrets.toml.example` → `.streamlit/secrets.toml` and paste the key.
3. Never commit `secrets.toml` (already in `.gitignore`).

Without a key, the chatbot still answers incomplete courses, next assessment, next holiday, course topics, semester status, scores and checklist status from the CSVs, and shows **"AI API not connected"** for questions needing generation.

## Phase 8 — Deploy (≈5 min)

1. Create a GitHub repo named `engineering-degree-os` and upload everything **except** `.streamlit/secrets.toml`:
   ```bash
   git init && git add . && git commit -m "Engineering Degree OS v1"
   git branch -M main
   git remote add origin https://github.com/<your-username>/engineering-degree-os.git
   git push -u origin main
   ```
2. Open **share.streamlit.io** → sign in with GitHub → **Create app** → choose the repo → branch `main` → file `app.py` → **Deploy**.
3. (If using Gemini) App → **Settings → Secrets** → paste `GEMINI_API_KEY = "..."` → Save.
4. Open the `*.streamlit.app` URL in a new window and ask one chatbot question.

> Note: on Streamlit Cloud, Data Admin edits persist until the app restarts. Commit the updated CSVs (Download CSV button) to make them permanent.

## Troubleshooting

| Problem | Fix |
|---|---|
| `streamlit: command not found` | `python -m pip install streamlit` then `python -m streamlit run app.py` |
| CSV not found | The app shows a friendly warning; check the `data/` folder and file names |
| Column not found | Compare CSV headers with the required columns shown on Data Admin |
| Chatbot fails on cloud | Add `GEMINI_API_KEY` in app Secrets; the local engine still works without it |
| Gemini rate limit | The app automatically falls back to the local engine |

See `TESTING.md` for the evidence log and `SUBMISSION.md` for the submission sheet.
