# 🌍 JSON Translator Pro

Traducător inteligent de fișiere JSON cu interfață multilingvă, bazat pe modelele GPT de la OpenAI.  
Compară, analizează și traduce rapid fișiere JSON — traduce doar cheile noi sau lipsă.

---

## ✨ Funcționalități

- 🔁 Compară fișierele **VECHI** și **NOU** după chei  
- 🌍 Traduce doar **cheile noi** folosind **GPT-4o-mini**  
- 📊 Afișează în timp real numărul de tokeni și costul aproximativ  
- 🌐 Interfață în mai multe limbi (din folderul `/lang/`)  
- 📑 Dialog cu paginare pentru fișiere mari  
- 🌙 Temă întunecată modernă  
- 👁️ Previziune și vizualizare directă a fișierului tradus  

---

## 🧩 Structura proiectului

```text
json-translator-pro/
├── json_translator_pro.py     # Aplicația principală
├── README.md                  # Documentația în engleză
├── README_RO.md               # Această documentație
├── requirements.txt           # Dependențe
├── .gitignore                 # Fișiere ignorate
└── lang/
    ├── en.json
    ├── ro.json
    └── ...
````

---

## 🐍 Instalare și configurare

Se recomandă folosirea unui **mediu virtual (venv)** pentru a evita conflictele între librării.

---

### 🪟 Windows:

```cmd
# 1. Deschide CMD în folderul proiectului
cd C:\calea\ta\catre\json-translator-pro

# 2. Creează mediul virtual
python -m venv venv

# 3. Activează-l
venv\Scripts\activate

# 4. Instalează librăriile necesare
pip install -r requirements.txt
```

---

### 🐧 Mac / Linux:

```bash
# 1. Deschide terminalul în folderul proiectului
cd /path/to/json-translator-pro

# 2. Creează mediul virtual
python3 -m venv venv

# 3. Activează-l
source venv/bin/activate

# 4. Instalează librăriile necesare
pip install -r requirements.txt
```

---

### 🔚 Dezactivează mediul (opțional)

```bash
deactivate
```

---

## ▶️ Rulare aplicație

### Windows:

```cmd
python json_translator_pro.py
```

### Mac / Linux:

```bash
python3 json_translator_pro.py
```

Dacă totul e instalat corect, aplicația se va deschide într-o fereastră nouă.

---

## 🔑 Configurare OpenAI API Key

1. Intră pe [https://platform.openai.com/account/api-keys](https://platform.openai.com/account/api-keys)
2. Copiază cheia API
3. Deschide aplicația și introdu cheia în câmpul **API Key**, apoi apasă **💾 Save Key**

Cheia este salvată local în fișierul ascuns `.api_key`, care este ignorat de Git.

---

## 🚀 Utilizare

1. Deschide aplicația
2. Introdu cheia ta API
3. Alege:

   * **Fișier Vechi** → cel deja tradus (opțional)
   * **Fișier Nou** → cel cu cheile și textele noi în engleză de exemplu
4. Apasă **🔍 ANALYZE**

   * Vei vedea cheile noi, cele vechi și cele păstrate
5. Apasă **☑️ SELECT** pentru a alege ce chei să fie traduse
6. Apasă **👁️ PREVIEW** pentru a vedea o previzualizare
7. Apasă **🚀 TRANSLATE** pentru a începe traducerea
8. Când se termină, fișierul nou este salvat automat ca:

   ```
   nume_fisier_translated_YYYYMMDD_HHMMSS.json
   ```
9. Apasă **View Output** pentru a-l vedea în aplicație.

---

## 💰 Cost estimat

| Tip    | Preț per 1M tokeni |
| ------ | -----------------: |
| Input  |              $0.15 |
| Output |              $0.60 |

Aplicația calculează automat tokenii reali și costul total aproximativ.

---

## ⚙️ Cerințe

* Python **3.8+**
* Conexiune la internet
* Cheie OpenAI API
* Tkinter (inclus în Python)
* Dependențele din `requirements.txt`

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

## 💡 Sfaturi

* Poți adăuga traduceri pentru interfață în `/lang/`.
* Interfața se actualizează automat la schimbarea limbii.
* Traducerea rulează în fundal, fără să blocheze fereastra.

---

## 👤 Autor

**JSON Translator Pro**
Creat de **Raul, ChatGPT (OpenAI), și Claude (Anthropic)**
Licență: **MIT**