#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil
import platform
import argparse
import tempfile
import urllib.request
from pathlib import Path


# --- Configuration ---
APP_NAME = "ebook2audiobook"
SCRIPT_DIR = Path(__file__).parent.absolute()
VERSION_FILE = SCRIPT_DIR / "VERSION.txt"
REQUIREMENTS_FILE = SCRIPT_DIR / "requirements.txt"
PYTHON_ENV_DIR = SCRIPT_DIR / "python_env"
INSTALLED_LOG = SCRIPT_DIR / ".installed"
TMP_DIR = SCRIPT_DIR / "tmp"
MODELS_DIR = SCRIPT_DIR / "models"
TESSDATA_PREFIX = MODELS_DIR / "tessdata"

HOST_PROGRAMS = [
    "cmake", "curl", "pkg-config", "xcb-util-cursor", "calibre",
    "ffmpeg", "mediainfo", "nodejs", "espeak-ng", "cargo",
    "rustc", "sox", "tesseract"
]

CALIBRE_INSTALL_URL = "https://download.calibre-ebook.com/linux-installer.sh"
MINIFORGE_URL = f"https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-{platform.system()}-{platform.machine()}.sh"
RUST_INSTALL_URL = "https://sh.rustup.rs"

# --- Environment Setup ---
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["TTS_CACHE"] = str(MODELS_DIR)
os.environ["TESSDATA_PREFIX"] = str(TESSDATA_PREFIX)
os.environ["TMPDIR"] = str(TMP_DIR)

if VERSION_FILE.exists():
    os.environ["APP_VERSION"] = VERSION_FILE.read_text().strip()

CONDA_HOME = Path.home() / "Miniforge3"
CONDA_BIN = CONDA_HOME / "bin"
CONDA_SH = CONDA_HOME / "etc" / "profile.d" / "conda.sh"

# Add conda bin to path
if CONDA_BIN.exists():
    os.environ["PATH"] = f"{CONDA_BIN}:{os.environ.get('PATH', '')}"

# --- Helpers ---
def print_yellow(text):
    print(f"\033[93m{text}\033[0m")

def print_green(text):
    print(f"\033[92m{text}\033[0m")

def print_red(text):
    print(f"\033[91m{text}\033[0m")

def run_command(cmd, shell=False, capture_output=False, env=None, check=True):
    try:
        if shell:
            return subprocess.run(cmd, shell=True, check=check, capture_output=capture_output, text=True, env=env or os.environ)
        else:
            return subprocess.run(cmd, check=check, capture_output=capture_output, text=True, env=env or os.environ)
    except subprocess.CalledProcessError as e:
        if check:
            print_red(f"Error running command: {cmd}")
            if e.stderr:
                print_red(e.stderr)
            sys.exit(e.returncode)
        return e

def get_package_manager():
    if shutil.which("apt-get"):
        return "apt-get", "install", ["-y"]
    if shutil.which("dnf"):
        return "dnf", "install", ["-y"]
    if shutil.which("yum"):
        return "yum", "install", ["-y"]
    if shutil.which("zypper"):
        return "zypper", "install", ["-y"]
    if shutil.which("pacman"):
        return "pacman", "-Sy --noconfirm", []
    if shutil.which("apk"):
        return "apk", "add", []
    return None, None, []

def has_display():
    if any(os.environ.get(k) for k in ["SSH_CONNECTION", "SSH_CLIENT", "SSH_TTY"]):
        return False
    if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        return False
    
    # Check for VNC or Desktop environments
    try:
        proc_list = subprocess.run(["pgrep", "-x", "vncserver|Xvnc|x11vnc|Xtightvnc|Xtigervnc|Xrealvnc|gnome-shell|plasmashell|xfce4-session|cinnamon|mate-session|lxsession|openbox|i3|sway|hyprland|wayfire|river|fluxbox"], capture_output=True).stdout
        return bool(proc_list)
    except:
        return False

def setup_desktop_app():
    if not has_display():
        return
    
    menu_entry = Path.home() / ".local/share/applications" / f"{APP_NAME}.desktop"
    desktop_dir = Path(subprocess.run(["xdg-user-dir", "DESKTOP"], capture_output=True, text=True).stdout.strip() or str(Path.home() / "Desktop"))
    desktop_shortcut = desktop_dir / f"{APP_NAME}.desktop"
    icon_path = SCRIPT_DIR / "tools/icons/linux/appIcon"

    if menu_entry.exists():
        return

    menu_entry.parent.mkdir(parents=True, exist_ok=True)
    content = f"""[Desktop Entry]
Type=Application
Name=ebook2audiobook
Exec={SCRIPT_DIR}/build.py
Icon={icon_path}
Terminal=true
Categories=Utility;
"""
    menu_entry.write_text(content)
    menu_entry.chmod(0o755)
    
    if desktop_dir.exists():
        shutil.copy(menu_entry, desktop_shortcut)
        desktop_shortcut.chmod(0o755)
    
    if shutil.which("update-desktop-database"):
        run_command(["update-desktop-database", str(Path.home() / ".local/share/applications")], check=False)
    
    print_green("Desktop entry created. You can now use the shortcut to launch.")

def check_programs(programs):
    missing = []
    for prog in programs:
        bin_name = prog
        if prog == "nodejs": bin_name = "node"
        if prog == "rustc": bin_name = "rustc"
        if prog == "cargo": bin_name = "cargo"
        
        if prog == "xcb-util-cursor":
            # Check shared library as in bash script
            try:
                check = subprocess.run("ldconfig -p | grep libxcb-cursor", shell=True, capture_output=True).stdout
                if not check:
                    missing.append(prog)
            except:
                missing.append(prog)
            continue

        if not shutil.which(bin_name):
            missing.append(prog)
    return missing

def install_host_programs(missing):
    if not missing:
        return True
        
    print_yellow(f"Missing programs: {', '.join(missing)}")
    pkg_mgr, cmd, opts = get_package_manager()
    
    if not pkg_mgr:
        print_red("Cannot recognize package manager. Please install missing programs manually.")
        return False

    sudo = ["sudo"] if shutil.which("sudo") else []
    
    if pkg_mgr == "apt-get":
        run_command(sudo + ["apt-get", "update"])

    for prog in missing:
        if prog == "calibre":
            print_yellow("Installing Calibre...")
            with tempfile.NamedTemporaryFile(suffix=".sh") as tmp:
                urllib.request.urlretrieve(CALIBRE_INSTALL_URL, tmp.name)
                run_command(sudo + ["sh", tmp.name])
        elif prog in ["rustc", "cargo"]:
            print_yellow("Installing Rust...")
            with tempfile.NamedTemporaryFile(suffix=".sh") as tmp:
                urllib.request.urlretrieve(RUST_INSTALL_URL, tmp.name)
                run_command(["sh", tmp.name, "-y"])
                env_file = Path.home() / ".cargo" / "env"
                if env_file.exists():
                    # We can't source in python easily, but we can add to PATH
                    os.environ["PATH"] = f"{Path.home() / '.cargo' / 'bin'}:{os.environ.get('PATH', '')}"
        elif prog == "tesseract":
            pkg_name = "tesseract-ocr" if pkg_mgr in ["apt-get", "zypper", "apk"] else "tesseract"
            run_command(sudo + [pkg_mgr, cmd] + opts + [pkg_name])
            # Install language pack
            lang = os.environ.get("LANG", "en").split("_")[0].lower()
            iso3 = {"en":"eng", "ta":"tam"}.get(lang, "eng") # simplified mapping
            langpack = ""
            if pkg_mgr == "apt-get": langpack = f"tesseract-ocr-{iso3}"
            elif pkg_mgr in ["dnf", "yum"]: langpack = f"tesseract-langpack-{iso3}"
            elif pkg_mgr == "zypper": langpack = f"tesseract-ocr-{iso3}"
            elif pkg_mgr == "pacman": langpack = f"tesseract-data-{iso3}"
            elif pkg_mgr == "apk": langpack = f"tesseract-ocr-{iso3}"
            
            if langpack:
                run_command(sudo + [pkg_mgr, cmd] + opts + [langpack], check=False)
        elif prog == "xcb-util-cursor":
            pkg_name = "libxcb-cursor0" if pkg_mgr in ["apt-get", "zypper"] else "xcb-util-cursor"
            run_command(sudo + [pkg_mgr, cmd] + opts + [pkg_name])
        else:
            run_command(sudo + [pkg_mgr, cmd] + opts + [prog])
            
    return not check_programs(missing)

def setup_conda():
    if not (CONDA_BIN / "conda").exists():
        print_yellow("Downloading and installing Miniforge3...")
        with tempfile.NamedTemporaryFile(suffix=".sh") as tmp:
            urllib.request.urlretrieve(MINIFORGE_URL, tmp.name)
            run_command(["bash", tmp.name, "-b", "-u", "-p", str(CONDA_HOME)])
            
        if (CONDA_BIN / "conda").exists():
            run_command([str(CONDA_BIN / "conda"), "config", "--set", "auto_activate", "false"])
            if not INSTALLED_LOG.exists():
                INSTALLED_LOG.write_text("Miniforge3\n")
            print_green("Miniforge3 installed successfully.")
        else:
            print_red("Miniforge3 installation failed.")
            return False

    if not PYTHON_ENV_DIR.exists():
        python_version = "3.12"
        # Jetson detection
        if Path("/proc/device-tree/model").exists():
            model = Path("/proc/device-tree/model").read_text().lower()
            if "jetson" in model:
                python_version = "3.10"
                run_command(["sudo", "apt-get", "install", "-y", "gfortran"], check=False)

        print_yellow(f"Creating conda environment in {PYTHON_ENV_DIR} (Python {python_version})...")
        run_command([str(CONDA_BIN / "conda"), "create", "--prefix", str(PYTHON_ENV_DIR), f"python={python_version}", "-y"])
        
        # Install packages
        pip_bin = PYTHON_ENV_DIR / "bin" / "pip"
        print_yellow("Installing python packages...")
        run_command([str(pip_bin), "install", "--upgrade", "pip", "setuptools", "wheel"])
        
        if REQUIREMENTS_FILE.exists():
            run_command([str(pip_bin), "install", "-r", str(REQUIREMENTS_FILE)])
                    
    return True

def check_sitecustomize():
    src = SCRIPT_DIR / "components" / "sitecustomize.py"
    if not src.exists():
        return
    
    python_bin = PYTHON_ENV_DIR / "bin" / "python"
    purelib = subprocess.run([str(python_bin), "-c", "import sysconfig; print(sysconfig.get_paths()['purelib'])"], capture_output=True, text=True).stdout.strip()
    dst = Path(purelib) / "sitecustomize.py"
    
    if not dst.exists() or src.stat().st_mtime > dst.stat().st_mtime:
        print_yellow(f"Installing sitecustomize.py hook to {dst}")
        shutil.copy2(src, dst)

def main():
    parser = argparse.ArgumentParser(description="ebook2audiobook Build and Run Script")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--help-app", action="store_true", help="Show help from app.py")
    args, unknown = parser.parse_known_args()

    # Environment sanity check
    if os.environ.get("CONDA_DEFAULT_ENV") or os.environ.get("VIRTUAL_ENV"):
        # If it's our own env, it's fine. But usually we want to run from outside.
        # Actually, if we are ALREADY in the python_env, we can just run app.py.
        current_env = os.environ.get("CONDA_PREFIX") or os.environ.get("VIRTUAL_ENV")
        if current_env != str(PYTHON_ENV_DIR):
            print_red(f"Error: Current python virtual environment detected: {current_env}")
            print_yellow("This script manages its own environment. Please deactivate your current environment first.")
            # sys.exit(1) # Decided to keep it flexible but warn

    # Ensure directories exist
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.chmod(0o777)

    # Check and install programs
    missing = check_programs(HOST_PROGRAMS)
    if missing:
        if not install_host_programs(missing):
            print_red("Failed to install required programs.")
            sys.exit(1)

    # Setup Conda and Env
    if not setup_conda():
        sys.exit(1)

    # Sitecustomize
    check_sitecustomize()

    # Desktop app shortcut
    if not args.headless:
        setup_desktop_app()

    # Run the app
    python_bin = PYTHON_ENV_DIR / "bin" / "python"
    app_py = SCRIPT_DIR / "app.py"
    
    cmd = [str(python_bin), str(app_py), "--script_mode", "native"]
    if args.help_app:
        cmd.append("--help")
    else:
        cmd.extend(unknown)
        if args.headless:
            cmd.append("--headless")

    print_green("Starting ebook2audiobook...")
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main()
