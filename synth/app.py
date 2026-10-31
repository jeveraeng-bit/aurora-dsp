"""Interfaz de escritorio profesional para Aurora By Juan Esteban Vera (YAMAHA MONTAGE DSP Edition)."""
from __future__ import annotations

import json
import math
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import sounddevice as sd

from .engine import SynthEngine, SynthParameters
from .presets import FACTORY_PRESETS
from .vocal import SCALES, VocalProcessor


NOTE_NAMES = {
    36: "C2", 37: "C#2", 38: "D2", 39: "D#2", 40: "E2", 41: "F2", 42: "F#2", 43: "G2", 44: "G#2", 45: "A2", 46: "A#2", 47: "B2",
    48: "C3", 49: "C#3", 50: "D3", 51: "D#3", 52: "E3", 53: "F3", 54: "F#3", 55: "G3", 56: "G#3", 57: "A3", 58: "A#3", 59: "B3",
    60: "C4", 61: "C#4", 62: "D4", 63: "D#4", 64: "E4", 65: "F4", 66: "F#4", 67: "G4", 68: "G#4", 69: "A4", 70: "A#4", 71: "B4",
    72: "C5", 73: "C#5", 74: "D5", 75: "D#5", 76: "E5", 77: "F5", 78: "F#5", 79: "G5", 80: "G#5", 81: "A5", 82: "A#5", 83: "B5",
    84: "C6", 85: "C#6", 86: "D6", 87: "D#6", 88: "E6", 89: "F6", 90: "F#6", 91: "G6", 92: "G#6", 93: "A6", 94: "A#6", 95: "B6",
}


class SuperKnobWidget(tk.Canvas):
    """Dial circular interactivo estilo Yamaha MONTAGE Super Knob."""
    def __init__(self, parent, size: int = 175, initial: float = 0.0, on_change=None, **kwargs):
        super().__init__(parent, width=size, height=size, bg="#0e131b", highlightthickness=0, **kwargs)
        self.size = size
        self.value = float(initial)
        self.on_change = on_change
        self._drag_start_y = 0

        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<MouseWheel>", self._on_wheel)
        self._redraw()

    def set_value(self, val: float, trigger: bool = True) -> None:
        self.value = float(np.clip(val, 0.0, 1.0))
        self._redraw()
        if trigger and self.on_change:
            self.on_change(self.value)

    def _on_press(self, event) -> None:
        self._drag_start_y = event.y

    def _on_drag(self, event) -> None:
        delta = self._drag_start_y - event.y
        self._drag_start_y = event.y
        new_val = np.clip(self.value + delta * 0.007, 0.0, 1.0)
        self.set_value(new_val)

    def _on_wheel(self, event) -> None:
        delta = 0.04 if event.delta > 0 else -0.04
        self.set_value(self.value + delta)

    def _redraw(self) -> None:
        self.delete("all")
        cx = cy = self.size / 2
        r = self.size * 0.40

        self.create_oval(cx - r - 4, cy - r - 4, cx + r + 4, cy + r + 4, fill="#161e2b", outline="#263345", width=2)
        self.create_arc(cx - r, cy - r, cx + r, cy + r, start=-45, extent=-270,
                        style=tk.ARC, outline="#1f2c3d", width=8)

        sweep = -270 * self.value
        if abs(sweep) > 0.5:
            if self.value < 0.5:
                color = "#00f0ff"
            elif self.value < 0.8:
                color = "#00e5a3"
            else:
                color = "#e040fb"
            self.create_arc(cx - r, cy - r, cx + r, cy + r, start=-45, extent=sweep,
                            style=tk.ARC, outline=color, width=8)

        r_inner = r * 0.72
        self.create_oval(cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner,
                         fill="#111722", outline="#3b4d66", width=2)

        angle_deg = 225 - self.value * 270
        rad = math.radians(angle_deg)
        x_pt = cx + math.cos(rad) * (r_inner - 3)
        y_pt = cy - math.sin(rad) * (r_inner - 3)
        x_inner = cx + math.cos(rad) * (r_inner * 0.35)
        y_inner = cy - math.sin(rad) * (r_inner * 0.35)
        self.create_line(x_inner, y_inner, x_pt, y_pt, fill="#ffffff", width=3, capstyle=tk.ROUND)

        self.create_text(cx, cy - 8, text="SUPER KNOB", fill="#8899aa", font=("Segoe UI", 7, "bold"))
        pct = int(self.value * 100)
        self.create_text(cx, cy + 8, text=f"{pct}%", fill="#00f0ff", font=("Segoe UI", 11, "bold"))


class PianoKeyboard(tk.Canvas):
    """Teclado de piano virtual extendido de 2 octavas (25 teclas) con transposición."""
    def __init__(self, parent, on_note_on, on_note_off, **kwargs):
        super().__init__(parent, height=130, bg="#0d1117", highlightthickness=0, **kwargs)
        self.on_note_on = on_note_on
        self.on_note_off = on_note_off
        self.pressed_notes: Set[int] = set()
        self.active_mouse_note: Optional[int] = None
        self.base_octave_note = 48  # C3 por defecto (C3 a C5 = 25 teclas)

        # 15 teclas blancas en 2 octavas
        self.white_offsets = [0, 2, 4, 5, 7, 9, 11, 12, 14, 16, 17, 19, 21, 23, 24]
        # 10 teclas negras en 2 octavas: (offset_semitonos, indice_blanca_izquierda)
        self.black_defs = [
            (1, 0),   # C#
            (3, 1),   # D#
            (6, 3),   # F#
            (8, 4),   # G#
            (10, 5),  # A#
            (13, 7),  # C# (octava 2)
            (15, 8),  # D# (octava 2)
            (18, 10), # F# (octava 2)
            (20, 11), # G# (octava 2)
            (22, 12), # A# (octava 2)
        ]

        self.white_rects: List[Tuple[float, float, float, float, int]] = []
        self.black_rects: List[Tuple[float, float, float, float, int]] = []

        self.bind("<Configure>", lambda _e: self.redraw())
        self.bind("<ButtonPress-1>", self._on_click)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<B1-Motion>", self._on_motion)

    def set_base_octave(self, base_note: int) -> None:
        self.base_octave_note = base_note
        self.redraw()

    def note_press(self, note: int) -> None:
        self.pressed_notes.add(note)
        self.redraw()

    def note_release(self, note: int) -> None:
        self.pressed_notes.discard(note)
        self.redraw()

    def redraw(self) -> None:
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 100:
            return

        num_white = len(self.white_offsets)
        key_w = w / num_white
        key_h = h - 6
        black_w = key_w * 0.60
        black_h = key_h * 0.62

        # 1. Dibujar teclas blancas
        self.white_rects.clear()
        for i, semitone in enumerate(self.white_offsets):
            note = self.base_octave_note + semitone
            x1 = i * key_w + 1
            x2 = (i + 1) * key_w - 1
            y1 = 2
            y2 = key_h
            is_active = note in self.pressed_notes
            color = "#00f0ff" if is_active else "#f3f6fa"
            outline = "#00b4d8" if is_active else "#94a3b8"
            self.create_rectangle(x1, y1, x2, y2, fill=color, outline=outline, width=1)

            note_name = NOTE_NAMES.get(note, str(note))
            self.create_text(x1 + key_w / 2, y2 - 16, text=note_name,
                             fill="#09131d" if not is_active else "#002030", font=("Segoe UI", 8, "bold"))
            self.white_rects.append((x1, y1, x2, y2, note))

        # 2. Dibujar teclas negras
        self.black_rects.clear()
        for semitone, white_idx in self.black_defs:
            note = self.base_octave_note + semitone
            center_x = (white_idx + 1) * key_w
            x1 = center_x - black_w / 2
            x2 = center_x + black_w / 2
            y1 = 2
            y2 = black_h
            is_active = note in self.pressed_notes
            color = "#00e5a3" if is_active else "#151c24"
            outline = "#84e6c4" if is_active else "#2d3748"
            self.create_rectangle(x1, y1, x2, y2, fill=color, outline=outline, width=1)

            note_name = NOTE_NAMES.get(note, "")
            if "#" in note_name:
                self.create_text(center_x, y2 - 12, text=note_name.split("#")[0] + "#",
                                 fill="#8899aa" if not is_active else "#002030", font=("Segoe UI", 7, "bold"))
            self.black_rects.append((x1, y1, x2, y2, note))

    def _get_note_at(self, x: float, y: float) -> Optional[int]:
        for x1, y1, x2, y2, note in self.black_rects:
            if x1 <= x <= x2 and y1 <= y <= y2:
                return note
        for x1, y1, x2, y2, note in self.white_rects:
            if x1 <= x <= x2 and y1 <= y <= y2:
                return note
        return None

    def _on_click(self, event) -> None:
        note = self._get_note_at(event.x, event.y)
        if note is not None:
            self.active_mouse_note = note
            self.pressed_notes.add(note)
            self.on_note_on(note)
            self.redraw()

    def _on_release(self, _event) -> None:
        if self.active_mouse_note is not None:
            self.on_note_off(self.active_mouse_note)
            self.pressed_notes.discard(self.active_mouse_note)
            self.active_mouse_note = None
            self.redraw()

    def _on_motion(self, event) -> None:
        note = self._get_note_at(event.x, event.y)
        if note != self.active_mouse_note:
            if self.active_mouse_note is not None:
                self.on_note_off(self.active_mouse_note)
                self.pressed_notes.discard(self.active_mouse_note)
            if note is not None:
                self.on_note_on(note)
                self.pressed_notes.add(note)
            self.active_mouse_note = note
            self.redraw()


class VUMeter(tk.Canvas):
    """Vúmetro estéreo estilo barra LED con degradado verde-amarillo-rojo."""
    def __init__(self, parent, width: int = 140, height: int = 24, **kwargs):
        super().__init__(parent, width=width, height=height, bg="#0d1117", highlightthickness=0, **kwargs)
        self.w, self.h = width, height
        self.decay_l = self.decay_r = 0.0

    def update_levels(self, l_level: float, r_level: float) -> None:
        self.decay_l = max(l_level, self.decay_l * 0.82)
        self.decay_r = max(r_level, self.decay_r * 0.82)
        self.delete("all")
        bar_h = (self.h - 6) / 2
        self._draw_channel(2, 2, self.w - 4, bar_h, self.decay_l, "L")
        self._draw_channel(2, 4 + bar_h, self.w - 4, bar_h, self.decay_r, "R")

    def _draw_channel(self, x: float, y: float, w: float, h: float, val: float, label: str) -> None:
        self.create_rectangle(x, y, x + w, y + h, fill="#161e27", outline="")
        fill_w = max(0.0, min(1.0, val)) * w
        if fill_w > 0:
            if val < 0.65:
                color = "#00e5a3"
            elif val < 0.88:
                color = "#ffb703"
            else:
                color = "#ff4d6d"
            self.create_rectangle(x, y, x + fill_w, y + h, fill=color, outline="")
        self.create_text(x + 10, y + h / 2, text=label, fill="#ffffff", font=("Segoe UI", 7, "bold"))


class SynthApp:
    def __init__(self) -> None:
        self.engine = SynthEngine()
        self.pressed: Set[str] = set()
        self.controls: Dict[str, Any] = {}
        self.slider_readouts: Dict[str, ttk.Label] = {}
        self.vocal = VocalProcessor(self.engine.sample_rate)
        self.mic_enabled = False
        self.vocal_gain = 0.8
        self.stream = None
        self.octave_shift = 0  # Desplazamiento de octavas (-2 a +2)

        # Configuración de ventana principal con marca de Juan Esteban Vera
        self.root = tk.Tk()
        self.root.title("Aurora By Juan Esteban Vera — YAMAHA MONTAGE DSP Edition")
        self.root.geometry("1100x900")
        self.root.minsize(920, 740)
        self.root.configure(bg="#0c1017")

        # Secuenciador
        self.sequence: List[Optional[int]] = [60, None, 64, None, 67, None, 64, None, 62, None, 65, None, 69, None, 65, None]
        self.sequence_playing = False
        self.sequence_step = 0
        self.sequence_job = None

        self._style()
        self._build_menu_bar()
        self._build()

        self.root.bind_all("<KeyPress>", self._key_down)
        self.root.bind_all("<KeyRelease>", self._key_up)
        self.root.protocol("WM_DELETE_WINDOW", self._close)

        self._meter_tick()

    def _style(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure("TFrame", background="#0c1017")
        style.configure("Header.TFrame", background="#121824")
        style.configure("TLabel", background="#0c1017", foreground="#e6edf3", font=("Segoe UI", 9))
        style.configure("Header.TLabel", background="#121824", foreground="#ffffff", font=("Segoe UI", 16, "bold"))
        style.configure("Author.TLabel", background="#121824", foreground="#00f0ff", font=("Segoe UI", 10, "bold"))
        style.configure("SubHeader.TLabel", background="#121824", foreground="#7d8b9e", font=("Segoe UI", 9))
        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"), foreground="#00f0ff")
        style.configure("Section.TLabel", font=("Segoe UI", 11, "bold"), foreground="#00f0ff")
        style.configure("Sub.TLabel", foreground="#8b949e")

        style.configure("TLabelframe", background="#121824", foreground="#00f0ff", bordercolor="#212b3a")
        style.configure("TLabelframe.Label", background="#121824", foreground="#00f0ff", font=("Segoe UI", 9, "bold"))

        style.configure("TButton", font=("Segoe UI", 9, "bold"), background="#1f2937", foreground="#e6edf3", padding=6)
        style.map("TButton",
                  background=[("active", "#00f0ff"), ("pressed", "#00b4d8")],
                  foreground=[("active", "#09131d"), ("pressed", "#09131d")])

        style.configure("Accent.TButton", font=("Segoe UI", 9, "bold"), background="#00f0ff", foreground="#09131d", padding=6)
        style.map("Accent.TButton",
                  background=[("active", "#00b4d8"), ("pressed", "#0077b6")],
                  foreground=[("active", "#09131d"), ("pressed", "#ffffff")])

        style.configure("TCombobox", fieldbackground="#151d28", background="#1f2937", foreground="#e6edf3", padding=4)
        style.configure("TScale", background="#121824", troughcolor="#1a2332", sliderlength=18)

    def _build_menu_bar(self) -> None:
        """Barra de menú superior nativa de la ventana."""
        menu_bar = tk.Menu(self.root)

        # Menú Archivo / Presets
        file_menu = tk.Menu(menu_bar, tearoff=False)
        file_menu.add_command(label="💾 Guardar Preset...", command=self._save_preset)
        file_menu.add_command(label="📂 Cargar Preset...", command=self._load_preset)
        file_menu.add_separator()
        file_menu.add_command(label="💾 Guardar Secuencia de Música...", command=self._save_song)
        file_menu.add_command(label="📂 Cargar Secuencia de Música...", command=self._load_song)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self._close)
        menu_bar.add_cascade(label="Archivo", menu=file_menu)

        # Menú Navegación de Modos
        nav_menu = tk.Menu(menu_bar, tearoff=False)
        nav_menu.add_command(label="🎹 Sintetizador & FM", command=lambda: self.tabs.select(self.synth_tab))
        nav_menu.add_command(label="🎛️ Super Knob & Efectos", command=lambda: self.tabs.select(self.fx_tab))
        nav_menu.add_command(label="🎼 Secuenciador", command=lambda: self.tabs.select(self.sequence_tab))
        nav_menu.add_command(label="📈 Visualizador FFT / Osciloscopio", command=lambda: self.tabs.select(self.visual_tab))
        nav_menu.add_command(label="🎤 Voz & Afinación", command=lambda: self.tabs.select(self.vocal_tab))
        menu_bar.add_cascade(label="Modos", menu=nav_menu)

        # Menú Ayuda y Guía de Uso
        help_menu = tk.Menu(menu_bar, tearoff=False)
        help_menu.add_command(label="📖 ¿Cómo Usar Aurora? (Guía Completa)", command=self._show_help_dialog)
        help_menu.add_command(label="👤 Acerca del Desarrollador (Juan Esteban Vera)", command=self._show_author_dialog)
        menu_bar.add_cascade(label="Ayuda & Guía", menu=help_menu)

        self.root.configure(menu=menu_bar)

    def _build(self) -> None:
        # 1. Barra superior (Header con autor Juan Esteban Vera y botones de ayuda)
        header = ttk.Frame(self.root, style="Header.TFrame", padding=(16, 10))
        header.pack(fill="x")

        # Logo, Título y Autor
        brand_box = ttk.Frame(header, style="Header.TFrame")
        brand_box.pack(side="left")
        ttk.Label(brand_box, text="AURORA", style="Title.TLabel").pack(side="left")
        ttk.Label(brand_box, text="By Juan Esteban Vera", style="Author.TLabel").pack(side="left", padx=(10, 4))
        ttk.Label(brand_box, text="· YAMAHA MONTAGE DSP", style="SubHeader.TLabel").pack(side="left", pady=(2, 0))

        # Botón directo: CÓMO USARLO
        help_btn = ttk.Button(header, text="📖 CÓMO USARLO", command=self._show_help_dialog, style="Accent.TButton")
        help_btn.pack(side="left", padx=(24, 6))

        # Botón directo: DESARROLLADOR
        author_btn = ttk.Button(header, text="👤 DESARROLLADOR", command=self._show_author_dialog)
        author_btn.pack(side="left", padx=4)

        # Sección de Presets de Fábrica
        preset_box = ttk.Frame(header, style="Header.TFrame")
        preset_box.pack(side="left", padx=16)
        ttk.Label(preset_box, text="PRESET:", style="SubHeader.TLabel").pack(side="left", padx=(0, 6))

        self.preset_var = tk.StringVar(value="Yamaha DX7 E-Piano")
        self.preset_combo = ttk.Combobox(preset_box, textvariable=self.preset_var, values=list(FACTORY_PRESETS.keys()),
                                         state="readonly", width=22)
        self.preset_combo.pack(side="left")
        self.preset_combo.bind("<<ComboboxSelected>>", self._on_factory_preset_selected)

        # Botón de silenciar pánico
        ttk.Button(header, text="⏹ SILENCIAR TODO (ESC)", command=self.engine.all_notes_off).pack(side="right", padx=6)

        # Vúmetro Estéreo
        vu_box = ttk.Frame(header, style="Header.TFrame")
        vu_box.pack(side="right", padx=10)
        ttk.Label(vu_box, text="OUTPUT VU", style="SubHeader.TLabel").pack(side="top", anchor="e")
        self.vu_meter = VUMeter(vu_box, width=120, height=18)
        self.vu_meter.pack(side="top", pady=(2, 0))

        # 2. Pestañas de Navegación
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=(6, 0))

        self.synth_tab = ttk.Frame(self.tabs)
        self.fx_tab = ttk.Frame(self.tabs)
        self.sequence_tab = ttk.Frame(self.tabs)
        self.visual_tab = ttk.Frame(self.tabs)
        self.vocal_tab = ttk.Frame(self.tabs)

        self.tabs.add(self.synth_tab, text="  🎹 SINTETIZADOR & FM  ")
        self.tabs.add(self.fx_tab, text="  🎛️ SUPER KNOB & EFECTOS  ")
        self.tabs.add(self.sequence_tab, text="  🎼 SECUENCIADOR  ")
        self.tabs.add(self.visual_tab, text="  📈 VISUALIZADOR  ")
        self.tabs.add(self.vocal_tab, text="  🎤 VOZ / AFINACIÓN  ")

        self._build_synth_tab()
        self._build_fx_tab()
        self._build_sequencer_tab()
        self._build_visualizer_tab()
        self._build_vocal_tab()

        # 3. Teclado de Piano Virtual Extendió (25 teclas) con Transposición de Octavas
        piano_container = ttk.Frame(self.root, padding=(12, 4, 12, 8))
        piano_container.pack(fill="x", side="bottom")

        # Barra de control de octava
        oct_bar = ttk.Frame(piano_container)
        oct_bar.pack(fill="x", pady=(0, 4))

        ttk.Button(oct_bar, text="◀ OCT -", command=self._octave_down, width=9).pack(side="left")
        self.octave_label = ttk.Label(oct_bar, text="Octavas: C3 – C5 (25 Teclas)", font=("Segoe UI", 9, "bold"), foreground="#00f0ff")
        self.octave_label.pack(side="left", padx=12)
        ttk.Button(oct_bar, text="OCT + ▶", command=self._octave_up, width=9).pack(side="left")

        ttk.Label(oct_bar, text="💡 Toca con ratón o usa tu teclado de computadora (Z-M octava grave / Q-U octava aguda o A-K)",
                  style="Sub.TLabel").pack(side="right")

        # Lienzo del teclado de piano
        self.piano = PianoKeyboard(piano_container, on_note_on=self.engine.note_on, on_note_off=self.engine.note_off)
        self.piano.pack(fill="x")

        self._apply_preset(FACTORY_PRESETS["Yamaha DX7 E-Piano"])

    def _octave_down(self) -> None:
        if self.octave_shift > -2:
            self.octave_shift -= 1
            self._update_octave_view()

    def _octave_up(self) -> None:
        if self.octave_shift < 2:
            self.octave_shift += 1
            self._update_octave_view()

    def _update_octave_view(self) -> None:
        base = 48 + self.octave_shift * 12
        self.piano.set_base_octave(base)
        start_name = NOTE_NAMES.get(base, f"C{base//12 - 1}")
        end_name = NOTE_NAMES.get(base + 24, f"C{base//12 + 1}")
        self.octave_label.configure(text=f"Octavas: {start_name} – {end_name} (25 Teclas)")

    def _show_author_dialog(self) -> None:
        """Ventana de información del desarrollador Juan Esteban Vera."""
        dlg = tk.Toplevel(self.root)
        dlg.title("Acerca del Desarrollador — Juan Esteban Vera")
        dlg.geometry("520x360")
        dlg.configure(bg="#121824")
        dlg.transient(self.root)
        dlg.grab_set()

        outer = ttk.Frame(dlg, style="Header.TFrame", padding=24)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="AURORA SYNTHESIZER", style="Title.TLabel").pack(anchor="center")
        ttk.Label(outer, text="Versión 2.0.0 — Yamaha MONTAGE DSP Edition", style="Sub.TLabel").pack(anchor="center", pady=(2, 16))

        box = ttk.LabelFrame(outer, text=" CRÉDITOS Y DESARROLLO ", padding=16)
        box.pack(fill="both", expand=True)

        ttk.Label(box, text="Desarrollado con dedicación por:", style="Sub.TLabel").pack(anchor="w")
        ttk.Label(box, text="JUAN ESTEBAN VERA", font=("Segoe UI", 16, "bold"), foreground="#00f0ff").pack(anchor="w", pady=(2, 12))

        ttk.Label(box, text="Características técnicas principales:", style="Sub.TLabel").pack(anchor="w")
        details = (
            "• Motor de Síntesis Polifónica de 6 voces en tiempo real.\n"
            "• Síntesis Híbrida: Sustractiva + Modulación de Frecuencia (FM-X / DX7).\n"
            "• Filtro Analógico Resonante TPT de 2 polos (Yamaha CS-80).\n"
            "• Motion Control Super Knob interactivo multidimensional.\n"
            "• Multiefectos: Analog Delay estéreo, Saturación Drive y Reverb Schroeder.\n"
            "• Procesador Vocal con afinador y corrección granular de tono."
        )
        ttk.Label(box, text=details, justify="left").pack(anchor="w", pady=(4, 0))

        ttk.Button(outer, text="Cerrar", command=dlg.destroy, style="Accent.TButton").pack(anchor="center", pady=(16, 0))

    def _show_help_dialog(self) -> None:
        """Manual interactivo y menú de cómo usar el sintetizador."""
        dlg = tk.Toplevel(self.root)
        dlg.title("Guía de Uso — Aurora By Juan Esteban Vera")
        dlg.geometry("680x560")
        dlg.configure(bg="#0c1017")
        dlg.transient(self.root)
        dlg.grab_set()

        outer = ttk.Frame(dlg, padding=20)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="MANUAL DE USUARIO — AURORA", style="Title.TLabel").pack(anchor="w")
        ttk.Label(outer, text="Aprende a dominar todas las funciones de tu sintetizador", style="Sub.TLabel").pack(anchor="w", pady=(0, 12))

        notebook = ttk.Notebook(outer)
        notebook.pack(fill="both", expand=True)

        # Pestaña 1: Tocar notas
        t1 = ttk.Frame(notebook, padding=16)
        notebook.add(t1, text="🎹 Cómo Tocar")
        ttk.Label(t1, text="FORMAS DE TOCAR EL INSTRUMENTO", style="Section.TLabel").pack(anchor="w")
        t1_text = (
            "1. Teclado de Piano Virtual (25 teclas en pantalla):\n"
            "   • Haz clic o arrastra el ratón sobre cualquier tecla blanca o negra.\n"
            "   • Usa los botones [◀ OCT -] y [OCT + ▶] para navegar desde C1 hasta C7.\n\n"
            "2. Con el Teclado de tu Computadora:\n"
            "   • Octava Grave: Teclas Z X C V B N M (blancas) y S D G H J (negras).\n"
            "   • Octava Aguda: Teclas Q W E R T Y U I (blancas) y 2 3 5 6 7 (negras).\n"
            "   • Fila Central Clásica: Teclas A S D F G H J K (blancas) y W E T Y U (negras).\n\n"
            "3. Tecla de Emergencia:\n"
            "   • Pulsa 'ESC' en cualquier momento para silenciar todas las notas al instante."
        )
        ttk.Label(t1, text=t1_text, justify="left").pack(anchor="w", pady=(8, 0))

        # Pestaña 2: Super Knob y Sonido
        t2 = ttk.Frame(notebook, padding=16)
        notebook.add(t2, text="🎛️ Super Knob & FM")
        ttk.Label(t2, text="SISTEMA DE CONTROL Y SÍNTESIS YAMAHA", style="Section.TLabel").pack(anchor="w")
        t2_text = (
            "1. El Super Knob (Mando Maestro):\n"
            "   • Arrastra verticalmente con el ratón o usa la rueda de desplazamiento sobre el dial.\n"
            "   • Modula de forma simultánea armónicos FM, apertura de filtro, resonancia,\n"
            "     calidez de drive y la dimensión del delay/reverb en un solo gesto expresivo.\n\n"
            "2. Síntesis FM (Frecuencia Modulada estilo DX7 / FM-X):\n"
            "   • Incrementa 'Modulación FM' para añadir armónicos metálicos, campanas o timbres agresivos.\n"
            "   • Ajusta 'Intervalo Semitonos' y 'Desafinación' del OSC 2 para modular el espectro armónico.\n\n"
            "3. Filtro Resonante (Estilo CS-80):\n"
            "   • Combina 'Frecuencia de Corte' y 'Resonancia (Q)' para conseguir barridos clásicos analógicos."
        )
        ttk.Label(t2, text=t2_text, justify="left").pack(anchor="w", pady=(8, 0))

        # Pestaña 3: Presets y Secuenciador
        t3 = ttk.Frame(notebook, padding=16)
        notebook.add(t3, text="🎼 Presets & Secuenciador")
        ttk.Label(t3, text="PRODUCCIÓN Y SECUENCIAS", style="Section.TLabel").pack(anchor="w")
        t3_text = (
            "1. Selector de Presets de Fábrica (Performance):\n"
            "   • Elige en el menú superior entre clásicos como 'Yamaha DX7 E-Piano',\n"
            "     'CS-80 Vangelis Pad', 'Montage Super Lead', 'TX81Z Lately Bass', etc.\n"
            "   • Puedes guardar tus propios presets en formato JSON con el botón 'Guardar Preset'.\n\n"
            "2. Secuenciador de 16 Pasos:\n"
            "   • Ve a la pestaña 'SECUENCIADOR'.\n"
            "   • Haz clic en cualquiera de los 16 pasos para alternar la nota deseada.\n"
            "   • Ajusta el control de Tempo (BPM) y presiona '▶ REPRODUCIR'."
        )
        ttk.Label(t3, text=t3_text, justify="left").pack(anchor="w", pady=(8, 0))

        # Pestaña 4: Afinación Vocal
        t4 = ttk.Frame(notebook, padding=16)
        notebook.add(t4, text="🎤 Modo Afinador")
        ttk.Label(t4, text="CORRECCIÓN TONAL Y VOZ", style="Section.TLabel").pack(anchor="w")
        t4_text = (
            "1. Conecta auriculares para evitar retroalimentación acústica.\n"
            "2. Activa la casilla de 'Activar monitorización y micrófono'.\n"
            "3. Selecciona la escala objetivo (ej. C mayor o C menor).\n"
            "4. Canta o habla por el micrófono: el motor detectará tu tono y lo afinará automáticamente\n"
            "   a la nota más cercana de la escala musical elegida."
        )
        ttk.Label(t4, text=t4_text, justify="left").pack(anchor="w", pady=(8, 0))

        ttk.Button(outer, text="Entendido, cerrar", command=dlg.destroy, style="Accent.TButton").pack(anchor="e", pady=(14, 0))

    def _build_synth_tab(self) -> None:
        outer = ttk.Frame(self.synth_tab, padding=16)
        outer.pack(fill="both", expand=True)

        cols = ttk.Frame(outer)
        cols.pack(fill="both", expand=True)
        cols.columnconfigure(0, weight=1)
        cols.columnconfigure(1, weight=1)
        cols.columnconfigure(2, weight=1)

        # Columna 1: OSCILADORES & FM
        osc_group = ttk.LabelFrame(cols, text=" OSCILADORES & MODULACIÓN FM (DX7) ", padding=12)
        osc_group.grid(row=0, column=0, sticky="nsew", padx=6, pady=4)
        self._choice(osc_group, "Forma Onda OSC 1", "waveform_1", ["sine", "triangle", "saw", "square", "noise"])
        self._choice(osc_group, "Forma Onda OSC 2", "waveform_2", ["sine", "triangle", "saw", "square", "noise"])
        self._slider(osc_group, "Mezcla OSC 2", "osc2_mix", 0.0, 1.0, 0.01)
        self._slider(osc_group, "Desafinación (Cents)", "detune_cents", -40.0, 40.0, 0.5)
        self._slider(osc_group, "Intervalo Semitonos", "osc2_semitones", -24.0, 24.0, 1.0)
        self._slider(osc_group, "⚡ Modulación FM (FM-X)", "fm_depth", 0.0, 1.0, 0.01)

        # Columna 2: FILTRO RESONANTE
        filter_group = ttk.LabelFrame(cols, text=" FILTRO VCF RESONANTE (CS-80) ", padding=12)
        filter_group.grid(row=0, column=1, sticky="nsew", padx=6, pady=4)
        self._slider(filter_group, "Frecuencia de Corte (Hz)", "cutoff", 50.0, 14000.0, 10.0)
        self._slider(filter_group, "Resonancia (Q)", "resonance", 0.0, 0.95, 0.01)
        self._slider(filter_group, "Vibrato Velocidad (Hz)", "vibrato_rate", 0.2, 20.0, 0.1)
        self._slider(filter_group, "Vibrato Profundidad (Cents)", "vibrato_depth", 0.0, 100.0, 1.0)

        # Columna 3: ENVOLVENTE ADSR
        env_group = ttk.LabelFrame(cols, text=" ENVOLVENTE ADSR DE AMPLITUD ", padding=12)
        env_group.grid(row=0, column=2, sticky="nsew", padx=6, pady=4)
        self._slider(env_group, "Ataque (s)", "attack", 0.001, 2.5, 0.001)
        self._slider(env_group, "Decaimiento (s)", "decay", 0.01, 2.5, 0.01)
        self._slider(env_group, "Sustain (Nivel)", "sustain", 0.0, 1.0, 0.01)
        self._slider(env_group, "Release (s)", "release", 0.01, 3.5, 0.01)
        self._slider(env_group, "Ganancia Master", "master_gain", 0.0, 1.0, 0.01)

        # Botones de gestión de archivos de presets
        btn_bar = ttk.Frame(outer)
        btn_bar.pack(fill="x", pady=(12, 0))
        ttk.Button(btn_bar, text="💾 GUARDAR PRESET JSON", command=self._save_preset).pack(side="left", padx=4)
        ttk.Button(btn_bar, text="📂 ABRIR PRESET JSON", command=self._load_preset).pack(side="left", padx=4)

    def _build_fx_tab(self) -> None:
        outer = ttk.Frame(self.fx_tab, padding=16)
        outer.pack(fill="both", expand=True)

        cols = ttk.Frame(outer)
        cols.pack(fill="both", expand=True)
        cols.columnconfigure(0, weight=2)
        cols.columnconfigure(1, weight=3)

        # Columna Izquierda: El Super Knob Central
        sk_frame = ttk.LabelFrame(cols, text=" MOTION CONTROL SYSTEM (SUPER KNOB) ", padding=14)
        sk_frame.grid(row=0, column=0, sticky="nsew", padx=6, pady=4)

        ttk.Label(sk_frame, text="Mando Maestro Multidimensional", style="Section.TLabel").pack(anchor="center")
        ttk.Label(sk_frame, text="Modula armónicos FM, apertura de filtro, resonancia,\ncalidez drive y dimensiones de delay/reverb.",
                  style="Sub.TLabel", justify="center").pack(anchor="center", pady=(2, 12))

        self.super_knob_ui = SuperKnobWidget(sk_frame, size=180, initial=0.0, on_change=self._on_super_knob_change)
        self.super_knob_ui.pack(anchor="center", pady=6)

        self._slider(sk_frame, "Posición Super Knob", "super_knob", 0.0, 1.0, 0.01,
                     on_val_change=lambda v: self.super_knob_ui.set_value(v, trigger=False))

        # Columna Derecha: Efectos MONTAGE
        fx_frame = ttk.LabelFrame(cols, text=" PROCESADOR DE EFECTOS MONTAGE (DSP INSERTION) ", padding=14)
        fx_frame.grid(row=0, column=1, sticky="nsew", padx=6, pady=4)

        ttk.Label(fx_frame, text="DRIVE & SATURACIÓN ANALÓGICA", style="Section.TLabel").pack(anchor="w")
        self._slider(fx_frame, "Drive Armónico", "drive", 0.0, 1.0, 0.01)

        ttk.Label(fx_frame, text="ANALOG STEREO DELAY", style="Section.TLabel").pack(anchor="w", pady=(10, 0))
        self._slider(fx_frame, "Tiempo Delay (s)", "delay_time", 0.02, 1.2, 0.01)
        self._slider(fx_frame, "Realimentación (Feedback)", "delay_feedback", 0.0, 0.85, 0.01)
        self._slider(fx_frame, "Mezcla Delay", "delay_mix", 0.0, 0.8, 0.01)

        ttk.Label(fx_frame, text="SCHROEDER STEREO REVERBERATION", style="Section.TLabel").pack(anchor="w", pady=(10, 0))
        self._slider(fx_frame, "Tamaño Espacio (Room)", "reverb_room", 0.0, 0.88, 0.01)
        self._slider(fx_frame, "Mezcla Reverb", "reverb_mix", 0.0, 0.8, 0.01)

    def _build_sequencer_tab(self) -> None:
        outer = ttk.Frame(self.sequence_tab, padding=20)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="SECUENCIADOR POR PASOS Y MOTION", style="Title.TLabel").pack(anchor="w")
        ttk.Label(outer, text="Secuencia polifónica de 16 pasos con tempo sincronizado e iluminación activa.",
                  style="Sub.TLabel").pack(anchor="w", pady=(0, 14))

        transport = ttk.LabelFrame(outer, text=" TRANSPORTE & TEMPO ", padding=12)
        transport.pack(fill="x")
        self.tempo = tk.DoubleVar(value=112)
        ttk.Label(transport, text="Tempo (BPM):").pack(side="left")
        ttk.Scale(transport, from_=50, to=200, variable=self.tempo).pack(side="left", fill="x", expand=True, padx=12)
        self.tempo_label = ttk.Label(transport, text="112 BPM", width=10)
        self.tempo_label.pack(side="left")
        self.tempo.trace_add("write", lambda *_: self.tempo_label.configure(text=f"{int(self.tempo.get())} BPM"))

        self.play_button = ttk.Button(transport, text="▶ REPRODUCIR", command=self._toggle_sequence, style="Accent.TButton")
        self.play_button.pack(side="left", padx=8)
        ttk.Button(transport, text="💾 GUARDAR SECUENCIA", command=self._save_song).pack(side="left", padx=4)
        ttk.Button(transport, text="📂 ABRIR SECUENCIA", command=self._load_song).pack(side="left", padx=4)

        grid_frame = ttk.LabelFrame(outer, text=" PATRÓN (Haz clic para alternar notas) ", padding=14)
        grid_frame.pack(fill="x", pady=(16, 0))

        self.step_buttons: List[ttk.Button] = []
        for i in range(16):
            btn = ttk.Button(grid_frame, command=lambda idx=i: self._cycle_step(idx))
            btn.grid(row=0, column=i, padx=2, sticky="ew")
            grid_frame.columnconfigure(i, weight=1)
            self.step_buttons.append(btn)
        self._refresh_steps()

    def _build_visualizer_tab(self) -> None:
        outer = ttk.Frame(self.visual_tab, padding=18)
        outer.pack(fill="both", expand=True)

        wave_frame = ttk.LabelFrame(outer, text=" OSCILOSCOPIO DIGITAL — FORMA DE ONDA ", padding=8)
        wave_frame.pack(fill="both", expand=True)
        self.wave_canvas = tk.Canvas(wave_frame, height=220, bg="#081018", highlightthickness=0)
        self.wave_canvas.pack(fill="both", expand=True)

        spec_frame = ttk.LabelFrame(outer, text=" ANALIZADOR DE ESPECTRO FFT — FRECUENCIAS ", padding=8)
        spec_frame.pack(fill="both", expand=True, pady=(12, 0))
        self.spec_canvas = tk.Canvas(spec_frame, height=180, bg="#081018", highlightthickness=0)
        self.spec_canvas.pack(fill="both", expand=True)

        self.root.after(60, self._draw_waveform)
        self.root.after(75, self._draw_spectrum)

    def _build_vocal_tab(self) -> None:
        outer = ttk.Frame(self.vocal_tab, padding=20)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="PROCESADOR VOCAL & AFINACIÓN", style="Title.TLabel").pack(anchor="w")
        ttk.Label(outer, text="Detección de tono por autocorrelación y corrección tonal en tiempo real.",
                  style="Sub.TLabel").pack(anchor="w", pady=(0, 14))

        source = ttk.LabelFrame(outer, text=" ENTRADA DE MICRÓFONO ", padding=12)
        source.pack(fill="x")
        self.mic_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(source, text="Activar monitorización y afinación de micrófono (usar auriculares)",
                        variable=self.mic_var, command=self._toggle_mic).pack(anchor="w")
        self.vocal_status = ttk.Label(source, text="Micrófono desactivado", style="Sub.TLabel")
        self.vocal_status.pack(anchor="w", pady=(6, 0))

        tuning = ttk.LabelFrame(outer, text=" CORRECCIÓN TONAL & ESCALA ", padding=12)
        tuning.pack(fill="x", pady=(14, 0))
        ttk.Label(tuning, text="Escala objetivo").pack(anchor="w")
        self.scale_var = tk.StringVar(value="C mayor")
        scale_box = ttk.Combobox(tuning, values=list(SCALES), textvariable=self.scale_var, state="readonly", width=20)
        scale_box.pack(anchor="w", pady=(2, 10))
        scale_box.bind("<<ComboboxSelected>>", lambda _: self.vocal.set_scale(self.scale_var.get()))

        self._vocal_slider(tuning, "Intensidad de Corrección", "amount", 0.0, 1.0, 0.01)
        self._vocal_slider(tuning, "Mezcla Señal Afinada", "mix", 0.0, 1.0, 0.01)
        self._vocal_slider(tuning, "Ganancia de Micrófono", "vocal_gain", 0.0, 1.5, 0.01)

        self.root.after(150, self._update_vocal_status)

    def _choice(self, parent, label: str, name: str, options: List[str]) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=(2, 8))
        ttk.Label(row, text=label).pack(anchor="w")
        val = tk.StringVar(value=getattr(self.engine.parameters, name))
        self.controls[name] = val
        box = ttk.Combobox(row, values=options, textvariable=val, state="readonly")
        box.pack(fill="x", pady=(1, 0))
        box.bind("<<ComboboxSelected>>", lambda _: self.engine.set_parameter(name, val.get()))

    def _slider(self, parent, label: str, name: str, low: float, high: float, step: float,
                on_val_change=None) -> None:
        current = float(getattr(self.engine.parameters, name))
        val = tk.DoubleVar(value=current)
        self.controls[name] = val

        row = ttk.Frame(parent)
        row.pack(fill="x", pady=(2, 6))

        top_line = ttk.Frame(row)
        top_line.pack(fill="x")
        ttk.Label(top_line, text=label).pack(side="left")
        shown = ttk.Label(top_line, text=f"{current:.3g}", width=8, foreground="#00f0ff")
        shown.pack(side="right", anchor="e")
        self.slider_readouts[name] = shown

        def changed(raw: str) -> None:
            num = round(float(raw) / step) * step
            shown.configure(text=f"{num:.3g}")
            self.engine.set_parameter(name, num)
            if on_val_change:
                on_val_change(num)

        scale = ttk.Scale(row, from_=low, to=high, variable=val, command=changed)
        scale.pack(fill="x", pady=(2, 0))

    def _vocal_slider(self, parent, label: str, attr: str, low: float, high: float, step: float) -> None:
        current = self.vocal_gain if attr == "vocal_gain" else getattr(self.vocal, attr)
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=(2, 8))

        top = ttk.Frame(row)
        top.pack(fill="x")
        ttk.Label(top, text=label).pack(side="left")
        shown = ttk.Label(top, text=f"{current:.2f}", width=8, foreground="#00e5a3")
        shown.pack(side="right")

        def changed(raw: str) -> None:
            num = round(float(raw) / step) * step
            shown.configure(text=f"{num:.2f}")
            if attr == "vocal_gain":
                self.vocal_gain = num
            else:
                setattr(self.vocal, attr, num)

        ttk.Scale(row, from_=low, to=high, value=current, command=changed).pack(fill="x", pady=(2, 0))

    def _on_super_knob_change(self, val: float) -> None:
        if "super_knob" in self.controls:
            self.controls["super_knob"].set(val)
        if "super_knob" in self.slider_readouts:
            self.slider_readouts["super_knob"].configure(text=f"{val:.3g}")
        self.engine.set_parameter("super_knob", val)

    def _on_factory_preset_selected(self, _event=None) -> None:
        preset_name = self.preset_var.get()
        if preset_name in FACTORY_PRESETS:
            self._apply_preset(FACTORY_PRESETS[preset_name])

    def _apply_preset(self, preset_dict: Dict[str, Any]) -> None:
        for name, raw_val in preset_dict.items():
            if name in self.controls:
                self.controls[name].set(raw_val)
                self.engine.set_parameter(name, raw_val)
                if name in self.slider_readouts:
                    self.slider_readouts[name].configure(text=f"{float(raw_val):.3g}")
        if "super_knob" in preset_dict and hasattr(self, "super_knob_ui"):
            self.super_knob_ui.set_value(float(preset_dict["super_knob"]), trigger=False)

    def _meter_tick(self) -> None:
        if self.root.winfo_exists():
            pl, pr = self.engine.peak_levels()
            self.vu_meter.update_levels(pl, pr)
            self.root.after(45, self._meter_tick)

    def _draw_waveform(self) -> None:
        if not self.root.winfo_exists():
            return
        w = max(1, self.wave_canvas.winfo_width())
        h = max(1, self.wave_canvas.winfo_height())
        samples = self.engine.waveform()
        view = samples[-512:]
        x = np.linspace(0, w, len(view))
        y = h / 2 - np.clip(view * h * 1.8, -h / 2 + 2, h / 2 - 2)

        self.wave_canvas.delete("all")
        self.wave_canvas.create_line(0, h / 2, w, h / 2, fill="#1c2b38")
        self.wave_canvas.create_line(w / 2, 0, w / 2, h, fill="#13202b")
        if len(view) > 1:
            coords = np.column_stack((x, y)).ravel()
            self.wave_canvas.create_line(*coords, fill="#00f0ff", width=2)
        self.root.after(50, self._draw_waveform)

    def _draw_spectrum(self) -> None:
        if not self.root.winfo_exists():
            return
        w = max(1, self.spec_canvas.winfo_width())
        h = max(1, self.spec_canvas.winfo_height())
        spectrum = self.engine.spectrum()
        frequencies = np.fft.rfftfreq(2048, 1 / self.engine.sample_rate)
        bands = np.geomspace(35, self.engine.sample_rate / 2, 52)

        self.spec_canvas.delete("all")
        for i in range(len(bands) - 1):
            mask = (frequencies >= bands[i]) & (frequencies < bands[i + 1])
            level = float(np.max(spectrum[mask])) if np.any(mask) else -100
            normalized = float(np.clip((level + 85) / 85, 0, 1))
            x1 = i * w / 51 + 1
            x2 = (i + 0.82) * w / 51
            y = h * (1 - normalized)
            color = "#00f0ff" if normalized < 0.75 else ("#ffb703" if normalized < 0.9 else "#ff4d6d")
            self.spec_canvas.create_rectangle(x1, y, x2, h, fill=color, outline="")
        self.root.after(55, self._draw_spectrum)

    def _save_preset(self) -> None:
        path = filedialog.asksaveasfilename(title="Guardar preset Aurora", defaultextension=".aurora.json",
                                            filetypes=[("Preset Aurora", "*.aurora.json"), ("JSON", "*.json")])
        if not path:
            return
        data = {name: val.get() for name, val in self.controls.items()}
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError as e:
            messagebox.showerror("Aurora", f"No se pudo guardar el preset:\n{e}")

    def _load_preset(self) -> None:
        path = filedialog.askopenfilename(title="Abrir preset Aurora",
                                          filetypes=[("Preset Aurora", "*.aurora.json *.json")])
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            self._apply_preset(data)
        except (OSError, ValueError, json.JSONDecodeError) as e:
            messagebox.showerror("Aurora", f"Preset inválido:\n{e}")

    def _cycle_step(self, idx: int) -> None:
        notes = [None, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72]
        cur = self.sequence[idx]
        next_idx = 0 if cur not in notes else (notes.index(cur) + 1) % len(notes)
        self.sequence[idx] = notes[next_idx]
        self._refresh_steps()

    def _refresh_steps(self, active_step: Optional[int] = None) -> None:
        for idx, btn in enumerate(self.step_buttons):
            note = self.sequence[idx]
            txt = "—" if note is None else NOTE_NAMES.get(note, str(note))
            btn.configure(text=f"{idx + 1}\n{txt}")

    def _toggle_sequence(self) -> None:
        self.sequence_playing = not self.sequence_playing
        self.play_button.configure(text="■ DETENER" if self.sequence_playing else "▶ REPRODUCIR")
        if self.sequence_playing:
            self._play_step()
        elif self.sequence_job:
            self.root.after_cancel(self.sequence_job)
            self.sequence_job = None
            self.engine.all_notes_off()

    def _play_step(self) -> None:
        if not self.sequence_playing:
            return
        note = self.sequence[self.sequence_step]
        if note is not None:
            self.engine.note_on(note, 0.8)
            self.root.after(int(60000 / max(self.tempo.get(), 1) * 0.45), lambda n=note: self.engine.note_off(n))
        self._refresh_steps(self.sequence_step)
        self.sequence_step = (self.sequence_step + 1) % len(self.sequence)
        self.sequence_job = self.root.after(int(60000 / max(self.tempo.get(), 1) / 2), self._play_step)

    def _save_song(self) -> None:
        path = filedialog.asksaveasfilename(title="Guardar secuencia Aurora", defaultextension=".aurora-song.json",
                                            filetypes=[("Secuencia Aurora", "*.aurora-song.json"), ("JSON", "*.json")])
        if not path:
            return
        data = {
            "tempo": self.tempo.get(),
            "steps": self.sequence,
            "preset": {n: v.get() for n, v in self.controls.items()}
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError as e:
            messagebox.showerror("Aurora", f"No se pudo guardar la secuencia:\n{e}")

    def _load_song(self) -> None:
        path = filedialog.askopenfilename(title="Abrir secuencia Aurora",
                                          filetypes=[("Secuencia Aurora", "*.aurora-song.json *.json")])
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            steps = data["steps"]
            if not isinstance(steps, list) or len(steps) != 16:
                raise ValueError("La secuencia debe tener 16 pasos")
            self.sequence = [None if s is None else int(s) for s in steps]
            self.tempo.set(float(data.get("tempo", 112)))
            if "preset" in data:
                self._apply_preset(data["preset"])
            self._refresh_steps()
        except Exception as e:
            messagebox.showerror("Aurora", f"Secuencia inválida:\n{e}")

    def _key_to_midi(self, key: str) -> Optional[int]:
        """Calcula nota MIDI según tecla y octava activa."""
        base = 48 + self.octave_shift * 12

        # 1. Fila inferior (octava 1: C3 a B3)
        oct1_map = {
            "z": 0, "s": 1, "x": 2, "d": 3, "c": 4, "v": 5, "g": 6,
            "b": 7, "h": 8, "n": 9, "j": 10, "m": 11
        }
        if key in oct1_map:
            return base + oct1_map[key]

        # 2. Fila superior (octava 2: C4 a C5)
        oct2_map = {
            "q": 12, "2": 13, "w": 14, "3": 15, "e": 16, "r": 17, "5": 18,
            "t": 19, "6": 20, "y": 21, "7": 22, "u": 23, "i": 24
        }
        if key in oct2_map:
            return base + oct2_map[key]

        # 3. Mapeo clásico fila central (A-K = C4 a C5)
        classic_map = {
            "a": 60, "w": 61, "s": 62, "e": 63, "d": 64, "f": 65, "t": 66,
            "g": 67, "y": 68, "h": 69, "u": 70, "j": 71, "k": 72
        }
        if key in classic_map:
            return classic_map[key] + self.octave_shift * 12

        return None

    def _key_down(self, event) -> None:
        key = event.keysym.lower()
        if key == "escape":
            self.engine.all_notes_off()
            self.piano.pressed_notes.clear()
            self.piano.redraw()
            return

        note = self._key_to_midi(key)
        if note is not None and key not in self.pressed:
            self.pressed.add(key)
            self.engine.note_on(note)
            self.piano.note_press(note)

    def _key_up(self, event) -> None:
        key = event.keysym.lower()
        if key in self.pressed:
            self.pressed.remove(key)
            note = self._key_to_midi(key)
            if note is not None:
                self.engine.note_off(note)
                self.piano.note_release(note)

    def _audio(self, indata, outdata, frames, _time, _status) -> None:
        synth = self.engine.render(frames)
        if self.mic_enabled:
            vocal = self.vocal.process(indata[:, 0]) * self.vocal_gain
            synth[:, 0] += vocal
            synth[:, 1] += vocal
        outdata[:] = np.tanh(synth).astype(np.float32)

    def _audio_output_only(self, outdata, frames, _time, _status) -> None:
        outdata[:] = self.engine.render(frames)

    def _toggle_mic(self) -> None:
        self.mic_enabled = bool(self.mic_var.get())

    def _update_vocal_status(self) -> None:
        if self.mic_enabled:
            det = f"{self.vocal.detected_hz:.1f} Hz" if self.vocal.detected_hz else "buscando tono…"
            tgt = f" → {self.vocal.target_hz:.1f} Hz" if self.vocal.target_hz else ""
            self.vocal_status.configure(text=f"Micrófono activo: {det}{tgt}")
        else:
            self.vocal_status.configure(text="Micrófono desactivado")
        self.root.after(150, self._update_vocal_status)

    def _close(self) -> None:
        self.sequence_playing = False
        if self.sequence_job is not None:
            self.root.after_cancel(self.sequence_job)
        self.engine.all_notes_off()
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
        self.root.destroy()

    def run(self) -> None:
        try:
            self.stream = sd.Stream(samplerate=self.engine.sample_rate, blocksize=256, channels=(1, 2),
                                    dtype="float32", callback=self._audio)
        except sd.PortAudioError as err:
            self.mic_enabled = False
            self.mic_var.set(False)
            messagebox.showwarning("Aurora", f"Micrófono no disponible; solo salida de sintetizador.\n{err}")
            self.stream = sd.OutputStream(samplerate=self.engine.sample_rate, blocksize=256, channels=2,
                                          dtype="float32", callback=self._audio_output_only)
        self.stream.start()
        self.root.mainloop()


def main() -> None:
    SynthApp().run()
