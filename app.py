"""
MY ENGINEERING DEGREE OS
A self-managed Semester 1 -> Semester 8 command center for an engineering student.

Stack: Python + Streamlit + Pandas (+ optional google-genai for the chatbot).
All maintainable data lives in CSV files under ./data and can be edited from the
Data Admin page without touching this code.
"""
from __future__ import annotations

import html as _html
import os
import re
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

# ----------------------------------------------------------------------------
# Page setup
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="My Engineering Degree OS",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
BACKUP_DIR = DATA_DIR / ".backups"

# key -> (file name, required columns, friendly label)
TABLES: dict[str, tuple[str, list[str], str]] = {
    "semesters": ("semesters.csv", ["semester", "status", "total_credits", "completed_credits"], "Semesters"),
    "courses": ("courses.csv", ["semester", "course_code", "course_name", "credits", "syllabus", "status"], "Courses & Syllabus"),
    "calendar": ("academic_calendar.csv", ["academic_year", "semester", "date", "event_type", "title"], "Academic / Leave Calendar"),
    "assessments": ("assessments.csv", ["semester", "course_code", "assessment_type", "date", "max_marks", "status"], "Internal Assessments"),
    "scores": ("scores.csv", ["semester", "course_code", "assessment_type", "score", "max_marks", "grade"], "Scores"),
    "plan": ("plan_checklist.csv", ["category", "item", "target_date", "status", "notes"], "Plan & Checklist"),
    "programme": ("university_syllabus.csv", ["field", "value", "source_reference"], "University Syllabus"),
}

COURSE_STATUSES = ["Not Started", "In Progress", "Completed"]
PLAN_STATUSES = ["Not Started", "In Progress", "Done"]
PLAN_CATEGORIES = ["Semester Preparation", "Assessments", "Labs", "Projects", "Documents", "Skills", "Internship/Placement"]
PLAN_SCOPES = ["Semester", "Degree"]
EVENT_TYPES = ["Academic", "Exam", "Holiday", "Leave"]
ASSESS_TYPES = ["IA1", "IA2", "Assignment", "Lab Evaluation", "Project Review", "Quiz", "Mid Semester", "End Semester"]
ASSESS_STATUSES = ["Planned", "Completed", "Missed"]
GRADE_ORDER = ["O", "A+", "A", "B+", "B", "C", "P", "F"]

LIME, CYAN, VIOLET, CORAL, AMBER, PINK = "#C8F65D", "#5EE6FF", "#A78BFA", "#FF7A7A", "#FFC857", "#FF8FD8"
MUTED, TEXT, IDLE = "#8A93B2", "#E8ECF8", "#3A4466"
EVENT_COLORS = {"Academic": CYAN, "Exam": AMBER, "Holiday": VIOLET, "Leave": PINK}
STATUS_COLORS = {"Not Started": IDLE, "In Progress": CYAN, "Completed": LIME}

NAV = [
    "🏠  Dashboard",
    "🧭  Semesters 1-8",
    "📚  Courses & Syllabus",
    "🏛️  University Syllabus",
    "🗓️  Academic / Leave Calendar",
    "📝  Internal Assessments",
    "✅  Status Tracker",
    "📊  Scorecard",
    "🎯  Plan & Checklist",
    "🤖  Ask Degree AI",
    "🛠️  Data Admin",
]

# ----------------------------------------------------------------------------
# Visual design (custom CSS on top of the dark theme in .streamlit/config.toml)
# ----------------------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');
:root{--bg:#0A0E1A;--panel:#10172B;--panel2:#162040;--line:rgba(148,163,209,.16);--text:#E8ECF8;--muted:#8A93B2;
--lime:#C8F65D;--cyan:#5EE6FF;--violet:#A78BFA;--coral:#FF7A7A;--amber:#FFC857;--pink:#FF8FD8;}
.stApp{background-color:var(--bg);
background-image:radial-gradient(1100px 520px at 88% -8%,rgba(94,230,255,.10),transparent 60%),
radial-gradient(800px 480px at -8% 12%,rgba(200,246,93,.07),transparent 60%),
linear-gradient(rgba(148,163,209,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(148,163,209,.035) 1px,transparent 1px);
background-size:auto,auto,36px 36px,36px 36px;background-attachment:fixed;}
.stApp,.stMarkdown,.stMarkdown p,input,textarea{font-family:'Space Grotesk',system-ui,sans-serif;}
[data-testid="stHeader"]{background:transparent;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0D1427 0%,#0A0E1A 100%);border-right:1px solid var(--line);}
.block-container{padding-top:2.2rem;padding-bottom:3rem;max-width:1320px;}
.mono{font-family:'JetBrains Mono',monospace;}
[data-testid="stMetric"]{background:linear-gradient(160deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:16px;padding:14px 16px;}
[data-testid="stMetricLabel"] p{font-family:'JetBrains Mono',monospace;font-size:11px !important;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);}
[data-testid="stMetricValue"]{font-weight:700;}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:14px;overflow:hidden;}
.stButton>button,.stDownloadButton>button,[data-testid="stFormSubmitButton"]>button{border-radius:12px;border:1px solid var(--line);transition:all .15s ease;}
.stButton>button:hover{border-color:var(--lime);color:var(--lime);transform:translateY(-1px);}
.stProgress>div>div>div>div{background:linear-gradient(90deg,var(--cyan),var(--lime));}
[data-testid="stExpander"] details{border:1px solid var(--line);border-radius:14px;background:rgba(16,23,43,.6);}
[data-testid="stChatMessage"]{background:rgba(16,23,43,.72);border:1px solid var(--line);border-radius:16px;}
section[data-testid="stSidebar"] div[role="radiogroup"]{gap:2px;}
section[data-testid="stSidebar"] div[role="radiogroup"] label{padding:7px 10px;border-radius:10px;border:1px solid transparent;width:100%;transition:background .15s;}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover{background:rgba(148,163,209,.08);}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked){background:linear-gradient(90deg,rgba(200,246,93,.16),rgba(200,246,93,.02));border-color:rgba(200,246,93,.35);}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p{color:var(--lime);font-weight:600;}

.brand{display:flex;gap:12px;align-items:center;padding:4px 2px 14px;border-bottom:1px solid var(--line);margin-bottom:12px;}
.brand .logo{width:42px;height:42px;border-radius:12px;display:grid;place-items:center;background:conic-gradient(from 210deg,var(--lime),var(--cyan),var(--violet),var(--lime));color:#0A0E1A;font-weight:800;font-family:'JetBrains Mono',monospace;font-size:15px;}
.brand .bt{font-weight:700;font-size:16px;letter-spacing:-.01em;color:var(--text);line-height:1.1}
.brand .bs{font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:.14em;color:var(--muted);text-transform:uppercase}
.sysbox{border:1px solid var(--line);border-radius:14px;padding:10px 12px;background:rgba(16,23,43,.7);font-size:12.5px;color:var(--muted);margin-top:8px}
.sysbox b{color:var(--text);font-weight:600}
.led{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:7px;vertical-align:middle}
.led.on{background:var(--lime);box-shadow:0 0 10px var(--lime)}.led.off{background:var(--amber);box-shadow:0 0 10px var(--amber)}

.sec{display:flex;gap:16px;align-items:center;margin:2px 0 20px}
.sec .idx{font-family:'JetBrains Mono',monospace;font-size:13px;color:#0A0E1A;background:var(--lime);border-radius:11px;padding:9px 11px;font-weight:700}
.sec .kick{font-family:'JetBrains Mono',monospace;font-size:10.5px;letter-spacing:.16em;color:var(--muted)}
.sec .ttl{font-size:30px;font-weight:700;letter-spacing:-.025em;line-height:1.1;color:var(--text)}
.sec .sub{color:var(--muted);font-size:14.5px;margin-top:3px}
.subhead{font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin:22px 0 12px;display:flex;align-items:center;gap:10px}
.subhead:after{content:"";flex:1;height:1px;background:var(--line)}

.hero{display:flex;justify-content:space-between;align-items:center;gap:28px;padding:28px 32px;border-radius:24px;border:1px solid var(--line);
background:linear-gradient(135deg,rgba(22,32,64,.96),rgba(13,19,39,.96));position:relative;overflow:hidden;margin-bottom:16px}
.hero:before{content:"";position:absolute;right:-90px;bottom:-140px;width:360px;height:360px;background:radial-gradient(circle,rgba(200,246,93,.18),transparent 65%)}
.boot{font-family:'JetBrains Mono',monospace;font-size:11.5px;letter-spacing:.14em;color:var(--lime)}
.boot:after{content:"▍";animation:blink 1s steps(1) infinite;margin-left:4px}
@keyframes blink{50%{opacity:0}}
.hero .h1{font-size:clamp(26px,3.4vw,40px);line-height:1.08;margin:.45rem 0 .5rem;font-weight:700;letter-spacing:-.03em;color:var(--text)}
.hl{background:linear-gradient(90deg,var(--lime),var(--cyan));-webkit-background-clip:text;background-clip:text;color:transparent}
.hero p{color:var(--muted);margin:0;font-size:15px}
.ring{width:150px;height:150px;border-radius:50%;display:grid;place-items:center;flex-shrink:0;position:relative;z-index:1}
.ring>div{width:120px;height:120px;border-radius:50%;background:#0F1630;display:flex;flex-direction:column;align-items:center;justify-content:center}
.ring b{font-size:30px;font-weight:700;color:var(--text)}
.ring span{font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:.14em;color:var(--muted);text-transform:uppercase}

.track{display:grid;grid-template-columns:repeat(8,minmax(74px,1fr));padding:18px 8px 12px;margin:0 0 18px;overflow-x:auto;border:1px solid var(--line);border-radius:20px;background:rgba(16,23,43,.55)}
.node{display:flex;flex-direction:column;align-items:center;position:relative;text-align:center}
.node:before{content:"";position:absolute;top:21px;left:-50%;width:100%;height:3px;background:rgba(148,163,209,.18);z-index:0}
.node:first-child:before{display:none}
.node.done:before{background:var(--lime)}
.node.active:before{background:linear-gradient(90deg,var(--lime),var(--cyan))}
.dot{width:44px;height:44px;border-radius:50%;display:grid;place-items:center;font-family:'JetBrains Mono',monospace;font-weight:700;z-index:1;border:2px solid rgba(148,163,209,.3);background:#0F1630;color:var(--muted);position:relative}
.node.done .dot{background:var(--lime);border-color:var(--lime);color:#0A0E1A}
.node.active .dot{border-color:var(--cyan);color:var(--cyan);animation:pulse 2s infinite}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(94,230,255,.55)}70%{box-shadow:0 0 0 14px rgba(94,230,255,0)}100%{box-shadow:0 0 0 0 rgba(94,230,255,0)}}
.nl{font-family:'JetBrains Mono',monospace;font-size:10.5px;letter-spacing:.1em;color:var(--text);margin-top:8px}
.ns{font-size:11.5px;color:var(--muted)}

.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin-bottom:6px}
.kpi{background:linear-gradient(160deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:18px;padding:16px 18px 15px;position:relative;overflow:hidden}
.kpi:after{content:"";position:absolute;left:0;top:0;height:3px;width:100%;background:var(--acc,var(--lime))}
.kpi .lab{font-family:'JetBrains Mono',monospace;font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
.kpi .val{font-size:26px;font-weight:700;color:var(--text);margin:6px 0 2px;letter-spacing:-.02em;line-height:1.15}
.kpi .val small{font-size:14px;color:var(--muted);font-weight:500}
.kpi .foot{color:var(--muted);font-size:12.5px;line-height:1.35}

.pill{display:inline-block;padding:2px 10px;border-radius:999px;font-size:11.5px;font-family:'JetBrains Mono',monospace;border:1px solid;white-space:nowrap}
.pill.ok{color:var(--lime);border-color:rgba(200,246,93,.45);background:rgba(200,246,93,.08)}
.pill.prog{color:var(--cyan);border-color:rgba(94,230,255,.45);background:rgba(94,230,255,.08)}
.pill.todo{color:#AEB6D3;border-color:rgba(148,163,209,.35);background:rgba(148,163,209,.07)}
.pill.warn{color:var(--amber);border-color:rgba(255,200,87,.5);background:rgba(255,200,87,.08)}
.pill.bad{color:var(--coral);border-color:rgba(255,122,122,.5);background:rgba(255,122,122,.08)}
.pill.vio{color:var(--violet);border-color:rgba(167,139,250,.5);background:rgba(167,139,250,.08)}
.pill.pink{color:var(--pink);border-color:rgba(255,143,216,.5);background:rgba(255,143,216,.08)}

.ev{display:flex;gap:14px;align-items:center;padding:10px 12px;border:1px solid var(--line);border-radius:14px;background:rgba(16,23,43,.75);margin-bottom:8px}
.evd{min-width:52px;text-align:center;border-radius:11px;padding:6px 0;background:rgba(148,163,209,.06);border-left:3px solid var(--c,var(--cyan))}
.evd b{display:block;font-size:19px;color:var(--text);line-height:1}
.evd span{font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:.12em;color:var(--muted)}
.evb{flex:1;min-width:0}
.evt{color:var(--text);font-weight:600;font-size:14.5px}
.evs{color:var(--muted);font-size:12.5px}
.empty{border:1px dashed var(--line);border-radius:14px;padding:16px;color:var(--muted);text-align:center;font-size:13.5px}

.semgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px}
.semcard{background:linear-gradient(160deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:20px;padding:16px 18px;position:relative;overflow:hidden}
.semcard.active{border-color:rgba(94,230,255,.55);box-shadow:0 0 0 1px rgba(94,230,255,.25),0 10px 40px -12px rgba(94,230,255,.35)}
.semcard.done{border-color:rgba(200,246,93,.30)}
.semcard .top{display:flex;justify-content:space-between;align-items:center}
.semcard .mk{font-family:'JetBrains Mono',monospace;font-size:10.5px;letter-spacing:.16em;color:var(--muted)}
.semcard .row{display:flex;justify-content:space-between;align-items:center;margin:10px 0 12px}
.semcard .sn{font-size:22px;font-weight:700;color:var(--text);letter-spacing:-.02em}
.semcard .sy{font-size:12.5px;color:var(--muted)}
.mring{width:62px;height:62px;border-radius:50%;display:grid;place-items:center}
.mring>div{width:48px;height:48px;border-radius:50%;background:#0F1630;display:grid;place-items:center;font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--text);font-weight:700}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-bottom:12px}
.stats div{background:rgba(148,163,209,.06);border-radius:10px;padding:7px 8px}
.stats b{display:block;color:var(--text);font-size:15px}
.stats span{font-size:10.5px;color:var(--muted);font-family:'JetBrains Mono',monospace;letter-spacing:.06em;text-transform:uppercase}
.bar{height:6px;border-radius:99px;background:rgba(148,163,209,.14);overflow:hidden}
.bar i{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,var(--cyan),var(--lime))}

.cgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}
.course{background:linear-gradient(160deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:18px;padding:15px 17px}
.course .ctop{display:flex;justify-content:space-between;align-items:center;gap:8px}
.course .code{font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--cyan);letter-spacing:.06em}
.course .cname{font-size:17px;font-weight:600;color:var(--text);margin:8px 0 2px;line-height:1.25}
.course .cmeta{font-size:12.5px;color:var(--muted);margin-bottom:10px}
.chip{display:inline-block;margin:3px 5px 3px 0;padding:3px 9px;border-radius:8px;background:rgba(94,230,255,.07);border:1px solid rgba(94,230,255,.22);font-size:12px;color:#CFEFFF}

.kanban{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.kcol{border:1px solid var(--line);border-radius:18px;padding:12px;background:rgba(16,23,43,.6);min-height:120px}
.kcol .kh{display:flex;justify-content:space-between;align-items:center;font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);padding:2px 4px 10px}
.kcol .kh b{color:var(--text);font-size:13px}
.kc{border:1px solid var(--line);border-left:3px solid var(--c);border-radius:12px;padding:9px 11px;background:var(--panel);margin-bottom:8px}
.kc .k1{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--muted)}
.kc .k2{color:var(--text);font-size:14px;font-weight:500;line-height:1.3}

.pgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}
.pcard{border:1px solid var(--line);border-radius:18px;padding:15px 17px;background:linear-gradient(160deg,var(--panel2),var(--panel))}
.pcard .pf{font-family:'JetBrains Mono',monospace;font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
.pcard .pv{color:var(--text);font-size:15.5px;margin:6px 0 10px;line-height:1.45}
.pcard .ps{font-size:12px;color:var(--muted);border-top:1px solid var(--line);padding-top:8px}
.pcard .ps b{color:#C9D0E6;font-weight:500}

.panel{border:1px solid var(--line);border-radius:18px;padding:14px 14px 6px;background:rgba(16,23,43,.6);height:100%}
.panel .ph{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
.panel .pt{font-weight:600;color:var(--text);font-size:15px}
.ti{display:flex;gap:10px;align-items:flex-start;padding:9px 10px;border-radius:12px;background:var(--panel);border:1px solid var(--line);margin-bottom:8px}
.ti .tx{flex:1;min-width:0}
.ti .t1{color:var(--text);font-size:13.5px;font-weight:500;line-height:1.3}
.ti .t2{color:var(--muted);font-size:11.5px;margin-top:2px}
.ti .bx{width:16px;height:16px;border-radius:5px;border:2px solid rgba(148,163,209,.5);margin-top:2px;flex-shrink:0}
.ti .bx.done{background:var(--lime);border-color:var(--lime)}
.ti .bx.prog{border-color:var(--cyan);background:linear-gradient(135deg,var(--cyan) 50%,transparent 50%)}

.note{border:1px dashed rgba(255,200,87,.45);background:rgba(255,200,87,.06);color:#F3DFA8;padding:10px 14px;border-radius:12px;font-size:13.5px;margin:6px 0 14px}
.note.info{border-color:rgba(94,230,255,.4);background:rgba(94,230,255,.05);color:#CFEFFF}
.mhead{font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:.18em;color:var(--lime);margin:14px 0 8px}
.foot-note{margin-top:34px;padding-top:14px;border-top:1px solid var(--line);color:var(--muted);font-size:12px;font-family:'JetBrains Mono',monospace;letter-spacing:.04em}
@media (max-width:780px){.kanban{grid-template-columns:1fr}.hero{flex-direction:column;align-items:flex-start}}
</style>
"""

# ----------------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------------
WARNINGS: list[str] = []


def H(markup: str) -> None:
    """Render HTML. Lines are flattened so Markdown never mistakes indentation for code."""
    flat = " ".join(line.strip() for line in markup.strip().splitlines() if line.strip())
    st.markdown(flat, unsafe_allow_html=True)


def esc(x) -> str:
    return _html.escape("" if x is None else str(x))


def num(s) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def dts(s) -> pd.Series:
    return pd.to_datetime(s, errors="coerce")


def pct(a: float, b: float) -> float:
    return float(a) / float(b) * 100 if b else 0.0


def load_table(key: str) -> pd.DataFrame:
    fname, required, label = TABLES[key]
    path = DATA_DIR / fname
    if not path.exists():
        WARNINGS.append(f"`data/{fname}` is missing — the **{label}** area will stay empty until you add it (Data Admin can create it).")
        return pd.DataFrame({c: pd.Series(dtype=object) for c in required})
    try:
        df = pd.read_csv(path, dtype=str, keep_default_na=False)
    except Exception as exc:  # noqa: BLE001
        WARNINGS.append(f"Could not read `data/{fname}` ({exc}). Showing it as empty.")
        return pd.DataFrame({c: pd.Series(dtype=object) for c in required})
    df.columns = [str(c).strip() for c in df.columns]
    for c in required:
        if c not in df.columns:
            WARNINGS.append(f"`data/{fname}` has no `{c}` column — treated as blank. Check the CSV header.")
            df[c] = ""
    df = df.astype(object)
    for c in df.columns:
        df[c] = df[c].map(lambda v: v.strip() if isinstance(v, str) else ("" if v is None else v))
    return df


def save_table(key: str, df: pd.DataFrame) -> Path:
    fname, _, _ = TABLES[key]
    path = DATA_DIR / fname
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if path.exists():
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy(path, BACKUP_DIR / f"{path.stem}_{datetime.now():%Y%m%d_%H%M%S}.csv")
    out = df.copy()
    out = out.where(pd.notna(out), "")
    out.to_csv(path, index=False)
    return path


def themed(chart, height: int = 260):
    return (
        chart.properties(height=height, background="transparent")
        .configure_view(strokeOpacity=0)
        .configure_axis(
            labelColor=MUTED, titleColor=MUTED, gridColor="#1C2540", domainColor="#2A3456", tickColor="#2A3456",
            labelFont="JetBrains Mono", titleFont="Space Grotesk", labelFontSize=11, titleFontSize=12,
        )
        .configure_legend(labelColor="#C9D0E6", titleColor=MUTED, orient="bottom", labelFont="Space Grotesk", symbolType="circle")
        .configure_title(color=TEXT, font="Space Grotesk")
    )


def show_chart(chart, height: int = 260) -> None:
    st.altair_chart(themed(chart, height), width="stretch")


def status_kind(s: str) -> str:
    s = (s or "").strip().lower()
    return {
        "completed": "ok", "done": "ok", "in progress": "prog", "planned": "todo", "not started": "todo",
        "overdue": "bad", "missed": "bad", "due soon": "warn", "on track": "prog",
        "holiday": "vio", "leave": "pink", "exam": "warn", "academic": "prog",
    }.get(s, "todo")


def pill(text: str, kind: str | None = None) -> str:
    return f'<span class="pill {kind or status_kind(text)}">{esc(text)}</span>'


def ring_style(p: float, color: str = LIME) -> str:
    p = max(0.0, min(100.0, p))
    return f"background:conic-gradient({color} {p:.1f}%, rgba(148,163,209,.13) 0)"


def header(idx: int, title: str, sub: str) -> None:
    H(f"""
    <div class="sec"><div class="idx">{idx:02d}</div>
    <div><div class="kick">DEGREE OS / {esc(title.upper())}</div>
    <div class="ttl">{esc(title)}</div><div class="sub">{esc(sub)}</div></div></div>
    """)


def subhead(text: str) -> None:
    H(f'<div class="subhead">{esc(text)}</div>')


def note(text: str, kind: str = "") -> None:
    H(f'<div class="note {kind}">{text}</div>')


def rel_days(d) -> str:
    if pd.isna(d):
        return "no date"
    n = (pd.Timestamp(d).date() - TODAY).days
    if n == 0:
        return "today"
    if n == 1:
        return "tomorrow"
    if n == -1:
        return "yesterday"
    return f"in {n} days" if n > 0 else f"{-n} days ago"


def fmt_date(d, long: bool = False) -> str:
    if pd.isna(d):
        return "—"
    return pd.Timestamp(d).strftime("%a, %d %b %Y" if long else "%d %b %Y")


def event_row(d, title: str, sub: str, color: str, right_html: str) -> str:
    if pd.isna(d):
        day, mon = "—", ""
    else:
        ts = pd.Timestamp(d)
        day, mon = ts.strftime("%d"), ts.strftime("%b").upper()
    return (f'<div class="ev"><div class="evd" style="--c:{color}"><b>{day}</b><span>{mon}</span></div>'
            f'<div class="evb"><div class="evt">{esc(title)}</div><div class="evs">{esc(sub)}</div></div>'
            f'<div>{right_html}</div></div>')


def empty(text: str) -> None:
    H(f'<div class="empty">{esc(text)}</div>')


# ----------------------------------------------------------------------------
# Data load + derived views
# ----------------------------------------------------------------------------
D: dict[str, pd.DataFrame] = {k: load_table(k) for k in TABLES}


def course_lookup() -> dict[str, dict]:
    c = D["courses"]
    return {str(r["course_code"]): r.to_dict() for _, r in c.iterrows() if str(r["course_code"])}


COURSES_BY_CODE = course_lookup()


def course_label(code: str, short: bool = False) -> str:
    row = COURSES_BY_CODE.get(str(code))
    if not row:
        return str(code)
    if short:
        return row.get("short_name") or row["course_name"]
    return row["course_name"]


def prog_field(name: str) -> tuple[str, str]:
    p = D["programme"]
    hit = p[p["field"].str.lower() == name.lower()]
    if hit.empty:
        return "", ""
    return str(hit.iloc[0]["value"]), str(hit.iloc[0]["source_reference"])


def semesters_view() -> pd.DataFrame:
    s = D["semesters"].copy()
    s["n"] = num(s["semester"])
    s = s.dropna(subset=["n"]).copy()
    s["n"] = s["n"].astype(int)
    s["tc"] = num(s["total_credits"]).fillna(0)
    s["cc"] = num(s["completed_credits"]).fillna(0)
    for c in ("academic_year", "term"):
        if c not in s.columns:
            s[c] = ""
    return s.sort_values("n")


def current_semester() -> int:
    s = semesters_view()
    if s.empty:
        return 1
    low = s["status"].str.lower()
    for state in ("in progress", "not started"):
        hit = s[low == state]
        if not hit.empty:
            return int(hit["n"].min())
    return int(s["n"].max())


WEIGHTS = {"completed": 1.0, "in progress": 0.5}


def sem_course_stats(n: int) -> dict:
    c = D["courses"]
    c = c[num(c["semester"]) == n]
    cr = num(c["credits"]).fillna(0)
    low = c["status"].str.lower()
    total = float(cr.sum())
    weighted = float((cr * low.map(WEIGHTS).fillna(0)).sum())
    return {
        "count": len(c),
        "credits": total,
        "completed": int((low == "completed").sum()),
        "in_progress": int((low == "in progress").sum()),
        "not_started": int((~low.isin(["completed", "in progress"])).sum()),
        "completed_credits": float(cr[low == "completed"].sum()),
        "progress": pct(weighted, total),
    }


def assessments_view() -> pd.DataFrame:
    a = D["assessments"].copy()
    a["d"] = dts(a["date"])
    a["n"] = num(a["semester"])
    a["course"] = a["course_code"].map(lambda c: course_label(c))
    a["short"] = a["course_code"].map(lambda c: course_label(c, short=True))
    if "notes" not in a.columns:
        a["notes"] = ""
    return a


def upcoming_assessments() -> pd.DataFrame:
    a = assessments_view()
    a = a[(a["d"] >= TS) & (a["status"].str.lower() != "completed")]
    return a.sort_values("d")


def calendar_view() -> pd.DataFrame:
    c = D["calendar"].copy()
    c["d"] = dts(c["date"])
    c["n"] = num(c["semester"])
    return c.sort_values("d")


def upcoming_breaks() -> pd.DataFrame:
    c = calendar_view()
    return c[(c["d"] >= TS) & c["event_type"].str.lower().isin(["holiday", "leave"])]


def scores_view() -> pd.DataFrame:
    s = D["scores"].copy()
    s["n"] = num(s["semester"])
    s["sc"] = num(s["score"])
    s["mx"] = num(s["max_marks"])
    s["course"] = s["course_code"].map(lambda c: course_label(c))
    return s


def score_summary() -> pd.DataFrame:
    s = scores_view().dropna(subset=["n", "sc", "mx"])
    s = s[s["mx"] > 0]
    if s.empty:
        return pd.DataFrame(columns=["Semester", "Assessments", "Score", "Max", "Percentage", "Cumulative"])
    g = s.groupby("n").agg(Assessments=("sc", "size"), Score=("sc", "sum"), Max=("mx", "sum")).reset_index().sort_values("n")
    g["Percentage"] = g["Score"] / g["Max"] * 100
    g["Cumulative"] = g["Score"].cumsum() / g["Max"].cumsum() * 100
    g = g.rename(columns={"n": "Semester"})
    g["Semester"] = g["Semester"].astype(int)
    return g


def plan_view() -> pd.DataFrame:
    p = D["plan"].copy()
    if "scope" not in p.columns:
        p["scope"] = p["category"].map(
            lambda c: "Degree" if c in ("Documents", "Skills", "Internship/Placement") else "Semester")
    p["d"] = dts(p["target_date"])
    p["health"] = p.apply(plan_health, axis=1)
    return p


def plan_health(row) -> str:
    if str(row.get("status", "")).strip().lower() == "done":
        return "Done"
    d = row.get("d")
    if d is None or pd.isna(d):
        return "No date"
    days = (pd.Timestamp(d).date() - TODAY).days
    if days < 0:
        return "Overdue"
    if days <= 7:
        return "Due Soon"
    return "On Track"


# ----------------------------------------------------------------------------
# Sidebar (navigation + system clock)
# ----------------------------------------------------------------------------
def get_secret(name: str) -> str | None:
    try:
        val = st.secrets.get(name)
        if val:
            return str(val)
    except Exception:  # noqa: BLE001 - no secrets file locally is fine
        pass
    return os.environ.get(name) or None


GEMINI_KEY = get_secret("GEMINI_API_KEY")

st.markdown(CSS, unsafe_allow_html=True)

student, _ = prog_field("Student")
programme, _ = prog_field("Programme")
with st.sidebar:
    H(f"""
    <div class="brand"><div class="logo">OS</div>
    <div><div class="bt">My Engineering Degree OS</div>
    <div class="bs">{esc(student or 'Student')} · {esc(programme or 'B.Tech')}</div></div></div>
    """)
    page = st.radio("Navigate", NAV, key="nav", label_visibility="collapsed")
    st.divider()
    picked = st.date_input(
        "System clock", value=date.today(), key="today",
        help="Defaults to today. Change it to preview what the OS shows on another day.",
    )
    loaded = sum(1 for k in TABLES if (DATA_DIR / TABLES[k][0]).exists())
    led = '<span class="led on"></span>' if GEMINI_KEY else '<span class="led off"></span>'
    ai_txt = "<b>Gemini connected</b>" if GEMINI_KEY else "<b>Local engine</b> · AI API not connected"
    H(f"""
    <div class="sysbox"><span class="led on"></span><b>{loaded}/{len(TABLES)}</b> data files loaded<br>
    {led}{ai_txt}</div>
    """)

TODAY: date = picked if isinstance(picked, date) else date.today()
TS = pd.Timestamp(TODAY)
CUR = current_semester()

if WARNINGS:
    for w in WARNINGS:
        st.warning(w, icon="⚠️")


# ----------------------------------------------------------------------------
# 01 Dashboard
# ----------------------------------------------------------------------------
def page_dashboard() -> None:
    s = semesters_view()
    tc, cc = float(s["tc"].sum()), float(s["cc"].sum())
    deg = pct(cc, tc)
    cur_row = s[s["n"] == CUR]
    year = cur_row["academic_year"].iloc[0] if not cur_row.empty else ""
    term = cur_row["term"].iloc[0] if not cur_row.empty else ""

    H(f"""
    <div class="hero"><div style="position:relative;z-index:1">
    <div class="boot">DEGREE OS v1.0 · SYSTEM ONLINE · {TODAY.strftime('%d %b %Y').upper()}</div>
    <div class="h1">Hey {esc(student or 'there')}, you're in <span class="hl">Semester {CUR}</span>.</div>
    <p>{esc(programme or 'Engineering degree')} · {deg:.0f}% of the degree complete · {tc - cc:.0f} credits to go</p>
    </div>
    <div class="ring" style="{ring_style(deg)}"><div><b>{deg:.0f}%</b><span>degree</span></div></div></div>
    """)

    nodes = []
    for _, r in s.iterrows():
        st_low = str(r["status"]).lower()
        cls = "done" if st_low == "completed" else ("active" if int(r["n"]) == CUR else "todo")
        mark = "✓" if cls == "done" else str(int(r["n"]))
        nodes.append(f'<div class="node {cls}"><div class="dot">{mark}</div>'
                     f'<div class="nl">SEM {int(r["n"])}</div><div class="ns">{esc(r["status"])}</div></div>')
    H(f'<div class="track">{"".join(nodes)}</div>')

    up = upcoming_assessments()
    if not up.empty:
        a = up.iloc[0]
        nxt_val = f"{esc(a['assessment_type'])} <small>· {esc(a['short'])}</small>"
        nxt_foot = f"{fmt_date(a['d'])} · {rel_days(a['d'])} · {esc(a['max_marks'])} marks"
    else:
        nxt_val, nxt_foot = "None", "No upcoming assessment in the data"
    br = upcoming_breaks()
    if not br.empty:
        b = br.iloc[0]
        hol_val = esc(b["title"])
        hol_foot = f"{esc(b['event_type'])} · {fmt_date(b['d'])} · {rel_days(b['d'])}"
    else:
        hol_val, hol_foot = "None", "No upcoming holiday/leave in the data"
    sc = score_summary()
    if not sc.empty:
        overall = pct(sc["Score"].sum(), sc["Max"].sum())
        sc_val = f"{overall:.1f}%"
        sc_foot = f"Prototype score % · {int(sc['Assessments'].sum())} scored assessments"
    else:
        sc_val, sc_foot = "—", "Add rows to scores.csv"
    p = plan_view()
    od = int((p["health"] == "Overdue").sum())
    ds = int((p["health"] == "Due Soon").sum())
    stats = sem_course_stats(CUR)

    H(f"""
    <div class="kpis">
    <div class="kpi" style="--acc:{CYAN}"><div class="lab">Current semester</div><div class="val">Sem {CUR}</div>
    <div class="foot">{esc(year)} {esc(term)} · {stats['count']} courses · {stats['credits']:.0f} credits</div></div>
    <div class="kpi" style="--acc:{LIME}"><div class="lab">Degree completion</div><div class="val">{deg:.1f}%</div>
    <div class="foot">{cc:.0f} / {tc:.0f} credits completed</div></div>
    <div class="kpi" style="--acc:{AMBER}"><div class="lab">Next assessment</div><div class="val">{nxt_val}</div>
    <div class="foot">{nxt_foot}</div></div>
    <div class="kpi" style="--acc:{VIOLET}"><div class="lab">Next holiday / leave</div><div class="val">{hol_val}</div>
    <div class="foot">{hol_foot}</div></div>
    <div class="kpi" style="--acc:{PINK}"><div class="lab">Score summary</div><div class="val">{sc_val}</div>
    <div class="foot">{sc_foot}</div></div>
    <div class="kpi" style="--acc:{CORAL}"><div class="lab">Plan health</div><div class="val">{od} <small>overdue</small> · {ds} <small>due soon</small></div>
    <div class="foot">{int((p['health'] == 'Done').sum())} of {len(p)} checklist items done</div></div>
    </div>
    """)

    left, right = st.columns([1.35, 1], gap="large")
    with left:
        subhead("Semester progress — credits by course status")
        rows = []
        for n in range(1, 9):
            c = D["courses"]
            c = c[num(c["semester"]) == n]
            for i, status in enumerate(COURSE_STATUSES):
                cr = num(c.loc[c["status"].str.lower() == status.lower(), "credits"]).fillna(0).sum()
                rows.append({"Semester": f"S{n}", "Status": status, "Credits": float(cr), "o": i})
        df = pd.DataFrame(rows)
        ch = alt.Chart(df).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5, size=30).encode(
            x=alt.X("Semester:N", sort=[f"S{i}" for i in range(1, 9)], axis=alt.Axis(labelAngle=0, title=None)),
            y=alt.Y("Credits:Q", stack="zero", title="Credits"),
            color=alt.Color("Status:N", scale=alt.Scale(domain=COURSE_STATUSES, range=[IDLE, CYAN, LIME]), legend=alt.Legend(title=None)),
            order=alt.Order("o:Q", sort="descending"),
            tooltip=["Semester", "Status", "Credits"],
        )
        show_chart(ch, 300)
    with right:
        subhead("Next 14 days")
        horizon = TS + pd.Timedelta(days=14)
        items = []
        for _, a in up[up["d"] <= horizon].iterrows():
            items.append((a["d"], f"{a['assessment_type']} · {a['short']}", f"{a['course_code']} · {a['max_marks']} marks", AMBER,
                          pill(rel_days(a["d"]), "warn")))
        cal = calendar_view()
        cal = cal[(cal["d"] >= TS) & (cal["d"] <= horizon)]
        for _, e in cal.iterrows():
            items.append((e["d"], e["title"], f"{e['event_type']} · Sem {e['semester']}", EVENT_COLORS.get(e["event_type"], CYAN),
                          pill(e["event_type"])))
        items.sort(key=lambda t: t[0])
        if items:
            H("".join(event_row(*it) for it in items[:7]))
        else:
            empty("Nothing scheduled in the next two weeks.")

    subhead(f"Semester {CUR} at a glance")
    c = D["courses"]
    c = c[num(c["semester"]) == CUR]
    cards = []
    for _, r in c.iterrows():
        nxt = up[up["course_code"] == r["course_code"]]
        nxt_txt = f"Next: {nxt.iloc[0]['assessment_type']} · {rel_days(nxt.iloc[0]['d'])}" if not nxt.empty else "No upcoming assessment"
        cards.append(f'<div class="kc" style="--c:{STATUS_COLORS.get(r["status"], IDLE)}"><div class="k1">{esc(r["course_code"])} · {esc(r["credits"])} cr · {esc(r["status"])}</div>'
                     f'<div class="k2">{esc(r["course_name"])}</div><div class="k1" style="margin-top:4px">{esc(nxt_txt)}</div></div>')
    if cards:
        H(f'<div class="cgrid" style="grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:10px">{"".join(cards)}</div>')
    else:
        empty("No courses for the current semester yet.")


# ----------------------------------------------------------------------------
# 02 Semesters
# ----------------------------------------------------------------------------
def page_semesters() -> None:
    header(2, "Semesters 1-8", "Eight modules, one degree. Each card is driven by semesters.csv + courses.csv.")
    s = semesters_view()
    cards = []
    for _, r in s.iterrows():
        n = int(r["n"])
        stt = sem_course_stats(n)
        low = str(r["status"]).lower()
        cls = "done" if low == "completed" else ("active" if n == CUR else "")
        color = LIME if low == "completed" else (CYAN if n == CUR else MUTED)
        earned = pct(r["cc"], r["tc"])
        cards.append(f"""
        <div class="semcard {cls}"><div class="top"><span class="mk">MODULE {n:02d}</span>{pill(r['status'])}</div>
        <div class="row"><div><div class="sn">Semester {n}</div><div class="sy">{esc(r['academic_year'])} · {esc(r['term'])}</div></div>
        <div class="mring" style="{ring_style(stt['progress'], color)}"><div>{stt['progress']:.0f}%</div></div></div>
        <div class="stats"><div><b>{stt['count']}</b><span>courses</span></div><div><b>{r['tc']:.0f}</b><span>credits</span></div>
        <div><b>{r['cc']:.0f}</b><span>earned</span></div></div>
        <div class="bar"><i style="width:{earned:.0f}%"></i></div></div>""")
    H(f'<div class="semgrid">{"".join(cards)}</div>')
    note("Ring = semester progress weighted by course credits (Completed = 1, In Progress = ½). "
         "Bar = completed_credits ÷ total_credits from semesters.csv.", "info")

    subhead("Inspect a semester")
    options = list(range(1, 9))
    pick = st.selectbox("Semester", options, index=min(max(CUR - 1, 0), 7), format_func=lambda n: f"Semester {n}", key="sem_pick")
    row = s[s["n"] == pick]
    stt = sem_course_stats(pick)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Status", row["status"].iloc[0] if not row.empty else "—")
    m2.metric("Courses", stt["count"])
    m3.metric("Credits earned", f"{(row['cc'].iloc[0] if not row.empty else 0):.0f} / {(row['tc'].iloc[0] if not row.empty else 0):.0f}")
    m4.metric("Course progress", f"{stt['progress']:.0f}%")
    c = D["courses"]
    c = c[num(c["semester"]) == pick]
    t1, t2, t3 = st.tabs(["Courses", "Assessments", "Calendar"])
    with t1:
        cols = [x for x in ["course_code", "course_name", "credits", "faculty", "status"] if x in c.columns]
        st.dataframe(c[cols], hide_index=True, width="stretch")
    with t2:
        a = assessments_view()
        a = a[a["n"] == pick].sort_values("d")
        if a.empty:
            empty("No assessments recorded for this semester.")
        else:
            st.dataframe(a[["date", "course_code", "course", "assessment_type", "max_marks", "status"]], hide_index=True, width="stretch")
    with t3:
        cal = calendar_view()
        cal = cal[cal["n"] == pick]
        if cal.empty:
            empty("No calendar events for this semester.")
        else:
            st.dataframe(cal[["date", "event_type", "title", "academic_year"]], hide_index=True, width="stretch")


# ----------------------------------------------------------------------------
# 03 Courses & Syllabus
# ----------------------------------------------------------------------------
def page_courses() -> None:
    header(3, "Courses & Syllabus", "Every course, its credits, owner, status and topic list — filtered by semester.")
    labels = [f"Sem {i}" for i in range(1, 9)]
    choice = st.radio("Semester", labels, index=CUR - 1, horizontal=True, key="course_sem")
    n = int(choice.split()[1])
    f1, f2 = st.columns([1, 1.4])
    statuses = f1.multiselect("Status", COURSE_STATUSES, default=COURSE_STATUSES, key="course_status")
    query = f2.text_input("Search course or topic", placeholder="e.g. RSA, automata, OOAD", key="course_q")

    c = D["courses"].copy()
    c = c[num(c["semester"]) == n]
    c = c[c["status"].isin(statuses)]
    if query:
        ql = query.lower()
        mask = c.apply(lambda r: ql in " ".join(str(v) for v in r.values).lower(), axis=1)
        c = c[mask]
    stt = sem_course_stats(n)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Courses", stt["count"])
    m2.metric("Credits", f"{stt['credits']:.0f}")
    m3.metric("Completed", stt["completed"])
    m4.metric("In progress", stt["in_progress"])

    subhead(f"Semester {n} · course table")
    show = c.copy()
    show["credits"] = num(show["credits"])
    cols = [x for x in ["course_code", "course_name", "short_name", "credits", "faculty", "status", "syllabus"] if x in show.columns]
    st.dataframe(
        show[cols], hide_index=True, width="stretch",
        column_config={
            "course_code": st.column_config.TextColumn("Code"),
            "course_name": st.column_config.TextColumn("Course", width="large"),
            "short_name": st.column_config.TextColumn("Short"),
            "credits": st.column_config.NumberColumn("Credits", format="%d"),
            "faculty": st.column_config.TextColumn("Faculty / owner"),
            "status": st.column_config.TextColumn("Status"),
            "syllabus": st.column_config.TextColumn("Syllabus topics", width="large"),
        },
    )
    subhead("Syllabus cards")
    if c.empty:
        empty("No courses match these filters.")
        return
    cards = []
    for _, r in c.iterrows():
        topics = [t.strip() for t in str(r["syllabus"]).split(";") if t.strip()]
        chips = "".join(f'<span class="chip">{esc(t)}</span>' for t in topics) or '<span class="chip">No topics yet</span>'
        cards.append(f'<div class="course"><div class="ctop"><span class="code">{esc(r["course_code"])}</span>{pill(r["status"])}</div>'
                     f'<div class="cname">{esc(r["course_name"])}</div>'
                     f'<div class="cmeta">{esc(r["credits"])} credits · {esc(r.get("faculty", ""))}</div>{chips}</div>')
    H(f'<div class="cgrid">{"".join(cards)}</div>')


# ----------------------------------------------------------------------------
# 04 University Syllabus
# ----------------------------------------------------------------------------
def page_university() -> None:
    header(4, "University Syllabus", "Programme-level overview with a source / reference for every field.")
    p = D["programme"]
    note("Only fields with a verifiable source should be filled. Blank official fields (CGPA formula, regulations) "
         "are intentional — Degree AI will refuse to guess them.")
    cards = []
    for _, r in p.iterrows():
        val = str(r["value"]).strip()
        val_html = esc(val) if val else pill("Not loaded", "warn")
        cards.append(f'<div class="pcard"><div class="pf">{esc(r["field"])}</div><div class="pv">{val_html}</div>'
                     f'<div class="ps">Source / reference: <b>{esc(r["source_reference"]) or "—"}</b></div></div>')
    if cards:
        H(f'<div class="pgrid">{"".join(cards)}</div>')
    else:
        empty("university_syllabus.csv is empty.")

    subhead("Update syllabus source / reference")
    cur_val, cur_src = prog_field("Official syllabus document")
    with st.form("syllabus_src"):
        v = st.text_input("Official syllabus document (link or file name)", value=cur_val, placeholder="https://… or Sem-wise syllabus PDF name")
        src = st.text_input("Source / reference", value=cur_src, placeholder="e.g. University website → Academics → Programme handbook")
        if st.form_submit_button("Save reference", type="primary"):
            df = D["programme"].copy()
            mask = df["field"].str.lower() == "official syllabus document"
            if mask.any():
                df.loc[mask, "value"] = v
                df.loc[mask, "source_reference"] = src
            else:
                df = pd.concat([df, pd.DataFrame([{"field": "Official syllabus document", "value": v, "source_reference": src}])], ignore_index=True)
            save_table("programme", df)
            st.success("Saved to data/university_syllabus.csv")
            st.rerun()

    subhead("Programme structure (computed from courses.csv)")
    c = D["courses"].copy()
    c["n"] = num(c["semester"])
    c["cr"] = num(c["credits"]).fillna(0)
    if c.empty:
        empty("No courses yet.")
        return
    g = c.groupby("n").agg(Courses=("course_code", "size"), Credits=("cr", "sum"),
                           List=("course_name", lambda x: ", ".join(x))).reset_index()
    g = g.rename(columns={"n": "Semester"})
    g["Semester"] = g["Semester"].astype(int)
    a, b = st.columns([1, 1.6], gap="large")
    with a:
        ch = alt.Chart(g).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5, color=LIME, size=26).encode(
            x=alt.X("Semester:O", axis=alt.Axis(labelAngle=0)), y=alt.Y("Credits:Q"), tooltip=["Semester", "Courses", "Credits"])
        show_chart(ch, 260)
        st.metric("Programme credits in the data", f"{g['Credits'].sum():.0f}")
    with b:
        st.dataframe(g, hide_index=True, width="stretch", column_config={
            "List": st.column_config.TextColumn("Courses", width="large"),
            "Credits": st.column_config.NumberColumn(format="%d")})


# ----------------------------------------------------------------------------
# 05 Academic / Leave Calendar
# ----------------------------------------------------------------------------
def page_calendar() -> None:
    header(5, "Academic / Leave Calendar", "Academic dates, exams, holidays and leave in one timeline.")
    cal = calendar_view()
    years = sorted([y for y in cal["academic_year"].unique() if y])
    cur_year = semesters_view().query("n == @CUR")["academic_year"]
    default_year = cur_year.iloc[0] if not cur_year.empty and cur_year.iloc[0] in years else "All"
    f1, f2, f3, f4 = st.columns([1, 1, 1.6, 0.9])
    year = f1.selectbox("Academic year", ["All"] + years, index=(["All"] + years).index(default_year), key="cal_year")
    sems = sorted({int(x) for x in cal["n"].dropna()})
    sem = f2.selectbox("Semester", ["All"] + sems, key="cal_sem")
    types = f3.multiselect("Event type", EVENT_TYPES, default=EVENT_TYPES, key="cal_types")
    only_up = f4.toggle("Upcoming only", value=False, key="cal_up")

    f = cal.copy()
    if year != "All":
        f = f[f["academic_year"] == year]
    if sem != "All":
        f = f[f["n"] == sem]
    f = f[f["event_type"].isin(types)]
    if only_up:
        f = f[f["d"] >= TS]

    m = st.columns(4)
    for i, t in enumerate(EVENT_TYPES):
        m[i].metric(t, int((f["event_type"] == t).sum()))

    if f.empty:
        empty("No events match these filters.")
        return
    subhead("Timeline")
    tl = f.dropna(subset=["d"]).copy()
    pts = alt.Chart(tl).mark_circle(size=170, opacity=.95).encode(
        x=alt.X("d:T", title=None, axis=alt.Axis(format="%d %b %y")),
        y=alt.Y("event_type:N", title=None, sort=EVENT_TYPES),
        color=alt.Color("event_type:N", scale=alt.Scale(domain=EVENT_TYPES, range=[EVENT_COLORS[t] for t in EVENT_TYPES]), legend=None),
        tooltip=[alt.Tooltip("d:T", title="Date", format="%a %d %b %Y"), alt.Tooltip("title:N", title="Event"), alt.Tooltip("event_type:N", title="Type")],
    )
    today_rule = alt.Chart(pd.DataFrame({"d": [TS]})).mark_rule(color=LIME, strokeDash=[4, 4]).encode(x="d:T")
    show_chart(alt.layer(pts, today_rule), 210)

    subhead("Events by month")
    left, right = st.columns(2, gap="large")
    months = list(tl.groupby(tl["d"].dt.to_period("M")))
    half = (len(months) + 1) // 2
    for col, chunk in ((left, months[:half]), (right, months[half:])):
        with col:
            for period, grp in chunk:
                out = [f'<div class="mhead">{period.strftime("%B %Y").upper()}</div>']
                for _, e in grp.iterrows():
                    out.append(event_row(e["d"], e["title"], f"Sem {e['semester']} · {e['academic_year']} · {rel_days(e['d'])}",
                                         EVENT_COLORS.get(e["event_type"], CYAN), pill(e["event_type"])))
                H("".join(out))
    with st.expander("Raw calendar table"):
        st.dataframe(f[["academic_year", "semester", "date", "event_type", "title"]], hide_index=True, width="stretch")


# ----------------------------------------------------------------------------
# 06 Internal Assessments
# ----------------------------------------------------------------------------
def page_assessments() -> None:
    header(6, "Internal Assessments", "IA1, IA2, assignments, lab evaluations, project reviews and exams — date-based.")
    a = assessments_view()
    sems = sorted({int(x) for x in a["n"].dropna()}) or [CUR]
    f1, f2, f3 = st.columns([0.8, 1.6, 1.2])
    sem = f1.selectbox("Semester", ["All"] + sems, index=(["All"] + sems).index(CUR) if CUR in sems else 0, key="as_sem")
    types_present = [t for t in ASSESS_TYPES if t in set(a["assessment_type"])] + sorted(set(a["assessment_type"]) - set(ASSESS_TYPES))
    types = f2.multiselect("Type", types_present, default=types_present, key="as_types")
    statuses = sorted(set(a["status"]) | {"Planned", "Completed"})
    stat = f3.multiselect("Status", statuses, default=statuses, key="as_stat")
    f = a.copy()
    if sem != "All":
        f = f[f["n"] == sem]
    f = f[f["assessment_type"].isin(types) & f["status"].isin(stat)].sort_values("d")

    up = f[(f["d"] >= TS) & (f["status"].str.lower() != "completed")]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Assessments", len(f))
    m2.metric("Upcoming", len(up))
    m3.metric("Completed", int((f["status"].str.lower() == "completed").sum()))
    m4.metric("Next in", rel_days(up.iloc[0]["d"]) if not up.empty else "—")
    covered = sorted(set(f["assessment_type"]))
    H("<div style='margin:6px 0 4px'>" + "".join(f'<span class="chip">{esc(t)}</span>' for t in covered) + "</div>")

    if f.empty:
        empty("No assessments match these filters.")
        return
    subhead("Assessment timeline")
    tl = f.dropna(subset=["d"]).copy()
    pts = alt.Chart(tl).mark_point(filled=True, size=150, opacity=.95).encode(
        x=alt.X("d:T", title=None, axis=alt.Axis(format="%d %b")),
        y=alt.Y("short:N", title=None),
        color=alt.Color("assessment_type:N", legend=alt.Legend(title=None),
                        scale=alt.Scale(range=[CYAN, LIME, AMBER, VIOLET, PINK, CORAL, "#7DD3FC", "#FDE68A"])),
        shape=alt.Shape("status:N", legend=None),
        tooltip=[alt.Tooltip("d:T", title="Date", format="%a %d %b %Y"), "course:N", "assessment_type:N", "max_marks:N", "status:N"],
    )
    rule = alt.Chart(pd.DataFrame({"d": [TS]})).mark_rule(color=LIME, strokeDash=[4, 4]).encode(x="d:T")
    show_chart(alt.layer(pts, rule), 280)

    left, right = st.columns([1, 1.5], gap="large")
    with left:
        subhead("Coming up")
        if up.empty:
            empty("Nothing upcoming for these filters.")
        else:
            H("".join(event_row(r["d"], f"{r['assessment_type']} · {r['course']}",
                                f"{r['course_code']} · {r['max_marks']} marks · {r.get('notes', '')}".rstrip(" ·"),
                                AMBER if r["assessment_type"] == "End Semester" else CYAN, pill(rel_days(r["d"]), "warn"))
                      for _, r in up.head(8).iterrows()))
    with right:
        subhead("All records")
        t = f.copy()
        t["days_left"] = t["d"].map(lambda d: (pd.Timestamp(d).date() - TODAY).days if pd.notna(d) else None)
        st.dataframe(t[["date", "days_left", "course_code", "course", "assessment_type", "max_marks", "status", "notes"]],
                     hide_index=True, width="stretch",
                     column_config={"days_left": st.column_config.NumberColumn("Days left", format="%d"),
                                    "course": st.column_config.TextColumn("Course", width="medium")})


# ----------------------------------------------------------------------------
# 07 Status Tracker
# ----------------------------------------------------------------------------
def page_status() -> None:
    header(7, "Status Tracker", "Not Started → In Progress → Completed, per course and per semester.")
    pick = st.selectbox("Semester", list(range(1, 9)), index=CUR - 1, format_func=lambda n: f"Semester {n}", key="st_sem")
    stt = sem_course_stats(pick)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Not Started", stt["not_started"])
    m2.metric("In Progress", stt["in_progress"])
    m3.metric("Completed", stt["completed"])
    m4.metric("Credits completed", f"{stt['completed_credits']:.0f} / {stt['credits']:.0f}")
    done_share = pct(stt["completed"], stt["count"])
    st.progress(min(done_share / 100, 1.0), text=f"Semester {pick}: {stt['completed']} of {stt['count']} courses completed ({done_share:.0f}%) · weighted progress {stt['progress']:.0f}%")

    c = D["courses"]
    c = c[num(c["semester"]) == pick]
    cols = []
    for status in COURSE_STATUSES:
        grp = c[c["status"].str.lower() == status.lower()] if status != "Not Started" else c[~c["status"].str.lower().isin(["in progress", "completed"])]
        cards = "".join(f'<div class="kc" style="--c:{STATUS_COLORS[status]}"><div class="k1">{esc(r["course_code"])} · {esc(r["credits"])} cr</div>'
                        f'<div class="k2">{esc(r["course_name"])}</div></div>' for _, r in grp.iterrows())
        cols.append(f'<div class="kcol"><div class="kh"><span>{status}</span><b>{len(grp)}</b></div>{cards or "<div class=k1 style=padding:6px>—</div>"}</div>')
    subhead("Board")
    H(f'<div class="kanban">{"".join(cols)}</div>')

    subhead("Whole degree — courses by status")
    rows = []
    for n in range(1, 9):
        s2 = sem_course_stats(n)
        rows += [{"Semester": f"S{n}", "Status": "Completed", "Courses": s2["completed"]},
                 {"Semester": f"S{n}", "Status": "In Progress", "Courses": s2["in_progress"]},
                 {"Semester": f"S{n}", "Status": "Not Started", "Courses": s2["not_started"]}]
    df = pd.DataFrame(rows)
    a, b = st.columns([1.6, 1], gap="large")
    with a:
        ch = alt.Chart(df).mark_bar(size=28, cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            x=alt.X("Semester:N", sort=[f"S{i}" for i in range(1, 9)], axis=alt.Axis(labelAngle=0, title=None)),
            y=alt.Y("Courses:Q"), color=alt.Color("Status:N", scale=alt.Scale(domain=COURSE_STATUSES, range=[IDLE, CYAN, LIME]), legend=alt.Legend(title=None)),
            tooltip=["Semester", "Status", "Courses"])
        show_chart(ch, 260)
    with b:
        tot = df.groupby("Status")["Courses"].sum().reset_index()
        donut = alt.Chart(tot).mark_arc(innerRadius=62, cornerRadius=4, padAngle=.02).encode(
            theta="Courses:Q", color=alt.Color("Status:N", scale=alt.Scale(domain=COURSE_STATUSES, range=[IDLE, CYAN, LIME]), legend=alt.Legend(title=None)),
            tooltip=["Status", "Courses"])
        show_chart(donut, 260)
    note("To change a status, open <b>Data Admin → Courses & Syllabus</b>, edit the <code>status</code> cell and save — this board updates instantly.", "info")


# ----------------------------------------------------------------------------
# 08 Scorecard
# ----------------------------------------------------------------------------
def page_scorecard() -> None:
    header(8, "Scorecard", "Marks, grades and a transparent, data-driven prototype score percentage.")
    note("<b>Prototype score percentage</b> = total score ÷ total max marks × 100, computed from scores.csv. "
         "This is <b>not</b> an official university CGPA/SGPA — no official formula is loaded.")
    g = score_summary()
    s = scores_view()
    if g.empty:
        empty("Add rows to scores.csv to see the scorecard.")
        return
    overall = pct(g["Score"].sum(), g["Max"].sum())
    best = g.loc[g["Percentage"].idxmax()]
    latest = g.iloc[-1]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Prototype score % (all)", f"{overall:.1f}%")
    m2.metric("Best semester", f"Sem {int(best['Semester'])}", f"{best['Percentage']:.1f}%")
    m3.metric("Latest semester", f"Sem {int(latest['Semester'])}", f"{latest['Percentage']:.1f}%")
    m4.metric("Scored assessments", int(g["Assessments"].sum()))

    a, b = st.columns([1.5, 1], gap="large")
    with a:
        subhead("Semester vs cumulative prototype %")
        long = g.melt(id_vars="Semester", value_vars=["Percentage", "Cumulative"], var_name="Metric", value_name="Percent")
        long["Metric"] = long["Metric"].map({"Percentage": "Semester %", "Cumulative": "Cumulative %"})
        lo = max(0, float(long["Percent"].min()) - 10)
        ch = alt.Chart(long).mark_line(point=alt.OverlayMarkDef(size=80, filled=True), strokeWidth=3).encode(
            x=alt.X("Semester:O", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Percent:Q", scale=alt.Scale(domain=[lo, 100]), title="%"),
            color=alt.Color("Metric:N", scale=alt.Scale(range=[LIME, CYAN]), legend=alt.Legend(title=None)),
            tooltip=["Semester", "Metric", alt.Tooltip("Percent:Q", format=".1f")])
        show_chart(ch, 270)
    with b:
        subhead("Grade distribution")
        gr = s[s["grade"].astype(str).str.strip() != ""]
        if gr.empty:
            empty("No grades yet.")
        else:
            cnt = gr["grade"].value_counts().reset_index()
            cnt.columns = ["Grade", "Count"]
            order = [x for x in GRADE_ORDER if x in set(cnt["Grade"])] + sorted(set(cnt["Grade"]) - set(GRADE_ORDER))
            ch = alt.Chart(cnt).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5, size=26, color=VIOLET).encode(
                x=alt.X("Grade:N", sort=order, axis=alt.Axis(labelAngle=0)), y="Count:Q", tooltip=["Grade", "Count"])
            show_chart(ch, 270)

    subhead("Semester summary")
    view = g.copy()
    st.dataframe(view, hide_index=True, width="stretch", column_config={
        "Score": st.column_config.NumberColumn(format="%.0f"), "Max": st.column_config.NumberColumn(format="%.0f"),
        "Percentage": st.column_config.ProgressColumn("Semester %", format="%.1f%%", min_value=0, max_value=100),
        "Cumulative": st.column_config.ProgressColumn("Cumulative %", format="%.1f%%", min_value=0, max_value=100)})

    subhead("Course-level detail")
    sems = [int(x) for x in g["Semester"]]
    pick = st.selectbox("Semester", sems, index=len(sems) - 1, format_func=lambda n: f"Semester {n}", key="sc_sem")
    d = s[s["n"] == pick].copy()
    d["percent"] = d["sc"] / d["mx"] * 100
    d["credits"] = d["course_code"].map(lambda c: COURSES_BY_CODE.get(c, {}).get("credits", ""))
    st.dataframe(d[["course_code", "course", "credits", "assessment_type", "score", "max_marks", "percent", "grade"]],
                 hide_index=True, width="stretch", column_config={
                     "percent": st.column_config.ProgressColumn("Score %", format="%.0f%%", min_value=0, max_value=100),
                     "course": st.column_config.TextColumn("Course", width="medium")})


# ----------------------------------------------------------------------------
# 09 Plan & Checklist
# ----------------------------------------------------------------------------
def task_html(r) -> str:
    st_low = str(r["status"]).lower()
    bx = "done" if st_low == "done" else ("prog" if st_low == "in progress" else "")
    sub = f"{r['category']} · {fmt_date(r['d'])} · {rel_days(r['d'])}" if pd.notna(r["d"]) else str(r["category"])
    if str(r.get("notes", "")).strip():
        sub += f" · {r['notes']}"
    return (f'<div class="ti"><div class="bx {bx}"></div><div class="tx"><div class="t1">{esc(r["item"])}</div>'
            f'<div class="t2">{esc(sub)}</div></div>{pill(r["health"])}</div>')


def page_plan() -> None:
    header(9, "Plan & Checklist", "Your degree execution control panel — not a decorative to-do list.")
    p = plan_view()
    total = len(p)
    done = int((p["health"] == "Done").sum())
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total items", total)
    m2.metric("Done", done)
    m3.metric("In progress", int((p["status"].str.lower() == "in progress").sum()))
    m4.metric("Due soon (≤7d)", int((p["health"] == "Due Soon").sum()))
    m5.metric("Overdue", int((p["health"] == "Overdue").sum()))
    st.progress(done / total if total else 0.0, text=f"{done} of {total} items done ({pct(done, total):.0f}%)")

    week_end = TS + pd.Timedelta(days=7)
    open_items = p[p["health"] != "Done"]
    this_week = open_items[(open_items["d"] <= week_end)].sort_values("d")  # includes overdue ones
    sem_ms = p[p["scope"].str.lower() == "semester"].sort_values("d")
    deg_ms = p[p["scope"].str.lower() == "degree"].sort_values("d")

    c1, c2, c3 = st.columns(3, gap="medium")
    for col, title, frame, tag in (
        (c1, "This Week", this_week, f"{len(this_week)} open"),
        (c2, "Semester Milestones", sem_ms, f"{int((sem_ms['health'] == 'Done').sum())}/{len(sem_ms)} done"),
        (c3, "Degree Milestones", deg_ms, f"{int((deg_ms['health'] == 'Done').sum())}/{len(deg_ms)} done"),
    ):
        with col:
            body = "".join(task_html(r) for _, r in frame.iterrows()) or '<div class="empty">Nothing here 🎉</div>'
            H(f'<div class="panel"><div class="ph"><div class="pt">{title}</div>{pill(tag, "prog")}</div>{body}</div>')

    subhead("Edit the plan")
    st.caption("Change status Not Started → In Progress → Done, adjust dates, add or delete rows, then press **Save checklist**. "
               "Health is calculated automatically from the target date.")
    ed = p[["category", "item", "target_date", "status", "notes", "scope", "health"]].copy()
    ed["target_date"] = dts(ed["target_date"]).dt.date
    ed["target_date"] = ed["target_date"].astype(object).where(ed["target_date"].notna(), None)
    edited = st.data_editor(
        ed, key="plan_editor", num_rows="dynamic", hide_index=True, width="stretch",
        column_config={
            "category": st.column_config.SelectboxColumn("Category", options=PLAN_CATEGORIES, required=True),
            "item": st.column_config.TextColumn("Item", width="large", required=True),
            "target_date": st.column_config.DateColumn("Target date", format="DD MMM YYYY"),
            "status": st.column_config.SelectboxColumn("Status", options=PLAN_STATUSES, required=True, default="Not Started"),
            "notes": st.column_config.TextColumn("Notes", width="medium"),
            "scope": st.column_config.SelectboxColumn("Milestone level", options=PLAN_SCOPES, default="Semester"),
            "health": st.column_config.TextColumn("Health", disabled=True),
        },
    )
    if st.button("💾  Save checklist", type="primary", key="save_plan"):
        out = edited.drop(columns=["health"]).copy()
        out = out[out["item"].astype(str).str.strip().replace("None", "") != ""]
        out["target_date"] = pd.to_datetime(out["target_date"], errors="coerce").dt.strftime("%Y-%m-%d").fillna("")
        for c in ("category", "status", "notes", "scope"):
            out[c] = out[c].fillna("").astype(str).replace("None", "")
        out.loc[out["status"] == "", "status"] = "Not Started"
        out.loc[out["scope"] == "", "scope"] = "Semester"
        save_table("plan", out[["category", "item", "target_date", "status", "notes", "scope"]])
        st.success(f"Saved {len(out)} items to data/plan_checklist.csv")
        st.rerun()


# ----------------------------------------------------------------------------
# 10 Ask Degree AI
# ----------------------------------------------------------------------------
SYSTEM_INSTRUCTION = (
    "You are Degree AI. Answer only from the supplied degree data. Do not invent university rules, dates, marks, "
    "formulas or syllabus content. If the requested information is missing, say: I cannot verify that from the "
    "current Degree OS data."
)
FORMAT_RULES = (
    "Keep answers concise and student-friendly (short sentences or a short bullet list, markdown allowed). "
    "Treat TODAY in the data as the current date when deciding what is 'next' or 'upcoming'. "
    "Any 'prototype score percentage' must be called exactly that, never CGPA. "
    "On the very last line write DATA_AREAS: followed by the comma-separated data areas you used, chosen from "
    "Courses, Calendar, Assessments, Scores, Plan, Semesters, Syllabus."
)
CANNOT = "I cannot verify that from the current Degree OS data."

RULE_TOPICS = [
    (r"\bc?gpa\b|\bsgpa\b|grade point|formula", "cgpa"),
    (r"regulation|eligib|passing (criteria|marks?)|pass marks?|attendance (rule|requirement|criteria|policy|percentage)|"
     r"minimum attendance|grace marks?|detain|detention|backlog|re-?exam|supplementary|university rule|official rule|ordinance",
     "regulation"),
]
STOP = {"and", "with", "engineering", "fundamentals", "basic", "systems", "theory", "design", "analysis", "lab",
        "project", "phase", "elective", "program", "open", "computer", "introduction", "advanced", "management",
        "evaluation", "the", "for", "into", "i", "ii", "iii", "iv"}
ORD = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6, "seventh": 7, "eighth": 8, "last": 8}


def parse_semester(ql: str) -> int | None:
    m = re.search(r"\bsem(?:ester)?\s*[-#]?\s*([1-8])\b", ql) or re.search(r"\b([1-8])(?:st|nd|rd|th)?\s+sem", ql)
    if m:
        return int(m.group(1))
    m = re.search(r"\b(first|second|third|fourth|fifth|sixth|seventh|eighth|last)\s+sem", ql)
    if m:
        return ORD[m.group(1)]
    if re.search(r"\b(this|current|ongoing|present)\s+sem", ql):
        return CUR
    return None


def find_course(ql: str):
    best, best_score = None, 0
    for _, r in D["courses"].iterrows():
        code = str(r["course_code"]).lower()
        name = str(r["course_name"]).lower()
        short = str(r.get("short_name", "")).lower()
        score = 0
        if code and re.search(rf"\b{re.escape(code)}\b", ql):
            score = 100
        elif name and name in ql:
            score = 90
        elif len(short) >= 2 and re.search(rf"\b{re.escape(short)}\b", ql):
            score = 80
        else:
            toks = [t for t in re.findall(r"[a-z]+", name) if len(t) > 3 and t not in STOP]
            hits = sum(1 for t in toks if re.search(rf"\b{t}", ql))
            if toks and hits >= min(2, len(toks)):
                score = 40 + hits
        if score > best_score:
            best, best_score = r, score
    return best


def rule_guard(ql: str) -> dict | None:
    for pattern, topic in RULE_TOPICS:
        if re.search(pattern, ql):
            p = D["programme"]
            hits = p[p["field"].str.lower().str.contains(topic if topic == "cgpa" else "regulation") & (p["value"].str.strip() != "")]
            if not hits.empty:
                r = hits.iloc[0]
                return {"text": f"**{r['field']}:** {r['value']}\n\n_Source: {r['source_reference'] or 'not stated'}_",
                        "areas": ["Syllabus"], "engine": "Local engine · safety layer"}
            extra = ""
            if topic == "cgpa":
                g = score_summary()
                if not g.empty:
                    extra = (f"\n\nWhat I *can* show: your **prototype score percentage** is "
                             f"**{pct(g['Score'].sum(), g['Max'].sum()):.1f}%** (total score ÷ total max marks) — this is not a CGPA.")
            return {"text": f"**{CANNOT}**\n\nNo official {'CGPA/SGPA formula' if topic == 'cgpa' else 'university regulation'} "
                            f"is loaded in the University Syllabus data, so I won't guess one. Add it there with its official source "
                            f"and I'll use it.{extra}",
                    "areas": ["Syllabus"] + (["Scores"] if extra else []), "engine": "Local engine · safety layer", "refused": True}
    return None


def ans_help() -> dict:
    return {"text": "I'm **Degree AI** — I answer from your Degree OS data only. Try:\n"
                    "- *What subjects are left in Sem 5?*\n- *When is my next IA?*\n- *Show my next holiday*\n"
                    "- *What topics are in FLAT?*\n- *What's the status of semester 6?*\n- *What's overdue in my checklist?*\n"
                    "- *How are my scores in semester 4?*",
            "areas": ["General"]}


def ans_incomplete(n: int | None) -> dict:
    n = n or CUR
    c = D["courses"]
    c = c[num(c["semester"]) == n]
    left = c[c["status"].str.lower() != "completed"]
    if c.empty:
        return {"text": f"There are no courses recorded for Semester {n}. {CANNOT}", "areas": ["Courses"]}
    if left.empty:
        return {"text": f"All **{len(c)} courses** in Semester {n} are marked **Completed**. 🎉", "areas": ["Courses"]}
    lines = "\n".join(f"- **{r['course_name']}** ({r['course_code']}, {r['credits']} cr) — {r['status']}" for _, r in left.iterrows())
    return {"text": f"**{len(left)} of {len(c)} courses** in Semester {n} are not completed yet:\n{lines}", "areas": ["Courses"]}


def ans_assessment(ql: str, n: int | None, course) -> dict:
    up = upcoming_assessments()
    note_txt = ""
    if n:
        up = up[up["n"] == n]
    type_filters = [
        (r"end[\s-]?sem", ["End Semester"]), (r"mid[\s-]?sem", ["Mid Semester"]),
        (r"\bia\s?-?1\b", ["IA1"]), (r"\bia\s?-?2\b", ["IA2"]), (r"\bias?\b", ["IA1", "IA2"]),
        (r"assignment", ["Assignment"]), (r"\blab\b", ["Lab Evaluation"]), (r"review", ["Project Review"]),
        (r"quiz", ["Quiz"]),
    ]
    for pat, types in type_filters:
        if re.search(pat, ql):
            up = up[up["assessment_type"].isin(types)]
            break
    else:
        if "internal" in ql:
            up = up[up["assessment_type"] != "End Semester"]
    if course is not None:
        only = up[up["course_code"] == course["course_code"]]
        if only.empty:
            note_txt = f"\n\n_No upcoming record for {course['course_name']}, so I showed the next ones overall._"
        else:
            up = only
    if up.empty:
        return {"text": f"There is no upcoming assessment matching that in the data. {CANNOT}", "areas": ["Assessments"]}
    a = up.iloc[0]
    txt = (f"Your next one is **{a['assessment_type']} — {a['course']}** ({a['course_code']}) on "
           f"**{fmt_date(a['d'], long=True)}** ({rel_days(a['d'])}) · {a['max_marks']} marks.")
    if str(a.get("notes", "")).strip():
        txt += f" Note: _{a['notes']}_."
    rest = up.iloc[1:5]
    if not rest.empty:
        txt += "\n\nAfter that:\n" + "\n".join(f"- {fmt_date(r['d'])} · {r['assessment_type']} — {r['course']} ({rel_days(r['d'])})" for _, r in rest.iterrows())
    return {"text": txt + note_txt, "areas": ["Assessments", "Courses"]}


def ans_holiday(n: int | None) -> dict:
    b = upcoming_breaks()
    if n:
        b = b[b["n"] == n]
    if b.empty:
        return {"text": f"No upcoming holiday or leave is in the calendar data. {CANNOT}", "areas": ["Calendar"]}
    h = b.iloc[0]
    txt = f"Your next break is **{h['title']}** ({h['event_type']}) on **{fmt_date(h['d'], long=True)}** — {rel_days(h['d'])}."
    rest = b.iloc[1:4]
    if not rest.empty:
        txt += "\n\nComing after:\n" + "\n".join(f"- {fmt_date(r['d'])} · {r['title']} ({r['event_type']})" for _, r in rest.iterrows())
    return {"text": txt, "areas": ["Calendar"]}


def ans_topics(course) -> dict:
    topics = [t.strip() for t in str(course["syllabus"]).split(";") if t.strip()]
    if not topics:
        return {"text": f"**{course['course_name']}** has no syllabus topics in the data. {CANNOT}", "areas": ["Courses"]}
    lines = "\n".join(f"- {t}" for t in topics)
    return {"text": f"**{course['course_name']}** ({course['course_code']} · Sem {course['semester']} · {course['credits']} credits · "
                    f"{course['status']}) covers:\n{lines}\n\n_Topics come from courses.csv — check them against your official syllabus._",
            "areas": ["Courses"]}


def ans_scores(n: int | None) -> dict:
    g = score_summary()
    if g.empty:
        return {"text": f"No scores are recorded yet. {CANNOT}", "areas": ["Scores"]}
    if n:
        row = g[g["Semester"] == n]
        if row.empty:
            return {"text": f"No scores are recorded for Semester {n}. {CANNOT}", "areas": ["Scores"]}
        r = row.iloc[0]
        s = scores_view()
        s = s[s["n"] == n]
        lines = "\n".join(f"- {x['course']} · {x['assessment_type']}: {x['score']}/{x['max_marks']}"
                          + (f" (grade {x['grade']})" if str(x['grade']).strip() else "") for _, x in s.iterrows())
        return {"text": f"Semester {n} **prototype score percentage: {r['Percentage']:.1f}%** "
                        f"({r['Score']:.0f}/{r['Max']:.0f} across {int(r['Assessments'])} assessments).\n{lines}",
                "areas": ["Scores"]}
    lines = "\n".join(f"- Sem {int(r['Semester'])}: {r['Percentage']:.1f}% (cumulative {r['Cumulative']:.1f}%)" for _, r in g.iterrows())
    return {"text": f"Overall **prototype score percentage: {pct(g['Score'].sum(), g['Max'].sum()):.1f}%** "
                    f"(not an official CGPA).\n{lines}", "areas": ["Scores"]}


def ans_status(n: int | None) -> dict:
    s = semesters_view()
    if n:
        row = s[s["n"] == n]
        if row.empty:
            return {"text": f"Semester {n} is not in the data. {CANNOT}", "areas": ["Semesters"]}
        r = row.iloc[0]
        stt = sem_course_stats(n)
        return {"text": f"**Semester {n}** is **{r['status']}** ({r['academic_year']} {r['term']}). Credits: {r['cc']:.0f}/{r['tc']:.0f}. "
                        f"Courses: {stt['completed']} completed · {stt['in_progress']} in progress · {stt['not_started']} not started "
                        f"(weighted progress {stt['progress']:.0f}%).", "areas": ["Semesters", "Courses"]}
    tc, cc = s["tc"].sum(), s["cc"].sum()
    done = int((s["status"].str.lower() == "completed").sum())
    return {"text": f"You're in **Semester {CUR}**. Degree completion: **{pct(cc, tc):.1f}%** ({cc:.0f}/{tc:.0f} credits). "
                    f"{done} of {len(s)} semesters completed.", "areas": ["Semesters"]}


def ans_courses(n: int | None) -> dict:
    n = n or CUR
    c = D["courses"]
    c = c[num(c["semester"]) == n]
    if c.empty:
        return {"text": f"No courses recorded for Semester {n}. {CANNOT}", "areas": ["Courses"]}
    lines = "\n".join(f"- {r['course_code']} · **{r['course_name']}** · {r['credits']} cr · {r['status']}" for _, r in c.iterrows())
    return {"text": f"Semester {n} has **{len(c)} courses** ({num(c['credits']).sum():.0f} credits):\n{lines}", "areas": ["Courses"]}


def ans_plan(ql: str) -> dict:
    p = plan_view()
    if p.empty:
        return {"text": f"Your checklist is empty. {CANNOT}", "areas": ["Plan"]}
    od = p[p["health"] == "Overdue"].sort_values("d")
    ds = p[p["health"] == "Due Soon"].sort_values("d")
    done = int((p["health"] == "Done").sum())
    txt = f"Checklist: **{done}/{len(p)} done**, {len(ds)} due soon, {len(od)} overdue."
    if not od.empty:
        txt += "\n\n**Overdue:**\n" + "\n".join(f"- {r['item']} (was due {fmt_date(r['d'])})" for _, r in od.iterrows())
    if not ds.empty and "overdue" not in ql:
        txt += "\n\n**Due in the next 7 days:**\n" + "\n".join(f"- {r['item']} — {fmt_date(r['d'])} · {r['status']}" for _, r in ds.iterrows())
    return {"text": txt, "areas": ["Plan"]}


def local_answer(q: str) -> dict | None:
    ql = q.lower().strip()
    n = parse_semester(ql)
    course = find_course(ql)
    if re.fullmatch(r"(hi|hello|hey|help|yo|hii+|what can you do\??)[!. ]*", ql):
        return ans_help()
    if re.search(r"\b(write|poem|essay|story|joke|compose|summari[sz]e|explain|why|advice|suggest|recommend|motivat)\w*", ql):
        return None  # needs free-form generation -> Gemini, or the "AI API not connected" message
    if re.search(r"checklist|to-?do|\bplan\b|\btasks?\b|overdue|due soon|milestone", ql):
        return ans_plan(ql)
    if re.search(r"holiday|\bleave\b|vacation|\bbreak\b|day off|\boff\b", ql):
        return ans_holiday(n)
    if course is not None and re.search(r"topic|syllabus|cover|unit|chapter|contents?|about", ql):
        return ans_topics(course)
    if re.search(r"\bias?\b|ia\s?[12]|assessment|exam|\btest\b|quiz|assignment|viva|review|evaluation|deadline|\blab\b", ql):
        return ans_assessment(ql, n, course)
    if re.search(r"incomplete|\bleft\b|remaining|pending|not (yet )?(completed|done|finished)|unfinished|\bstill\b", ql):
        return ans_incomplete(n)
    if re.search(r"score|marks?|grade|percent|perform|result", ql):
        return ans_scores(n)
    if re.search(r"credit|complet|progress|how far|status|where am i", ql):
        return ans_status(n)
    if re.search(r"course|subject|paper|what.*(study|studying)", ql):
        return ans_courses(n)
    if course is not None:
        return ans_topics(course)
    return None


def build_context() -> str:
    parts = [f"TODAY: {TODAY.isoformat()}", f"CURRENT SEMESTER: {CUR}"]
    for key in ("semesters", "courses", "calendar", "assessments", "scores", "plan", "programme"):
        fname = TABLES[key][0]
        parts.append(f"### {fname}\n{D[key].to_csv(index=False)}")
    g = score_summary()
    if not g.empty:
        parts.append("### computed prototype score percentage by semester\n" + g.round(2).to_csv(index=False))
    return "\n\n".join(parts)


def gemini_answer(q: str, history: list[dict]) -> tuple[str, list[str], str]:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_KEY)
    hist = "\n".join(f"{m['role'].upper()}: {m['content'][:400]}" for m in history[-6:])
    prompt = (f"DEGREE OS DATA (the only source of truth):\n{build_context()}\n\n"
              f"RECENT CHAT:\n{hist or '(none)'}\n\nSTUDENT QUESTION: {q}")
    candidates = []
    for m in (get_secret("GEMINI_MODEL"), "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash"):
        if m and m not in candidates:
            candidates.append(m)
    last_err: Exception | None = None
    for model in candidates:
        try:
            resp = client.models.generate_content(
                model=model, contents=prompt,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION + "\n" + FORMAT_RULES, temperature=0.2),
            )
            text = (resp.text or "").strip()
            if not text:
                raise RuntimeError("empty response")
            areas: list[str] = []
            mm = re.search(r"^\s*DATA_AREAS:\s*(.+)$", text, re.M | re.I)
            if mm:
                areas = [a.strip(" .`*_") for a in mm.group(1).split(",") if a.strip(" .`*_")]
                text = (text[:mm.start()] + text[mm.end():]).strip()
            return text, areas, model
        except Exception as exc:  # noqa: BLE001
            last_err = exc
    raise last_err or RuntimeError("Gemini unavailable")


def degree_ai(q: str, history: list[dict]) -> dict:
    ql = q.lower()
    guard = rule_guard(ql)
    if guard:
        return guard
    local = local_answer(q)
    if GEMINI_KEY:
        try:
            text, areas, model = gemini_answer(q, history)
            return {"text": text, "areas": areas or (local or {}).get("areas", ["General"]), "engine": f"Gemini · {model}"}
        except Exception as exc:  # noqa: BLE001
            if local:
                local["engine"] = f"Local engine (Gemini unavailable: {type(exc).__name__})"
                return local
            return {"text": f"Gemini is unavailable right now ({type(exc).__name__}). {CANNOT}", "areas": [], "engine": "Local engine"}
    if local:
        local["engine"] = "Local engine"
        return local
    return {"text": "**AI API not connected.** This question needs free-form generation, which only works with a Gemini key. "
                    "I can still answer from your data — try *incomplete courses*, *next assessment*, *next holiday*, "
                    "*topics in a course*, *semester status*, *scores* or *checklist status*.",
            "areas": [], "engine": "Local engine", "refused": True}


SUGGESTIONS = [
    "What courses are still incomplete in Semester 5?",
    "When is my next internal assessment?",
    "Show my next holiday",
    "What topics are in Data Structures?",
    "What's overdue in my checklist?",
    "What is my official university CGPA formula?",
]


def render_msg(m: dict) -> None:
    with st.chat_message(m["role"], avatar="🧑‍🎓" if m["role"] == "user" else "🤖"):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            areas = ", ".join(m.get("areas") or []) or "—"
            badge = " · 🛡️ safe refusal" if m.get("refused") else ""
            st.caption(f"📂 Data used: {areas}  ·  ⚙️ {m.get('engine', 'Local engine')}{badge}")


def page_ai() -> None:
    header(10, "Ask Degree AI", "A grounded assistant that answers only from your Degree OS data.")
    if GEMINI_KEY:
        note("🟢 <b>Gemini connected.</b> Answers are generated from a context built only from your CSVs. "
             "University-rule questions pass through a local safety layer first.", "info")
    else:
        note("🟡 <b>AI API not connected</b> — running the deterministic local engine. Add <code>GEMINI_API_KEY</code> "
             "to Streamlit secrets to enable natural-language generation.")
    st.session_state.setdefault("chat", [])
    subhead("Try a question")
    cols = st.columns(3)
    for i, s in enumerate(SUGGESTIONS):
        if cols[i % 3].button(s, key=f"sug_{i}", width="stretch"):
            st.session_state["pending_q"] = s
    typed = st.chat_input("Ask about courses, dates, scores, plan…")
    q = typed or st.session_state.pop("pending_q", None)

    for m in st.session_state["chat"]:
        render_msg(m)
    if q:
        user_msg = {"role": "user", "content": q}
        st.session_state["chat"].append(user_msg)
        render_msg(user_msg)
        with st.spinner("Reading your Degree OS data…"):
            res = degree_ai(q, st.session_state["chat"][:-1])
        bot = {"role": "assistant", "content": res["text"], "areas": res.get("areas"), "engine": res.get("engine"),
               "refused": res.get("refused", False)}
        st.session_state["chat"].append(bot)
        render_msg(bot)
    if st.session_state["chat"]:
        if st.button("Clear conversation", key="clear_chat"):
            st.session_state["chat"] = []
            st.rerun()
    with st.expander("What the AI can see (context built from your CSVs)"):
        st.code(build_context()[:6000] + ("\n…" if len(build_context()) > 6000 else ""), language="text")


# ----------------------------------------------------------------------------
# 11 Data Admin
# ----------------------------------------------------------------------------
def admin_column_config(key: str) -> dict:
    cfg = st.column_config
    sem_opts = [str(i) for i in range(1, 9)]
    common = {"semester": cfg.SelectboxColumn("semester", options=sem_opts)}
    return {
        "semesters": {**common, "status": cfg.SelectboxColumn("status", options=COURSE_STATUSES)},
        "courses": {**common, "status": cfg.SelectboxColumn("status", options=COURSE_STATUSES),
                    "syllabus": cfg.TextColumn("syllabus", width="large", help="Separate topics with ;")},
        "calendar": {**common, "event_type": cfg.SelectboxColumn("event_type", options=EVENT_TYPES),
                     "date": cfg.TextColumn("date", help="YYYY-MM-DD")},
        "assessments": {**common, "assessment_type": cfg.SelectboxColumn("assessment_type", options=ASSESS_TYPES),
                        "status": cfg.SelectboxColumn("status", options=ASSESS_STATUSES), "date": cfg.TextColumn("date", help="YYYY-MM-DD")},
        "scores": {**common},
        "plan": {"status": cfg.SelectboxColumn("status", options=PLAN_STATUSES),
                 "category": cfg.SelectboxColumn("category", options=PLAN_CATEGORIES),
                 "scope": cfg.SelectboxColumn("scope", options=PLAN_SCOPES),
                 "target_date": cfg.TextColumn("target_date", help="YYYY-MM-DD")},
        "programme": {"value": cfg.TextColumn("value", width="large"), "source_reference": cfg.TextColumn("source_reference", width="large")},
    }.get(key, {})


def validate(key: str, df: pd.DataFrame) -> list[str]:
    errs = []
    _, required, _ = TABLES[key]
    for c in required:
        if c not in df.columns:
            errs.append(f"Missing required column `{c}`.")
    date_col = {"calendar": "date", "assessments": "date", "plan": "target_date"}.get(key)
    if date_col and date_col in df.columns:
        vals = df[date_col].fillna("").astype(str).str.strip()
        bad = vals[(vals != "") & dts(vals).isna()]
        if not bad.empty:
            errs.append(f"`{date_col}` must be YYYY-MM-DD — fix: {', '.join(bad.head(5))}")
    for c in ("credits", "total_credits", "completed_credits", "max_marks", "score"):
        if c in df.columns:
            vals = df[c].fillna("").astype(str).str.strip()
            bad = vals[(vals != "") & num(vals).isna()]
            if not bad.empty:
                errs.append(f"`{c}` must be numeric — fix: {', '.join(bad.head(5))}")
    return errs


def page_admin() -> None:
    header(11, "Data Admin", "Maintain the whole OS by editing tables — no code changes needed.")
    labels = {TABLES[k][2] + f"  ·  {TABLES[k][0]}": k for k in TABLES}
    choice = st.selectbox("Table", list(labels), key="admin_table")
    key = labels[choice]
    fname, required, _ = TABLES[key]
    df = D[key].copy()
    st.caption(f"Required columns: `{', '.join(required)}` · {len(df)} rows · add rows with the ➕ at the bottom, "
               "delete by selecting rows and pressing the bin icon.")
    edited = st.data_editor(df, key=f"admin_editor_{key}", num_rows="dynamic", hide_index=True, width="stretch",
                            column_config=admin_column_config(key))
    errs = validate(key, edited)
    for e in errs:
        st.error(e)
    b1, b2, b3 = st.columns([1, 1, 2])
    if b1.button(f"💾  Save {fname}", type="primary", key=f"save_{key}", disabled=bool(errs)):
        out = edited.copy().fillna("")
        out = out[~(out.astype(str).apply(lambda r: "".join(r).strip(), axis=1) == "")]
        save_table(key, out)
        st.success(f"Saved {len(out)} rows to data/{fname} (previous version backed up).")
        st.rerun()
    b2.download_button("⬇️  Download CSV", edited.to_csv(index=False).encode(), file_name=fname, mime="text/csv", key=f"dl_{key}")

    with st.expander("Replace this table by uploading a CSV"):
        up = st.file_uploader(f"Upload a new {fname}", type=["csv"], key=f"up_{key}")
        if up is not None:
            try:
                new = pd.read_csv(up, dtype=str, keep_default_na=False)
                errs2 = validate(key, new)
                st.dataframe(new.head(10), hide_index=True, width="stretch")
                if errs2:
                    for e in errs2:
                        st.error(e)
                elif st.button("Replace with uploaded file", key=f"rep_{key}"):
                    save_table(key, new)
                    st.success("Replaced.")
                    st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(f"Could not read that CSV: {exc}")

    if key in ("semesters", "courses"):
        with st.expander("Sync semester credits from course statuses"):
            st.write("Recalculates `total_credits` and `completed_credits` in semesters.csv from courses.csv, "
                     "and sets each semester's status from its courses.")
            if st.button("Run sync", key="sync"):
                s = D["semesters"].copy()
                for i, r in s.iterrows():
                    n = num(pd.Series([r["semester"]])).iloc[0]
                    if pd.isna(n):
                        continue
                    stt = sem_course_stats(int(n))
                    if stt["count"] == 0:
                        continue
                    s.at[i, "total_credits"] = f"{stt['credits']:.0f}"
                    s.at[i, "completed_credits"] = f"{stt['completed_credits']:.0f}"
                    s.at[i, "status"] = ("Completed" if stt["completed"] == stt["count"]
                                         else "Not Started" if stt["in_progress"] == 0 and stt["completed"] == 0 else "In Progress")
                save_table("semesters", s)
                st.success("semesters.csv synced from courses.csv")
                st.rerun()

    backups = sorted(BACKUP_DIR.glob(f"{Path(fname).stem}_*.csv")) if BACKUP_DIR.exists() else []
    st.caption(f"🗂️ {len(backups)} automatic backup(s) of {fname} in data/.backups/")


# ----------------------------------------------------------------------------
# Router
# ----------------------------------------------------------------------------
PAGES = {
    NAV[0]: page_dashboard, NAV[1]: page_semesters, NAV[2]: page_courses, NAV[3]: page_university,
    NAV[4]: page_calendar, NAV[5]: page_assessments, NAV[6]: page_status, NAV[7]: page_scorecard,
    NAV[8]: page_plan, NAV[9]: page_ai, NAV[10]: page_admin,
}
PAGES.get(page, page_dashboard)()

H("""<div class="foot-note">MY ENGINEERING DEGREE OS · data lives in /data/*.csv · edit it from Data Admin ·
prototype metrics are not official university figures</div>""")
