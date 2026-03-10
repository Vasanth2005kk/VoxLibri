#!/usr/bin/env python3
"""
Ebook2Audiobook — Streamlit App Launcher
Run with:  streamlit run app_streamlit.py
           python app_streamlit.py
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent
    ui   = root / "lib" / "streamlit_ui.py"
    port = os.environ.get("STREAMLIT_PORT", "7860")
    host = os.environ.get("STREAMLIT_HOST", "0.0.0.0")

    cmd = [
        sys.executable, "-W", "ignore::UserWarning", "-W", "ignore::SyntaxWarning", "-m", "streamlit", "run",
        str(ui),
        "--server.address",     host,
        "--server.port",        port,
        "--server.headless",    "true",
        "--server.enableCORS",  "false",
        "--browser.gatherUsageStats", "false",
        "--theme.base",         "dark",
        "--theme.primaryColor", "#ff8c00",
        "--theme.backgroundColor",      "#0e1117",
        "--theme.secondaryBackgroundColor", "#1a1d27",
        "--theme.textColor",    "#e0e4f0",
        "--theme.font",         "sans serif",
    ]

    print(f"Starting Ebook2Audiobook Streamlit UI at http://{host}:{port}")
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nShutdown.")

if __name__ == "__main__":
    main()
