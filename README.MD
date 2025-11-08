# 🌍 JSON Translator Pro

Smart JSON translation tool with a multilingual interface, powered by OpenAI GPT models.  
Easily compare, analyze, and translate JSON files — it only translates new or missing keys.

## ☕ Support My Work

If you like my project and want to support me 💪  
you can buy me a coffee or send a tip via Revolut 👇

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-ffdd00?style=for-the-badge&logo=buymeacoffee&logoColor=black)](https://buymeacoffee.com/raur)
[![Revolut](https://img.shields.io/badge/Revolut-2800ff?style=for-the-badge&logo=revolut&logoColor=white)](https://revolut.me/raur)

---

## ✨ Features

- 🔁 Compare **OLD** and **NEW** JSON files by keys  
- 🌍 Translate only **new keys** using **GPT-4o-mini**  
- 📊 Real-time token counting and cost estimation  
- 🌐 Multi-language interface (from the `/lang/` folder)  
- 📑 Paginated selection dialog for large files  
- 🌙 Modern dark theme 
- 👁️ Preview and view translated JSON directly in the app  

---

## 🧩 Project Structure

```text
json-translator-pro/
├── json_translator_pro.py     # Main application
├── README.md                  # English documentation
├── README_RO.md               # Romanian documentation
├── requirements.txt           # Dependencies
├── .gitignore                 # Ignored files
└── lang/
    ├── en.json
    ├── ro.json
    └── ...
````

---

## 🐍 Installation and Setup

It is recommended to use a **virtual environment (venv)** to avoid library conflicts.

---

### 🪟 Windows:

```cmd
# 1. Open CMD in the project folder
cd C:\path\to\json-translator-pro

# 2. Create a virtual environment
python -m venv venv

# 3. Activate it
venv\Scripts\activate

# 4. Install required libraries
pip install -r requirements.txt
```

---

### 🐧 Mac / Linux:

```bash
# 1. Open Terminal in the project folder
cd /path/to/json-translator-pro

# 2. Create a virtual environment
python3 -m venv venv

# 3. Activate it
source venv/bin/activate

# 4. Install required libraries
pip install -r requirements.txt
```

---

### 🔚 Deactivate the environment (optional)

```bash
deactivate
```

---

## ▶️ Run the Application

### Windows:

```cmd
python json_translator_pro.py
```

### Mac / Linux:

```bash
python3 json_translator_pro.py
```

If everything is installed correctly, the app window will open.

---

## 🔑 OpenAI API Key Setup

1. Go to [https://platform.openai.com/account/api-keys](https://platform.openai.com/account/api-keys)
2. Copy your API key
3. Open the app and paste your key into the **API Key** field, then click **💾 Save Key**

The key is stored locally in the hidden `.api_key` file, which is ignored by Git.

---

## 🚀 How to Use

1. Open the app
2. Enter your OpenAI API key
3. Choose:

   * **Old file** → previously translated file (optional)
   * **New file** → file with new keys or English texts
4. Click **🔍 ANALYZE**

   * You’ll see:

     * New keys (to translate)
     * Obsolete keys (removed)
     * Kept keys (unchanged)
5. Click **☑️ SELECT** to choose which keys to translate
6. Click **👁️ PREVIEW** to see a preview of the final JSON
7. Click **🚀 TRANSLATE** to start translation
8. When finished, the translated file is automatically saved as:

   ```
   filename_translated_YYYYMMDD_HHMMSS.json
   ```
9. Click **View Output** to see the file inside the app.

---

## 💰 Cost Estimation

| Type   | Price per 1M tokens |
| ------ | ------------------: |
| Input  |               $0.15 |
| Output |               $0.60 |

The app automatically calculates real token usage and the approximate total cost.

---

## ⚙️ Requirements

* Python **3.8+**
* Internet connection
* OpenAI API key
* Tkinter (included with Python)
* Dependencies listed in `requirements.txt`

---

## 📦 `requirements.txt`

```text
openai>=1.0.0
tiktoken>=0.5.0
```

---

## 🚫 `.gitignore`

```text
# ===========================================
# 🔒 Sensitive files
# ===========================================
.api_key
.env
*.key
*.pem

# ===========================================
# 🧠 Python cache / compiled files
# ===========================================
__pycache__/
*.py[cod]
*$py.class
*.pyo

# ===========================================
# 🧱 Virtual environments
# ===========================================
venv/
env/
.venv/
ENV/
env.bak/

# ===========================================
# 📦 Build & distribution folders
# ===========================================
build/
dist/
develop-eggs/
downloads/
eggs/
.eggs/
parts/
sdist/
wheels/
share/python-wheels/
pip-wheel-metadata/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# ===========================================
# ⚙️ PyInstaller / cx_Freeze / Nuitka
# ===========================================
*.spec
*.manifest
*.dll
*.so
*.dylib
*.pkg
*.app
*.exe

# ===========================================
# 🧰 IDE / Editor files
# ===========================================
.vscode/
.idea/
*.sublime-project
*.sublime-workspace
.DS_Store
Thumbs.db

# ===========================================
# 🧾 Logs / temporary / backup
# ===========================================
*.log
*.bak
*.tmp
*.swp
*.old
*.orig
*.save
*.zip
*.7z
*.tar
*.tar.gz
*.rar

# ===========================================
# 🧩 Project-specific files
# ===========================================
*_translated_*.json
lang/__backup__/
test/
tests/
output/
cache/
__output__/

# ===========================================
# 🌐 Notebooks / AI temp
# ===========================================
*.ipynb_checkpoints
*.pt
*.pth
*.onnx
*.ckpt

# ===========================================
# 🪄 Other ignore examples
# ===========================================
.tox/
coverage/
.coverage
coverage.xml
htmlcov/
.mypy_cache/
pytest_cache/
.pytest_cache/
*.cover
*.coverage
.cache/
.cache/

```

---

## 💡 Tips

* You can add or modify translations for the interface inside `/lang/`.
* The interface updates automatically when switching languages.
* Translation runs in the background, keeping the app responsive.

## 👤 Author

**JSON Translator Pro**
* Created by **Raul, ChatGPT (OpenAI), and Claude (Anthropic)**
* License: **MIT**