# wem2csv

**wem2csv** is a specialized tool designed for **Killing Floor 2**.
It automates the process of extracting and transcribing the **character voice lines** from the game’s Wwise `.wem` audio files.
It is not intended for use with music, weapons, or sound effects.

The program converts `.wem` into `.ogg`, normalizes them, and generates a CSV file that lists each filename and the spoken text contained in that voice line.

---

## ⚙️ Features

* Fully automated process: `.wem` to `.ogg` to `.csv`
* Designed specifically for **Killing Floor 2** voice lines
* Uses **Whisper** (via **faster whisper**) for accurate speech recognition
* GPU acceleration if available (NVIDIA CUDA)
* CLI automatically matches your system language (English fallback)
* Supported languages: English, French, German, Japanese, Russian, Spanish
* Optional English translation for non English lines
* Cleans up temporary data automatically
* Works as a simple console tool or standalone executable

---

## 📁 Project structure

```
wem2csv/
├─ pyproject.toml
├─ README.md
├─ LICENSE
├─ requirements.txt
├─ .gitignore
├─ tools/                # external converters (see below)
├─ wem-collection/       # temporary WEM workspace
├─ ogg-collection/       # temporary OGG workspace
└─ wem2csv/
   ├─ __init__.py
   ├─ __main__.py
   └─ cli.py
```

---

## 🔧 Installation

### 1. Clone the repository

```
git clone https://github.com/vonMort/wem2csv.git
cd wem2csv
```

### 2. Create a virtual environment

```
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```
pip install -e .
```

Note about Setuptools pin:
- This project temporarily pins `setuptools` to `<81` to avoid the upcoming removal of `pkg_resources` that `ctranslate2` still imports.
- Pip will install a compatible version automatically via `pyproject.toml`/`requirements.txt`.
- If your environment already has a newer Setuptools, you can downgrade explicitly:

```
pip install "setuptools<81"
```

If you have an NVIDIA GPU, install CUDA enabled PyTorch first:

```
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

Then install the remaining packages:

```
pip install faster-whisper pandas tqdm soundfile
```

---

## 🎧 Required external tools

These are **not included** in the repository because they are owned by other developers.
You must download them yourself and place them into a local folder named `tools` next to the script or executable.

| Tool           | Download                                                                                             | Purpose                                            |
| -------------- | ---------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| **ww2ogg.exe** | [http://www.hcs64.com/files/ww2ogg022.zip](http://www.hcs64.com/files/ww2ogg022.zip)                 | Converts `.wem` to `.ogg` using provided codebooks |
| **revorb.exe** | [http://yirkha.fud.cz/progs/foobar2000/revorb.exe](http://yirkha.fud.cz/progs/foobar2000/revorb.exe) | Normalizes and fixes OGG output                    |

The `tools` folder must contain:

```
tools/
├─ ww2ogg.exe
├─ revorb.exe
└─ packed_codebooks_aoTuV_603.bin
```

---

## 🚀 Usage

After installation, you can run the tool as a command:

```
wem2csv -d <KF2_WEM_DIRECTORY> -t <TEXT_FILE> [options]
```

### Example

```
wem2csv -d "D:\KF2\WwiseAudio" -t "D:\lists\voice_lines.txt"
```

This will:

1. Find all `.wem` filenames listed in the text file
2. Copy them from the given directory
3. Convert them into `.ogg`
4. Transcribe their spoken content using Whisper
5. Save everything into a CSV named `voicelines.csv`

---

## 🧠 Parameters

| Option              | Description                                                                     |
| ------------------- | ------------------------------------------------------------------------------- |
| `-d`, `--dir`       | Directory to search for `.wem` files                                            |
| `-t`, `--txt`       | Text file that lists `.wem` entries                                             |
| `--model`           | Whisper model: `tiny`, `base`, `small`, `medium`, `large-v3` (default: `small`) |
| `--audio-lang`      | Audio language: `auto`, `en`, `fr`, `de`, `ja`, `ru`, `es` (default: `auto`)    |
| `--ui-lang`         | CLI language: `system`, `en`, `fr`, `de`, `ja`, `ru`, `es` (default: `system`)  |
| `--transcript-lang` | Translate transcription to English (only English supported)                     |

---

## 📄 Output

* Converted `.ogg` files → `ogg-collection`
* Result CSV → `voicelines.csv`
* Format:
  `filename,voiceline`

Example:

```
filename,voiceline
commando_taunt_01.ogg,"Let's dance!"
medic_heal_02.ogg,"You're patched up!"
```

---

## ⚡ GPU acceleration

If an NVIDIA GPU is available, the tool automatically uses CUDA for Whisper.
If not, it runs on CPU using quantized models for speed.

Recommended models:

* `small` → best balance of speed and quality
* `medium` → better accuracy, slower
* `large-v3` → maximum accuracy

---

## 🧩 Building an executable

To create a single file executable for Windows:

```
pip install pyinstaller
pyinstaller --onefile --name wem2csv wem2csv/cli.py
```

Make sure your folder contains:

```
wem2csv.exe
tools/
├─ ww2ogg.exe
├─ revorb.exe
└─ packed_codebooks_aoTuV_603.bin
```

You can now simply run:

```
wem2csv.exe -d "D:\KF2\WwiseAudio" -t "D:\lists\voice_lines.txt"
```

---

## ⚖️ Legal information

This tool was developed for **personal research and modding** purposes within the **Killing Floor 2** community.
It does not contain or distribute any of the game’s original data or assets.

You must own a legitimate copy of the game to use this software.

* Do not share or redistribute extracted voice content.
* Do not use this tool for music, weapons, or SFX. It is meant only for **character voice lines**.
* The included Python source code is MIT licensed.
* The external converter binaries belong to their respective creators.

Links for convenience only:
[ww2ogg (by hcs64)](http://www.hcs64.com/files/ww2ogg022.zip)
[revorb (by yirkha)](http://yirkha.fud.cz/progs/foobar2000/revorb.exe)

---

## 🪪 License

MIT License © 2025 Mo

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, subject to the following conditions:

See the full license text in [LICENSE](LICENSE).

---

## 🧭 Credits

* **Developed by:** [vonMort](https://github.com/vonMort)
* **ww2ogg** by **HCS**
* **revorb** by **Yirkha**
* **faster whisper** by **Guillaume Klein**
* **Whisper** by **OpenAI**

---

## 💬 Summary

| Component      | Default                            | Description                                        |
| -------------- | ---------------------------------- | -------------------------------------------------- |
| CLI language   | System language (fallback English) | Automatic detection                                |
| Audio language | Auto                               | Whisper auto detect                                |
| Model          | small                              | Balanced speed and accuracy                        |
| Translation    | Disabled                           | Use `--transcript-lang en` for English translation |
| GPU            | Auto detect                        | CUDA if available                                  |
| Cleanup        | Deletes WEM files on success       | Keeps them on failure                              |

---

**Author:** Mo
**GitHub:** [vonMort](https://github.com/vonMort)
**Project:** `wem2csv`
**Purpose:** Automated and language aware transcription of Killing Floor 2 character voice lines for documentation and analysis.

---

*(End of README.md)*
