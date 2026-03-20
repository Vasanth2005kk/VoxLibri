# ─── Custom CSS ────────────────────────────────────────────────────────────

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --primary:    #ff8c00;
    --primary-dk: #c06a00;
    --accent:     #4fc3f7;
    --bg:         #0e1117;
    --surface:    #1a1d27;
    --surface2:   #242838;
    --border:     #2e3347;
    --text:       #e0e4f0;
    --text-muted: #7c8099;
    --success:    #4caf50;
    --warning:    #ff9800;
    --error:      #f44336;
}

html, body, [class*="css"]  { font-family: 'Inter', sans-serif !important; }

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* App background */
[data-testid="stAppViewContainer"] { background: var(--bg); color: var(--text); }
[data-testid="stSidebar"] {
    background: var(--surface);
    border-right: 1px solid var(--border);
}

/* ─── Header Banner ─────────────────────────────────────────── */
.app-header {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    border-radius: 14px;
    padding: 22px 30px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border: 1px solid var(--border);
    box-shadow: 0 8px 32px rgba(0,0,0,.4);
}
.app-header h1 {
    font-size: 2rem;
    font-weight: 700;
    color: #ffffff;
    margin: 0;
    background: linear-gradient(90deg, #ff8c00, #ffd54f);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.app-header .subtitle {
    color: var(--text-muted);
    font-size: .9rem;
    margin-top: 4px;
}
.version-badge {
    background: rgba(255,140,0,.15);
    border: 1px solid var(--primary);
    color: var(--primary);
    padding: 4px 12px;
    border-radius: 20px;
    font-size: .75rem;
    font-family: 'JetBrains Mono', monospace;
}

/* ─── Cards ─────────────────────────────────────────────────── */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 16px;
    transition: border-color .2s;
}
.card:hover { border-color: var(--primary); }
.card-title {
    font-size: .7rem;
    font-weight: 600;
    letter-spacing: .12em;
    text-transform: uppercase;
    color: var(--primary);
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 6px;
}

/* ─── Streamlit Widget Overrides ────────────────────────────── */
[data-testid="stSelectbox"] label,
[data-testid="stFileUploader"] label,
[data-testid="stSlider"] label,
[data-testid="stCheckbox"] label  { color: var(--text) !important; font-size: .85rem !important; }

.stButton > button {
    background: linear-gradient(135deg, var(--primary), var(--primary-dk)) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    padding: 10px 20px !important;
    transition: transform .15s, box-shadow .15s !important;
    width: 100% !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(255,140,0,.4) !important;
}
.stButton > button:disabled {
    background: var(--surface2) !important;
    color: var(--text-muted) !important;
    cursor: not-allowed !important;
    transform: none !important;
    box-shadow: none !important;
}

/* Progress & Status */
.status-box {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px;
    font-family: 'JetBrains Mono', monospace;
    font-size: .78rem;
    color: var(--text);
    min-height: 80px;
    max-height: 220px;
    overflow-y: auto;
    white-space: pre-wrap;
}
.status-box.running { border-color: var(--warning); }
.status-box.done    { border-color: var(--success); }
.status-box.error   { border-color: var(--error);   }

/* Language Pills */
.lang-pill {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: .72rem;
    font-weight: 600;
    margin: 2px;
}
.lang-eng { background: rgba(79,195,247,.15); color: #4fc3f7; border: 1px solid #4fc3f7; }
.lang-tam { background: rgba(255,140,0,.15);  color: var(--primary); border: 1px solid var(--primary); }

/* Device badges */
.device-cpu { color: #81c784; }
.device-gpu { color: #ff8a65; }

/* Scrollbar */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 4px; }

/* File uploader */
[data-testid="stFileUploader"] {
    border: 2px dashed var(--border) !important;
    border-radius: 10px !important;
    background: var(--surface2) !important;
    transition: border-color .2s !important;
}
[data-testid="stFileUploader"]:hover { border-color: var(--primary) !important; }

/* Expander */
[data-testid="stExpander"] {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 10px;
}

/* Tabs */
[data-testid="stTabs"] [role="tablist"] button {
    color: var(--text-muted) !important;
    border-radius: 8px 8px 0 0 !important;
}
[data-testid="stTabs"] [role="tablist"] button[aria-selected="true"] {
    color: var(--primary) !important;
    border-bottom: 2px solid var(--primary) !important;
}

/* Divider */
.st-divider { border-color: var(--border) !important; }

/* Audio player */
audio { border-radius: 8px; width: 100%; }
</style>
"""
