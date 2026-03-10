#!/usr/bin/env bash

set -euo pipefail

: "${HOME:=$PWD}"

CURRENT_PYVENV=""

if [[ -n "${BASH_SOURCE:-}" ]]; then
	script_path="${BASH_SOURCE[0]}"
else
	script_path="$0"
fi

export BASHRCSOURCED=1
export SCRIPT_DIR="$(cd "$(dirname "$script_path")" >/dev/null 2>&1 && pwd -P)"
export PYTHONUTF8="1"
export PYTHONIOENCODING="utf-8"
export TTS_CACHE="$SCRIPT_DIR/models"
export TESSDATA_PREFIX="$SCRIPT_DIR/models/tessdata"
export TMPDIR="$SCRIPT_DIR/tmp"
export APP_VERSION=$(<"$SCRIPT_DIR/VERSION.txt")
export DEVICE_TAG="${DEVICE_TAG:-}"
export CONDA_HOME="$HOME/Miniforge3"
export CONDA_BIN_PATH="$CONDA_HOME/bin"
export CONDA_ENV="$CONDA_HOME/etc/profile.d/conda.sh"
export PATH="$CONDA_BIN_PATH:${PATH-}"

NATIVE="native"
ARCH=$(uname -m)
MIN_PYTHON_VERSION="3.10"
MAX_PYTHON_VERSION="3.12"
PYTHON_VERSION="$MAX_PYTHON_VERSION"
PYTHON_ENV="python_env"
SCRIPT_MODE="$NATIVE"
APP_NAME="ebook2audiobook"
OS_LANG=$(echo "${LANG:-en}" | cut -d_ -f1 | tr '[:upper:]' '[:lower:]')
HOST_PROGRAMS=("cmake" "curl" "pkg-config" "xcb-util-cursor" "calibre" "ffmpeg" "mediainfo" "nodejs" "espeak-ng" "cargo" "rust" "sox" "tesseract")
DEVICE_INFO_STR=""
CALIBRE_INSTALLER_URL="https://download.calibre-ebook.com/linux-installer.sh"
MINIFORGE_LINUX_INSTALLER_URL="https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
RUST_INSTALLER_URL="https://sh.rustup.rs"
INSTALLED_LOG="$SCRIPT_DIR/.installed"
UNINSTALLER="$SCRIPT_DIR/uninstall.sh"
WGET="$(command -v wget 2>/dev/null || true)"

typeset -A arguments=() # associative array
typeset -a programs_missing=() # indexed array

PACK_MGR=""
PACK_MGR_OPTIONS=""
ISO3_LANG="eng"
SUDO="sudo"

ARGS=("$@")

# Parse arguments
while (( $# > 0 )); do
	case "$1" in
		--*)
			key="${1#--}"
			if (( $# > 1 )) && [[ "$2" != --* ]]; then
				arguments[$key]=$2
				shift 2
				continue
			else
				arguments[$key]=true
				shift
				continue
			fi
			;;
		*)
			echo "Unknown option: $1"
			exit 1
			;;
	esac
done

SUDO="sudo"
SHELL_NAME="bash"

cd "$SCRIPT_DIR"

if [[ ! -f "$INSTALLED_LOG" ]]; then
	touch "$INSTALLED_LOG"
fi

############### FUNCTIONS ##############

###### DESKTOP APP
function has_no_display {
	if [[ -n "${SSH_CONNECTION-}" || -n "${SSH_CLIENT-}" || -n "${SSH_TTY-}" ]]; then
		return 1
	fi
	if [[ -z "${DISPLAY-}" && -z "${WAYLAND_DISPLAY-}" ]]; then
		return 1   # No display server → headless
	fi
	if pgrep -x vncserver	>/dev/null 2>&1 || \
		pgrep -x Xvnc		 >/dev/null 2>&1 || \
		pgrep -x x11vnc	   >/dev/null 2>&1 || \
		pgrep -x Xtightvnc	>/dev/null 2>&1 || \
		pgrep -x Xtigervnc	>/dev/null 2>&1 || \
		pgrep -x Xrealvnc	 >/dev/null 2>&1; then
		return 0
	fi

	if pgrep -x gnome-shell	   >/dev/null 2>&1 || \
		pgrep -x plasmashell	   >/dev/null 2>&1 || \
		pgrep -x xfce4-session	 >/dev/null 2>&1 || \
		pgrep -x cinnamon		  >/dev/null 2>&1 || \
		pgrep -x mate-session	  >/dev/null 2>&1 || \
		pgrep -x lxsession		 >/dev/null 2>&1 || \
		pgrep -x openbox		   >/dev/null 2>&1 || \
		pgrep -x i3				>/dev/null 2>&1 || \
		pgrep -x sway			  >/dev/null 2>&1 || \
		pgrep -x hyprland		  >/dev/null 2>&1 || \
		pgrep -x wayfire		   >/dev/null 2>&1 || \
		pgrep -x river			 >/dev/null 2>&1 || \
		pgrep -x fluxbox		   >/dev/null 2>&1; then
		return 0   # Desktop environment detected
	fi
	return 1
}

function open_desktop_app {
	(
		host=127.0.0.1
		port=7860
		url="http://$host:$port/"
		timeout=120
		start_time=$(date +%s)

		while ! nc -z "$host" "$port" >/dev/null 2>&1; do
			sleep 1
			elapsed=$(( $(date +%s) - start_time ))
			if [[ "$elapsed" -ge "$timeout" ]]; then
				exit 0
			fi
		done

		if command -v xdg-open >/dev/null 2>&1; then
			xdg-open "$url" >/dev/null 2>&1 &
		elif command -v gio >/dev/null 2>&1; then
			gio open "$url" >/dev/null 2>&1 &
		elif command -v x-www-browser >/dev/null 2>&1; then
			x-www-browser "$url" >/dev/null 2>&1 &
		else
			echo "No method found to open the default web browser." >&2
		fi
		exit 0
	) &
}

function linux_app {
	local MENU_ENTRY="$HOME/.local/share/applications/$APP_NAME.desktop"
	local DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
	local DESKTOP_SHORTCUT="$DESKTOP_DIR/$APP_NAME.desktop"
	local ICON_PATH="$SCRIPT_DIR/tools/icons/linux/appIcon"
	if [[ -f "$MENU_ENTRY" ]]; then
		open_desktop_app
		return 0
	fi
	mkdir -p "$HOME/.local/share/applications"
	cat > "$MENU_ENTRY" <<EOF
[Desktop Entry]
Type=Application
Name=ebook2audiobook
Exec=$SCRIPT_DIR/ebook2audiobook.sh
Icon=$ICON_PATH
Terminal=true
Categories=Utility;
EOF
	chmod +x "$MENU_ENTRY"
	mkdir -p "$HOME/Desktop" 2>&1 > /dev/null
	cp "$MENU_ENTRY" "$DESKTOP_SHORTCUT"
	chmod +x "$DESKTOP_SHORTCUT"
	if command -v update-desktop-database >/dev/null 2>&1; then
		update-desktop-database ~/.local/share/applications >/dev/null 2>&1
	fi
	echo -e "Next launch in GUI mode you just need to double click on the desktop shortcut or go to menu entry and click on ebook2audiobook icon."
	open_desktop_app
}

function check_desktop_app {
	if [[ " ${ARGS[*]} " == *" --headless "* ]] || ! has_no_display; then
		return 0
	fi
	linux_app
	return 0
}
#################

function get_iso3_lang {
	case "$1" in
		en) echo "eng" ;;
		fr) echo "fra" ;;
		de) echo "deu" ;;
		it) echo "ita" ;;
		es) echo "spa" ;;
		pt) echo "por" ;;
		ar) echo "ara" ;;
		tr) echo "tur" ;;
		ru) echo "rus" ;;
		bn) echo "ben" ;;
		zh) echo "chi_sim" ;;
		fa) echo "fas" ;;
		hi) echo "hin" ;;
		hu) echo "hun" ;;
		id) echo "ind" ;;
		jv) echo "jav" ;;
		ja) echo "jpn" ;;
		ko) echo "kor" ;;
		pl) echo "pol" ;;
		ta) echo "tam" ;;
		te) echo "tel" ;;
		yo) echo "yor" ;;
		*)  echo "eng" ;;
	esac
}

function check_required_programs {
	local programs=("$@")
	programs_missing=()
	for program in "${programs[@]}"; do
		local pkg="$program"
		local bin="$program"
		# Normalize special binaries
		[[ "$program" == "nodejs" ]] && bin="node"
		[[ "$program" == "rust" ]]   && bin="rustc"
		# Special case: tesseract OCR
		if [[ "$program" == "tesseract" || "$program" == "tesseract-ocr" ]]; then
			bin="tesseract"
			if command -v zypper >/dev/null 2>&1 || command -v apt-get >/dev/null 2>&1 || command -v apk >/dev/null 2>&1; then
				pkg="tesseract-ocr"
			else
				pkg="$program"
			fi
		elif [[ "$program" == "xcb-util-cursor" ]]; then
			bin=""
			if command -v apt-get >/dev/null 2>&1 || command -v zypper >/dev/null 2>&1; then
				pkg="libxcb-cursor0"
			elif command -v apk >/dev/null 2>&1; then
				pkg="xcb-util-cursor"
			else
				pkg="$program"
			fi
			check_xcb=$(ldconfig -p 2>/dev/null | grep libxcb-cursor)
			if [[ "$check_xcb" == "" ]]; then
				programs_missing+=("$pkg")
			fi
		fi
		if [[ "$bin" != "" ]]; then
			if ! command -v "$bin" &>/dev/null; then
				echo -e "\e[33m$pkg is not installed.\e[0m"
				programs_missing+=("$pkg")
			fi
		fi
	done
	(( ${#programs_missing[@]} == 0 ))
}

function install_programs {
	if [[ "$SUDO" == "sudo" ]]; then
		echo -e "\e[33mInstalling required programs. NOTE: you must have 'sudo' priviliges to install ebook2audiobook.\e[0m"
	fi
	local PACK_MGR_OPTIONS=""
	if command -v emerge &> /dev/null; then
		PACK_MGR="emerge"
	elif command -v dnf &> /dev/null; then
		PACK_MGR="dnf install"
		PACK_MGR_OPTIONS="-y"
	elif command -v yum &> /dev/null; then
		PACK_MGR="yum install"
		PACK_MGR_OPTIONS="-y"
	elif command -v zypper &> /dev/null; then
		PACK_MGR="zypper install"
		PACK_MGR_OPTIONS="-y"
	elif command -v pacman &> /dev/null; then
		PACK_MGR="pacman -Sy --noconfirm"
	elif command -v apt-get &> /dev/null; then
		$SUDO apt-get update
		PACK_MGR="apt-get install"
		PACK_MGR_OPTIONS="-y"
	elif [[ -f /etc/unraid-version ]] || command -v installplg &>/dev/null; then
		if ! command -v un-get &>/dev/null; then
			echo "  → Installing un-get plugin…"
			installplg ./ext/app/un-get.plg
			mkdir -p /boot/config/plugins/un-get
			cat > /boot/config/plugins/un-get/sources.list <<EOF
https://slackware.uk/slackware/slackware64-current/
https://slackware.uk/people/shinji257/unraid7/
EOF
			sleep 8
		fi
		PACK_MGR="un-get install"
	elif command -v apk &>/dev/null; then
		PACK_MGR="apk add"
	else
		echo "Cannot recognize your applications package manager. Please install the required applications manually."
		return 1
	fi

	if [[ -z "$WGET" ]]; then
		echo -e "\e[33m wget is missing! trying to install it… \e[0m"
		result=$(eval "$PACK_MGR wget $PACK_MGR_OPTIONS" 2>&1)
		result_code=$?
		if [[ $result_code -eq 0 ]]; then
			WGET="$(command -v wget 2>/dev/null || true)"
		else
			echo "Cannot 'wget'. Please install 'wget'  manually."
			return 1
		fi
	fi
	for program in "${programs_missing[@]}"; do
		if [[ "$program" == "calibre" ]]; then		
			if command -v $program >/dev/null 2>&1; then
				echo -e "\e[32m=============== Calibre OK! ===============\e[0m"
			else
				python3 -m pip uninstall -y lxml 2>/dev/null || true
				echo -e "\e[33mInstalling Calibre…\e[0m"
				tmp="$(mktemp)"
				$WGET -nv -O "$tmp" "$CALIBRE_INSTALLER_URL" || return 1
				if [[ "$SUDO" == "sudo" ]]; then
					$SUDO sh "$tmp"
				else
					sh "$tmp"
				fi
				rm -f "$tmp"
				eval "$SUDO $PACK_MGR $program $PACK_MGR_OPTIONS"				
				if command -v $program >/dev/null 2>&1; then
					echo -e "\e[32m=============== $program OK! ===============\e[0m"
				else
					echo -e "\e[31m=============== $program failed.\e[0m"
				fi
			fi	
		elif [[ "$program" == "rust" || "$program" == "rustc" ]]; then
			RUSTUP_TMP="$(mktemp)"
			curl -fL "$RUST_INSTALLER_URL" -o "$RUSTUP_TMP" || return 1
			sh "$RUSTUP_TMP" -y
			rm -f "$RUSTUP_TMP"
			if [[ -f "$HOME/.cargo/env" ]]; then
				source "$HOME/.cargo/env"
			fi
			if command -v $program &>/dev/null; then
				echo -e "\e[32m=============== $program OK! ===============\e[0m"
			else
				echo -e "\e[31m=============== $program failed.\e[0m"
			fi
		elif [[ "$program" == "tesseract" || "$program" == "tesseract-ocr" ]]; then
			eval "$SUDO $PACK_MGR $program $PACK_MGR_OPTIONS"
			if command -v $program >/dev/null 2>&1; then
				echo -e "\e[32m=============== $program OK! ===============\e[0m"
				ISO3_LANG="$(get_iso3_lang "${OS_LANG:-en}")"
				echo "Detected system language: $OS_LANG → installing Tesseract OCR language: $ISO3_LANG"
				langpack=""
				if command -v apt-get &>/dev/null; then
					langpack="tesseract-ocr-$ISO3_LANG"
				elif command -v dnf &>/dev/null || command -v yum &>/dev/null; then
					langpack="tesseract-langpack-$ISO3_LANG"
				elif command -v zypper &>/dev/null; then
					langpack="tesseract-ocr-$ISO3_LANG"
				elif command -v pacman &>/dev/null; then
					langpack="tesseract-data-$ISO3_LANG"
				elif command -v apk &>/dev/null; then
					langpack="tesseract-ocr-$ISO3_LANG"
				else
					echo "Cannot recognize your applications package manager. Please install the required applications manually."
					return 1
				fi
				if [[ -n "$langpack" ]]; then
					eval "$SUDO $PACK_MGR $langpack $PACK_MGR_OPTIONS"
					if tesseract --list-langs | grep -q "$ISO3_LANG"; then
						echo "Tesseract OCR language '$ISO3_LANG' successfully installed."
					else
						echo "Tesseract OCR language '$ISO3_LANG' not installed properly."
					fi
				fi
			else
				echo -e "\e[31m=============== $program failed.\e[0m"
			fi
		else
			eval "$SUDO $PACK_MGR $program $PACK_MGR_OPTIONS"
			if command -v $program >/dev/null 2>&1; then
				echo -e "\e[32m=============== $program OK! ===============\e[0m"
			else
				echo -e "\e[31m=============== $program failed.\e[0m"
			fi
		fi
	done
	if check_required_programs "${HOST_PROGRAMS[@]}"; then
		return 0
	else
		echo "Some programs didn't install successfuly, please report the log to the support"
	fi
}

function check_conda {

	function compare_versions {
		local ver1=$1
		local ver2=$2
		# Pad each version to 3 parts
		IFS='.' read -r v1_major v1_minor <<<"$ver1"
		IFS='.' read -r v2_major v2_minor <<<"$ver2"

		((v1_major < v2_major)) && return 1
		((v1_major > v2_major)) && return 2
		((v1_minor < v2_minor)) && return 1
		((v1_minor > v2_minor)) && return 2
		return 0
	}

	if ! command -v conda &> /dev/null || [[ ! -f "$CONDA_ENV" ]]; then
		local installer_path="/tmp/Miniforge3.sh"
		local config_path="$HOME/.bashrc"
		echo -e "\e[33mDownloading Miniforge3 installer…\e[0m"
		wget -O "$installer_path" "$MINIFORGE_LINUX_INSTALLER_URL"
		if [[ -f "$installer_path" ]]; then
			echo -e "\e[33mInstalling Miniforge3…\e[0m"
			bash "$installer_path" -b -u -p "$CONDA_HOME"
			rm -f "$installer_path"
			if [[ -f "$CONDA_HOME/bin/conda" ]]; then
				if [[ ! -f "$HOME/.condarc" ]]; then
					$CONDA_HOME/bin/conda config --set auto_activate false
				fi
				[[ -f "$config_path" ]] || touch "$config_path"
				[[ "$CONDA_HOME" == "$HOME/Miniforge3" ]] && grep -qxF 'export PATH="$HOME/Miniforge3/bin:$PATH"' "$config_path" || echo 'export PATH="$HOME/Miniforge3/bin:$PATH"' >> "$config_path"
				[[ "$CONDA_HOME" == "$HOME/Miniforge3" ]] && source "$config_path"
				echo -e "\e[32m=============== Miniforge3 OK! ===============\e[0m"
					if ! grep -iqFx "Miniforge3" "$INSTALLED_LOG"; then
						echo "Miniforge3" >> "$INSTALLED_LOG"
					fi
			else
				echo -e "\e[31m=============== Miniforge3 failed.\e[0m"
				return 1
			fi
		else
			echo -e "\e[31m=============== Miniforge3 installer not found!.\e[0m"
			return 1
		fi
	fi
	if [[ ! -d "$SCRIPT_DIR/$PYTHON_ENV" ]]; then
		if [[ -r /proc/device-tree/model ]]; then
			# Detect Jetson and select correct Python version
			MODEL="$(tr -d '\0' </proc/device-tree/model 2>/dev/null | tr 'A-Z' 'a-z' || true)"
			if [[ "$MODEL" == *jetson* ]]; then
				# needed gfortran to compile pip scipy pkg
				sudo apt-get install gfortran
				PYTHON_VERSION="3.10"
			fi
		else
			compare_versions "$PYTHON_VERSION" "$MIN_PYTHON_VERSION"
			case $? in
				1) PYTHON_VERSION="$MIN_PYTHON_VERSION" ;;
			esac
			compare_versions "$PYTHON_VERSION" "$MAX_PYTHON_VERSION"
			case $? in
				2) PYTHON_VERSION="$MAX_PYTHON_VERSION" ;;
			esac
		fi
		echo -e "\e[33mCreating ./python_env version $PYTHON_VERSION…\e[0m"
		chmod -R u+rwX,go+rX "$SCRIPT_DIR/audiobooks" "$SCRIPT_DIR/tmp" "$SCRIPT_DIR/models"
		conda update -n base -c conda-forge conda -y
		conda update --all -y
		conda clean --index-cache -y
		conda clean --packages --tarballs -y
		conda create --prefix "$SCRIPT_DIR/$PYTHON_ENV" python=$PYTHON_VERSION -y || return 1
		source "$CONDA_ENV" || return 1
		conda activate "$SCRIPT_DIR/$PYTHON_ENV" || return 1
		install_python_packages || return 1
		conda deactivate > /dev/null 2>&1
		conda deactivate > /dev/null 2>&1
	fi
	return 0
}

function install_python_packages {
	echo "[ebook2audiobook] Installing dependencies…"
	python3 -m pip cache purge > /dev/null 2>&1
	python3 -m pip install --upgrade pip setuptools wheel >nul 2>&1
	python3 -m pip install --upgrade llvmlite numba --only-binary=:all:
	total=$(grep -vE '^\s*($|#)' "$SCRIPT_DIR/requirements.txt" | wc -l | tr -d ' ')
	i=0
	progress_bar() {
		local cur=$1 max=$2 width=30
		local filled=$(( cur * width / max ))
		printf "\r[%-${width}s] %d/%d" "$(printf '#%.0s' $(printf '%*s' "$filled" ''))" "$cur" "$max"
	}
	while IFS= read -r pkg || [[ -n "$pkg" ]]; do
		[[ -z "$pkg" || "$pkg" == \#* ]] && continue
		((i++))
		progress_bar "$i" "$total"
		echo " Installing $pkg"
		python3 -m pip install --upgrade --no-cache-dir "$pkg"
	done < "$SCRIPT_DIR/requirements.txt"
	python3 -m unidic download || exit 1
	echo "[ebook2audiobook] Installation completed."
	return 0
}

function check_sitecustomized {
	local src_pyfile="$SCRIPT_DIR/components/sitecustomize.py"
	local site_packages_path=$(python3 -c "import sysconfig;print(sysconfig.get_paths()['purelib'])")
	local dst_pyfile="$site_packages_path/sitecustomize.py"
	if [ ! -f "$dst_pyfile" ] || [ "$src_pyfile" -nt "$dst_pyfile" ]; then
		if cp -p "$src_pyfile" "$dst_pyfile"; then
			echo "Installed sitecustomize.py hook in $dst_pyfile"
		else
			echo -e "\e[31m=============== sitecustomize.py hook error: copy failed.\e[0m" >&2
			exit 1
		fi
	fi
	return 0
}

######################################## MAIN Logic

if [[ -n "${arguments[help]+exists}" && ${arguments[help]} == true ]]; then
	python "$SCRIPT_DIR/app.py" "${ARGS[@]}"
else
	chmod 777 "$TMPDIR"
	# Check if running in a Conda or Python virtual environment
	if [[ -n "${CONDA_DEFAULT_ENV:-}" ]]; then
		CURRENT_PYVENV="${CONDA_PREFIX:-}"
	elif [[ -n "${VIRTUAL_ENV:-}" ]]; then
		CURRENT_PYVENV="$VIRTUAL_ENV"
	fi
	# If neither environment variable is set, check Python path
	if [[ -z "${CURRENT_PYVENV:-}" ]]; then
		PYTHON_PATH="$(command -v python 2>/dev/null || true)"
		if [[ ( -n "${CONDA_PREFIX:-}" && "$PYTHON_PATH" == "${CONDA_PREFIX:-}/bin/python" ) || \
				( -n "${VIRTUAL_ENV:-}" && "$PYTHON_PATH" == "${VIRTUAL_ENV:-}/bin/python" ) ]]; then
			CURRENT_PYVENV="${CONDA_PREFIX:-${VIRTUAL_ENV:-}}"
		fi
	fi
	# Output result if a virtual environment is detected
	if [[ -n "$CURRENT_PYVENV" ]]; then
		echo -e "\e[31m=============== Error: Current python virtual environment detected: $CURRENT_PYVENV..\e[0m"
		echo -e "This script runs with its own virtual env and must be out of any other virtual environment when it's launched."
		echo -e "If you are using conda then you would type in:"
		echo -e "conda deactivate"
		exit 1
	fi
	check_required_programs "${HOST_PROGRAMS[@]}" || install_programs || exit 1
	check_conda || { echo -e "\e[31m=============== check_conda() failed.\e[0m"; exit 1; }
	source "$CONDA_ENV" || exit 1
	conda activate "$SCRIPT_DIR/$PYTHON_ENV" || { echo -e "\e[31m=============== conda activate failed.\e[0m"; exit 1; }
	check_sitecustomized || exit 1
	check_desktop_app || exit 1
	python "$SCRIPT_DIR/app.py" --script_mode "$SCRIPT_MODE" "${ARGS[@]}" || exit 1
	conda deactivate > /dev/null 2>&1
	conda deactivate > /dev/null 2>&1
fi

exit 0
