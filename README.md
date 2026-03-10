# 📚 VoxLibri

**VoxLibri** is a powerful, all-in-one solution for converting eBooks into high-quality audiobooks using state-of-the-art Text-to-Speech (TTS) technology. Whether you have a collection of EPUBs, PDFs, or even scanned images, VoxLibri can transform them into immersive audio experiences with natural-sounding voices and advanced customization.

---

## ✨ Key Features

- **🚀 Multiple TTS Engines:**
  - **Coqui XTTSv2:** Industry-leading voice cloning with emotional range and high fidelity.
  - **Suno Bark:** Generative audio model for diverse and expressive speech.
- **🎙️ Professional Voice Cloning:** Clone any voice using just a short audio sample (supports various formats like MP3, WAV, M4A).
- **📖 Broad Format Support:**
  - **eBooks:** EPUB, PDF, MOBI, AZW3, FB2, TXT, DOCX, and more.
  - **Images & Scans:** Integrated OCR (Tesseract) support for PNG, JPG, TIFF, etc.
- **🌍 Multilingual:** Support for dozens of languages including English, Tamil, Spanish, French, German, and many others.
- **🎨 Modern Dashboards:**
  - **Streamlit Web UI:** A sleek, dark-themed interface for easy management.
  - **Headless CLI:** Powerful command-line interface for automation and batch processing.
- **🛠️ Advanced Control:**
  - **SSML-like Tags:** Use `[pause]`, `[break]`, and `[voice:path]` to fine-tune the narration.
  - **Audio Processing:** Noise removal and music separation using Demucs.
  - **Format Conversion:** Output to M4B (with chapters), MP3, AAC, and more.
- **🖥️ Hardware Optimized:** Automatic setup for CPU, NVIDIA (CUDA), Apple Silicon (MPS), and Intel (XPU).

---

## 🛠️ Installation

VoxLibri is designed to be self-contained. The `build.py` script manages the entire environment for you.

### Prerequisites (Linux)
Ensure you have the basic build tools. Most other dependencies are handled automatically.
```bash
sudo apt-get update
sudo apt-get install python3-pip python3-venv git
```

### Quick Start
1. **Clone the repository:**
   ```bash
   git clone https://github.com/Vasanth2005kk/VoxLibri.git
   cd VoxLibri
   ```

2. **Run the installer and launcher:**
   ```bash
   python3 build.py
   ```
   *This will create a virtual environment, install system dependencies (Calibre, FFmpeg, Tesseract), and launch the application.*

---

## 🚀 How to Use

### 1. Web Interface (Recommended)
Launch the app using `build.py`. Once running, open your browser to:
`http://localhost:7860`

- **Upload:** Drop your eBook file.
- **Configure:** Select the language and TTS engine.
- **Clone:** Upload a voice sample to narrate the book in that specific voice.
- **Convert:** Click "Start" and wait for your audiobook to appear in the `audiobooks/` directory.

### 2. Headless Mode (CLI)
For power users or automation, use the headless flags:
```bash
./build.py --headless --ebook "/path/to/book.epub" --language eng --voice "/path/to/voice.wav"
```

---

