import streamlit as st
import os, sys, json, math, base64
import pandas as pd
from pathlib import Path

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PGCET Evaluator 2026",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ─── DESIGN SYSTEM ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&family=Inter:wght@400;500;600;700&display=swap');

/* ══════════════════════════════════════
   RESET & BASE (Light Theme)
══════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box !important; }

html, body, .stApp {
    font-family: 'Inter', sans-serif !important;
    background: #fbfafc !important;
    color: #1c1b1b !important;
}

/* Kill Streamlit chrome */
header[data-testid="stHeader"],
footer, #MainMenu, .stDeployButton,
div[data-testid="stToolbar"],
div[data-testid="stDecoration"] { display: none !important; }

section[data-testid="stSidebar"] { display: none !important; }

.block-container {
    padding: 0 !important;
    max-width: 540px !important;
    margin: 0 auto !important;
    position: relative; z-index: 1;
    background: #fdfcff !important;
    min-height: 100vh !important;
    box-shadow: 0 0 40px rgba(0,0,0,0.02) !important;
}

/* ══════════════════════════════════════
   APPBAR (Light Theme)
══════════════════════════════════════ */
.oe-appbar {
    position: sticky; top: 0; z-index: 9999;
    display: flex; align-items: center; justify-content: space-between;
    height: 64px; padding: 0 20px;
    background: #ffffff;
    border-bottom: 1px solid #efebf3;
    margin-bottom: 20px;
}
.oe-appbar-brand {
    font-family: 'Outfit', sans-serif !important;
    font-size: 20px; font-weight: 800;
    color: #2c1079;
    letter-spacing: -0.02em; margin: 0;
}
.oe-appbar-profile {
    display: flex; align-items: center; justify-content: center;
    width: 36px; height: 36px;
    border-radius: 50%;
    cursor: pointer;
}

/* ══════════════════════════════════════
   PAGE WRAPPER
══════════════════════════════════════ */
.oe-page {
    padding: 0 18px;
    display: flex; flex-direction: column; gap: 20px;
    padding-bottom: 28px;
}

/* ══════════════════════════════════════
   HERO CARD (Deep Purple Gradient)
══════════════════════════════════════ */
.oe-hero {
    background: linear-gradient(135deg, #4c28c4 0%, #2c1079 100%);
    border-radius: 22px; padding: 26px 22px;
    display: flex; align-items: center; gap: 18px;
    box-shadow: 0 10px 30px rgba(44,16,121,0.2);
    position: relative; overflow: hidden;
}
.oe-hero::before {
    content:''; position:absolute;
    width:200px; height:200px; border-radius:50%;
    background:rgba(255,255,255,0.05); top:-60px; right:-50px;
    pointer-events:none;
}
.oe-hero-icon-container {
    width: 52px; height: 52px; border-radius: 16px; flex-shrink: 0;
    background: #ffffff;
    display: flex; align-items: center; justify-content: center;
    position: relative; z-index: 1;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.oe-hero-body { position:relative; z-index:1; }
.oe-hero-body h2 {
    font-family:'Outfit',sans-serif;
    font-size:19px; font-weight:800; color:white; margin:0 0 5px 0; line-height:1.25;
}
.oe-hero-body p {
    font-size:12.5px; color:rgba(255,255,255,0.72); margin:0; line-height:1.5;
}

/* ══════════════════════════════════════
   STEPPER
══════════════════════════════════════ */
.oe-stepper {
    display: flex; align-items: center; justify-content: space-between;
    background: #f5f3f7; padding: 10px 18px; border-radius: 999px;
    margin-bottom: 4px;
}
.oe-step {
    display: flex; align-items: center; gap: 8px;
    font-family: 'Outfit', sans-serif;
    font-size: 13px; font-weight: 700;
}
.oe-step-num {
    width: 26px; height: 26px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    color: white; font-size: 11px; font-weight: 800;
}
.oe-step-lbl {
    font-size: 12.5px;
}
.oe-step-line {
    flex: 1; height: 2px; background: #e2dff0; margin: 0 14px;
}
.oe-step.step-done .oe-step-num { background: #007a41; }
.oe-step.step-done .oe-step-lbl { color: #007a41; }
.oe-step.step-active .oe-step-num { background: #2c1079; }
.oe-step.step-active .oe-step-lbl { color: #2c1079; }
.oe-step.step-todo .oe-step-num { background: #c0c0c0; }
.oe-step.step-todo .oe-step-lbl { color: #8e8e8e; }

/* ══════════════════════════════════════
   SECTION LABEL
══════════════════════════════════════ */
.oe-sec {
    font-size:10.5px; font-weight:700; letter-spacing:0.09em;
    text-transform:uppercase; color:#432d8f; margin:4px 0 10px 0;
}

/* ══════════════════════════════════════
   SELECTS — override Streamlit (Light)
══════════════════════════════════════ */
div[data-testid="stSelectbox"] label {
    font-family:'Inter',sans-serif !important; font-size:12px !important;
    font-weight:700 !important; color:#484552 !important;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    border-radius:13px !important; border:1.5px solid #cac4d3 !important;
    background:#ffffff !important; font-size:14.5px !important;
    font-weight:500 !important; font-family:'Inter',sans-serif !important;
    padding:6px 12px !important; min-height:48px !important;
    color: #1c1b1b !important;
    transition:border 0.18s, box-shadow 0.18s !important;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"]:focus-within > div {
    border-color:#432d8f !important;
    box-shadow:0 0 0 3px rgba(67,45,143,0.13) !important;
}
/* Ensure option text color is visible in dropdown menu */
div[role="listbox"] ul li {
    color: #1c1b1b !important;
}

/* ══════════════════════════════════════
   ALERT BANNERS (Light Theme)
══════════════════════════════════════ */
.oe-alert-ok {
    display:flex; align-items:center; gap:10px;
    padding:13px 16px; border-radius:14px;
    background:#eafaf2; border:1.5px solid #77f8ab;
    color:#006d3e; font-size:13.5px; font-weight:600;
}
.oe-alert-warn {
    display:flex; align-items:center; gap:10px;
    padding:13px 16px; border-radius:14px;
    background:#fff8e1; border:1.5px solid #f9a825;
    color:#7b5800; font-size:13.5px; font-weight:600;
}
.oe-alert-tip {
    display:flex; align-items:flex-start; gap:10px;
    padding:13px 16px; border-radius:14px;
    background:#ede9ff; border:1.5px solid #9b89f5;
    color:#2c1079; font-size:13px; font-weight:500;
    line-height:1.5;
}

/* ══════════════════════════════════════
   TABS (Light flat style)
══════════════════════════════════════ */
div[data-testid="stTabs"] > div:first-child {
    background:transparent !important;
    border-bottom:1px solid #efebf3 !important;
    padding:0 !important; gap:4px !important; border-top:none !important; border-left:none !important; border-right:none !important;
}
button[data-baseweb="tab"] {
    border-radius:0px !important; border:none !important;
    font-size:13.5px !important; font-weight:600 !important;
    font-family:'Inter',sans-serif !important;
    color:#6e6a84 !important; background:transparent !important;
    padding:12px 16px !important; transition:all 0.18s !important;
    border-bottom:2px solid transparent !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    background:transparent !important; color:#2c1079 !important;
    border-bottom:2px solid #2c1079 !important;
    box-shadow:none !important;
}
div[data-testid="stTabContent"] { padding-top:18px !important; }

/* ══════════════════════════════════════
   FILE UPLOADER
══════════════════════════════════════ */
div[data-testid="stFileUploader"] label {
    font-family:'Inter',sans-serif !important; font-size:12px !important;
    font-weight:600 !important; color:#484552 !important;
}
div[data-testid="stFileUploader"] [data-testid="stFileUploadDropzone"] {
    border:2px dashed #cac4d3 !important; border-radius:18px !important;
    background:#ffffff !important; padding:30px 20px !important;
    transition:border-color 0.2s, background 0.2s !important;
    text-align:center !important;
}
div[data-testid="stFileUploader"] [data-testid="stFileUploadDropzone"]:hover {
    border-color:#432d8f !important; background:#f7f5fc !important;
}
div[data-testid="stFileUploader"] button {
    background:#e7deff !important; color:#2c1079 !important;
    border:none !important; border-radius:10px !important;
    font-family:'Inter',sans-serif !important; font-weight:600 !important;
}

/* ══════════════════════════════════════
   BUTTONS (Deep Purple)
══════════════════════════════════════ */
div.stButton > button {
    background:linear-gradient(135deg,#432d8f,#2c1079) !important;
    color:#ffffff !important; border:none !important;
    border-radius:15px !important; padding:15px 20px !important;
    font-size:15px !important; font-weight:700 !important;
    width:100% !important; font-family:'Inter',sans-serif !important;
    box-shadow:0 8px 26px rgba(67,45,143,0.25) !important;
    transition:filter 0.18s, transform 0.14s, box-shadow 0.18s !important;
    letter-spacing:-0.01em !important;
}
div.stButton > button:hover {
    filter:brightness(1.1) !important;
    transform:translateY(-2px) !important;
    box-shadow:0 14px 36px rgba(67,45,143,0.35) !important;
}
div.stButton > button:active {
    transform:scale(0.97) translateY(0) !important;
}

/* Hide Streamlit download button visually because we click it programmatically */
div[data-testid="stDownloadButton"] {
    display: none !important;
}

/* ══════════════════════════════════════
   IMAGE & CARDS
══════════════════════════════════════ */
.oe-image-card {
    position: relative;
    border-radius: 20px;
    overflow: hidden;
    border: 1.5px solid #e2dff3;
    box-shadow: 0 4px 24px rgba(0,0,0,0.04);
    margin: 16px 0;
}
.oe-live-preview-badge {
    position: absolute;
    bottom: 12px;
    left: 12px;
    background: rgba(0,0,0,0.75);
    color: #77f8ab;
    font-size: 10px;
    font-weight: 800;
    padding: 4px 10px;
    border-radius: 6px;
    letter-spacing: 0.05em;
}
.oe-image-overlay {
    position: absolute;
    bottom: 0; left: 0; right: 0;
    background: rgba(44, 16, 121, 0.85);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 18px;
    border-top: 1px solid rgba(255,255,255,0.1);
}

/* ══════════════════════════════════════
   DATA EDITOR & TEXT AREA
══════════════════════════════════════ */
div[data-testid="stDataEditor"] {
    border-radius:16px !important;
    border:1.5px solid rgba(202,196,211,0.25) !important;
    overflow:hidden !important; box-shadow:0 3px 14px rgba(0,0,0,0.04) !important;
}
textarea {
    border-radius:14px !important; border:1.5px solid #cac4d3 !important;
    font-family:'Inter',sans-serif !important; font-size:14px !important;
    background: #ffffff !important; color: #1c1b1b !important;
}
textarea:focus {
    border-color:#432d8f !important;
    box-shadow:0 0 0 3px rgba(67,45,143,0.13) !important;
}
div[data-testid="stCaptionContainer"] p {
    font-family:'Inter',sans-serif !important;
    font-size:12px !important; color:#797583 !important;
}

/* ══════════════════════════════════════
   SCORE CARD
══════════════════════════════════════ */
.oe-score-card {
    background: linear-gradient(135deg, #4c28c4 0%, #2c1079 100%);
    border-radius:24px; padding:28px 22px 22px;
    color:white; text-align:center;
    box-shadow:0 14px 42px rgba(44,16,121,0.3);
    position:relative; overflow:hidden;
}
.oe-score-card::before {
    content:''; position:absolute;
    width:240px; height:240px; border-radius:50%;
    background:rgba(255,255,255,0.04); top:-70px; right:-70px;
}
.oe-score-eval-lbl {
    font-size:20px; font-weight:700; color:#ffffff;
    margin:0 0 18px 0;
}
.oe-ring-wrap {
    position:relative; display:inline-flex;
    align-items:center; justify-content:center; margin-bottom:20px;
}
.oe-ring-inner {
    position:absolute; inset:0;
    display:flex; flex-direction:column; align-items:center; justify-content:center;
}
.oe-score-num {
    font-size:52px; font-weight:800; line-height:1;
    color:white; letter-spacing:-0.03em;
}
.oe-score-sub {
    font-size:11px; font-weight:600;
    color:rgba(255,255,255,0.5); margin-top:4px; letter-spacing:0.07em;
}
.oe-score-actions { display:flex; gap:12px; position:relative; z-index:1; }
.oe-btn-green {
    flex:1; padding:14px 10px; border-radius:14px;
    background:#7afbae; color:#00210f;
    font-family:'Inter',sans-serif; font-size:13px; font-weight:700;
    border:none; cursor:pointer; display:flex; flex-direction:column;
    align-items:center; gap:5px;
    transition:filter 0.18s,transform 0.14s;
}
.oe-btn-green:hover { filter:brightness(1.06); transform:translateY(-1px); }
.oe-btn-ghost {
    flex:1; padding:14px 10px; border-radius:14px;
    background:rgba(255,255,255,0.12); color:white;
    font-family:'Inter',sans-serif; font-size:13px; font-weight:700;
    border:1px solid rgba(255,255,255,0.2); cursor:pointer;
    display:flex; flex-direction:column; align-items:center; gap:5px;
    transition:background 0.18s, transform 0.14s;
}
.oe-btn-ghost:hover { background:rgba(255,255,255,0.2); transform:translateY(-1px); }

/* ══════════════════════════════════════
   STATS ROW
══════════════════════════════════════ */
.oe-stats { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; }
.oe-stat {
    background:#ffffff; border-radius:18px; padding:16px 6px;
    display:flex; flex-direction:column; align-items:center; gap:5px;
    box-shadow:0 2px 10px rgba(0,0,0,0.03);
    border:1.5px solid #e2dff3; text-align:center;
}
.oe-stat-ico { display:flex; align-items:center; justify-content:center; margin-bottom:2px; }
.oe-stat-val { font-size:24px; font-weight:800; line-height:1; }
.oe-stat-val.c { color:#007a41; }
.oe-stat-val.w { color:#ba1a1a; }
.oe-stat-val.s { color:#797583; }
.oe-stat-lbl { font-size:9.5px; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; color:#797583; }

/* ══════════════════════════════════════
   AUDIT HEADER & TABLE
══════════════════════════════════════ */
.oe-audit-hdr {
    display:flex; align-items:center; justify-content:space-between;
    margin-bottom:12px;
}
.oe-audit-title { font-size:16px; font-weight:700; color:#1c1b1b; }
.oe-badge {
    font-size:12px; font-weight:600; color:#4a3597;
    background:#e7deff; padding:5px 13px; border-radius:999px;
}
.oe-table-wrap {
    background:#ffffff; border-radius:20px;
    box-shadow:0 2px 14px rgba(0,0,0,0.04);
    border:1.5px solid #e2dff3; overflow:hidden;
}
.oe-table-wrap table { width:100%; border-collapse:collapse; }
.oe-table-wrap thead { background:#f6f3f2; }
.oe-table-wrap th {
    padding:13px 16px; font-size:11.5px; font-weight:700;
    letter-spacing:0.03em; color:#484552; text-align:left;
}
.oe-table-wrap th:nth-child(2),
.oe-table-wrap th:nth-child(3) { text-align:center; }
.oe-table-wrap tbody tr { border-top:1px solid #efebf3; transition:background 0.12s; }
.oe-table-wrap tbody tr:hover { background:#faf8fc; }
.oe-table-wrap td { padding:11px 16px; font-size:14px; font-weight:500; }
.oe-table-wrap td:nth-child(2),
.oe-table-wrap td:nth-child(3) { text-align:center; }
.oe-bub {
    display:inline-flex; align-items:center; justify-content:center;
    width:32px; height:32px; border-radius:50%;
    font-size:13px; font-weight:700;
}
.oe-bub.ck { background:#77f8ab; color:#007241; }
.oe-bub.wr { background:#ffdad6; color:#93000a; }
.oe-bub.ky { background:#f0edec; color:#1c1b1b; }
.oe-dash  { font-size:18px; color:#797583; font-weight:700; }

/* ══════════════════════════════════════
   BOTTOM NAV SPACER
══════════════════════════════════════ */
.oe-nav-spacer { height: 90px; }

/* ══════════════════════════════════════
   BOTTOM NAV
══════════════════════════════════════ */
.oe-bottom-nav {
    position:fixed; bottom:0; left:50%; transform:translateX(-50%);
    width:100%; max-width:540px;
    background:#ffffff;
    border-top:1px solid #e2dff3;
    display:flex; justify-content:space-around; align-items:center;
    height:74px; padding:0; z-index:9998;
}
.oe-nav-item {
    display:flex; flex-direction:column; align-items:center; gap:4px;
    font-size:11px; font-weight:700; color:#8a8894;
    cursor:pointer; width:25%; text-align:center;
}
.oe-nav-icon-container {
    width:56px; height:30px; border-radius:16px;
    display:flex; align-items:center; justify-content:center;
    transition:all 0.2s; font-size:18px; color:#6e6a84;
}
.oe-nav-item.active .oe-nav-icon-container {
    background:#432d8f; color:#ffffff;
}
.oe-nav-item.active {
    color:#432d8f;
}

/* Spinner */
.stSpinner > div { border-top-color:#432d8f !important; }
</style>
""", unsafe_allow_html=True)

# ─── CONSTANTS ──────────────────────────────────────────────────────────────────
KEYS_DIR = Path(r"C:\Users\vjaga\Downloads")
if not KEYS_DIR.exists():
    KEYS_DIR = Path(__file__).parent

MODEL_PATH = Path(__file__).parent / "best.pt"
if not MODEL_PATH.exists():
    MODEL_PATH = Path(r"C:\Users\vjaga\Downloads\omr test\best.pt")
MODEL_PATH = str(MODEL_PATH)

OMR_DIR = str(Path(__file__).parent)

def load_keys(course: str) -> dict:
    p = KEYS_DIR / ("mca_keys.json" if course == "MCA" else "mba_keys.json")
    if p.exists():
        with open(p) as f: return json.load(f)
    return {v: {str(q): "" for q in range(1, 101)} for v in ["A1","B1","C1","D1"]}

def save_keys(course: str, data: dict):
    p = KEYS_DIR / ("mca_keys.json" if course == "MCA" else "mba_keys.json")
    with open(p, "w") as f: json.dump(data, f, indent=4)

OPT = {"1":"A","2":"B","3":"C","4":"D"}

# ════════════════════════════════════════════════════════════════════════════════
#  APPBAR
# ════════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="oe-appbar" style="justify-content: flex-start; height: 72px; padding: 0 24px;">
  <span class="oe-appbar-brand" style="font-size: 30px; font-weight: 950; letter-spacing: -0.03em;">PGCET 2026 Evaluater</span>
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
#  PAGE CONTENT
# ════════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="oe-page">', unsafe_allow_html=True)

# \u2500\u2500 How-to Guide Card \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
_guide_img_path = Path(OMR_DIR) / "omr_crop_guide.png"
_guide_img_b64 = ""
if _guide_img_path.exists():
    import base64 as _b64mod
    with open(_guide_img_path, "rb") as _f:
        _guide_img_b64 = _b64mod.b64encode(_f.read()).decode()

_ref_img_tag = (
    f'<img src="data:image/png;base64,{_guide_img_b64}" '
    'style="width:100%;border-radius:12px;margin-top:8px;'
    'border:2px dashed rgba(255,255,255,0.35);" />'
    if _guide_img_b64 else ""
)

st.markdown(
    """
<div class="oe-hero" style="flex-direction:column;align-items:flex-start;gap:18px;padding:26px 22px 22px;">

<!-- header row -->
<div style="display:flex;align-items:center;gap:14px;width:100%;">
<div class="oe-hero-icon-container" style="flex-shrink:0;width:56px;height:56px;border-radius:18px;background:#ffffff;box-shadow:0 6px 20px rgba(0,0,0,0.15);">
<svg viewBox="0 0 24 24" width="28" height="28" stroke="#4c28c4" stroke-width="2.5"
fill="none" stroke-linecap="round" stroke-linejoin="round">
<circle cx="12" cy="12" r="10"/>
<line x1="12" y1="8" x2="12" y2="12"/>
<line x1="12" y1="16" x2="12.01" y2="16"/>
</svg>
</div>
<div>
<h2 style="font-family:'Outfit',sans-serif;font-size:23px;font-weight:900;
color:white;margin:0 0 4px 0;letter-spacing:-0.02em;line-height:1.2;">How to Get Your OMR Sheet</h2>
<p style="font-family:'Inter',sans-serif;font-size:13.5px;color:rgba(255,255,255,0.8);margin:0;line-height:1.4;">
Follow these steps to download, crop &amp; upload your PGCET OMR answer sheet
</p>
</div>
</div>

<!-- steps -->
<div style="width:100%;display:flex;flex-direction:column;gap:14px;">

<!-- Step 1 -->
<div style="background:rgba(255,255,255,0.07);border-radius:16px;padding:16px 18px;
border:1px solid rgba(255,255,255,0.15);box-shadow:0 4px 15px rgba(0,0,0,0.05);">
<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
<span style="background:#7afbae;color:#00210f;border-radius:50%;width:26px;height:26px;
display:flex;align-items:center;justify-content:center;
font-family:'Outfit',sans-serif;font-size:13px;font-weight:900;flex-shrink:0;">1</span>
<span style="font-family:'Outfit',sans-serif;font-size:16px;font-weight:800;color:white;letter-spacing:-0.01em;">Open the KEA OMR Portal</span>
</div>
<p style="font-family:'Inter',sans-serif;font-size:14.5px;color:#ffffff;margin:0 0 10px 38px;line-height:1.6;font-weight:400;">
Visit the official Karnataka Examinations Authority OMR result site:
</p>
<a href="https://cetonline.karnataka.gov.in/keaomrs/kries.aspx" target="_blank"
style="display:inline-block;margin-left:38px;background:rgba(122,251,174,0.16);
color:#7afbae;font-family:'Outfit',sans-serif;font-size:13px;font-weight:700;padding:8px 16px;
border-radius:10px;border:1.5px solid rgba(122,251,174,0.45);
text-decoration:none;word-break:break-all;transition:all 0.2s;">
&#127760; cetonline.karnataka.gov.in/keaomrs/kries.aspx
</a>
</div>

<!-- Step 2 -->
<div style="background:rgba(255,255,255,0.07);border-radius:16px;padding:16px 18px;
border:1px solid rgba(255,255,255,0.15);box-shadow:0 4px 15px rgba(0,0,0,0.05);">
<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
<span style="background:#7afbae;color:#00210f;border-radius:50%;width:26px;height:26px;
display:flex;align-items:center;justify-content:center;
font-family:'Outfit',sans-serif;font-size:13px;font-weight:900;flex-shrink:0;">2</span>
<span style="font-family:'Outfit',sans-serif;font-size:16px;font-weight:800;color:white;letter-spacing:-0.01em;">Fill Details &amp; Get OMR Sheet</span>
</div>
<p style="font-family:'Inter',sans-serif;font-size:14.5px;color:#ffffff;margin:0 0 10px 38px;line-height:1.6;font-weight:400;">
Select your <b style="color:white;font-weight:700;">Course</b>, <b style="color:white;font-weight:700;">District</b>, and <b style="color:white;font-weight:700;">Center</b> on the portal.
</p>
<div style="margin-left:38px;display:flex;flex-direction:column;gap:8px;">
<div style="background:rgba(0,0,0,0.18);padding:10px 14px;border-radius:10px;border:1px solid rgba(255,255,255,0.08);
font-family:'Inter',sans-serif;font-size:13.5px;color:rgba(255,255,255,0.95);line-height:1.5;">
💻 <b style="color:white;font-weight:700;">Computer Users:</b> Download/Save the OMR sheet PDF to your local drive.
</div>
<div style="background:rgba(0,0,0,0.18);padding:10px 14px;border-radius:10px;border:1px solid rgba(255,255,255,0.08);
font-family:'Inter',sans-serif;font-size:13.5px;color:rgba(255,255,255,0.95);line-height:1.5;">
📱 <b style="color:white;font-weight:700;">Mobile Users:</b> Take a screenshot or download the sheet directly to your phone.
</div>
</div>
</div>

<!-- Step 3 -->
<div style="background:rgba(255,255,255,0.07);border-radius:16px;padding:16px 18px;
border:1px solid rgba(255,255,255,0.15);box-shadow:0 4px 15px rgba(0,0,0,0.05);">
<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
<span style="background:#7afbae;color:#00210f;border-radius:50%;width:26px;height:26px;
display:flex;align-items:center;justify-content:center;
font-family:'Outfit',sans-serif;font-size:13px;font-weight:900;flex-shrink:0;">3</span>
<span style="font-family:'Outfit',sans-serif;font-size:16px;font-weight:800;color:white;letter-spacing:-0.01em;">Crop Only the Bubble Grid</span>
</div>
<div style="margin-left:38px;display:flex;flex-direction:column;gap:8px;margin-bottom:10px;">
<div style="background:rgba(0,0,0,0.18);padding:10px 14px;border-radius:10px;border:1px solid rgba(255,255,255,0.08);
font-family:'Inter',sans-serif;font-size:13.5px;color:rgba(255,255,255,0.95);line-height:1.5;">
💻 <b style="color:white;font-weight:700;">Computer Users:</b> Use <b style="color:white;font-weight:700;">Snipping Tool (Win+Shift+S)</b> to crop the answer bubbles.
</div>
<div style="background:rgba(0,0,0,0.18);padding:10px 14px;border-radius:10px;border:1px solid rgba(255,255,255,0.08);
font-family:'Inter',sans-serif;font-size:13.5px;color:rgba(255,255,255,0.95);line-height:1.5;">
📱 <b style="color:white;font-weight:700;">Mobile Users:</b> Open the screenshot in your gallery app and crop to the bubbles.
</div>
</div>
<p style="font-family:'Inter',sans-serif;font-size:14.5px;color:#ffffff;margin:0 0 10px 38px;line-height:1.6;font-weight:400;">
Crop <b style="color:white;font-weight:700;">only the Q1&ndash;Q100 answer bubbles</b> area. Do <b style="color:#ffdad6;font-weight:700;">NOT</b> include the header, roll number, or footer. Reference crop:
</p>
""" + _ref_img_tag + """
</div>

<!-- Step 4 -->
<div style="background:rgba(255,255,255,0.07);border-radius:16px;padding:16px 18px;
border:1px solid rgba(255,255,255,0.15);box-shadow:0 4px 15px rgba(0,0,0,0.05);">
<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
<span style="background:#7afbae;color:#00210f;border-radius:50%;width:26px;height:26px;
display:flex;align-items:center;justify-content:center;
font-family:'Outfit',sans-serif;font-size:13px;font-weight:900;flex-shrink:0;">4</span>
<span style="font-family:'Outfit',sans-serif;font-size:16px;font-weight:800;color:white;letter-spacing:-0.01em;">Upload &amp; Evaluate Below &#8595;</span>
</div>
<p style="font-family:'Inter',sans-serif;font-size:14.5px;color:#ffffff;margin:0 0 0 38px;line-height:1.6;font-weight:400;">
Upload the cropped <b style="color:white;font-weight:700;">JPG or PNG</b> in the uploader below.
The AI model will detect all 100 answers and generate your score instantly.
</p>
</div>

</div>
</div>
""",
    unsafe_allow_html=True,
)



# ── Stepper ───────────────────────────────────────────────────────────────────
step = 2 if st.session_state.get("uploader") else 1
stepper_html = f"""
<div class="oe-stepper">
  <div class="oe-step {'step-done' if step > 1 else 'step-active'}">
    <span class="oe-step-num">1</span>
    <span class="oe-step-lbl">Setup</span>
  </div>
  <div class="oe-step-line"></div>
  <div class="oe-step {'step-active' if step == 2 else 'step-todo'}">
    <span class="oe-step-num">2</span>
    <span class="oe-step-lbl">Upload</span>
  </div>
  <div class="oe-step-line"></div>
  <div class="oe-step step-todo">
    <span class="oe-step-num">3</span>
    <span class="oe-step-lbl">Grade</span>
  </div>
</div>
"""
st.markdown(stepper_html, unsafe_allow_html=True)

# ── Step 1 — Course & Booklet ─────────────────────────────────────────────────
st.markdown('<p class="oe-sec">Step 1 — Choose Course &amp; Booklet Version</p>', unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    course = st.selectbox("🎓 Course", ["MCA","MBA"], key="sel_course")
with c2:
    version = st.selectbox("📖 Booklet Version Code", ["A1","B1","C1","D1"], key="sel_version")

all_keys    = load_keys(course)
key_ans     = all_keys.get(version, {str(q): "" for q in range(1, 101)})
valid_cnt   = sum(1 for v in key_ans.values() if v in ["1","2","3","4"])

if valid_cnt == 100:
    st.markdown(f"""
    <div class="oe-alert-ok">
      <span>✅</span> All 100 answers loaded — {course} • {version}
    </div>""", unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="oe-alert-warn">
      <span>⚠️</span> Only <b>{valid_cnt}/100</b> answers set for {course} · {version} — go to <b>Set / Edit Key Answers</b>.
    </div>""", unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────


# ════════════════════════════════════════════════════════════════════════════════
#  TAB 1 — SCAN & GRADE
# ════════════════════════════════════════════════════════════════════════════════
st.markdown('<p class="oe-sec">Step 2 — Upload Student OMR Sheet</p>', unsafe_allow_html=True)

uploaded = st.file_uploader(
    "Choose student OMR image",
    type=["jpg","jpeg","png"], key="uploader",
    label_visibility="collapsed"
)
st.markdown(f"<p style='font-style:italic; font-size:12.5px; color:#797583; margin:4px 0 12px 0;'>Will be graded against {course} — Booklet {version}</p>", unsafe_allow_html=True)

temp_path = None
if uploaded:
    td = Path("temp_runs"); td.mkdir(exist_ok=True)
    temp_path = td / uploaded.name
    with open(temp_path, "wb") as f: f.write(uploaded.getbuffer())
    with open(temp_path, "rb") as image_file:
        img_base64 = base64.b64encode(image_file.read()).decode()
    st.markdown(f"""
    <div class="oe-image-card" style="border:2px solid #77f8ab;">
      <img src="data:image/jpeg;base64,{img_base64}" style="width:100%; display:block;" />
      <div class="oe-live-preview-badge">LIVE PREVIEW</div>
    </div>
    """, unsafe_allow_html=True)

if temp_path:
    if valid_cnt < 100:
        st.error("❌ Key answers incomplete. Go to **Set / Edit Key Answers** tab first.")
    else:
        st.markdown('<p class="oe-sec" style="margin-top:12px;">Step 3 — Evaluate</p>', unsafe_allow_html=True)
        if st.button("📋  Evaluate"):
            loader_slot = st.empty()
            loader_slot.markdown("""
            <div style="margin:18px 0 10px 0;">
              <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px;">
                <span style="font-size:14px;font-weight:700;color:#2c1079;">Analysing OMR sheet…</span>
                <span style="font-size:12px;color:#797583;">This takes ~1–2 sec</span>
              </div>
              <div style="position:relative;height:8px;border-radius:999px;background:#ede9ff;overflow:hidden;">
                <div style="
                  position:absolute;top:0;left:0;height:100%;width:40%;border-radius:999px;
                  background:linear-gradient(90deg,#7afbae,#432d8f,#7afbae);
                  background-size:200% 100%;
                  animation:pgbar 1.5s linear infinite;
                "></div>
              </div>
              <style>
                @keyframes pgbar {
                  0%   { background-position: 200% 0; left: -40%; }
                  100% { background-position: -200% 0; left: 110%; }
                }
              </style>
            </div>
            """, unsafe_allow_html=True)
            if True:
                try:
                    if OMR_DIR not in sys.path:
                        sys.path.insert(0, OMR_DIR)
                    from omr_pipeline import OMRPipeline
                    pipeline = OMRPipeline(model_path=MODEL_PATH, use_gpu=False, verbose=False)
                    student_answers = pipeline.process_sheet(str(temp_path), output_dir="temp_runs")
                    loader_slot.empty()

                    if not student_answers:
                        st.error("❌ Could not extract answers. Check image quality.")
                        st.stop()

                    rows = []
                    correct = incorrect = skipped = 0
                    for q in range(1, 101):
                        s_raw   = str(student_answers.get(q, "None"))
                        k_a     = str(key_ans.get(str(q), ""))
                        s_clean = s_raw.replace(" (Multiple)", "")
                        if s_raw == "None":
                            status = "skipped"; skipped += 1
                        elif s_clean == k_a:
                            status = "correct"; correct += 1
                        else:
                            status = "wrong"; incorrect += 1
                        rows.append({"q": q, "student": s_raw, "key": k_a, "status": status})

                    circ = 2 * math.pi * 84
                    score_html = f"""
                    <div id="result-anchor" style="scroll-margin-top:70px;"></div>
                    <div class="oe-score-card" id="result-score-card">
                      <canvas id="confetti-canvas" style="position:fixed;top:0;left:0;pointer-events:none;width:100vw;height:100vh;z-index:99999;"></canvas>
                      <p class="oe-score-eval-lbl">Evaluation Complete</p>
                      <div class="oe-ring-wrap">
                        <svg width="192" height="192" viewBox="0 0 192 192"
                             style="transform:rotate(-90deg);">
                          <circle cx="96" cy="96" r="84" fill="transparent"
                            stroke="rgba(255,255,255,0.1)" stroke-width="12"/>
                          <circle id="score-ring-progress" cx="96" cy="96" r="84" fill="transparent"
                            stroke="#7afbae" stroke-width="12"
                            stroke-dasharray="{circ:.2f}"
                            stroke-dashoffset="{circ - (correct / 100) * circ:.2f}"
                            stroke-linecap="round"/>
                        </svg>
                        <div class="oe-ring-inner">
                          <span class="oe-score-num" id="score-display">{correct}</span>
                          <span class="oe-score-sub">OUT OF 100</span>
                        </div>
                      </div>
                      <div class="oe-score-actions">
                        <button class="oe-btn-green" onclick="window.triggerDownload()">📥 Download Report (PDF)</button>
                        <button class="oe-btn-ghost" onclick="window.location.reload()">↻ Scan Another Sheet</button>
                      </div>
                    </div>

                    <script>
                    (function() {{
                      window.triggerDownload = function() {{
                        try {{
                          const btn = document.querySelector('div[data-testid="stDownloadButton"] button');
                          if (btn) {{
                            btn.click();
                          }} else {{
                            alert("Download not ready yet. Please wait.");
                          }}
                        }} catch (e) {{
                          console.error(e);
                        }}
                      }};

                      function initScoreAnimation() {{
                        const scoreDisplay = document.getElementById('score-display');
                        const ring = document.getElementById('score-ring-progress');
                        const anchor = document.getElementById('result-anchor');

                        if (!scoreDisplay || !ring || !anchor) {{
                          setTimeout(initScoreAnimation, 80);
                          return;
                        }}

                        const targetScore = {correct};
                        const circumference = {circ:.2f};

                        try {{
                          // Start animation from 0
                          scoreDisplay.textContent = 0;
                          ring.style.strokeDashoffset = circumference;

                          // Scroll into view safely
                          try {{
                            anchor.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                          }} catch (scrollErr) {{
                            try {{
                              anchor.scrollIntoView();
                            }} catch (e) {{}}
                          }}

                          const duration = 1800;
                          const startTime = performance.now();

                          function animate(now) {{
                            try {{
                              const elapsed = now - startTime;
                              const t = Math.min(elapsed / duration, 1);
                              const ease = 1 - Math.pow(1 - t, 3);
                              const cur = Math.round(ease * targetScore);
                              scoreDisplay.textContent = cur;
                              const offset = circumference - (cur / 100) * circumference;
                              ring.style.strokeDashoffset = offset;
                              if (t < 1) {{
                                requestAnimationFrame(animate);
                              }} else {{
                                scoreDisplay.textContent = targetScore;
                                ring.style.strokeDashoffset = circumference - (targetScore / 100) * circumference;
                                setTimeout(triggerConfetti, 100);
                              }}
                            }} catch (animateErr) {{
                              scoreDisplay.textContent = targetScore;
                              ring.style.strokeDashoffset = circumference - (targetScore / 100) * circumference;
                            }}
                          }}
                          requestAnimationFrame(animate);
                        }} catch (e) {{
                          // Fallback to static final display on any top-level error
                          scoreDisplay.textContent = targetScore;
                          ring.style.strokeDashoffset = circumference - (targetScore / 100) * circumference;
                        }}
                      }}

                      setTimeout(initScoreAnimation, 200);

                      function triggerConfetti() {{
                        const canvas = document.getElementById('confetti-canvas');
                        if (!canvas) return;
                        canvas.width  = window.innerWidth;
                        canvas.height = window.innerHeight;
                        const ctx = canvas.getContext('2d');

                        const colors = ['#f44336','#e91e63','#9c27b0','#3f51b5','#00bcd4','#4caf50','#ffeb3b','#ff9800','#7afbae','#ffffff'];
                        const particles = [];

                        // Burst from multiple positions for dramatic effect
                        const origins = [
                          {{ x: canvas.width * 0.5, y: canvas.height * 0.4 }},
                          {{ x: canvas.width * 0.2, y: canvas.height * 0.6 }},
                          {{ x: canvas.width * 0.8, y: canvas.height * 0.6 }}
                        ];

                        origins.forEach(origin => {{
                          for (let i = 0; i < 70; i++) {{
                            const angle = (Math.random() * Math.PI * 2);
                            const speed = Math.random() * 14 + 6;
                            particles.push({{
                              x: origin.x, y: origin.y,
                              w: Math.random() * 10 + 5,
                              h: Math.random() * 14 + 6,
                              color: colors[Math.floor(Math.random() * colors.length)],
                              vx: Math.cos(angle) * speed,
                              vy: Math.sin(angle) * speed - 8,
                              gravity: 0.3,
                              drag: 0.97,
                              rotX: Math.random() * 360,
                              rotY: Math.random() * 360,
                              rotSpX: (Math.random() - 0.5) * 18,
                              rotSpY: (Math.random() - 0.5) * 18,
                              opacity: 1,
                              fade: Math.random() * 0.007 + 0.004
                            }});
                          }}
                        }});

                        function draw() {{
                          ctx.clearRect(0, 0, canvas.width, canvas.height);
                          let any = false;
                          particles.forEach(p => {{
                            if (p.opacity <= 0) return;
                            any = true;
                            p.vx *= p.drag; p.vy *= p.drag; p.vy += p.gravity;
                            p.x += p.vx; p.y += p.vy;
                            p.rotX += p.rotSpX; p.rotY += p.rotSpY;
                            p.opacity -= p.fade;
                            ctx.save();
                            ctx.translate(p.x, p.y);
                            ctx.rotate(p.rotX * Math.PI / 180);
                            ctx.scale(Math.cos(p.rotY * Math.PI / 180), 1);
                            ctx.globalAlpha = Math.max(0, p.opacity);
                            ctx.fillStyle = p.color;
                            ctx.fillRect(-p.w/2, -p.h/2, p.w, p.h);
                            ctx.restore();
                          }});
                          if (any) requestAnimationFrame(draw);
                          else {{ ctx.clearRect(0,0,canvas.width,canvas.height); }}
                        }}
                        draw();
                      }}
                    }})();
                    </script>
                    """
                    st.markdown(score_html, unsafe_allow_html=True)

                    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

                    # ── Stats ─────────────────────────────────────────────
                    st.markdown(f"""
                    <div class="oe-stats">
                      <div class="oe-stat">
                        <span class="oe-stat-ico">
                          <svg viewBox="0 0 24 24" width="22" height="22" stroke="#007a41" stroke-width="3" fill="none"><circle cx="12" cy="12" r="10" stroke="#77f8ab" fill="#eafaf2"/><path d="M9 12l2 2 4-4"/></svg>
                        </span>
                        <span class="oe-stat-val c">{correct:02d}</span>
                        <span class="oe-stat-lbl">Correct</span>
                      </div>
                      <div class="oe-stat">
                        <span class="oe-stat-ico">
                          <svg viewBox="0 0 24 24" width="22" height="22" stroke="#93000a" stroke-width="3" fill="none"><circle cx="12" cy="12" r="10" stroke="#ffdad6" fill="#ffdad6"/><path d="M15 9l-6 6M9 9l6 6"/></svg>
                        </span>
                        <span class="oe-stat-val w">{incorrect:02d}</span>
                        <span class="oe-stat-lbl">Incorrect</span>
                      </div>
                      <div class="oe-stat">
                        <span class="oe-stat-ico">
                          <svg viewBox="0 0 24 24" width="22" height="22" stroke="#1c1b1b" stroke-width="3" fill="none"><circle cx="12" cy="12" r="10" stroke="#f0edec" fill="#f0edec"/><line x1="8" y1="12" x2="16" y2="12"/></svg>
                        </span>
                        <span class="oe-stat-val s">{skipped:02d}</span>
                        <span class="oe-stat-lbl">Skipped</span>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

                    # ── Annotated image (above audit) ─────────────────────
                    ann = Path("temp_runs") / f"{temp_path.stem}_annotated.jpeg"
                    if ann.exists():
                        st.markdown("""
                        <div class="oe-audit-hdr" style="margin-bottom:8px;">
                          <span class="oe-audit-title">Original Scan</span>
                        </div>""", unsafe_allow_html=True)
                        st.image(str(ann), use_container_width=True)
                        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

                    # ── Audit Table ───────────────────────────────────
                    st.markdown(f"""
                    <div class="oe-audit-hdr">
                      <span class="oe-audit-title">Detailed Question Audit</span>
                      <span class="oe-badge">{course} — Booklet {version}</span>
                    </div>""", unsafe_allow_html=True)

                    trs = ""
                    for r in rows:
                        q = r["q"]; s = r["student"]; k = r["key"]; st_r = r["status"]
                        s_l = OPT.get(s.replace(" (Multiple)",""), s)
                        k_l = OPT.get(k, k)
                        if st_r == "skipped":
                            s_cell = '<span class="oe-dash">—</span>'
                        elif st_r == "correct":
                            s_cell = f'<span class="oe-bub ck">{s_l}</span>'
                        else:
                            s_cell = f'<span class="oe-bub wr">{s_l}</span>'
                        k_cell = f'<span class="oe-bub ky">{k_l}</span>' if k else '<span class="oe-dash">—</span>'
                        trs += f"<tr><td style='font-weight:700'>Q{q}</td><td>{s_cell}</td><td>{k_cell}</td></tr>"

                    st.markdown(f"""
                    <div class="oe-table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>Question</th>
                            <th>Student Answer</th>
                            <th>Correct Key</th>
                          </tr>
                        </thead>
                        <tbody>{trs}</tbody>
                      </table>
                    </div>""", unsafe_allow_html=True)

                    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

                    # ── CSV Download ──────────────────────────────────────
                    df = pd.DataFrame(rows)
                    csv = df.to_csv(index=False).encode()
                    st.download_button(
                        "📥  Download CSV Report",
                        data=csv,
                        file_name=f"OMR_{course}_{version}_{uploaded.name}.csv",
                        mime="text/csv"
                    )

                except Exception as e:
                    loader_slot.empty()
                    st.error(f"Pipeline error: {e}")
                    st.exception(e)
else:
    st.markdown("""
    <div class="oe-alert-tip">
      <span>💡</span>
      <span>Upload a student OMR sheet image above — JPG or PNG, taken clearly in good light.</span>
    </div>""", unsafe_allow_html=True)



st.markdown('</div>', unsafe_allow_html=True)   # close .oe-page
