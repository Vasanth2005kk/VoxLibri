"""
Streamlit UI for Ebook2Audiobook
Replaces the Gradio interface with a modern, dark-themed Streamlit UI.
Supports: English & Tamil | CPU & GPU | Voice Cloning | Multiple TTS Engines
"""

import os
import sys
import uuid
import time
import shutil
import threading
import subprocess
import queue
import streamlit as st
from pathlib import Path

# ─── ensure project root is importable ─────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.conf import (
    default_device, default_output_format, default_output_channel,
    devices, ebook_formats, voice_formats, output_formats,
    default_output_split, interface_component_options,
    interface_host, interface_port, NATIVE
)
from lib.conf_lang import language_mapping, default_language_code
from lib.conf_models import (
    TTS_ENGINES, default_engine_settings, default_fine_tuned,
    default_tts_engine
)

# ─── Page Config ───────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Ebook2Audiobook",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

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

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ─── Helpers ───────────────────────────────────────────────────────────────

def _prog_version() -> str:
    vfile = PROJECT_ROOT / "VERSION.txt"
    return vfile.read_text().strip() if vfile.exists() else "dev"

VERSION = _prog_version()

def _get_language_options():
    return [
        (
            f"{d['name']} — {d['native_name']}" if d['name'] != d['native_name'] else d['name'],
            code
        )
        for code, d in language_mapping.items()
    ]

def _get_device_options():
    return [(k, v['proc']) for k, v in devices.items()]

def _get_tts_engine_options(language: str):
    """Return TTS engines that support the given language."""
    compatible = []
    for eng_name, eng_key in TTS_ENGINES.items():
        settings = default_engine_settings.get(eng_key, {})
        langs = settings.get("languages", {})
        if language in langs:
            compatible.append((eng_name, eng_key))
    return compatible if compatible else [(k, v) for k, v in TTS_ENGINES.items()]

def _get_voice_list(language: str):
    """Return built-in voice names for the given language from the voices/ dir."""
    voices_dir = PROJECT_ROOT / "voices" / language
    if not voices_dir.exists():
        return []
    voices = []
    for d in sorted(voices_dir.iterdir()):
        if d.is_dir():
            for f in d.iterdir():
                if f.suffix.lower() == ".wav":
                    voices.append((f.name, str(f)))
    return voices

def _detect_gpu() -> list[str]:
    """Return list of available GPU processor tags."""
    available = []
    try:
        import torch
        if torch.cuda.is_available():
            available.append("cuda")
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            available.append("mps")
    except ImportError:
        pass
    try:
        result = subprocess.run(
            ["rocminfo"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=3
        )
        if result.returncode == 0 and b"Agent" in result.stdout:
            available.append("rocm")
    except Exception:
        pass
    return available

# ─── Session State Defaults ─────────────────────────────────────────────────

def _init_state():
    defaults = {
        "log_lines":        [],
        "status":           "idle",          # idle | running | done | error
        "audiobook_path":   None,
        "session_id":       None,
        "gpu_list":         None,
        "conversion_thread": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

if st.session_state.gpu_list is None:
    st.session_state.gpu_list = _detect_gpu()

# ─── Header ────────────────────────────────────────────────────────────────

gpu_tags = st.session_state.gpu_list
hw_badge = (
    f"<span class='device-gpu'>🖥️ GPU: {', '.join(gpu_tags).upper()}</span>"
    if gpu_tags
    else "<span class='device-cpu'>💻 CPU only</span>"
)
lang_badges = (
    "<span class='lang-pill lang-eng'>English</span>"
    "<span class='lang-pill lang-tam'>தமிழ்</span>"
)

st.markdown(f"""
<div class="app-header">
  <div>
    <h1>📚 Ebook2Audiobook</h1>
    <div class="subtitle">
      Convert eBooks to Audiobooks &nbsp;|&nbsp; {lang_badges} &nbsp;|&nbsp; {hw_badge}
    </div>
  </div>
  <div class="version-badge">v&nbsp;{VERSION}</div>
</div>
""", unsafe_allow_html=True)

# ─── Sidebar ───────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚙️ Settings")
    st.divider()

    # Language
    lang_opts = _get_language_options()
    lang_labels = [l for l, _ in lang_opts]
    lang_values = [v for _, v in lang_opts]
    default_lang_idx = lang_values.index(default_language_code) if default_language_code in lang_values else 0
    language_label = st.selectbox("🌐 Language", lang_labels, index=default_lang_idx, key="lang_label")
    language = lang_values[lang_labels.index(language_label)]

    # Device
    device_opts = _get_device_options()
    # put GPU first if available
    if gpu_tags:
        gpu_first = [d for d in device_opts if any(g in d[1].lower() for g in gpu_tags)]
        cpu_opts  = [d for d in device_opts if not any(g in d[1].lower() for g in gpu_tags)]
        device_opts = gpu_first + cpu_opts
    dev_labels = [k for k, _ in device_opts]
    dev_values = [v for _, v in device_opts]
    device_label = st.selectbox("🖥️ Processor", dev_labels, index=0, key="device_label")
    device = dev_values[dev_labels.index(device_label)]

    # TTS Engine
    engine_opts = _get_tts_engine_options(language)
    eng_labels = [k for k, _ in engine_opts]
    eng_values = [v for _, v in engine_opts]
    tts_engine_label = st.selectbox("🎙️ TTS Engine", eng_labels, index=0, key="tts_engine_label")
    tts_engine = eng_values[eng_labels.index(tts_engine_label)]

    st.divider()

    # Output format
    out_fmt = st.selectbox("📦 Output Format", output_formats,
                           index=output_formats.index(default_output_format) if default_output_format in output_formats else 0,
                           key="out_fmt")
    out_channel = st.selectbox("🔊 Channel", ["mono", "stereo"],
                               index=0 if default_output_channel == "mono" else 1,
                               key="out_channel")

    st.divider()

    # XTTSv2 advanced
    with st.expander("🔧 XTTSv2 Advanced Settings", expanded=False):
        xtts_cfg = default_engine_settings.get(TTS_ENGINES.get("XTTSv2", "xtts"), {})
        xtts_temperature = st.slider("Temperature",      0.05, 5.0,  float(xtts_cfg.get("temperature", 0.75)),  0.05, key="xtts_temp")
        xtts_rep_penalty = st.slider("Repetition Penalty", 1.0, 5.0, float(xtts_cfg.get("repetition_penalty", 2.0)), 0.1, key="xtts_rep")
        xtts_top_k       = st.slider("Top-k Sampling",   10,   100,  int(xtts_cfg.get("top_k", 40)),             1,    key="xtts_topk")
        xtts_top_p       = st.slider("Top-p Sampling",   0.1,  1.0,  float(xtts_cfg.get("top_p", 0.95)),         0.01, key="xtts_topp")
        xtts_speed       = st.slider("Speed",            0.5,  3.0,  float(xtts_cfg.get("speed", 1.0)),           0.1, key="xtts_speed")
        xtts_length_penalty = st.slider("Length Penalty",  0.5,  3.0,  float(xtts_cfg.get("length_penalty", 1.0)), 0.1, key="xtts_len_pen")
        xtts_num_beams   = st.slider("Num Beams",        1,    10,   int(xtts_cfg.get("num_beams", 1)),          1,    key="xtts_num_beams")
        xtts_text_split  = st.checkbox("Enable Text Splitting", value=bool(xtts_cfg.get("enable_text_splitting", True)), key="xtts_split")

    with st.expander("🌲 Bark Advanced Settings", expanded=False):
        bark_cfg = default_engine_settings.get(TTS_ENGINES.get("BARK", "bark"), {})
        bark_text_temp     = st.slider("Text Temperature",     0.0, 1.0, float(bark_cfg.get("text_temp",     0.7)), 0.01, key="bark_tt")
        bark_waveform_temp = st.slider("Waveform Temperature", 0.0, 1.0, float(bark_cfg.get("waveform_temp", 0.7)), 0.01, key="bark_wt")

    st.divider()
    st.markdown(
        "<div style='color:#555;font-size:.72rem;text-align:center'>Linux · English & Tamil · CPU / GPU</div>",
        unsafe_allow_html=True
    )

# ─── Main Layout ───────────────────────────────────────────────────────────

tab_convert, tab_models, tab_about = st.tabs(["📖 Convert", "🤖 Models", "ℹ️ About"])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 — Convert
# ═══════════════════════════════════════════════════════════════════════════
with tab_convert:
    col_left, col_right = st.columns([3, 2], gap="large")

    # ── LEFT: Input ───────────────────────────────────────────────────────
    with col_left:
        # eBook upload
        st.markdown('<div class="card"><div class="card-title">📂 Import eBook</div>', unsafe_allow_html=True)
        ebook_mode = st.radio("Mode", ["Single File", "Directory"], horizontal=True, key="ebook_mode")
        allowed_ext = [e.lstrip(".") for e in ebook_formats]
        if ebook_mode == "Single File":
            ebook_file = st.file_uploader(
                "Upload eBook",
                type=allowed_ext,
                key="ebook_upload",
                label_visibility="collapsed"
            )
        else:
            dir_path = st.text_input(
                "Directory path containing eBooks",
                placeholder="/path/to/ebooks/",
                key="ebook_dir"
            )
            ebook_file = None

        chapters_preview = st.checkbox("Show chapters preview before converting", value=False, key="chapters_preview")
        st.markdown('</div>', unsafe_allow_html=True)

        # Voice cloning
        st.markdown('<div class="card"><div class="card-title">🎤 Voice Cloning (Optional)</div>', unsafe_allow_html=True)
        voice_src = st.radio("Voice source", ["Built-in Voices", "Upload Custom Voice"], horizontal=True, key="voice_src")

        if voice_src == "Built-in Voices":
            builtin_voices = _get_voice_list(language)
            if builtin_voices:
                voice_labels = ["— Default —"] + [n for n, _ in builtin_voices]
                voice_paths  = [None] + [p for _, p in builtin_voices]
                v_idx = st.selectbox("Choose voice", voice_labels, key="builtin_voice_sel")
                selected_voice = voice_paths[voice_labels.index(v_idx)]
            else:
                st.info(f"No built-in voices found for **{language}**. Upload a custom voice file.")
                selected_voice = None
        else:
            voice_file_up = st.file_uploader(
                "Upload voice sample (.wav / .mp3)",
                type=[e.lstrip(".") for e in voice_formats],
                key="voice_upload"
            )
            selected_voice = None
            if voice_file_up is not None:
                tmp_voice = PROJECT_ROOT / "tmp" / f"voice_{uuid.uuid4().hex}{Path(voice_file_up.name).suffix}"
                tmp_voice.parent.mkdir(exist_ok=True)
                tmp_voice.write_bytes(voice_file_up.read())
                selected_voice = str(tmp_voice)
                st.audio(str(tmp_voice), format="audio/wav")

        st.markdown('</div>', unsafe_allow_html=True)

        # Custom model
        with st.expander("🧩 Custom TTS Model (ZIP)", expanded=False):
            custom_model_file = st.file_uploader(
                "Upload custom model ZIP",
                type=["zip"],
                key="custom_model_upload",
                help="ZIP must contain: config.json, model.pth, vocab.json (+ ref.wav for XTTSv2)"
            )
            custom_model_path = None
            if custom_model_file is not None:
                tmp_zip = PROJECT_ROOT / "tmp" / f"model_{uuid.uuid4().hex}.zip"
                tmp_zip.parent.mkdir(exist_ok=True)
                tmp_zip.write_bytes(custom_model_file.read())
                custom_model_path = str(tmp_zip)
                st.success(f"✅ Custom model uploaded: `{custom_model_file.name}`")

    # ── RIGHT: Session & Controls ─────────────────────────────────────────
    with col_right:
        st.markdown('<div class="card"><div class="card-title">🔧 Session</div>', unsafe_allow_html=True)
        session_id_input = st.text_input(
            "Resume Session ID (optional)",
            placeholder="Leave empty to start a new session",
            key="session_id_input"
        )
        st.markdown('</div>', unsafe_allow_html=True)

        # Summary card
        st.markdown(
            f"""
            <div class="card">
              <div class="card-title">📋 Conversion Summary</div>
              <table style="width:100%;font-size:.82rem;border-collapse:collapse">
                <tr><td style="color:var(--text-muted);padding:3px 0">Language</td>
                    <td><b>{language_label}</b></td></tr>
                <tr><td style="color:var(--text-muted);padding:3px 0">Device</td>
                    <td><b>{device_label}</b></td></tr>
                <tr><td style="color:var(--text-muted);padding:3px 0">TTS Engine</td>
                    <td><b>{tts_engine_label}</b></td></tr>
                <tr><td style="color:var(--text-muted);padding:3px 0">Output</td>
                    <td><b>{out_fmt} · {out_channel}</b></td></tr>
              </table>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Convert Button
        is_running = st.session_state.status == "running"
        convert_disabled = is_running or (
            ebook_mode == "Single File" and not st.session_state.get("ebook_upload")
        )

        col_btn_a, col_btn_b = st.columns(2)
        with col_btn_a:
            convert_clicked = st.button(
                "🚀 Convert" if not is_running else "⏳ Converting…",
                disabled=convert_disabled,
                key="convert_btn",
                use_container_width=True
            )
        with col_btn_b:
            cancel_clicked = st.button(
                "⛔ Cancel",
                disabled=not is_running,
                key="cancel_btn",
                use_container_width=True
            )

        # Status
        st.markdown("**Status**")
        status_cls = {
            "idle":    "",
            "running": "running",
            "done":    "done",
            "error":   "error",
        }.get(st.session_state.status, "")

        status_text = "\n".join(st.session_state.log_lines[-60:]) or "Idle — waiting for conversion…"
        st.markdown(
            f'<div class="status-box {status_cls}">{status_text}</div>',
            unsafe_allow_html=True
        )

        # Progress bar
        if is_running:
            st.progress(0, text="Converting…")

        # Audiobook output
        if st.session_state.audiobook_path and os.path.exists(st.session_state.audiobook_path):
            st.divider()
            st.markdown("### 🎧 Audiobook Ready")
            ab_path = st.session_state.audiobook_path
            ext = Path(ab_path).suffix.lower()
            if ext in (".mp3", ".wav", ".ogg", ".flac", ".m4a", ".m4b"):
                st.audio(ab_path)
            with open(ab_path, "rb") as f:
                st.download_button(
                    label=f"⬇️ Download {Path(ab_path).name}",
                    data=f,
                    file_name=Path(ab_path).name,
                    mime="audio/mpeg",
                    use_container_width=True,
                )

# ─── Conversion Logic ─────────────────────────────────────────────────────

def _run_conversion(args: dict, log_q: queue.Queue, done_event: threading.Event):
    """Run convert_ebook in a background thread; push log lines to queue."""
    import io
    import contextlib

    # Patch stdout / stderr to capture logs AND pass them to the real terminal
    original_out = sys.stdout
    original_err = sys.stderr

    class _Capture(io.TextIOBase):
        def __init__(self, is_err=False):
            self.orig = original_err if is_err else original_out

        def write(self, s):
            self.orig.write(s)
            self.orig.flush()

            clean_s = s.strip()
            if clean_s:
                # Filter out progress bars / download lines from the UI box
                if "%|" not in clean_s and "Downloading" not in clean_s:
                    # Also skip single characters or empty carriage returns
                    if len(clean_s) > 1:
                        log_q.put(clean_s)
            return len(s)

        def flush(self):
            self.orig.flush()

    cap_out = _Capture(False)
    cap_err = _Capture(True)
    with contextlib.redirect_stdout(cap_out), contextlib.redirect_stderr(cap_err):
        try:
            from lib.core import (
                SessionContext, SessionTracker, convert_ebook,
                convert_ebook_batch
            )
            import lib.core as _core

            _core.context = SessionContext()
            _core.context_tracker = SessionTracker()
            _core.active_sessions = set()

            session_id = args.get("session_id") or uuid.uuid4().hex
            _core.context.set_session(session_id)
            session = _core.context.get_session(session_id)

            session["script_mode"]      = NATIVE
            session["is_gui_process"]   = False
            session["device"]           = args["device"]
            session["tts_engine"]       = args["tts_engine"]
            session["language"]         = args["language"]
            session["voice"]            = args.get("voice")
            session["custom_model"]     = args.get("custom_model")
            session["output_format"]    = args["output_format"]
            session["output_channel"]   = args["output_channel"]
            session["chapters_preview"] = args.get("chapters_preview", False)
            session["audiobooks_dir"]   = args.get("audiobooks_dir", "Audiobooks")
            session["output_split"]     = args.get("output_split", False)
            session["output_split_hours"] = args.get("output_split_hours", 2.0)

            # XTTSv2 params
            session["xtts_temperature"]       = args.get("xtts_temperature", 0.75)
            session["xtts_repetition_penalty"] = args.get("xtts_repetition_penalty", 2.0)
            session["xtts_top_k"]             = args.get("xtts_top_k", 40)
            session["xtts_top_p"]             = args.get("xtts_top_p", 0.95)
            session["xtts_speed"]             = args.get("xtts_speed", 1.0)
            session["xtts_length_penalty"]    = args.get("xtts_length_penalty", 1.0)
            session["xtts_num_beams"]         = args.get("xtts_num_beams", 1)
            session["xtts_enable_text_splitting"] = args.get("xtts_enable_text_splitting", True)

            # Bark params
            session["bark_text_temp"]     = args.get("bark_text_temp", 0.7)
            session["bark_waveform_temp"] = args.get("bark_waveform_temp", 0.7)

            if args.get("ebook_list"):
                msg, ok = convert_ebook_batch({
                    **args, "id": session_id, "is_gui_process": False
                })
                out_path = session.get("audiobook") if ok else None
            else:
                msg, ok = convert_ebook({
                    **args, "id": session_id, "is_gui_process": False
                })
                out_path = session.get("audiobook") if ok else None

            if ok and out_path:
                log_q.put(f"✅ Done! Output: {out_path}")
                log_q.put(f"__AUDIOBOOK__:{out_path}")
            else:
                log_q.put(f"❌ Conversion failed: {msg}")
                log_q.put("__ERROR__")
        except Exception as exc:
            import traceback as _tb
            log_q.put(f"❌ Exception: {exc}")
            log_q.put(_tb.format_exc())
            log_q.put("__ERROR__")
        finally:
            done_event.set()


if "log_q"      not in st.session_state: st.session_state.log_q      = None
if "done_event" not in st.session_state: st.session_state.done_event = None

# Handle Convert click
if convert_clicked and not is_running:
    # Save ebook file to tmp
    ebook_src = None
    if ebook_mode == "Single File" and st.session_state.get("ebook_upload"):
        up = st.session_state.ebook_upload
        tmp_ebook = PROJECT_ROOT / "tmp" / f"ebook_{uuid.uuid4().hex}{Path(up.name).suffix}"
        tmp_ebook.parent.mkdir(exist_ok=True)
        tmp_ebook.write_bytes(up.read())
        ebook_src = str(tmp_ebook)
    elif ebook_mode == "Directory":
        ebook_src = dir_path if dir_path else None

    if not ebook_src:
        st.error("Please upload an eBook or specify a directory.")
    else:
        args = {
            "ebook":           ebook_src,
            "ebook_list":      None if ebook_mode == "Single File" else ebook_src,
            "language":        language,
            "device":          device,
            "tts_engine":      tts_engine,
            "fine_tuned":      default_fine_tuned,
            "voice":           selected_voice,
            "custom_model":    custom_model_path,
            "output_format":   out_fmt,
            "output_channel":  out_channel,
            "output_split":    False,
            "output_split_hours": 2.0,
            "chapters_preview": chapters_preview,
            "audiobooks_dir":  os.path.join(PROJECT_ROOT, "Audiobooks"),
            "session_id":      session_id_input.strip() or None,
            # XTTSv2 params
            "xtts_temperature":  xtts_temperature,
            "xtts_repetition_penalty": xtts_rep_penalty,
            "xtts_top_k":        xtts_top_k,
            "xtts_top_p":        xtts_top_p,
            "xtts_speed":        xtts_speed,
            "xtts_length_penalty": xtts_length_penalty,
            "xtts_num_beams":    xtts_num_beams,
            "xtts_enable_text_splitting": xtts_text_split,
            # Bark params
            "bark_text_temp":    bark_text_temp,
            "bark_waveform_temp": bark_waveform_temp,
        }

        lq = queue.Queue()
        de = threading.Event()
        st.session_state.log_q      = lq
        st.session_state.done_event = de
        import datetime
        ts_start = datetime.datetime.now().strftime("[%H:%M:%S]")
        st.session_state.log_lines  = [f"{ts_start} 🚀 Starting conversion…"]
        st.session_state.status     = "running"
        st.session_state.audiobook_path = None

        t = threading.Thread(target=_run_conversion, args=(args, lq, de), daemon=True)
        t.start()
        st.session_state.conversion_thread = t
        st.rerun()

# Drain log queue while running
if st.session_state.status == "running":
    lq = st.session_state.log_q
    de = st.session_state.done_event
    if lq:
        while not lq.empty():
            line = lq.get_nowait()
            if line.startswith("__AUDIOBOOK__:"):
                st.session_state.audiobook_path = line.split(":", 1)[1]
                st.session_state.status = "done"
            elif line == "__ERROR__":
                st.session_state.status = "error"
            else:
                import datetime
                ts_log = datetime.datetime.now().strftime("[%H:%M:%S]")
                st.session_state.log_lines.append(f"{ts_log} {line}")
    if de and de.is_set():
        if st.session_state.status == "running":
            st.session_state.status = "done"
    time.sleep(0.8)
    st.rerun()

# Handle Cancel
if cancel_clicked:
    de = st.session_state.get("done_event")
    if de:
        de.set()
    st.session_state.status = "idle"
    st.session_state.log_lines.append("⛔ Cancelled by user.")
    st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 — Models
# ═══════════════════════════════════════════════════════════════════════════
with tab_models:
    st.markdown("### 🤖 TTS Engine Capabilities")
    st.markdown(
        "The following engines are available. **XTTSv2** and **Fairseq** support Tamil."
    )

    for eng_name, eng_key in TTS_ENGINES.items():
        cfg = default_engine_settings.get(eng_key, {})
        langs = cfg.get("languages", {})
        rating = cfg.get("rating", {})
        supported = " · ".join(
            language_mapping[lc]['name'] for lc in langs if lc in language_mapping
        )

        def _star(n, max_n=5):
            return "🟠" * n + "⬛" * (max_n - n)

        with st.expander(f"**{eng_name}**  —  {supported or 'See docs'}", expanded=False):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("VRAM",     f"{rating.get('VRAM','?')} GB")
            c2.metric("CPU",      _star(rating.get('CPU', 0)))
            c3.metric("RAM",      f"{rating.get('RAM','?')} GB")
            c4.metric("Realism",  _star(rating.get('Realism', 0)))

            st.caption(f"Supported languages: `{', '.join(langs.keys()) or 'N/A'}`")
            if cfg.get("files"):
                st.caption(f"Required model files: `{', '.join(cfg['files'])}`")

    st.divider()
    st.markdown("### 🎙️ Built-in Voices")
    voices_root = PROJECT_ROOT / "voices"
    for lang_code, lang_info in language_mapping.items():
        lang_dir = voices_root / lang_code
        if lang_dir.exists():
            voices = list(lang_dir.rglob("*.wav"))
            st.markdown(f"**{lang_info['name']}** (`{lang_code}`) — {len(voices)} voice file(s)")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 — About
# ═══════════════════════════════════════════════════════════════════════════
with tab_about:
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.markdown(f"""
## 📚 Ebook2Audiobook `{VERSION}`

Convert eBooks into high-quality audiobooks using state-of-the-art TTS engines.

### ✨ Features
- **English & Tamil** language support
- **CPU & GPU** processing (CUDA, ROCm, XPU, Jetson)
- **Voice cloning** — use your own voice sample
- **Multiple TTS engines** — XTTSv2, Bark, Fairseq, VITS, and more
- **Multiple output formats** — M4B, MP3, FLAC, OGG, WAV, and more
- **Linux native** — no Docker, no Windows dependencies

### 🎛️ TTS Engines
| Engine | Tamil | Voice Clone | Quality |
|--------|-------|-------------|---------|
| **XTTSv2** | ✅ | ✅ | ⭐⭐⭐⭐⭐ |
| **Bark** | ✅ | ❌ | ⭐⭐⭐⭐ |
| **Fairseq** | ✅ | ❌ | ⭐⭐⭐ |
| **VITS** | ❌ | ❌ | ⭐⭐⭐ |

### 🚀 Usage
```bash
# GUI mode (this Streamlit UI)
streamlit run app_streamlit.py

# Headless / CLI mode
python app.py --headless --ebook /path/to/book.epub --language eng
```

### 🔗 Links
- [GitHub Repository](https://github.com/DrewThomasson/ebook2audiobook)
        """)
    with col_b:
        st.markdown("### 🤖 System Info")
        try:
            import torch
            st.success(f"PyTorch `{torch.__version__}`")
            if torch.cuda.is_available():
                st.info(f"CUDA `{torch.version.cuda}`  |  GPU: `{torch.cuda.get_device_name(0)}`")
            else:
                st.warning("CUDA not available — using CPU")
        except ImportError:
            st.error("PyTorch not installed")

        st.divider()
        st.markdown("### 📁 Project Structure")
        st.code("""
ebook2audiobook/
├── app.py              # CLI entry point
├── app_streamlit.py    # Streamlit launcher
├── requirements.txt
├── lib/
│   ├── conf.py
│   ├── conf_lang.py    # English + Tamil only
│   ├── conf_models.py
│   ├── core.py         # Conversion engine
│   ├── streamlit_ui.py # This file
│   └── classes/
├── voices/
│   ├── eng/
│   └── tam/
└── models/
""", language="")

        st.divider()
        st.markdown("### ⚡ Quick Commands")
        st.code("python app.py --help", language="bash")
        st.code("python app.py --headless --ebook book.epub --language tam --tts_engine XTTSv2", language="bash")
