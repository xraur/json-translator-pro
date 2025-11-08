"""
JSON Translator Pro - Multilingual Edition
UI translations loaded from lang/ folder

Author: Raul, ChatGPT (OpenAI), and Claude (Anthropic)
License: MIT
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import os
from datetime import datetime
from pathlib import Path
import threading
from typing import Dict, List, Optional, Set, Tuple

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# ============================================================================
# CONSTANTS
# ============================================================================

# Window dimensions
DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 800
MIN_WINDOW_WIDTH = 1000
MIN_WINDOW_HEIGHT = 700

DIALOG_WIDTH = 1100
DIALOG_HEIGHT = 750
MIN_DIALOG_WIDTH = 900
MIN_DIALOG_HEIGHT = 600

# UI dimensions
LEFT_PANEL_WIDTH = 360
HEADER_HEIGHT = 120
BOTTOM_HEIGHT = 80

# Pagination
KEYS_PER_PAGE = 200

# Translation settings
BATCH_SIZE = 60
TRANSLATION_TEMPERATURE = 0.3
MAX_TOKENS_PER_REQUEST = 2000

# Cost estimation (GPT-4o-mini pricing per 1M tokens)
COST_INPUT_PER_MILLION = 0.15
COST_OUTPUT_PER_MILLION = 0.60
AVG_TOKENS_PER_TRANSLATION = 150

# UI colors (dark theme)
COLOR_BG_DARK = "#050505"
COLOR_BG_HEADER = "#080810"
COLOR_BG_PANEL = "#101018"
COLOR_BG_INPUT = "#05070c"
COLOR_BG_ALTERNATE = "#111111"

COLOR_FG_PRIMARY = "#ffffff"
COLOR_FG_SECONDARY = "#f5f5f5"
COLOR_FG_MUTED = "#aaaaaa"
COLOR_FG_DIMMED = "#7f8c8d"

COLOR_ACCENT_CYAN = "#00d9ff"
COLOR_SUCCESS = "#2ecc71"
COLOR_WARNING = "#f39c12"
COLOR_ERROR = "#e74c3c"
COLOR_INFO = "#3498db"
COLOR_PURPLE = "#9b59b6"
COLOR_ORANGE = "#e67e22"
COLOR_TEAL = "#16a085"
COLOR_GRAY = "#95a5a6"
COLOR_DARK_GRAY = "#555555"
COLOR_DARKER_GRAY = "#34495e"

# Preview limits
MAX_PREVIEW_LENGTH = 80
MAX_KEYS_DISPLAY = 15
MAX_OBSOLETE_DISPLAY = 10

# File storage
API_KEY_FILE = ".api_key"


# ============================================================================
# LANGUAGE MANAGER
# ============================================================================

class LanguageManager:
    """Manages UI language translations loaded from lang/ folder."""

    def __init__(self, lang_dir: str = "lang"):
        """
        Initialize the language manager.
        
        Args:
            lang_dir: Directory containing language JSON files
        """
        self.current_lang: Optional[str] = None
        self.translations: Dict[str, Dict[str, str]] = {}
        self.lang_dir = Path(lang_dir)
        self.load_all_languages()

        if self.translations:
            self.current_lang = sorted(self.translations.keys())[0]

    def load_all_languages(self) -> None:
        """Load all language files from the lang/ folder."""
        if not self.lang_dir.exists():
            return

        for lang_file in self.lang_dir.glob("*.json"):
            lang_code = lang_file.stem
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)
            except Exception as e:
                print(f"Error loading {lang_file.name}: {e}")

    def get(self, key: str, *args) -> str:
        """
        Get translated text for current language.
        
        Args:
            key: Translation key
            *args: Format arguments for the translated string
            
        Returns:
            Translated and formatted string, or the key itself if not found
        """
        text = self.translations.get(self.current_lang, {}).get(key, key)

        if args:
            try:
                text = text.format(*args)
            except Exception:
                pass

        return text

    def set_language(self, lang_code: str) -> bool:
        """
        Change current language.
        
        Args:
            lang_code: Language code to switch to
            
        Returns:
            True if language was changed, False if not found
        """
        if lang_code in self.translations:
            self.current_lang = lang_code
            return True
        return False

    def get_available_languages(self) -> List[str]:
        """Get sorted list of available language codes."""
        return sorted(self.translations.keys())


# ============================================================================
# MAIN APPLICATION
# ============================================================================

class JSONTranslatorGUI:
    """Main GUI application for JSON translation."""

        # ========================================================================
    # PROTECTIVE HELPERS (placeholders, HTML, URLs, mentions, etc.)
    # ========================================================================

    def _protect_placeholders(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Replace placeholders, HTML tags, URLs, mentions, hashtags and emoji codes
        with safe tokens so GPT won't touch them.
        """
        import re
        protected = {}
        protected_text = str(text)
        token_index = 0

        # Regex patterns for everything that must NEVER be translated
        patterns = {
            "curly":      r"\{[^}]+\}",           # {variable}
            "square":     r"\[[^\]]+\]",          # [name], [count]
            "percent":    r"%\w",                 # %s, %d, etc.
            "html":       r"<[^>]+>",             # <a href="...">
            "url":        r"https?://[^\s\"']+",  # https://example.com
            "mention":    r"@\w+",                # @username
            "hashtag":    r"#\w+",                # #topic
            "emoji_code": r":[a-zA-Z0-9_]+:",     # :smile:
            "caps":       r"\b[A-Z]{2,5}\b"       # API, JSON, CSS, etc.
        }

        for label, pattern in patterns.items():
            for match in re.findall(pattern, protected_text):
                token = f"__P{token_index}__"
                protected[token] = match
                protected_text = protected_text.replace(match, token)
                token_index += 1

        return protected_text, protected

    def _restore_placeholders(self, text: str, protected: Dict[str, str]) -> str:
        """Restore original placeholders and tags from safe tokens."""
        for token, original in protected.items():
            text = text.replace(token, original)
        return text


    def __init__(self, root: tk.Tk):
        """
        Initialize the application.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.lang_manager = LanguageManager()

        if not self.lang_manager.translations:
            messagebox.showerror("Error", "No language files found in lang/ folder!")
            root.destroy()
            return

        # State variables
        self.api_key = tk.StringVar()
        self.source_lang = tk.StringVar(value="English")
        self.target_lang = tk.StringVar(value="Romanian")
        self.ui_lang = tk.StringVar(value=self.lang_manager.current_lang)
        self.remove_obsolete = tk.BooleanVar(value=True)
        self.progress_var = tk.DoubleVar(value=0.0)

        # Data state
        self.old_file: Optional[str] = None
        self.new_file: Optional[str] = None
        self.analysis_result: Optional[Dict] = None
        self.selected_keys: Dict[str, bool] = {}
        self.last_output_file: Optional[str] = None

        # Token counters
        self.total_prompt_tokens: int = 0
        self.total_completion_tokens: int = 0

        # Language choices
        self.language_choices = [
            "English", "Romanian", "Spanish", "French", "German", "Italian",
            "Portuguese", "Polish", "Turkish", "Dutch", "Russian", "Ukrainian",
            "Czech", "Slovak", "Hungarian", "Bulgarian", "Serbian", "Croatian",
            "Bosnian", "Greek", "Swedish", "Norwegian", "Finnish", "Danish",
            "Estonian", "Latvian", "Lithuanian", "Arabic", "Hebrew", "Persian",
            "Hindi", "Urdu", "Bengali", "Tamil", "Telugu", "Malayalam", "Indonesian",
            "Malay", "Thai", "Vietnamese", "Chinese (Simplified)", "Chinese (Traditional)",
            "Japanese", "Korean", "Filipino", "Swahili", "Afrikaans", "Amharic",
            "Esperanto", "Catalan", "Galician", "Basque", "Armenian", "Georgian",
            "Albanian", "Macedonian", "Slovenian", "Icelandic", "Irish", "Welsh",
            "Scottish Gaelic", "Haitian Creole", "Tagalog", "Somali", "Nepali",
            "Pashto", "Kazakh", "Mongolian", "Khmer", "Lao", "Burmese"
        ]


        # UI components (will be initialized in setup_ui)
        self.left_panel: Optional[tk.Frame] = None
        self.right_panel: Optional[tk.Frame] = None
        self.bottom_panel: Optional[tk.Frame] = None
        self.stats_frame: Optional[tk.LabelFrame] = None
        self.stats_text: Optional[tk.Label] = None
        self.results_text: Optional[scrolledtext.ScrolledText] = None
        self.progress_bar: Optional[ttk.Progressbar] = None
        self.old_label: Optional[tk.Label] = None
        self.new_label: Optional[tk.Label] = None
        self.lang_combo: Optional[ttk.Combobox] = None

        # Action buttons
        self.analyze_btn: Optional[tk.Button] = None
        self.select_btn: Optional[tk.Button] = None
        self.preview_btn: Optional[tk.Button] = None
        self.translate_btn: Optional[tk.Button] = None
        self.view_output_btn: Optional[tk.Button] = None

        self._setup_window()
        self._setup_styles()
        self.setup_ui()
        self.load_api_key()

    # ========================================================================
    # WINDOW SETUP
    # ========================================================================

    def _setup_window(self) -> None:
        """Configure main window properties and center it on screen."""
        self.root.title(self.lang_manager.get("app_title"))
        self.root.configure(bg=COLOR_BG_DARK)

        self.root.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        pos_x = (screen_w - DEFAULT_WINDOW_WIDTH) // 2
        pos_y = (screen_h - DEFAULT_WINDOW_HEIGHT) // 2

        self.root.geometry(
            f"{DEFAULT_WINDOW_WIDTH}x{DEFAULT_WINDOW_HEIGHT}+{pos_x}+{pos_y}"
        )
        self.root.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

    def _setup_styles(self) -> None:
        """Configure ttk styles for dark theme."""
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Combobox style
        style.configure(
            "TCombobox",
            fieldbackground=COLOR_BG_ALTERNATE,
            background=COLOR_BG_ALTERNATE,
            foreground=COLOR_FG_SECONDARY,
            arrowcolor=COLOR_FG_SECONDARY,
        )
        style.map("TCombobox", fieldbackground=[("readonly", COLOR_BG_ALTERNATE)])

        # Scrollbar style
        style.configure(
            "Vertical.TScrollbar",
            background=COLOR_BG_ALTERNATE,
            troughcolor=COLOR_BG_DARK,
            bordercolor=COLOR_BG_DARK,
            arrowcolor=COLOR_FG_SECONDARY,
        )

        # Progress bar style
        style.configure(
            "Green.Horizontal.TProgressbar",
            troughcolor=COLOR_BG_DARK,
            bordercolor=COLOR_BG_DARK,
            background=COLOR_SUCCESS,
        )

    # ========================================================================
    # UI CONSTRUCTION
    # ========================================================================

    def setup_ui(self) -> None:
        """Build the main UI layout."""
        self._create_header()
        self._create_main_panels()
        self._create_bottom_panel()

    def _create_header(self) -> None:
        """Create application header with title and language selector."""
        header = tk.Frame(self.root, bg=COLOR_BG_HEADER, height=HEADER_HEIGHT)
        header.pack(fill="x", padx=15, pady=15)

        # Title
        title = tk.Label(
            header,
            text=self.lang_manager.get("app_title"),
            font=("Segoe UI", 26, "bold"),
            bg=COLOR_BG_HEADER,
            fg=COLOR_FG_PRIMARY,
        )
        title.pack(pady=(10, 0))

        # Subtitle
        subtitle = tk.Label(
            header,
            text=self.lang_manager.get("app_subtitle"),
            font=("Segoe UI", 10),
            bg=COLOR_BG_HEADER,
            fg=COLOR_FG_MUTED,
        )
        subtitle.pack(pady=(0, 5))

        # Language selector
        lang_frame = tk.Frame(header, bg=COLOR_BG_HEADER)
        lang_frame.pack(pady=(0, 8))

        tk.Label(
            lang_frame,
            text=self.lang_manager.get("ui_language"),
            bg=COLOR_BG_HEADER,
            fg=COLOR_FG_SECONDARY,
            font=("Segoe UI", 9),
        ).pack(side="left", padx=5)

        self.lang_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.ui_lang,
            values=self.lang_manager.get_available_languages(),
            state="readonly",
            font=("Segoe UI", 9),
            width=10,
        )
        self.lang_combo.pack(side="left", padx=5)
        self.lang_combo.bind("<<ComboboxSelected>>", self.change_ui_language)

    def _create_main_panels(self) -> None:
        """Create left (settings) and right (results) panels."""
        main = tk.Frame(self.root, bg=COLOR_BG_DARK)
        main.pack(fill="both", expand=True, padx=15, pady=(0, 5))

        # Left panel
        self.left_panel = tk.Frame(main, bg=COLOR_BG_PANEL, width=LEFT_PANEL_WIDTH)
        self.left_panel.pack(side="left", fill="y", padx=(0, 12))
        self.left_panel.pack_propagate(False)
        self.setup_left_panel(self.left_panel)

        # Right panel
        self.right_panel = tk.Frame(main, bg=COLOR_BG_PANEL)
        self.right_panel.pack(side="right", fill="both", expand=True)
        self.setup_right_panel(self.right_panel)

    def _create_bottom_panel(self) -> None:
        """Create bottom panel with action buttons."""
        self.bottom_panel = tk.Frame(self.root, bg=COLOR_BG_DARK, height=BOTTOM_HEIGHT)
        self.bottom_panel.pack(fill="x", padx=15, pady=15)
        self.setup_bottom_panel(self.bottom_panel)

    def setup_left_panel(self, parent: tk.Frame) -> None:
        """
        Create left panel with API key, language settings, and statistics.
        
        Args:
            parent: Parent frame to attach components to
        """
        self._create_api_section(parent)
        self._create_language_section(parent)
        self._create_statistics_section(parent)

    def _create_api_section(self, parent: tk.Frame) -> None:
        """Create API key input section."""
        api_frame = tk.LabelFrame(
            parent,
            text=f"  {self.lang_manager.get('api_key_section')}  ",
            bg=COLOR_BG_PANEL,
            fg=COLOR_ACCENT_CYAN,
            font=("Segoe UI", 10, "bold"),
            borderwidth=2,
            relief="groove",
        )
        api_frame.pack(fill="x", padx=15, pady=15)

        api_entry = tk.Entry(
            api_frame,
            textvariable=self.api_key,
            show="●",
            font=("Segoe UI", 9),
            bg=COLOR_BG_INPUT,
            fg=COLOR_FG_PRIMARY,
            insertbackground=COLOR_ACCENT_CYAN,
            relief="flat",
            bd=0,
        )
        api_entry.pack(fill="x", padx=10, pady=(10, 5), ipady=8)

        save_btn = self._create_modern_button(
            api_frame,
            self.lang_manager.get("save_key"),
            self.save_api_key,
            COLOR_TEAL,
        )
        save_btn.pack(padx=10, pady=(5, 10), fill="x")

    def _create_language_section(self, parent: tk.Frame) -> None:
        """Create language selection section."""
        lang_frame = tk.LabelFrame(
            parent,
            text=f"  {self.lang_manager.get('languages_section')}  ",
            bg=COLOR_BG_PANEL,
            fg=COLOR_ACCENT_CYAN,
            font=("Segoe UI", 10, "bold"),
            borderwidth=2,
            relief="groove",
        )
        lang_frame.pack(fill="x", padx=15, pady=15)

        # Source language
        tk.Label(
            lang_frame,
            text=self.lang_manager.get("source_lang"),
            bg=COLOR_BG_PANEL,
            fg=COLOR_FG_SECONDARY,
            font=("Segoe UI", 9),
        ).pack(anchor="w", padx=10, pady=(10, 2))

        source_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.source_lang,
            state="readonly",
            font=("Segoe UI", 9),
            values=self.language_choices,
        )
        source_combo.pack(fill="x", padx=10, pady=(0, 10))

        # Target language
        tk.Label(
            lang_frame,
            text=self.lang_manager.get("target_lang"),
            bg=COLOR_BG_PANEL,
            fg=COLOR_FG_SECONDARY,
            font=("Segoe UI", 9),
        ).pack(anchor="w", padx=10, pady=(5, 2))

        target_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.target_lang,
            state="readonly",
            font=("Segoe UI", 9),
            values=self.language_choices,
        )
        target_combo.pack(fill="x", padx=10, pady=(0, 10))

    def _create_statistics_section(self, parent: tk.Frame) -> None:
        """Create statistics display section."""
        self.stats_frame = tk.LabelFrame(
            parent,
            text=f"  {self.lang_manager.get('statistics_section')}  ",
            bg=COLOR_BG_PANEL,
            fg=COLOR_ACCENT_CYAN,
            font=("Segoe UI", 10, "bold"),
            borderwidth=2,
            relief="groove",
        )
        self.stats_frame.pack(fill="both", expand=True, padx=15, pady=15)

        self.stats_text = tk.Label(
            self.stats_frame,
            text=self.lang_manager.get("no_analysis"),
            bg=COLOR_BG_PANEL,
            fg=COLOR_FG_DIMMED,
            font=("Segoe UI", 9),
            justify="left",
            anchor="nw",
        )
        self.stats_text.pack(padx=15, pady=15, fill="both", expand=True)

    def setup_right_panel(self, parent: tk.Frame) -> None:
        """
        Create right panel with file selection and results display.
        
        Args:
            parent: Parent frame to attach components to
        """
        self._create_files_section(parent)
        self._create_results_section(parent)

    def _create_files_section(self, parent: tk.Frame) -> None:
        """Create file selection section."""
        files_frame = tk.LabelFrame(
            parent,
            text=f"  {self.lang_manager.get('files_section')}  ",
            bg=COLOR_BG_PANEL,
            fg=COLOR_ACCENT_CYAN,
            font=("Segoe UI", 10, "bold"),
            borderwidth=2,
            relief="groove",
        )
        files_frame.pack(fill="x", padx=15, pady=15)

        # Old file
        self._create_file_row(
            files_frame,
            self.lang_manager.get("old_file_label"),
            "old",
            COLOR_SUCCESS
        )

        # New file
        self._create_file_row(
            files_frame,
            self.lang_manager.get("new_file_label"),
            "new",
            COLOR_ORANGE
        )

    def _create_file_row(
        self,
        parent: tk.Frame,
        label_text: str,
        file_type: str,
        label_color: str
    ) -> None:
        """
        Create a file selection row with label and buttons.
        
        Args:
            parent: Parent frame
            label_text: Text for the label
            file_type: Type identifier ('old' or 'new')
            label_color: Color for the label text
        """
        row_frame = tk.Frame(parent, bg=COLOR_BG_PANEL)
        pady = 10 if file_type == "old" else (0, 10)
        row_frame.pack(fill="x", padx=10, pady=pady)

        tk.Label(
            row_frame,
            text=label_text,
            bg=COLOR_BG_PANEL,
            fg=label_color,
            font=("Segoe UI", 9, "bold"),
        ).pack(side="left")

        label = tk.Label(
            row_frame,
            text=self.lang_manager.get("no_file_selected"),
            bg=COLOR_BG_PANEL,
            fg=COLOR_FG_DIMMED,
            font=("Segoe UI", 9),
        )
        label.pack(side="left", padx=10)

        if file_type == "old":
            self.old_label = label
        else:
            self.new_label = label

        self._create_icon_button(
            row_frame, "📂", lambda: self.select_file(file_type), COLOR_INFO
        ).pack(side="right", padx=2)

        if file_type == "old":
            self._create_icon_button(
                row_frame, "✖", lambda: self.clear_file(file_type), COLOR_ERROR
            ).pack(side="right", padx=2)

    def _create_results_section(self, parent: tk.Frame) -> None:
        """Create results display section with progress bar."""
        results_frame = tk.LabelFrame(
            parent,
            text=f"  {self.lang_manager.get('analysis_results')}  ",
            bg=COLOR_BG_PANEL,
            fg=COLOR_ACCENT_CYAN,
            font=("Segoe UI", 10, "bold"),
            borderwidth=2,
            relief="groove",
        )
        results_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Progress bar
        self.progress_bar = ttk.Progressbar(
            results_frame,
            variable=self.progress_var,
            maximum=100.0,
            mode="determinate",
            style="Green.Horizontal.TProgressbar",
        )
        self.progress_bar.pack(fill="x", padx=10, pady=(8, 0))

        # Results text area
        self.results_text = scrolledtext.ScrolledText(
            results_frame,
            bg=COLOR_BG_INPUT,
            fg=COLOR_FG_SECONDARY,
            font=("Consolas", 9),
            insertbackground=COLOR_ACCENT_CYAN,
            wrap="word",
            relief="flat",
            borderwidth=0,
        )
        self.results_text.pack(fill="both", expand=True, padx=10, pady=10)

        # Configure text tags for syntax highlighting
        self._configure_text_tags()

    def _configure_text_tags(self) -> None:
        """Configure color tags for results text display."""
        if not self.results_text:
            return

        tags = {
            "new": COLOR_SUCCESS,
            "obsolete": COLOR_ERROR,
            "kept": COLOR_INFO,
            "info": COLOR_ACCENT_CYAN,
            "warning": COLOR_WARNING,
            "json_key": COLOR_ACCENT_CYAN,
            "json_value": COLOR_SUCCESS,
            "json_brace": COLOR_GRAY,
        }

        for tag_name, color in tags.items():
            self.results_text.tag_config(tag_name, foreground=color)

    def setup_bottom_panel(self, parent: tk.Frame) -> None:
        """
        Create bottom panel with action buttons.
        
        Args:
            parent: Parent frame to attach components to
        """
        btn_frame = tk.Frame(parent, bg=COLOR_BG_DARK)
        btn_frame.pack(expand=True)

        # Analyze button
        self.analyze_btn = self._create_action_button(
            btn_frame,
            self.lang_manager.get("analyze_button"),
            self.analyze_files,
            COLOR_INFO,
            20,
        )
        self.analyze_btn.pack(side="left", padx=8)
        self._set_button_state(self.analyze_btn, True)

        # Select button
        self.select_btn = self._create_action_button(
            btn_frame,
            self.lang_manager.get("select_button"),
            self.show_selection_dialog,
            COLOR_PURPLE,
            18,
        )
        self.select_btn.pack(side="left", padx=8)
        self._set_button_state(self.select_btn, False)

        # Preview button
        self.preview_btn = self._create_action_button(
            btn_frame,
            self.lang_manager.get("preview_button"),
            self.show_preview,
            COLOR_ORANGE,
            18,
        )
        self.preview_btn.pack(side="left", padx=8)
        self._set_button_state(self.preview_btn, False)

        # Translate button
        self.translate_btn = self._create_action_button(
            btn_frame,
            self.lang_manager.get("translate_button"),
            self.start_translation,
            COLOR_SUCCESS,
            24,
        )
        self.translate_btn.pack(side="left", padx=8)
        self._set_button_state(self.translate_btn, False)

        # View output button
        self.view_output_btn = self._create_action_button(
            btn_frame,
            self.lang_manager.get("view_output_button"),
            self.view_output_file_in_results,
            COLOR_PURPLE,
            24,
        )
        self.view_output_btn.pack(side="left", padx=8)
        self._set_button_state(self.view_output_btn, False)

    # ========================================================================
    # BUTTON CREATION HELPERS
    # ========================================================================

    def _create_modern_button(
        self,
        parent: tk.Widget,
        text: str,
        command: callable,
        color: str
    ) -> tk.Button:
        """
        Create a styled modern button.
        
        Args:
            parent: Parent widget
            text: Button text
            command: Click callback
            color: Button background color
            
        Returns:
            Created button widget
        """
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg=COLOR_FG_PRIMARY,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
            relief="flat",
            borderwidth=0,
            padx=15,
            pady=8,
            activebackground=self._darken_color(color),
            activeforeground=COLOR_FG_PRIMARY,
        )
        return btn

    def _create_icon_button(
        self,
        parent: tk.Widget,
        icon: str,
        command: callable,
        color: str
    ) -> tk.Button:
        """
        Create a small icon button.
        
        Args:
            parent: Parent widget
            icon: Button icon/emoji
            command: Click callback
            color: Button background color
            
        Returns:
            Created button widget
        """
        btn = tk.Button(
            parent,
            text=icon,
            command=command,
            bg=color,
            fg=COLOR_FG_PRIMARY,
            font=("Segoe UI", 11),
            cursor="hand2",
            relief="flat",
            width=3,
            height=1,
            borderwidth=0,
            activebackground=self._darken_color(color),
            activeforeground=COLOR_FG_PRIMARY,
        )
        return btn

    def _create_action_button(
        self,
        parent: tk.Widget,
        text: str,
        command: callable,
        color: str,
        width: int
    ) -> tk.Button:
        """
        Create a large action button.
        
        Args:
            parent: Parent widget
            text: Button text
            command: Click callback
            color: Button background color
            width: Button width in characters
            
        Returns:
            Created button widget
        """
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg=COLOR_FG_PRIMARY,
            font=("Segoe UI", 12, "bold"),
            cursor="hand2",
            relief="flat",
            width=width,
            height=2,
            borderwidth=0,
            activebackground=self._darken_color(color),
            activeforeground=COLOR_FG_PRIMARY,
            disabledforeground=COLOR_DARK_GRAY,
        )
        btn.original_bg = color
        return btn

    def _set_button_state(self, button: Optional[tk.Button], enabled: bool) -> None:
        """
        Enable or disable a button with appropriate styling.
        
        Args:
            button: Button to modify
            enabled: Whether button should be enabled
        """
        if button is None:
            return

        if enabled:
            button.config(
                state="normal",
                bg=getattr(button, "original_bg", button.cget("bg")),
            )
        else:
            button.config(state="disabled", bg=COLOR_DARK_GRAY)

    @staticmethod
    def _darken_color(color: str) -> str:
        """
        Darken a hex color by 20%.
        
        Args:
            color: Hex color string (e.g., '#00d9ff')
            
        Returns:
            Darkened hex color string
        """
        color = color.lstrip("#")
        rgb = tuple(int(color[i: i + 2], 16) for i in (0, 2, 4))
        darker = tuple(int(c * 0.8) for c in rgb)
        return f"#{darker[0]:02x}{darker[1]:02x}{darker[2]:02x}"

    # ========================================================================
    # UI LANGUAGE CHANGE
    # ========================================================================

    def change_ui_language(self, event=None) -> None:
        """Change UI language and refresh all text elements."""
        new_lang = self.ui_lang.get()
        if self.lang_manager.set_language(new_lang):
            self.refresh_ui()

    def refresh_ui(self) -> None:
        """Refresh all UI elements with new language strings."""
        # Titrele ferestrei în noua limbă
        self.root.title(self.lang_manager.get("app_title"))

        # Ștergem TOȚI copiii ferestrei (header + main + bottom)
        for widget in self.root.winfo_children():
            widget.destroy()

        # Reconstruim UI-ul complet
        self._create_header()
        self._create_main_panels()
        self._create_bottom_panel()

        # Ne asigurăm că în combobox e setată limba curentă
        if self.lang_combo is not None:
            self.lang_combo.set(self.ui_lang.get())

        # Dacă avem deja o analiză făcută, o reafișăm în noul UI
        if self.analysis_result:
            self.display_analysis(self.analysis_result)


    # ========================================================================
    # API KEY MANAGEMENT
    # ========================================================================

    def load_api_key(self) -> None:
        """Load API key from file if it exists."""
        try:
            if os.path.exists(API_KEY_FILE):
                with open(API_KEY_FILE, "r") as f:
                    self.api_key.set(f.read().strip())
        except Exception:
            pass

    def save_api_key(self) -> None:
        """Save API key to file."""
        key = self.api_key.get().strip()
        if not key:
            messagebox.showerror(
                self.lang_manager.get("error"),
                self.lang_manager.get("enter_api_key"),
            )
            return

        try:
            with open(API_KEY_FILE, "w") as f:
                f.write(key)
            messagebox.showinfo(
                self.lang_manager.get("success"),
                self.lang_manager.get("api_key_saved"),
            )
        except Exception as e:
            messagebox.showerror(
                self.lang_manager.get("error"),
                f"{self.lang_manager.get('save_failed')}: {e}",
            )

    # ========================================================================
    # FILE SELECTION
    # ========================================================================

    def select_file(self, file_type: str) -> None:
        """
        Open file dialog to select a JSON file.
        
        Args:
            file_type: Type of file ('old' or 'new')
        """
        title = (
            self.lang_manager.get("select_old_file")
            if file_type == "old"
            else self.lang_manager.get("select_new_file")
        )
        filename = filedialog.askopenfilename(
            title=title,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            if file_type == "old":
                self.old_file = filename
                self.old_label.config(
                    text=os.path.basename(filename),
                    fg=COLOR_SUCCESS
                )
            else:
                self.new_file = filename
                self.new_label.config(
                    text=os.path.basename(filename),
                    fg=COLOR_ORANGE
                )

    def clear_file(self, file_type: str) -> None:
        """
        Clear selected file.
        
        Args:
            file_type: Type of file to clear ('old')
        """
        if file_type == "old":
            self.old_file = None
            self.old_label.config(
                text=self.lang_manager.get("no_file_selected"),
                fg=COLOR_FG_DIMMED,
            )

    # ========================================================================
    # FILE ANALYSIS
    # ========================================================================

    def analyze_files(self) -> None:
        """Analyze and compare old and new JSON files."""
        if not self.new_file:
            messagebox.showerror(
                self.lang_manager.get("error"),
                self.lang_manager.get("select_new_file_error"),
            )
            return

        try:
            # Load new file
            with open(self.new_file, "r", encoding="utf-8") as f:
                new_data = json.load(f)

            # Load old file if exists
            old_data = {}
            if self.old_file:
                with open(self.old_file, "r", encoding="utf-8") as f:
                    old_data = json.load(f)

            # Compare files
            analysis = self._compare_json_files(old_data, new_data)
            self.display_analysis(analysis)

            # Update button states
            if analysis["new_keys"] or analysis["obsolete_keys"]:
                self.selected_keys = {key: True for key in analysis["new_keys"]}
                self._set_button_state(self.select_btn, True)
                self._set_button_state(self.preview_btn, True)
                self._set_button_state(self.translate_btn, True)
            else:
                messagebox.showinfo(
                    self.lang_manager.get("info"),
                    self.lang_manager.get("nothing_to_translate"),
                )
                self._set_button_state(self.select_btn, False)
                self._set_button_state(self.preview_btn, False)
                self._set_button_state(self.translate_btn, False)

            self._set_button_state(self.view_output_btn, False)

        except Exception as e:
            messagebox.showerror(
                self.lang_manager.get("error"),
                f"{self.lang_manager.get('analysis_error')}:\n{e}",
            )

    def _compare_json_files(
        self,
        old_data: Dict,
        new_data: Dict
    ) -> Dict:
        """
        Compare old and new JSON data by keys.
        
        Args:
            old_data: Dictionary from old file
            new_data: Dictionary from new file
            
        Returns:
            Analysis dictionary with new, obsolete, and kept keys
        """
        old_keys = set(old_data.keys())
        new_keys = set(new_data.keys())

        return {
            "new_keys": list(new_keys - old_keys),
            "obsolete_keys": list(old_keys - new_keys),
            "kept_keys": list(new_keys & old_keys),
            "new_data": new_data,
            "old_data": old_data,
        }

    def display_analysis(self, analysis: Dict) -> None:
        """
        Display analysis results in the UI.
        
        Args:
            analysis: Analysis dictionary from _compare_json_files
        """
        self.analysis_result = analysis
        self.results_text.delete("1.0", "end")

        # Header
        self._insert_header()

        # Statistics
        new_count = len(analysis["new_keys"])
        obsolete_count = len(analysis["obsolete_keys"])
        kept_count = len(analysis["kept_keys"])

        self._insert_statistics_box(new_count, obsolete_count, kept_count)
        self._insert_file_totals(analysis)
        self._update_stats_panel(new_count, obsolete_count, kept_count)

        # Display key categories
        if analysis["new_keys"]:
            self._display_new_keys(analysis["new_keys"], analysis["new_data"])

        if analysis["obsolete_keys"]:
            self._display_obsolete_keys(analysis["obsolete_keys"])

        if analysis["kept_keys"]:
            self._display_kept_keys(kept_count)

        # Footer
        self.results_text.insert("end", "\n" + "═" * 90 + "\n", "info")
        self.progress_var.set(0.0)

    def _insert_header(self) -> None:
        """Insert analysis header in results."""
        self.results_text.insert("end", "═" * 90 + "\n", "info")
        self.results_text.insert(
            "end",
            f"  {self.lang_manager.get('smart_analysis')}\n",
            "info"
        )
        self.results_text.insert("end", "═" * 90 + "\n\n", "info")

    def _insert_statistics_box(
        self,
        new_count: int,
        obsolete_count: int,
        kept_count: int
    ) -> None:
        """Insert formatted statistics box."""
        cost = self._estimate_cost(new_count)
        stats = f"""
╔══════════════════════════════════════════════════════════════╗
║  {self.lang_manager.get('new_keys_to_translate')}: {new_count:<33} ║
║  {self.lang_manager.get('obsolete_keys')}: {obsolete_count:<30} ║
║  {self.lang_manager.get('kept_keys')}: {kept_count:<26} ║
╠══════════════════════════════════════════════════════════════╣
║  {self.lang_manager.get('estimated_cost')}: ~${cost:.4f}{' ' * 38}║
╚══════════════════════════════════════════════════════════════╝
"""
        self.results_text.insert("end", stats, "info")

    def _insert_file_totals(self, analysis: Dict) -> None:
        """Insert file totals information."""
        self.results_text.insert(
            "end",
            f"\n{self.lang_manager.get('total_in_new', len(analysis['new_data']))}\n",
            "info",
        )
        self.results_text.insert(
            "end",
            f"{self.lang_manager.get('total_in_old', len(analysis['old_data']))}\n\n",
            "info",
        )

    def _update_stats_panel(
        self,
        new_count: int,
        obsolete_count: int,
        kept_count: int
    ) -> None:
        """Update statistics panel in left sidebar."""
        self.stats_text.config(
            text=(
                f"{self.lang_manager.get('new_keys_to_translate')}: {new_count}\n"
                f"{self.lang_manager.get('obsolete_keys')}: {obsolete_count}\n"
                f"{self.lang_manager.get('kept_keys')}: {kept_count}\n\n"
                f"{self.lang_manager.get('estimated_cost')}: ${self._estimate_cost(new_count):.4f}"
            ),
            fg=COLOR_FG_SECONDARY,
        )

    def _display_new_keys(self, new_keys: List[str], new_data: Dict) -> None:
        """Display new keys section."""
        count = len(new_keys)
        self.results_text.insert(
            "end",
            f"\n{self.lang_manager.get('new_keys_header', count)}\n",
            "new",
        )
        self.results_text.insert("end", "─" * 90 + "\n", "new")

        for idx, key in enumerate(new_keys[:MAX_KEYS_DISPLAY], 1):
            value = new_data[key]
            preview = self._truncate_text(value, 70)
            self.results_text.insert("end", f"  {idx:2}. {key}\n", "new")
            self.results_text.insert("end", f"      → {preview}\n", "kept")

        if count > MAX_KEYS_DISPLAY:
            self.results_text.insert(
                "end",
                f"  {self.lang_manager.get('and_more', count - MAX_KEYS_DISPLAY)}\n",
                "new",
            )

    def _display_obsolete_keys(self, obsolete_keys: List[str]) -> None:
        """Display obsolete keys section."""
        count = len(obsolete_keys)
        self.results_text.insert(
            "end",
            f"\n{self.lang_manager.get('obsolete_keys_header', count)}\n",
            "obsolete",
        )
        self.results_text.insert("end", "─" * 90 + "\n", "obsolete")
        self.results_text.insert(
            "end",
            f"  {self.lang_manager.get('obsolete_warning1')}\n",
            "warning",
        )
        self.results_text.insert(
            "end",
            f"  {self.lang_manager.get('obsolete_warning2')}\n\n",
            "warning",
        )

        for idx, key in enumerate(obsolete_keys[:MAX_OBSOLETE_DISPLAY], 1):
            self.results_text.insert("end", f"  {idx:2}. {key}\n", "obsolete")

        if count > MAX_OBSOLETE_DISPLAY:
            self.results_text.insert(
                "end",
                f"  {self.lang_manager.get('and_more', count - MAX_OBSOLETE_DISPLAY)}\n",
                "obsolete",
            )

    def _display_kept_keys(self, kept_count: int) -> None:
        """Display kept keys section."""
        self.results_text.insert(
            "end",
            f"\n{self.lang_manager.get('kept_keys_header', kept_count)}\n",
            "kept",
        )
        self.results_text.insert("end", "─" * 90 + "\n", "kept")
        self.results_text.insert(
            "end",
            f"  {self.lang_manager.get('kept_info1')}\n",
            "kept",
        )
        self.results_text.insert(
            "end",
            f"  {self.lang_manager.get('kept_info2')}\n",
            "kept",
        )

    @staticmethod
    def _estimate_cost(num_translations: int) -> float:
        """
        Estimate translation cost.
        
        Args:
            num_translations: Number of translations to perform
            
        Returns:
            Estimated cost in USD
        """
        avg_tokens = num_translations * AVG_TOKENS_PER_TRANSLATION
        return (avg_tokens / 1_000_000) * COST_OUTPUT_PER_MILLION

    @staticmethod
    def _truncate_text(text: str, max_length: int) -> str:
        """
        Truncate text with ellipsis if too long.
        
        Args:
            text: Text to truncate
            max_length: Maximum length before truncation
            
        Returns:
            Truncated text with '...' if needed
        """
        return (text[:max_length] + "...") if len(text) > max_length else text

    # ========================================================================
    # KEY SELECTION DIALOG
    # ========================================================================

    def show_selection_dialog(self) -> None:
        """Show dialog for selecting which keys to translate."""
        if not self.analysis_result or not self.analysis_result["new_keys"]:
            return

        new_keys = self.analysis_result["new_keys"]
        dialog = self._create_selection_dialog()

        # Pagination state
        page_vars: Dict[str, tk.BooleanVar] = {}
        current_page = tk.IntVar(value=1)
        total_pages = (len(new_keys) + KEYS_PER_PAGE - 1) // KEYS_PER_PAGE

        # Create UI components
        header_frame = self._create_dialog_header(dialog)
        self._create_selection_buttons(header_frame, new_keys, page_vars)
        self._create_obsolete_checkbox(header_frame)

        # List frame with canvas for scrolling
        list_frame = tk.Frame(dialog, bg=COLOR_BG_PANEL)
        list_frame.pack(fill="both", expand=True, padx=15, pady=10)

        canvas, scrollbar, scrollable = self._create_scrollable_frame(list_frame)

        # Page info label
        page_info = tk.Label(
            dialog,
            text="",
            bg=COLOR_BG_DARK,
            fg=COLOR_FG_MUTED,
            font=("Segoe UI", 9),
        )
        page_info.pack(pady=(0, 5))

        # Footer with buttons
        footer = self._create_dialog_footer(
            dialog,
            new_keys,
            page_vars,
            current_page,
            total_pages,
            scrollable,
            page_info
        )

        # Render first page
        self._render_selection_page(
            new_keys,
            scrollable,
            page_vars,
            current_page,
            total_pages,
            page_info
        )

    def _create_selection_dialog(self) -> tk.Toplevel:
        """Create and configure selection dialog window."""
        dialog = tk.Toplevel(self.root)
        dialog.title(self.lang_manager.get("select_keys_title"))
        dialog.configure(bg=COLOR_BG_DARK)

        # Center dialog
        dialog.update_idletasks()
        screen_w = dialog.winfo_screenwidth()
        screen_h = dialog.winfo_screenheight()
        pos_x = (screen_w - DIALOG_WIDTH) // 2
        pos_y = (screen_h - DIALOG_HEIGHT) // 2
        dialog.geometry(f"{DIALOG_WIDTH}x{DIALOG_HEIGHT}+{pos_x}+{pos_y}")
        dialog.minsize(MIN_DIALOG_WIDTH, MIN_DIALOG_HEIGHT)

        return dialog

    def _create_dialog_header(self, dialog: tk.Toplevel) -> tk.Frame:
        """Create dialog header with title."""
        header = tk.Frame(dialog, bg=COLOR_BG_HEADER)
        header.pack(fill="x", padx=15, pady=15)

        tk.Label(
            header,
            text=self.lang_manager.get("select_keys_header"),
            font=("Segoe UI", 16, "bold"),
            bg=COLOR_BG_HEADER,
            fg=COLOR_FG_PRIMARY,
        ).pack(pady=10)

        return header

    def _create_selection_buttons(
        self,
        parent: tk.Frame,
        new_keys: List[str],
        page_vars: Dict[str, tk.BooleanVar]
    ) -> None:
        """Create select all/deselect all buttons."""
        btn_frame = tk.Frame(parent, bg=COLOR_BG_HEADER)
        btn_frame.pack(pady=10)

        def on_select_all():
            for k in new_keys:
                self.selected_keys[k] = True
            for k, var in page_vars.items():
                var.set(True)

        def on_deselect_all():
            for k in new_keys:
                self.selected_keys[k] = False
            for k, var in page_vars.items():
                var.set(False)

        self._create_modern_button(
            btn_frame,
            self.lang_manager.get("select_all"),
            on_select_all,
            COLOR_SUCCESS,
        ).pack(side="left", padx=5)

        self._create_modern_button(
            btn_frame,
            self.lang_manager.get("deselect_all"),
            on_deselect_all,
            COLOR_ERROR,
        ).pack(side="left", padx=5)

    def _create_obsolete_checkbox(self, parent: tk.Frame) -> None:
        """Create checkbox for removing obsolete keys."""
        if not self.analysis_result["obsolete_keys"]:
            return

        obsolete_frame = tk.Frame(parent, bg=COLOR_BG_HEADER)
        obsolete_frame.pack(pady=10)

        tk.Checkbutton(
            obsolete_frame,
            text=self.lang_manager.get(
                "remove_obsolete",
                len(self.analysis_result["obsolete_keys"]),
            ),
            variable=self.remove_obsolete,
            bg=COLOR_BG_HEADER,
            fg=COLOR_ERROR,
            selectcolor=COLOR_BG_HEADER,
            font=("Segoe UI", 10, "bold"),
            activebackground=COLOR_BG_HEADER,
            activeforeground=COLOR_ERROR,
        ).pack()

    def _create_scrollable_frame(
        self,
        parent: tk.Frame
    ) -> Tuple[tk.Canvas, ttk.Scrollbar, tk.Frame]:
        """Create canvas with scrollbar for scrollable content."""
        canvas = tk.Canvas(
            parent,
            bg=COLOR_BG_INPUT,
            highlightthickness=0,
            bd=0
        )
        scrollbar = ttk.Scrollbar(
            parent,
            orient="vertical",
            command=canvas.yview
        )
        scrollable = tk.Frame(canvas, bg=COLOR_BG_INPUT)

        scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )

        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        return canvas, scrollbar, scrollable

    def _create_dialog_footer(
        self,
        dialog: tk.Toplevel,
        new_keys: List[str],
        page_vars: Dict[str, tk.BooleanVar],
        current_page: tk.IntVar,
        total_pages: int,
        scrollable: tk.Frame,
        page_info: tk.Label
    ) -> tk.Frame:
        """Create dialog footer with navigation and action buttons."""
        footer = tk.Frame(dialog, bg=COLOR_BG_DARK)
        footer.pack(fill="x", padx=15, pady=15)

        # Selection counter
        count_label = tk.Label(
            footer,
            text="",
            bg=COLOR_BG_DARK,
            fg=COLOR_SUCCESS,
            font=("Segoe UI", 11, "bold"),
        )
        count_label.pack(pady=10)

        self._start_selection_counter(dialog, new_keys, page_vars, count_label)

        # Button frame
        btn_frame2 = tk.Frame(footer, bg=COLOR_BG_DARK)
        btn_frame2.pack()

        # Navigation buttons
        self._create_action_button(
            btn_frame2,
            "<< Prev",
            lambda: self._navigate_page(
                -1, current_page, total_pages, new_keys,
                scrollable, page_vars, page_info
            ),
            COLOR_DARKER_GRAY,
            10,
        ).pack(side="left", padx=5)

        self._create_action_button(
            btn_frame2,
            "Next >>",
            lambda: self._navigate_page(
                1, current_page, total_pages, new_keys,
                scrollable, page_vars, page_info
            ),
            COLOR_DARKER_GRAY,
            10,
        ).pack(side="left", padx=5)

        # Save and close button
        def on_save_and_close():
            for key, var in page_vars.items():
                self.selected_keys[key] = var.get()
            count = sum(1 for k in new_keys if self.selected_keys.get(k, True))
            messagebox.showinfo(
                self.lang_manager.get("success"),
                self.lang_manager.get("selection_saved", count),
            )
            dialog.destroy()

        self._create_action_button(
            btn_frame2,
            self.lang_manager.get("save_selection"),
            on_save_and_close,
            COLOR_INFO,
            18,
        ).pack(side="left", padx=10)

        self._create_action_button(
            btn_frame2,
            self.lang_manager.get("cancel"),
            dialog.destroy,
            COLOR_GRAY,
            14,
        ).pack(side="left", padx=10)

        return footer

    def _start_selection_counter(
        self,
        dialog: tk.Toplevel,
        new_keys: List[str],
        page_vars: Dict[str, tk.BooleanVar],
        count_label: tk.Label
    ) -> None:
        """Start periodic update of selection counter."""
        def update_count():
            if not dialog.winfo_exists():
                return

            count = 0
            for key in new_keys:
                if key in page_vars:
                    selected = page_vars[key].get()
                else:
                    selected = self.selected_keys.get(key, True)
                if selected:
                    count += 1

            cost = self._estimate_cost(count)
            count_label.config(
                text=self.lang_manager.get(
                    "selected_count",
                    count,
                    len(new_keys),
                    cost
                )
            )
            dialog.after(400, update_count)

        update_count()

    def _navigate_page(
        self,
        direction: int,
        current_page: tk.IntVar,
        total_pages: int,
        new_keys: List[str],
        scrollable: tk.Frame,
        page_vars: Dict[str, tk.BooleanVar],
        page_info: tk.Label
    ) -> None:
        """Navigate to next or previous page."""
        new_page = current_page.get() + direction
        if 1 <= new_page <= total_pages:
            current_page.set(new_page)
            self._render_selection_page(
                new_keys,
                scrollable,
                page_vars,
                current_page,
                total_pages,
                page_info
            )

    def _render_selection_page(
        self,
        new_keys: List[str],
        scrollable: tk.Frame,
        page_vars: Dict[str, tk.BooleanVar],
        current_page: tk.IntVar,
        total_pages: int,
        page_info: tk.Label
    ) -> None:
        """Render current page of keys."""
        # Save selections from previous page
        for key, var in page_vars.items():
            self.selected_keys[key] = var.get()

        page_vars.clear()

        # Clear scrollable area
        for widget in scrollable.winfo_children():
            widget.destroy()

        # Calculate page range
        page = current_page.get()
        start = (page - 1) * KEYS_PER_PAGE
        end = min(start + KEYS_PER_PAGE, len(new_keys))

        # Render keys for current page
        for idx in range(start, end):
            self._create_key_row(scrollable, new_keys[idx], idx, page_vars)

        # Update page info
        page_info.config(
            text=f"Page {page}/{total_pages}  •  Showing {end}/{len(new_keys)} keys"
        )

    def _create_key_row(
        self,
        parent: tk.Frame,
        key: str,
        idx: int,
        page_vars: Dict[str, tk.BooleanVar]
    ) -> None:
        """Create a single key selection row."""
        frame_bg = COLOR_BG_PANEL if idx % 2 else COLOR_BG_INPUT
        frame = tk.Frame(parent, bg=frame_bg, pady=6)
        frame.pack(fill="x", padx=8, pady=1)

        # Checkbox
        var = tk.BooleanVar(value=self.selected_keys.get(key, True))
        page_vars[key] = var

        cb = tk.Checkbutton(
            frame,
            variable=var,
            bg=frame_bg,
            fg=COLOR_FG_PRIMARY,
            selectcolor=frame_bg,
            activebackground=frame_bg,
            activeforeground=COLOR_FG_PRIMARY,
            font=("Segoe UI", 9),
        )
        cb.pack(side="left", padx=10)

        # Key label
        key_label = tk.Label(
            frame,
            text=key,
            bg=frame_bg,
            fg=COLOR_ACCENT_CYAN,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
            width=35,
        )
        key_label.pack(side="left", padx=5)

        # Value preview
        value = self.analysis_result["new_data"][key]
        preview = self._truncate_text(value, 65)
        val_label = tk.Label(
            frame,
            text=preview,
            bg=frame_bg,
            fg=COLOR_FG_SECONDARY,
            font=("Segoe UI", 8),
            anchor="w",
        )
        val_label.pack(side="left", padx=5, fill="x", expand=True)

    # ========================================================================
    # PREVIEW DIALOG
    # ========================================================================

    def show_preview(self) -> None:
        """Show preview of final translation result."""
        if not self.analysis_result:
            messagebox.showerror(
                self.lang_manager.get("error"),
                self.lang_manager.get("analyze_first"),
            )
            return

        preview_data = self._build_preview_data()
        dialog = self._create_preview_dialog()
        self._populate_preview_dialog(dialog, preview_data)

    def _build_preview_data(self) -> Dict[str, str]:
        """Build preview data dictionary."""
        preview_data = {}

        # Add kept keys
        for key in self.analysis_result["kept_keys"]:
            preview_data[key] = self.analysis_result["old_data"][key]

        # Add new keys with status markers
        for key in self.analysis_result["new_keys"]:
            if self.selected_keys.get(key, True):
                preview_data[key] = (
                    f"[{self.lang_manager.get('will_translate')}] "
                    f"{self.analysis_result['new_data'][key]}"
                )
            else:
                preview_data[key] = (
                    f"[{self.lang_manager.get('skipped')}] "
                    f"{self.analysis_result['new_data'][key]}"
                )

        # Sort by new file order
        new_order = list(self.analysis_result["new_data"].keys())
        return {k: preview_data[k] for k in new_order if k in preview_data}

    def _create_preview_dialog(self) -> tk.Toplevel:
        """Create preview dialog window."""
        dialog = tk.Toplevel(self.root)
        dialog.title(self.lang_manager.get("preview_title"))
        dialog.configure(bg=COLOR_BG_DARK)

        # Center dialog
        dialog.update_idletasks()
        screen_w = dialog.winfo_screenwidth()
        screen_h = dialog.winfo_screenheight()
        pos_x = (screen_w - DIALOG_WIDTH) // 2
        pos_y = (screen_h - DIALOG_HEIGHT) // 2
        dialog.geometry(f"{DIALOG_WIDTH}x{DIALOG_HEIGHT}+{pos_x}+{pos_y}")
        dialog.minsize(MIN_DIALOG_WIDTH, MIN_DIALOG_HEIGHT)

        return dialog

    def _populate_preview_dialog(
        self,
        dialog: tk.Toplevel,
        preview_data: Dict[str, str]
    ) -> None:
        """Populate preview dialog with data."""
        # Header
        header = tk.Frame(dialog, bg=COLOR_BG_HEADER)
        header.pack(fill="x", padx=15, pady=15)

        tk.Label(
            header,
            text=self.lang_manager.get("preview_title"),
            font=("Segoe UI", 16, "bold"),
            bg=COLOR_BG_HEADER,
            fg=COLOR_FG_PRIMARY,
        ).pack(pady=10)

        tk.Label(
            header,
            text=self.lang_manager.get("preview_legend"),
            font=("Segoe UI", 9),
            bg=COLOR_BG_HEADER,
            fg=COLOR_FG_MUTED,
        ).pack()

        # Text area
        text_frame = tk.Frame(dialog, bg=COLOR_BG_PANEL)
        text_frame.pack(fill="both", expand=True, padx=15, pady=10)

        text = scrolledtext.ScrolledText(
            text_frame,
            bg=COLOR_BG_INPUT,
            fg=COLOR_FG_SECONDARY,
            font=("Consolas", 9),
            wrap="none",
        )
        text.pack(fill="both", expand=True, padx=10, pady=10)

        # Configure tags
        text.tag_config("translated", foreground=COLOR_SUCCESS)
        text.tag_config("will_translate", foreground=COLOR_WARNING)
        text.tag_config("skipped", foreground=COLOR_ERROR)
        text.tag_config("key", foreground=COLOR_ACCENT_CYAN)
        text.tag_config("bracket", foreground=COLOR_GRAY)

        # Insert preview data
        self._insert_preview_json(text, preview_data)
        text.config(state="disabled")

        # OK button
        self._create_action_button(
            dialog,
            self.lang_manager.get("ok_button"),
            dialog.destroy,
            COLOR_INFO,
            14,
        ).pack(pady=15)

    def _insert_preview_json(
        self,
        text: scrolledtext.ScrolledText,
        data: Dict[str, str]
    ) -> None:
        """Insert formatted JSON preview into text widget."""
        text.insert("end", "{\n", "bracket")
        items = list(data.items())

        for idx, (key, value) in enumerate(items):
            comma = "," if idx < len(items) - 1 else ""

            text.insert("end", '  "', "bracket")
            text.insert("end", key, "key")
            text.insert("end", '": "', "bracket")

            # Colorize based on status
            if self.lang_manager.get("will_translate") in value:
                text.insert("end", value, "will_translate")
            elif self.lang_manager.get("skipped") in value:
                text.insert("end", value, "skipped")
            else:
                text.insert("end", value, "translated")

            text.insert("end", f'"{comma}\n', "bracket")

        text.insert("end", "}", "bracket")

    # ========================================================================
    # TRANSLATION
    # ========================================================================

    def start_translation(self) -> None:
        """Start translation process after confirmation."""
        if not self.api_key.get().strip():
            messagebox.showerror(
                self.lang_manager.get("error"),
                self.lang_manager.get("set_api_key_error"),
            )
            return

        if not self.analysis_result or not self.analysis_result["new_keys"]:
            messagebox.showinfo(
                self.lang_manager.get("info"),
                self.lang_manager.get("nothing_to_translate_info"),
            )
            return

        to_translate = [
            k for k in self.analysis_result["new_keys"]
            if self.selected_keys.get(k, True)
        ]

        if not to_translate:
            messagebox.showinfo(
                self.lang_manager.get("info"),
                self.lang_manager.get("no_keys_selected"),
            )
            return

        # Confirm translation
        cost = self._estimate_cost(len(to_translate))
        response = messagebox.askyesno(
            self.lang_manager.get("confirm_translation"),
            self.lang_manager.get(
                "confirm_message",
                len(to_translate),
                cost,
                len(to_translate) * 2
            ),
        )

        if not response:
            return

        # Disable all buttons during translation
        self._disable_all_buttons()
        self.progress_var.set(0.0)

        # Start translation in background thread
        thread = threading.Thread(target=self.translate_keys, daemon=True)
        thread.start()

    def _disable_all_buttons(self) -> None:
        """Disable all action buttons."""
        buttons = [
            self.analyze_btn,
            self.select_btn,
            self.preview_btn,
            self.translate_btn,
            self.view_output_btn
        ]
        for btn in buttons:
            self._set_button_state(btn, False)

    def translate_keys(self) -> None:
        """
        Perform translation in batches with real token counting.
        Runs in background thread.
        """
        try:
            if OpenAI is None:
                raise RuntimeError("openai package is not installed.")

            client = OpenAI(api_key=self.api_key.get().strip())
            result = {}

            # Keep existing keys
            for key in self.analysis_result["kept_keys"]:
                result[key] = self.analysis_result["old_data"][key]

            # Reset token counters
            self.total_prompt_tokens = 0
            self.total_completion_tokens = 0

            # Initialize UI
            self.root.after(0, self._init_translation_ui)

            # Get keys to translate
            to_translate = [
                k for k in self.analysis_result["new_keys"]
                if self.selected_keys.get(k, True)
            ]

            if not to_translate:
                raise RuntimeError("No keys selected for translation.")

            # Create batches
            batches = [
                to_translate[i: i + BATCH_SIZE]
                for i in range(0, len(to_translate), BATCH_SIZE)
            ]

            source = self.source_lang.get()
            target = self.target_lang.get()

            # Process batches
            self._process_translation_batches(
                client,
                batches,
                source,
                target,
                result
            )

            # Add untranslated keys
            for key in self.analysis_result["new_keys"]:
                if not self.selected_keys.get(key, True):
                    result[key] = self.analysis_result["new_data"][key]

            # Sort by original order
            new_order = list(self.analysis_result["new_data"].keys())
            sorted_result = {k: result[k] for k in new_order if k in result}

            # Save result
            output_file = self._save_translation_result(sorted_result)
            self.last_output_file = output_file

            # Show summary
            self.root.after(0, lambda: self._show_translation_summary(output_file))

        except Exception as e:
            self.root.after(0, lambda: self._show_translation_error(e))

        finally:
            self.root.after(0, self._enable_buttons_after_translation)

    def _init_translation_ui(self) -> None:
        """Initialize UI for translation process."""
        self.results_text.delete("1.0", "end")
        self.results_text.insert(
            "end",
            self.lang_manager.get("translation_in_progress") + "\n\n",
            "info",
        )
        self.progress_var.set(0.0)

    def _process_translation_batches(
        self,
        client: OpenAI, # type: ignore
        batches: List[List[str]],
        source: str,
        target: str,
        result: Dict[str, str]
    ) -> None:
        """Process translation batches."""
        num_batches = len(batches)
        if num_batches == 0:
            raise RuntimeError("No batches to process.")

        initial_progress = 100.0 / (2 * num_batches)
        per_batch_increment = (100.0 - initial_progress) / num_batches
        current_progress = initial_progress

        self.root.after(0, lambda: self.progress_var.set(initial_progress))

        for batch_index, batch_keys in enumerate(batches, 1):
            # Translate batch
            translated_batch = self._translate_batch(
                client,
                batch_keys,
                source,
                target
            )

            # Apply results
            for key in batch_keys:
                translated_value = translated_batch.get(key)
                if isinstance(translated_value, str):
                    result[key] = translated_value
                else:
                    result[key] = self.analysis_result["new_data"][key]

            # Update progress
            current_progress += per_batch_increment
            current_progress = min(current_progress, 100.0)

            self.root.after(
                0,
                lambda idx=batch_index, keys=batch_keys, prog=current_progress:
                self._update_batch_progress(idx, len(batches), keys, result, prog)
            )

    def _translate_batch(self, client, batch_keys, source, target) -> Dict[str, str]:
        """Translate a batch safely (with placeholder protection & retry)."""
        batch_dict = {k: self.analysis_result["new_data"][k] for k in batch_keys}

        # STEP 1: Protect placeholders
        protected_batches = {}
        protected_data = {}
        for key, value in batch_dict.items():
            safe_value, placeholders = self._protect_placeholders(str(value))
            protected_batches[key] = safe_value
            protected_data[key] = placeholders

        json_chunk = json.dumps(protected_batches, ensure_ascii=False, indent=2)

        system_prompt = (
            "You are a professional AI translator specialized in precise, grammatically correct, and context-aware localization of structured data such as JSON. "
            "Translate only the text values into the target language, ensuring the result sounds natural, clear, and idiomatic for native speakers. "
            "Always use correct grammar, punctuation, and full word forms in the target language, following official linguistic standards and spelling conventions (for example, if the language uses diacritics or hyphenation, apply them correctly). "
            "Adapt sentence structure and phrasing to what is natural for the target language, maintaining fluency and readability rather than literal word-by-word translation. "
            "Ensure a professional, human-like tone suitable for user interfaces, notifications, and documentation. "
            "Do not translate or modify placeholders, variables, numbers, code fragments, HTML tags, or URLs. "
            "Preserve the exact JSON structure and return only the translated JSON object with no explanations or extra text. "
            "Prioritize translation meanings appropriate for user interfaces, system messages, and software contexts, rather than generic or abstract interpretations. "
            "Reorder short noun phrases only when it improves natural word order in the target language, without altering full sentences or breaking grammatical correctness."
            "Apply correct prepositions and articles between nouns according to the grammar of the target language, ensuring natural phrasing when such connectors are required."
        )



        user_prompt = f"""
Translate ALL values from {source} to {target}.
Keep placeholders ({{variable}}, [name], %s, etc.), HTML tags, and URLs unchanged.
Do NOT translate tokens like __P0__, __P1__, etc.
Return ONLY a valid JSON object with the same keys.

JSON:
{json_chunk}

Translated JSON:
"""

        def _try_request():
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=TRANSLATION_TEMPERATURE,
                max_tokens=MAX_TOKENS_PER_REQUEST,
            )
            content = response.choices[0].message.content.strip()
            return self._clean_json_response(content)

        # STEP 2: Try up to 2 times to get valid JSON
        parsed, raw = {}, ""
        for attempt in range(2):
            raw = _try_request()
            try:
                parsed = json.loads(raw)
                break
            except Exception:
                parsed = {}
                continue

        # STEP 3: Restore placeholders
        result = {}
        for key, original_value in batch_dict.items():
            translated_value = parsed.get(key) if isinstance(parsed, dict) else None
            if not isinstance(translated_value, str) or not translated_value.strip():
                translated_value = original_value  # fallback

            translated_value = self._restore_placeholders(translated_value, protected_data[key])
            result[key] = translated_value

        return result


    @staticmethod
    def _clean_json_response(content: str) -> str:
        """Remove markdown code fences from JSON response."""
        if content.startswith("```"):
            lines = content.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            content = "\n".join(lines).strip()
        return content

    def _update_batch_progress(
        self,
        batch_idx: int,
        total_batches: int,
        keys: List[str],
        result: Dict[str, str],
        progress: float
    ) -> None:
        """Update UI with batch progress."""
        self.results_text.insert(
            "end",
            f"Batch {batch_idx}/{total_batches} finished ({len(keys)} keys)\n",
            "info",
        )

        # Show preview of first key
        first_key = keys[0]
        preview = self._truncate_text(result[first_key], MAX_PREVIEW_LENGTH)
        self.results_text.insert(
            "end",
            f"  ✅ {first_key}: {preview}\n\n",
            "new",
        )

        self.results_text.see("end")
        self.progress_var.set(progress)

    def _show_translation_summary(self, output_file: str) -> None:
        """Show translation completion summary."""
        self.progress_var.set(100.0)

        # Calculate costs
        input_tokens = self.total_prompt_tokens
        output_tokens = self.total_completion_tokens
        total_tokens = input_tokens + output_tokens

        cost_input = input_tokens / 1_000_000 * COST_INPUT_PER_MILLION
        cost_output = output_tokens / 1_000_000 * COST_OUTPUT_PER_MILLION
        total_cost = cost_input + cost_output

        # Update results text
        self.results_text.insert("end", "═" * 90 + "\n", "info")
        self.results_text.insert("end", "Real token usage & cost\n", "info")
        self.results_text.insert("end", f"  Prompt tokens: {input_tokens}\n", "info")
        self.results_text.insert("end", f"  Completion tokens: {output_tokens}\n", "info")
        self.results_text.insert("end", f"  Total tokens: {total_tokens}\n", "info")
        self.results_text.insert(
            "end",
            f"  Real cost (approx): ${total_cost:.4f} "
            f"(input ${cost_input:.4f} + output ${cost_output:.4f})\n",
            "info",
        )
        self.results_text.see("end")

        # Update stats panel
        self._update_stats_with_tokens(total_tokens, input_tokens, output_tokens, total_cost)

        # Show success message
        messagebox.showinfo(
            self.lang_manager.get("success"),
            self.lang_manager.get("translation_complete", output_file)
            + f"\n\nTokens: {total_tokens}\nCost (approx): ${total_cost:.4f}",
        )

    def _update_stats_with_tokens(
        self,
        total_tokens: int,
        input_tokens: int,
        output_tokens: int,
        total_cost: float
    ) -> None:
        """Update statistics panel with token information."""
        self.stats_text.config(
            text=(
                f"{self.lang_manager.get('new_keys_to_translate')}: {len(self.analysis_result['new_keys'])}\n"
                f"{self.lang_manager.get('obsolete_keys')}: {len(self.analysis_result['obsolete_keys'])}\n"
                f"{self.lang_manager.get('kept_keys')}: {len(self.analysis_result['kept_keys'])}\n\n"
                f"Real tokens: {total_tokens} (in {input_tokens} / out {output_tokens})\n"
                f"Real cost: ${total_cost:.4f}"
            ),
            fg=COLOR_FG_SECONDARY,
        )

    def _show_translation_error(self, error: Exception) -> None:
        """Show translation error message."""
        messagebox.showerror(
            self.lang_manager.get("error"),
            f"{self.lang_manager.get('translation_error')}:\n{error}",
        )

    def _enable_buttons_after_translation(self) -> None:
        """Re-enable buttons after translation completes."""
        self._set_button_state(self.analyze_btn, True)

        has_analysis = self.analysis_result is not None
        has_new_keys = has_analysis and bool(self.analysis_result["new_keys"])

        if has_new_keys:
            self._set_button_state(self.select_btn, True)
            self._set_button_state(self.preview_btn, True)
            self._set_button_state(self.translate_btn, True)
        else:
            self._set_button_state(self.select_btn, False)
            self._set_button_state(self.preview_btn, False)
            self._set_button_state(self.translate_btn, False)

        if self.last_output_file and os.path.exists(self.last_output_file):
            self._set_button_state(self.view_output_btn, True)
        else:
            self._set_button_state(self.view_output_btn, False)

    def _save_translation_result(self, data: Dict[str, str]) -> str:
        """
        Save translation result to file.
        
        Args:
            data: Translated data dictionary
            
        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = Path(self.new_file).stem
        output_file = f"{base_name}_translated_{timestamp}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        return output_file

    # ========================================================================
    # VIEW OUTPUT FILE
    # ========================================================================

    def view_output_file_in_results(self) -> None:
        """Display translated output file in results area."""
        if not self.last_output_file or not os.path.exists(self.last_output_file):
            messagebox.showerror(
                self.lang_manager.get("error"),
                self.lang_manager.get("no_output_file"),
            )
            return

        try:
            with open(self.last_output_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showerror(
                self.lang_manager.get("error"),
                f"{self.lang_manager.get('no_output_file')} ({e})",
            )
            return

        self._display_output_file(data)

    def _display_output_file(self, data: Dict[str, str]) -> None:
        """Display output file with syntax highlighting."""
        self.results_text.delete("1.0", "end")

        # Header
        header_text = self.lang_manager.get(
            "output_file_header",
            os.path.basename(self.last_output_file),
        )
        self.results_text.insert("end", header_text + "\n\n", "info")

        # JSON content
        self.results_text.insert("end", "{\n", "json_brace")
        items = list(data.items())

        for idx, (key, value) in enumerate(items):
            comma = "," if idx < len(items) - 1 else ""

            self.results_text.insert("end", '  "', "json_brace")
            self.results_text.insert("end", key, "json_key")
            self.results_text.insert("end", '": "', "json_brace")

            # Format value
            if isinstance(value, str):
                v_str = value.replace("\n", "\\n")
            else:
                v_str = json.dumps(value, ensure_ascii=False)

            self.results_text.insert("end", v_str, "json_value")
            self.results_text.insert("end", f'"{comma}\n', "json_brace")

        self.results_text.insert("end", "}", "json_brace")
        self.results_text.see("1.0")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = JSONTranslatorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()