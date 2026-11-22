# Phase 7 — Test evidence log

Run date: 13 Nov 2026 (re-run after switching the current semester to Semester 3) · Streamlit 1.66.1 · pandas 3.0.5 · Tested with `streamlit.testing.v1.AppTest` and headless Chrome.

## Every page once (no crashes)

| Page | Result |
|---|---|
| Dashboard, Semesters 1-8, Courses & Syllabus, University Syllabus, Academic / Leave Calendar, Internal Assessments, Status Tracker, Scorecard, Plan & Checklist, Ask Degree AI, Data Admin | ✅ 0 exceptions (AppTest + real browser, 0 JS errors) |
| All pages with `scores.csv` deleted | ✅ friendly warning, 0 exceptions |

## Data-change tests

| Test | Before | After | Result |
|---|---|---|---|
| Course status changed (DevSecOps Lab → Completed) → Status Tracker | Completed 0 · In Progress 7 | Completed 1 · In Progress 6 | ✅ |
| New holiday added → Calendar | 9 holidays | 10, "Test Fest Holiday" visible | ✅ |
| New score added (OOAD assignment 10/10) → Scorecard | Sem 3: 78.7%, 20 assessments | Sem 3: 79.4%, 21 assessments | ✅ |
| Checklist item marked Done → summary | Done 7 · Overdue 1 | Done 8 · Overdue 0 | ✅ |
| Course table changes with semester filter | Sem 1: MATH1028, PHYS1019… | Sem 3: CSEG2001, CSEG2002… | ✅ |
| Semester 1–8 all selectable | — | — | ✅ |
| Data Admin loads all 7 tables with validation | — | — | ✅ |

## Chatbot (local engine, no API key)

| Question | Answer (summary) | Data used |
|---|---|---|
| What courses are still incomplete in Semester 2? | All 7 courses completed | Courses |
| What subjects are left in Sem 3? | 7 of 7 in progress, listed | Courses |
| When is my next internal assessment? | IA2 — Formal Languages and Automata Theory, 13 Nov 2026 + next four | Assessments |
| Show my next holiday | Children's Day / College Holiday, Sat 14 Nov 2026 | Calendar |
| What topics are in Data Structures? | Arrays, Linked lists, Stacks, Queues, Trees, Graphs, Hashing, Sorting | Courses |
| What topics are in FLAT? | DFA/NFA … Turing machines | Courses |
| What's overdue in my checklist? | Submit lab record file (due 30 Oct) | Plan |
| Status of semester 4 | Not Started, 0/24 credits, 6 courses | Semesters |
| How are my scores in semester 3? | Prototype score 78.7% + per course | Scores |
| **What is my official university CGPA formula?** | **"I cannot verify that from the current Degree OS data."** + prototype % offered, labelled not-a-CGPA | Syllabus · 🛡️ safe refusal |
| **What is the minimum attendance requirement?** | **"I cannot verify that from the current Degree OS data."** | Syllabus · 🛡️ safe refusal |
| Write me a poem about compilers | "AI API not connected" message | — |

## Seven acceptance tests

- [x] All 11 required navigation items are visible.
- [x] Semester 1 to Semester 8 can all be selected.
- [x] Course data changes when the semester filter changes.
- [x] Calendar distinguishes academic events and leave/holidays.
- [x] Assessment dates and score data are visible.
- [x] Plan & Checklist can be edited without touching code.
- [x] Chatbot gives a grounded answer and a safe "cannot verify" response.

Bug found and fixed during testing: a generative request ("write a poem about compilers") was being matched to the Compiler Design course; generation requests now route to Gemini or the "AI API not connected" message.

## Supabase — Cloud Feedback (22 Nov 2026)

**Database (live project `lsyjwixpiqtwczzzcjub`), checked as real user roles** — run as the `authenticated` / `anon` roles with JWT claims inside one transaction that was rolled back (no data kept):

| Check | Result |
|---|---|
| Table `public.app_feedback` exists, RLS enabled, 2 policies (Read own / Insert own) | ✅ PASS |
| `anon` has no select/insert; `authenticated` has select+insert only (no update/delete) | ✅ PASS |
| User A inserts a row and sees it (A_sees=1) | ✅ PASS |
| Blank name rejected by the check constraint | ✅ PASS |
| User B sees none of A's rows (B_sees=0) | ✅ PASS |
| User B inserting a row with A's user_id → blocked by RLS | ✅ PASS |
| User B update of A's row → permission denied | ✅ PASS |
| Signed-out visitor select / insert → denied | ✅ PASS |
| Supabase security advisor | ✅ 0 issues |

**App (Streamlit AppTest with a stand-in Supabase client; the test workspace cannot reach supabase.co):**

| Check | Result |
|---|---|
| No secrets → friendly "not configured" note, other pages unaffected | ✅ |
| Signed out → only the sign-in form is shown | ✅ |
| Wrong password → "Sign in failed" | ✅ |
| Empty name → warning, 0 rows written | ✅ |
| One valid Save → exactly 1 insert, row shown in "Your saved feedback" | ✅ |
| Normal rerun + Refresh → still 1 insert (no duplicates) | ✅ |
| User B after sign-out/sign-in sees 0 rows; B's own save shows only B's row | ✅ |
| New browser session → must sign in again; A's record still there | ✅ |
| All 12 pages render with no exceptions | ✅ |
| Real `supabase` 2.34.1 client accepts every call the page makes | ✅ |

**Still to run by you (needs your test accounts + network):** sign in on localhost and on the deployed app, Save once, confirm the row in Supabase Table Editor, restart the app and confirm it is still there.
