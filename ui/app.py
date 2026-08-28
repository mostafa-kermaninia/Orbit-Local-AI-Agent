from __future__ import annotations

import math
import queue
import threading
import time
from tkinter import messagebox
from typing import Any

import customtkinter as ctk
import psutil

from assistant.config import AppConfig, save_config
from assistant.orchestrator import VoiceAssistant
from assistant.tool_registry import ToolSpec


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class OrbitUI(ctk.CTk):
    """Responsive HUD for ORBIT.

    This file intentionally contains UI-only changes.  The public callbacks and
    assistant integration are kept compatible with the existing project.
    """

    BG = "#02070B"
    HEADER = "#030B10"
    PANEL = "#061117"
    PANEL_ALT = "#081A22"
    PANEL_SOFT = "#0A2029"
    BORDER = "#123943"
    BORDER_BRIGHT = "#176072"

    CYAN = "#45EDFF"
    CYAN_2 = "#1AC6DC"
    BLUE = "#5283FF"
    GREEN = "#4FFFA8"
    AMBER = "#FFD166"
    PURPLE = "#C99CFF"
    RED = "#FF647A"
    TEXT = "#EAFBFF"
    MUTED = "#70949E"
    DIM = "#3E616A"

    def __init__(self, config: AppConfig, assistant: VoiceAssistant) -> None:
        super().__init__()
        self.config = config
        self.assistant = assistant

        self.title(f"{config.assistant_name} // LOCAL AGENT SYSTEM")
        self.geometry("1600x920")
        self.minsize(1320, 780)
        self.configure(fg_color=self.BG)

        self._events: queue.Queue[tuple[str, Any]] = queue.Queue()
        self._state = "BOOTING"
        self._phase = 0.0
        self._working = False
        self._continuous_running = False
        self._continuous_thread: threading.Thread | None = None
        self._tool_active = False
        self._last_net = psutil.net_io_counters()
        self._last_net_at = time.monotonic()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        self._build_header()
        self._build_body()
        self._build_console()

        self.bind("<F8>", lambda _e: self.interrupt())
        self.bind("<F2>", lambda _e: self.toggle_continuous())
        self.bind("<Configure>", self._on_window_resize)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.after(40, self._animate)
        self.after(80, self._drain_events)
        self.after(650, self._update_metrics)
        self.after(200, self._update_clock)
        self.after(250, self._refresh_wraplengths)

        self._log("SYSTEM", f"{config.assistant_name} interface initialized.")
        self._set_state("IDLE")

        if self.config.continuous_listening and self.config.auto_start_listening:
            self.after(700, self.start_continuous)

    # ------------------------------------------------------------------
    # Generic widgets / layout helpers
    # ------------------------------------------------------------------

    def _panel(self, parent, *, radius: int = 14, **kwargs):
        return ctk.CTkFrame(
            parent,
            fg_color=self.PANEL,
            corner_radius=radius,
            border_width=1,
            border_color=self.BORDER,
            **kwargs,
        )

    def _section_title(self, parent, text: str, row: int, *, pady=(12, 6)) -> None:
        ctk.CTkLabel(
            parent,
            text=text,
            font=("Consolas", 10, "bold"),
            text_color=self.MUTED,
        ).grid(row=row, column=0, padx=14, pady=pady, sticky="w")

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color=self.HEADER, corner_radius=0, height=86)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=0)
        header.grid_columnconfigure(1, weight=1)
        header.grid_columnconfigure(2, weight=0)

        # Brand block
        brand = ctk.CTkFrame(header, fg_color="transparent")
        brand.grid(row=0, column=0, padx=(24, 10), pady=12, sticky="w")

        emblem = ctk.CTkFrame(
            brand,
            width=38,
            height=38,
            fg_color="#08242D",
            corner_radius=10,
            border_width=1,
            border_color=self.CYAN_2,
        )
        emblem.pack(side="left", padx=(0, 12))
        emblem.pack_propagate(False)
        ctk.CTkLabel(
            emblem,
            text="◇",
            font=("Consolas", 25, "bold"),
            text_color=self.CYAN,
        ).pack(expand=True)

        labels = ctk.CTkFrame(brand, fg_color="transparent")
        labels.pack(side="left")
        ctk.CTkLabel(
            labels,
            text=self.config.assistant_name,
            font=("Segoe UI", 23, "bold"),
            text_color=self.TEXT,
        ).pack(anchor="w")
        ctk.CTkLabel(
            labels,
            text="LOCAL COGNITIVE OPERATIONS NODE",
            font=("Consolas", 9, "bold"),
            text_color=self.CYAN_2,
        ).pack(anchor="w", pady=(1, 0))

        # State block -- deliberately given its own pill so text never collides
        # with the mode label below it.
        center = ctk.CTkFrame(header, fg_color="transparent")
        center.grid(row=0, column=1, pady=11)

        self.status_pill = ctk.CTkFrame(
            center,
            fg_color="#092127",
            corner_radius=14,
            border_width=1,
            border_color="#16424C",
        )
        self.status_pill.pack(pady=(0, 5))
        self.header_state = ctk.CTkLabel(
            self.status_pill,
            text="● IDLE",
            font=("Consolas", 12, "bold"),
            text_color=self.GREEN,
        )
        self.header_state.pack(padx=18, pady=5)

        self.mode_label = ctk.CTkLabel(
            center,
            text="AUTONOMOUS AUDIO LOOP",
            font=("Consolas", 9),
            text_color=self.MUTED,
        )
        self.mode_label.pack()

        # Clock / privacy block
        right = ctk.CTkFrame(header, fg_color="transparent")
        right.grid(row=0, column=2, padx=(10, 24), pady=10, sticky="e")
        ctk.CTkLabel(
            right,
            text="LOCAL // PRIVATE",
            font=("Consolas", 9, "bold"),
            text_color=self.GREEN,
        ).pack(anchor="e")
        self.clock_label = ctk.CTkLabel(
            right,
            text="--:--:--",
            font=("Consolas", 17, "bold"),
            text_color=self.TEXT,
        )
        self.clock_label.pack(anchor="e", pady=(3, 0))

    def _build_body(self) -> None:
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, padx=16, pady=12, sticky="nsew")
        body.grid_columnconfigure(0, weight=0, minsize=255)
        body.grid_columnconfigure(1, weight=1, minsize=620)
        body.grid_columnconfigure(2, weight=0, minsize=350)
        body.grid_rowconfigure(0, weight=1)

        self._build_left(body)
        self._build_center(body)
        self._build_right(body)

    def _module_card(
        self,
        parent,
        title: str,
        value: str,
        row: int,
        accent: str | None = None,
    ) -> ctk.CTkLabel:
        card = ctk.CTkFrame(
            parent,
            fg_color=self.PANEL_ALT,
            corner_radius=9,
            border_width=1,
            border_color="#0F3039",
            height=62,
        )
        card.grid(row=row, column=0, padx=12, pady=4, sticky="ew")
        card.grid_propagate(False)
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text=title,
            font=("Consolas", 8, "bold"),
            text_color=self.MUTED,
        ).grid(row=0, column=0, padx=11, pady=(7, 0), sticky="w")

        label = ctk.CTkLabel(
            card,
            text=value,
            font=("Segoe UI", 11, "bold"),
            text_color=accent or self.TEXT,
            anchor="w",
        )
        label.grid(row=1, column=0, padx=11, pady=(1, 7), sticky="ew")
        return label

    # ------------------------------------------------------------------
    # Left rail
    # ------------------------------------------------------------------

    def _build_left(self, parent) -> None:
        left = self._panel(parent)
        left.grid(row=0, column=0, padx=(0, 7), sticky="nsew")
        left.grid_columnconfigure(0, weight=1)
        # The tool list is the elastic row.  This is the key fix that prevents
        # the CONTROL buttons from being pushed below the viewport.
        left.grid_rowconfigure(7, weight=1)

        ctk.CTkLabel(
            left,
            text="CORE MATRIX",
            font=("Consolas", 12, "bold"),
            text_color=self.CYAN,
        ).grid(row=0, column=0, padx=15, pady=(16, 8), sticky="w")

        self._module_card(left, "LANGUAGE MODEL", self.config.ollama_model.upper(), 1, self.CYAN)
        self._module_card(
            left,
            "SPEECH RECOGNITION",
            f"WHISPER / {self.config.stt_model.upper()} / {self.config.stt_language.upper()}",
            2,
        )
        self._module_card(
            left,
            "VOICE SYNTHESIS",
            "WINDOWS SAPI" if self.config.tts_enabled else "DISABLED",
            3,
        )
        self.listen_mode_value = self._module_card(
            left,
            "LISTENING MODE",
            "CONTINUOUS / MIC-GATED",
            4,
            self.GREEN,
        )
        self._module_card(
            left,
            "TOOL BUS",
            f"{len(self.assistant.registry.names())} MODULES ONLINE",
            5,
            self.PURPLE,
        )

        self._section_title(left, "AVAILABLE MODULES", 6, pady=(14, 5))

        tool_shell = ctk.CTkFrame(
            left,
            fg_color="#041016",
            corner_radius=8,
            border_width=1,
            border_color="#0D2A34",
        )
        tool_shell.grid(row=7, column=0, padx=12, pady=(0, 7), sticky="nsew")
        tool_shell.grid_columnconfigure(0, weight=1)
        tool_shell.grid_rowconfigure(0, weight=1)

        self.tools_box = ctk.CTkTextbox(
            tool_shell,
            fg_color="transparent",
            border_width=0,
            corner_radius=0,
            font=("Consolas", 9),
            text_color="#99BBC4",
            wrap="word",
            activate_scrollbars=True,
        )
        self.tools_box.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        tools_text = "\n".join(
            f"  ›  {name.replace('_', ' ').upper()}"
            for name in self.assistant.registry.names()
        )
        self.tools_box.insert("1.0", tools_text)
        self.tools_box.configure(state="disabled")

        self._section_title(left, "CONTROL", 8, pady=(5, 4))

        self.auto_button = ctk.CTkButton(
            left,
            text="F2  //  PAUSE AUTO LISTEN",
            command=self.toggle_continuous,
            height=36,
            corner_radius=8,
            fg_color="#0C5361",
            hover_color="#0F7486",
            font=("Consolas", 9, "bold"),
        )
        self.auto_button.grid(row=9, column=0, padx=12, pady=3, sticky="ew")

        ctk.CTkButton(
            left,
            text="F8  //  INTERRUPT",
            command=self.interrupt,
            height=36,
            corner_radius=8,
            fg_color="#522531",
            hover_color="#783244",
            font=("Consolas", 9, "bold"),
        ).grid(row=10, column=0, padx=12, pady=(3, 12), sticky="ew")

    # ------------------------------------------------------------------
    # Center stage
    # ------------------------------------------------------------------

    def _build_center(self, parent) -> None:
        center = self._panel(parent, radius=12)
        center.grid(row=0, column=1, padx=7, sticky="nsew")
        center.grid_columnconfigure(0, weight=1)
        center.grid_rowconfigure(1, weight=1)

        strip = ctk.CTkFrame(center, fg_color="#06151C", corner_radius=0, height=42)
        strip.grid(row=0, column=0, sticky="ew")
        strip.grid_propagate(False)
        strip.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            strip,
            text="VOICE // AGENTIC INTERFACE",
            font=("Consolas", 10, "bold"),
            text_color=self.CYAN,
        ).grid(row=0, column=0, padx=15, pady=10, sticky="w")

        self.signal_label = ctk.CTkLabel(
            strip,
            text="SIGNAL: STANDBY",
            font=("Consolas", 9),
            text_color=self.MUTED,
        )
        self.signal_label.grid(row=0, column=2, padx=15, sticky="e")

        self.canvas = ctk.CTkCanvas(center, bg=self.PANEL, highlightthickness=0)
        self.canvas.grid(row=1, column=0, padx=3, pady=(3, 0), sticky="nsew")

        # Pipeline strip: keeps the architecture visible without crowding the HUD.
        pipeline = ctk.CTkFrame(center, fg_color="#041015", corner_radius=8)
        pipeline.grid(row=2, column=0, padx=18, pady=(5, 6), sticky="ew")
        for i in range(9):
            pipeline.grid_columnconfigure(i, weight=1 if i % 2 == 0 else 0)

        self.pipeline_labels: dict[str, ctk.CTkLabel] = {}
        stages = [("MIC", 0), ("STT", 2), ("LLM", 4), ("TOOLS", 6), ("VOICE", 8)]
        for idx, (name, col) in enumerate(stages):
            label = ctk.CTkLabel(
                pipeline,
                text=name,
                font=("Consolas", 9, "bold"),
                text_color=self.DIM,
            )
            label.grid(row=0, column=col, padx=8, pady=6)
            self.pipeline_labels[name] = label
            if idx < len(stages) - 1:
                ctk.CTkLabel(
                    pipeline,
                    text="›",
                    font=("Consolas", 13, "bold"),
                    text_color="#1B5664",
                ).grid(row=0, column=col + 1, padx=2)

        # Fixed-height dual readout avoids layout jumps on long responses.
        readouts = ctk.CTkFrame(center, fg_color="transparent")
        readouts.grid(row=3, column=0, padx=18, pady=(0, 14), sticky="ew")
        readouts.grid_columnconfigure(0, weight=1)
        readouts.grid_columnconfigure(1, weight=1)

        self.input_card, self.input_text = self._make_readout_card(
            readouts,
            title="INPUT BUFFER",
            title_color=self.CYAN,
            column=0,
            padx=(0, 5),
        )
        self.output_card, self.output_text = self._make_readout_card(
            readouts,
            title=f"{self.config.assistant_name} // VOICE OUTPUT",
            title_color=self.BLUE,
            column=1,
            padx=(5, 0),
        )
        self._set_box_text(self.input_text, "Waiting for voice input…")
        self._set_box_text(self.output_text, "System ready.")

    def _make_readout_card(self, parent, *, title: str, title_color: str, column: int, padx) -> tuple[ctk.CTkFrame, ctk.CTkTextbox]:
        card = ctk.CTkFrame(
            parent,
            fg_color="#041015",
            corner_radius=9,
            border_width=1,
            border_color="#0D3440",
            height=98,
        )
        card.grid(row=0, column=column, padx=padx, sticky="ew")
        card.grid_propagate(False)
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            card,
            text=title,
            font=("Consolas", 8, "bold"),
            text_color=title_color,
        ).grid(row=0, column=0, padx=11, pady=(7, 1), sticky="w")

        box = ctk.CTkTextbox(
            card,
            fg_color="transparent",
            border_width=0,
            corner_radius=0,
            font=("Consolas", 10),
            text_color="#C4E6EC",
            wrap="word",
            activate_scrollbars=True,
            height=60,
        )
        box.grid(row=1, column=0, padx=6, pady=(0, 5), sticky="nsew")
        box.configure(state="disabled")
        return card, box

    # ------------------------------------------------------------------
    # Right rail
    # ------------------------------------------------------------------

    def _build_right(self, parent) -> None:
        right = self._panel(parent)
        right.grid(row=0, column=2, padx=(7, 0), sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(12, weight=1)

        ctk.CTkLabel(
            right,
            text="LIVE TELEMETRY",
            font=("Consolas", 12, "bold"),
            text_color=self.CYAN,
        ).grid(row=0, column=0, padx=15, pady=(16, 10), sticky="w")

        metrics = ctk.CTkFrame(
            right,
            fg_color=self.PANEL_ALT,
            corner_radius=9,
            border_width=1,
            border_color="#0F3039",
        )
        metrics.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")
        metrics.grid_columnconfigure(0, weight=1)

        self.cpu_value = ctk.CTkLabel(metrics, text="CPU  --.-%", font=("Consolas", 10, "bold"), text_color=self.TEXT)
        self.cpu_value.grid(row=0, column=0, padx=11, pady=(9, 0), sticky="w")
        self.cpu_bar = ctk.CTkProgressBar(metrics, height=5, progress_color=self.CYAN, fg_color="#10232B")
        self.cpu_bar.grid(row=1, column=0, padx=11, pady=(3, 8), sticky="ew")

        self.ram_value = ctk.CTkLabel(metrics, text="MEM  --.-%", font=("Consolas", 10, "bold"), text_color=self.TEXT)
        self.ram_value.grid(row=2, column=0, padx=11, sticky="w")
        self.ram_bar = ctk.CTkProgressBar(metrics, height=5, progress_color=self.PURPLE, fg_color="#10232B")
        self.ram_bar.grid(row=3, column=0, padx=11, pady=(3, 8), sticky="ew")

        self.net_value = ctk.CTkLabel(
            metrics,
            text="NET  ↓ 0 KB/s  ↑ 0 KB/s",
            font=("Consolas", 9),
            text_color=self.MUTED,
            anchor="w",
        )
        self.net_value.grid(row=4, column=0, padx=11, pady=(0, 9), sticky="ew")

        self._section_title(right, "AGENT BUS", 2, pady=(8, 4))

        bus = ctk.CTkFrame(
            right,
            fg_color="#041016",
            corner_radius=8,
            border_width=1,
            border_color="#0D2A34",
        )
        bus.grid(row=3, column=0, padx=12, pady=(0, 8), sticky="ew")
        bus.grid_columnconfigure(0, weight=1)

        self.agent_status = ctk.CTkLabel(
            bus,
            text="● TOOL CHANNEL READY",
            font=("Consolas", 9, "bold"),
            text_color=self.GREEN,
            anchor="w",
        )
        self.agent_status.grid(row=0, column=0, padx=11, pady=(8, 2), sticky="ew")

        self.last_tool_label = ctk.CTkLabel(
            bus,
            text="LAST TOOL // NONE",
            font=("Consolas", 8),
            text_color="#8AA9B1",
            anchor="w",
        )
        self.last_tool_label.grid(row=1, column=0, padx=11, pady=(0, 8), sticky="ew")

        self._section_title(right, "ACTIVITY STREAM", 4, pady=(7, 5))

        # Activity stream is the only elastic component in the right rail.
        log_shell = ctk.CTkFrame(
            right,
            fg_color="#020A0E",
            corner_radius=8,
            border_width=1,
            border_color="#0D2A34",
        )
        log_shell.grid(row=12, column=0, padx=12, pady=(0, 12), sticky="nsew")
        log_shell.grid_columnconfigure(0, weight=1)
        log_shell.grid_rowconfigure(0, weight=1)

        self.logbox = ctk.CTkTextbox(
            log_shell,
            fg_color="transparent",
            border_width=0,
            corner_radius=0,
            font=("Consolas", 9),
            text_color="#A8C9D0",
            wrap="word",
            activate_scrollbars=True,
        )
        self.logbox.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.logbox.configure(state="disabled")
        # Better paragraph spacing on the underlying Tk Text widget.
        try:
            self.logbox._textbox.configure(spacing1=1, spacing3=2)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Bottom command channel
    # ------------------------------------------------------------------

    def _build_console(self) -> None:
        console = ctk.CTkFrame(self, fg_color=self.HEADER, corner_radius=0, height=64)
        console.grid(row=2, column=0, sticky="ew")
        console.grid_propagate(False)
        console.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            console,
            text=">_",
            font=("Consolas", 18, "bold"),
            text_color=self.CYAN,
        ).grid(row=0, column=0, padx=(20, 9), pady=12)

        self.text_entry = ctk.CTkEntry(
            console,
            placeholder_text="manual command channel // type here",
            height=38,
            corner_radius=8,
            fg_color="#061218",
            border_color="#16404C",
            font=("Consolas", 10),
        )
        self.text_entry.grid(row=0, column=1, padx=2, pady=12, sticky="ew")
        self.text_entry.bind("<Return>", lambda _e: self.submit_text())

        ctk.CTkButton(
            console,
            text="EXECUTE",
            command=self.submit_text,
            width=116,
            height=38,
            corner_radius=8,
            fg_color="#0B6070",
            hover_color="#0E8094",
            font=("Consolas", 10, "bold"),
        ).grid(row=0, column=2, padx=(10, 20), pady=12)

    # ------------------------------------------------------------------
    # Responsive behaviour
    # ------------------------------------------------------------------

    def _on_window_resize(self, event) -> None:
        if event.widget is self:
            self.after_idle(self._refresh_wraplengths)

    def _refresh_wraplengths(self) -> None:
        # Textboxes handle wrapping themselves; this function intentionally only
        # keeps future label-based additions responsive.
        pass

    # ------------------------------------------------------------------
    # State / HUD animation
    # ------------------------------------------------------------------

    def _state_color(self) -> str:
        return {
            "IDLE": self.GREEN,
            "LISTENING": self.CYAN,
            "TRANSCRIBING": self.PURPLE,
            "THINKING": self.AMBER,
            "SPEAKING": self.BLUE,
            "INTERRUPTED": self.RED,
            "ERROR": self.RED,
            "BOOTING": self.MUTED,
        }.get(self._state, self.CYAN)

    def _state_dark(self) -> str:
        return {
            "IDLE": "#08241A",
            "LISTENING": "#07242A",
            "TRANSCRIBING": "#21152E",
            "THINKING": "#2B2410",
            "SPEAKING": "#101B38",
            "INTERRUPTED": "#32131A",
            "ERROR": "#32131A",
            "BOOTING": "#152126",
        }.get(self._state, "#07242A")

    def _update_pipeline(self) -> None:
        active = None
        if self._tool_active:
            active = "TOOLS"
        else:
            active = {
                "LISTENING": "MIC",
                "TRANSCRIBING": "STT",
                "THINKING": "LLM",
                "SPEAKING": "VOICE",
            }.get(self._state)

        color = self._state_color()
        for name, label in self.pipeline_labels.items():
            label.configure(text_color=color if name == active else self.DIM)

    def _draw_hud(self) -> None:
        """Draw the central ORBIT HUD.

        Design goals:
        - keep all typography inside a dedicated static safe-zone;
        - keep animated rings outside that safe-zone;
        - scale the core with the available canvas instead of a small fixed cap;
        - draw scanner/grid layers behind the core so animation never crosses text.
        """
        c = self.canvas
        w = max(1, c.winfo_width())
        h = max(1, c.winfo_height())

        # Leave extra room below for the waveform.
        cx = w / 2
        cy = h * 0.46
        c.delete("all")

        color = self._state_color()
        pulse = (math.sin(self._phase * 1.8) + 1.0) / 2.0

        # Background grid.
        spacing = 46 if w >= 760 else 38
        offset = int((self._phase * 4) % spacing)
        for x in range(-spacing + offset, int(w) + spacing, spacing):
            c.create_line(x, 0, x, h, fill="#07171E", width=1)
        for y in range(-spacing + offset, int(h) + spacing, spacing):
            c.create_line(0, y, w, y, fill="#07171E", width=1)

        # Scanner is painted first so it can never cross title/state text.
        scan_y = (h * 0.10) + (
            (math.sin(self._phase * 0.55) + 1) / 2
        ) * (h * 0.78)
        c.create_line(
            w * 0.10, scan_y, w * 0.90, scan_y,
            fill="#0A2D37", width=1,
        )

        # Corner targeting marks.
        margin = max(22, min(32, int(min(w, h) * 0.06)))
        arm = max(30, min(44, int(min(w, h) * 0.078)))
        for x1, y1, sx, sy in [
            (margin, margin, 1, 1),
            (w - margin, margin, -1, 1),
            (margin, h - margin, 1, -1),
            (w - margin, h - margin, -1, -1),
        ]:
            c.create_line(x1, y1, x1 + sx * arm, y1, fill="#15505F", width=2)
            c.create_line(x1, y1, x1, y1 + sy * arm, fill="#15505F", width=2)

        # Larger responsive core.
        min_dim = min(w, h)
        base = max(304.0, min(166.0, min_dim * 0.235))
        outer_r = base * 1.72

        # Horizon lines stop before reaching the HUD.
        left_end = max(w * 0.14, cx - outer_r - 24)
        right_start = min(w * 0.86, cx + outer_r + 24)
        c.create_line(w * 0.13, cy, left_end, cy, fill="#0D3540", width=1)
        c.create_line(right_start, cy, w * 0.87, cy, fill="#0D3540", width=1)

        # Animated segmented rings.
        rings = [
            (base * 1.72, 2.0, 54, 3),
            (base * 1.48, -2.7, 72, 2),
            (base * 1.26, 3.5, 40, 2),
        ]
        for radius, speed, extent, width in rings:
            ring_start = (self._phase * speed * 18) % 360
            for k in range(4):
                angle = ring_start + k * 90
                c.create_arc(
                    cx - radius, cy - radius,
                    cx + radius, cy + radius,
                    start=angle,
                    extent=extent,
                    style="arc",
                    outline=color if k % 2 == 0 else "#176173",
                    width=width,
                )

        # Engineering ticks.
        for degree in range(0, 360, 30):
            a = math.radians(degree)
            r1 = base * 1.56
            r2 = base * 1.62
            c.create_line(
                cx + math.cos(a) * r1,
                cy + math.sin(a) * r1,
                cx + math.cos(a) * r2,
                cy + math.sin(a) * r2,
                fill="#155465",
                width=1,
            )

        # Orbiting telemetry nodes.
        for i in range(8):
            angle = self._phase * (0.52 if i % 2 else -0.42) + i * math.tau / 8
            radius = base * (1.42 if i % 2 else 1.64)
            x = cx + math.cos(angle) * radius
            y = cy + math.sin(angle) * radius
            node_r = 3 if i % 3 else 5
            c.create_oval(
                x - node_r, y - node_r,
                x + node_r, y + node_r,
                fill=color, outline="",
            )

        def hex_points(radius: float, angle_shift: float = 0.0) -> list[float]:
            pts: list[float] = []
            for i in range(6):
                angle = angle_shift + math.radians(60 * i - 30)
                pts.extend([
                    cx + math.cos(angle) * radius,
                    cy + math.sin(angle) * radius,
                ])
            return pts

        # Opaque core layers create a protected typography zone.
        c.create_polygon(
            hex_points(base * 1.03, self._phase * 0.035),
            outline="#1B7182",
            fill="#04151B",
            width=2,
        )
        c.create_polygon(
            hex_points(base * 0.78, -self._phase * 0.055),
            outline=color,
            fill="#061D25",
            width=3,
        )
        c.create_oval(
            cx - base * 0.53, cy - base * 0.53,
            cx + base * 0.53, cy + base * 0.53,
            fill="#06171E",
            outline="#81EFF8",
            width=1,
        )

        glow = base * (0.405 + 0.025 * pulse)
        c.create_oval(
            cx - glow, cy - glow,
            cx + glow, cy + glow,
            fill="#082A34",
            outline=color,
            width=2,
        )

        halo = base * 0.31
        c.create_oval(
            cx - halo, cy - halo,
            cx + halo, cy + halo,
            outline="#2E7D8D",
            width=1,
        )

        # Only title + state live inside the animated core.
        title_size = 30 if base >= 135 else 26
        state_size = 12 if base >= 125 else 10

        c.create_text(
            cx,
            cy - base * 0.08,
            text=self.config.assistant_name,
            fill=self.TEXT,
            font=("Segoe UI", title_size, "bold"),
        )

        sep_y = cy + base * 0.05
        c.create_line(
            cx - base * 0.20, sep_y,
            cx + base * 0.20, sep_y,
            fill="#1B5663",
            width=1,
        )

        c.create_text(
            cx,
            cy + base * 0.22,
            text=self._state,
            fill=color,
            font=("Consolas", state_size, "bold"),
        )

        # Waveform sits completely outside the largest ring.
        active = self._state in {
            "LISTENING", "TRANSCRIBING", "THINKING", "SPEAKING"
        }
        energy = 30 if active else 8
        desired_bar_y = cy + outer_r + 20
        bar_y = min(h - 26, desired_bar_y)
        available = max(8.0, h - bar_y - 8)
        energy = min(energy, available * 1.7)

        for i in range(-17, 18):
            x = cx + i * 8
            value = abs(
                math.sin(self._phase * 2.2 + i * 0.61)
                * math.cos(self._phase * 0.7 + i * 0.19)
            )
            height = 4 + value * energy
            c.create_line(
                x,
                bar_y - height / 2,
                x,
                bar_y + height / 2,
                fill=color if abs(i) < 11 else "#176173",
                width=3,
            )

    def _animate(self) -> None:
        self._phase += 0.065
        self._draw_hud()
        self.after(40, self._animate)

    def _set_state(self, state: str) -> None:
        self._state = state
        color = self._state_color()
        self.header_state.configure(text=f"● {state}", text_color=color)
        self.signal_label.configure(text=f"SIGNAL: {state}", text_color=color)
        self.status_pill.configure(fg_color=self._state_dark(), border_color=color)
        self._update_pipeline()

    # ------------------------------------------------------------------
    # Readouts / activity stream
    # ------------------------------------------------------------------

    @staticmethod
    def _set_box_text(box: ctk.CTkTextbox, text: str) -> None:
        box.configure(state="normal")
        box.delete("1.0", "end")
        box.insert("1.0", str(text))
        box.see("1.0")
        box.configure(state="disabled")

    def _log(self, kind: str, text: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        clean = " ".join(str(text).split())
        self.logbox.configure(state="normal")
        self.logbox.insert("end", f"[{timestamp}]  {kind:<7}  {clean}\n")
        self.logbox.see("end")
        self.logbox.configure(state="disabled")

    def _event(self, kind: str, payload: Any = None) -> None:
        self._events.put((kind, payload))

    def _drain_events(self) -> None:
        while True:
            try:
                kind, payload = self._events.get_nowait()
            except queue.Empty:
                break

            if kind == "state":
                self._set_state(payload)

            elif kind == "transcript":
                self._set_box_text(self.input_text, payload)
                self._log("YOU", payload)

            elif kind == "answer":
                self._set_box_text(self.output_text, payload)
                self._log("VOICE", payload)

            elif kind == "tool":
                name, args = payload
                self._tool_active = True
                self._update_pipeline()
                self.agent_status.configure(
                    text="● TOOL EXECUTION ACTIVE",
                    text_color=self.AMBER,
                )
                self.last_tool_label.configure(text=f"LAST TOOL // {name.upper()}")
                self._log("TOOL", f"{name} {args}")

            elif kind == "tool_result":
                name, result = payload
                self._tool_active = False
                self._update_pipeline()
                ok = result.get("ok") is True
                self.agent_status.configure(
                    text="● TOOL EXECUTION SUCCESS" if ok else "● TOOL EXECUTION FAILED",
                    text_color=self.GREEN if ok else self.RED,
                )
                self._log("RESULT", f"{name}: {result}")

            elif kind == "system":
                self._log("SYSTEM", payload)

            elif kind == "error":
                self._set_state("ERROR")
                self._log("ERROR", str(payload))
                messagebox.showerror("Assistant error", str(payload))

            elif kind == "working":
                self._working = bool(payload)

        self.after(80, self._drain_events)

    # ------------------------------------------------------------------
    # Assistant integration (unchanged behaviour)
    # ------------------------------------------------------------------

    def _confirm_tool(self, spec: ToolSpec, args: dict[str, Any]) -> bool:
        event = threading.Event()
        result = {"ok": False}

        def ask() -> None:
            pretty = "\n".join(f"{k}: {v}" for k, v in args.items())
            result["ok"] = messagebox.askyesno(
                "Confirm external action",
                f"Allow tool '{spec.name}' to run?\n\n{pretty}",
            )
            event.set()

        self.after(0, ask)
        event.wait()
        return bool(result["ok"])

    def _callbacks(self) -> dict[str, Any]:
        return {
            "confirm": self._confirm_tool,
            "on_state": lambda s: self._event("state", s),
            "on_transcript": lambda t: self._event("transcript", t),
            "on_answer": lambda a: self._event("answer", a),
            "on_tool": lambda n, a: self._event("tool", (n, a)),
            "on_tool_result": lambda n, r: self._event("tool_result", (n, r)),
            "on_system": lambda s: self._event("system", s),
        }

    def start_continuous(self) -> None:
        if self._continuous_running:
            return

        self._continuous_running = True
        self.listen_mode_value.configure(
            text="CONTINUOUS / MIC-GATED",
            text_color=self.GREEN,
        )
        self.auto_button.configure(text="F2  //  PAUSE AUTO LISTEN")
        self.mode_label.configure(
            text="AUTONOMOUS AUDIO LOOP // ONLINE",
            text_color=self.GREEN,
        )
        self._event(
            "system",
            "Continuous listening started. Microphone is gated while assistant speech is playing.",
        )

        def worker() -> None:
            try:
                self.assistant.run_continuous(**self._callbacks())
            except Exception as exc:
                self._event("error", exc)
            finally:
                self._continuous_running = False
                self._event("system", "Continuous listening stopped.")

        self._continuous_thread = threading.Thread(
            target=worker,
            name="continuous-voice-loop",
            daemon=True,
        )
        self._continuous_thread.start()

    def stop_continuous(self) -> None:
        if not self._continuous_running:
            return

        self.assistant.stop_continuous()
        self._continuous_running = False
        self.listen_mode_value.configure(text="MANUAL", text_color=self.AMBER)
        self.auto_button.configure(text="F2  //  START AUTO LISTEN")
        self.mode_label.configure(
            text="AUTONOMOUS AUDIO LOOP // PAUSED",
            text_color=self.AMBER,
        )
        self._set_state("IDLE")

    def toggle_continuous(self) -> None:
        if self._continuous_running:
            self.stop_continuous()
        else:
            self.start_continuous()

    def submit_text(self) -> None:
        text = self.text_entry.get().strip()
        if not text or self._working:
            return

        self.text_entry.delete(0, "end")
        was_continuous = self._continuous_running
        if was_continuous:
            self.stop_continuous()

        self._event("transcript", text)
        self._event("working", True)

        def worker() -> None:
            try:
                answer = self.assistant.process_text(
                    text,
                    confirm=self._confirm_tool,
                    on_state=lambda s: self._event("state", s),
                    on_tool=lambda n, a: self._event("tool", (n, a)),
                    on_tool_result=lambda n, r: self._event("tool_result", (n, r)),
                )
                self._event("answer", answer)
            except Exception as exc:
                self._event("error", exc)
            finally:
                self._event("working", False)
                if was_continuous:
                    self.after(250, self.start_continuous)

        threading.Thread(target=worker, name="text-cycle", daemon=True).start()

    def interrupt(self) -> None:
        self.assistant.cancel_audio()
        self._log("SYSTEM", "Interrupt requested. Audio pipeline reset.")
        self._set_state("INTERRUPTED")
        self.after(
            350,
            lambda: self._set_state(
                "LISTENING" if self._continuous_running else "IDLE"
            ),
        )

    def _update_metrics(self) -> None:
        try:
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().percent
            self.cpu_bar.set(cpu / 100)
            self.ram_bar.set(ram / 100)
            self.cpu_value.configure(text=f"CPU  {cpu:05.1f}%")
            self.ram_value.configure(text=f"MEM  {ram:05.1f}%")

            now = time.monotonic()
            net = psutil.net_io_counters()
            dt = max(0.2, now - self._last_net_at)
            down = max(0, net.bytes_recv - self._last_net.bytes_recv) / dt / 1024
            up = max(0, net.bytes_sent - self._last_net.bytes_sent) / dt / 1024
            self.net_value.configure(
                text=f"NET  ↓ {down:,.0f} KB/s  ↑ {up:,.0f} KB/s"
            )
            self._last_net, self._last_net_at = net, now
        finally:
            self.after(900, self._update_metrics)

    def _update_clock(self) -> None:
        self.clock_label.configure(text=time.strftime("%H:%M:%S"))
        self.after(500, self._update_clock)

    def _on_close(self) -> None:
        try:
            save_config(self.config)
            self.assistant.stop_continuous()
        finally:
            self.destroy()
