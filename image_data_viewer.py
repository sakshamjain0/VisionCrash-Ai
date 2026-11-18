import os
import json
import datetime
import tkinter as tk
from tkinter import ttk
from PIL import Image
from PIL import ImageTk
from PIL.ImageTk import PhotoImage
import ctypes

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BG_PRIMARY = "#0c1016"
BG_SURFACE = "#131a23"
BG_PANEL = "#1b2430"
BG_STAGE = "#0f151d"
ACCENT_RED = "#d7263d"
ACCENT_RED_HOVER = "#ef3b54"
ACCENT_TEAL = "#24b3a8"
TEXT_PRIMARY = "#f5f7fa"
TEXT_MUTED = "#9ba8b9"
TEXT_DARK = "#0a0f15"

CANVAS_WIDTH = 980
CANVAS_HEIGHT = 560

HISTORY_FILE = os.path.join(_BASE_DIR, "outputs", "accident_history.jsonl")
FRAME_DIR = os.path.join(_BASE_DIR, "outputs", "frame_img")
LABEL_DIR = os.path.join(_BASE_DIR, "outputs", "inside_label_img")


class ImageViewer:
    def __init__(self, root):
        self.root = root
        self.root.state("zoomed")
        self.root.title("VisionCrash AI - Records")
        self.root.config(bg=BG_PRIMARY)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.title_bar_icon = PhotoImage(file=os.path.join(_BASE_DIR, "resources/icon/vehicle_crash_black.png"))
        self.root.iconphoto(False, self.title_bar_icon)

        self.icon_white = self._load_icon("resources/icon/vehicle_crash_white.png", (60, 60), BG_PANEL)
        self.icon_black = self._load_icon("resources/icon/vehicle_crash_black._32.png", (60, 60), BG_SURFACE)

        self.current_canvas_image = None
        self.history_records = []
        self.history_row_map = {}
        self.selected_record = None
        self.image_paths = []
        self.current_image_index = -1

        self._build_layout()
        self.refresh_current_view()

    def _load_icon(self, relative_path, size, fallback_color):
        icon_path = os.path.join(_BASE_DIR, relative_path)
        try:
            image = Image.open(icon_path).resize(size, Image.Resampling.LANCZOS)
        except Exception:
            image = Image.new("RGB", size, fallback_color)
        return ImageTk.PhotoImage(image)

    def _build_layout(self):
        self.sidebar = tk.Frame(self.root, bg=BG_PANEL, width=290)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.sidebar_border = tk.Frame(self.sidebar, bg=ACCENT_RED, width=3)
        self.sidebar_border.pack(side="right", fill="y")

        self.sidebar_icon_label = tk.Label(self.sidebar, image=self.icon_white, bg=BG_PANEL)
        self.sidebar_icon_label.pack(side="top", pady=(20, 8))

        self.sidebar_title = tk.Label(
            self.sidebar,
            text="VISIONCRASH AI",
            bg=BG_PANEL,
            fg=TEXT_PRIMARY,
            font=("Bahnschrift SemiBold", 16),
        )
        self.sidebar_title.pack(side="top")

        self.sidebar_subtitle = tk.Label(
            self.sidebar,
            text="Records Console",
            bg=BG_PANEL,
            fg=TEXT_MUTED,
            font=("Bahnschrift", 11),
        )
        self.sidebar_subtitle.pack(side="top", pady=(0, 26))

        self.open_detection_button = tk.Button(
            self.sidebar,
            text="Crash Detection",
            command=self.open_vcd,
            width=24,
            height=2,
            fg=TEXT_PRIMARY,
            bg=BG_PANEL,
            activebackground=ACCENT_RED,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("Bahnschrift", 12),
        )
        self.open_detection_button.pack(padx=18, pady=6)

        self.records_button = tk.Button(
            self.sidebar,
            text="Records",
            width=24,
            height=2,
            state="disabled",
            disabledforeground=TEXT_PRIMARY,
            bg=ACCENT_RED,
            activebackground=ACCENT_RED,
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("Bahnschrift", 12),
        )
        self.records_button.pack(padx=18, pady=6)

        self._add_sidebar_hover(self.open_detection_button)

        self.sidebar_tip = tk.Label(
            self.sidebar,
            text="Tip: Use Accident History for latest incidents, then open Frame or Label image sets.",
            wraplength=230,
            justify="left",
            bg=BG_PANEL,
            fg=TEXT_MUTED,
            font=("Bahnschrift", 10),
        )
        self.sidebar_tip.pack(side="bottom", padx=16, pady=20)

        self.content = tk.Frame(self.root, bg=BG_PRIMARY)
        self.content.pack(side="right", fill="both", expand=True)

        self.header_card = tk.Frame(self.content, bg=BG_SURFACE, height=120)
        self.header_card.pack(side="top", fill="x", padx=24, pady=(22, 14))
        self.header_card.pack_propagate(False)

        header_left = tk.Frame(self.header_card, bg=BG_SURFACE)
        header_left.pack(side="left", fill="both", expand=True, padx=20)

        self.title_label = tk.Label(
            header_left,
            text="Crash Records Viewer",
            bg=BG_SURFACE,
            fg=TEXT_PRIMARY,
            image=self.icon_black,
            compound="left",
            font=("Bahnschrift SemiBold", 26),
        )
        self.title_label.pack(side="top", anchor="w", pady=(12, 4))

        self.subtitle_label = tk.Label(
            header_left,
            text="Structured records with status tracking and instant preview",
            bg=BG_SURFACE,
            fg=TEXT_MUTED,
            font=("Bahnschrift", 12),
        )
        self.subtitle_label.pack(side="top", anchor="w")

        metrics_box = tk.Frame(self.header_card, bg=BG_SURFACE)
        metrics_box.pack(side="right", padx=20, pady=14)

        self.total_count_label = self._build_metric(metrics_box, "TOTAL", "0")
        self.email_sent_label = self._build_metric(metrics_box, "EMAIL OK", "0")
        self.email_failed_label = self._build_metric(metrics_box, "EMAIL FAIL", "0")

        control_bar = tk.Frame(self.content, bg=BG_SURFACE, height=98)
        control_bar.pack(side="top", fill="x", padx=24, pady=(0, 14))
        control_bar.pack_propagate(False)

        tk.Label(
            control_bar,
            text="Record Source:",
            fg=TEXT_MUTED,
            bg=BG_SURFACE,
            font=("Bahnschrift", 12),
        ).pack(side="left", padx=(20, 10), pady=20)

        self._configure_ttk_styles()

        self.combo_box = ttk.Combobox(
            control_bar,
            values=["Accident History", "Frame Images", "Inside Label Images"],
            state="readonly",
            width=22,
            font=("Bahnschrift", 11),
        )
        self.combo_box.set("Accident History")
        self.combo_box.pack(side="left", pady=20)
        self.combo_box.bind("<<ComboboxSelected>>", self.handle_combobox)

        tk.Label(
            control_bar,
            text="Filter:",
            fg=TEXT_MUTED,
            bg=BG_SURFACE,
            font=("Bahnschrift", 12),
        ).pack(side="left", padx=(16, 8))

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            control_bar,
            textvariable=self.search_var,
            width=26,
            bg=BG_PANEL,
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            relief="flat",
            font=("Bahnschrift", 11),
        )
        self.search_entry.pack(side="left", pady=20)
        self.search_entry.bind("<KeyRelease>", self.on_search)

        self.refresh_button = tk.Button(
            control_bar,
            text="Refresh",
            command=self.refresh_current_view,
            width=12,
            height=1,
            fg=TEXT_DARK,
            bg=ACCENT_TEAL,
            activebackground="#30c7bc",
            activeforeground=TEXT_DARK,
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("Bahnschrift SemiBold", 11),
        )
        self.refresh_button.pack(side="right", padx=20)

        body = tk.Frame(self.content, bg=BG_PRIMARY)
        body.pack(side="top", fill="both", expand=True, padx=24, pady=(0, 20))

        preview_panel = tk.Frame(body, bg=BG_SURFACE)
        preview_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tk.Label(
            preview_panel,
            text="Preview Stage",
            bg=BG_SURFACE,
            fg=TEXT_PRIMARY,
            font=("Bahnschrift SemiBold", 14),
        ).pack(side="top", anchor="w", padx=16, pady=(14, 8))

        self.preview_canvas = tk.Canvas(
            preview_panel,
            width=CANVAS_WIDTH,
            height=CANVAS_HEIGHT,
            bg=BG_STAGE,
            highlightthickness=0,
        )
        self.preview_canvas.pack(side="top", padx=16, pady=(0, 10))

        navigation_bar = tk.Frame(preview_panel, bg=BG_SURFACE)
        navigation_bar.pack(side="top", fill="x", padx=16, pady=(0, 14))

        self.back_button = tk.Button(
            navigation_bar,
            text="Previous",
            command=lambda: self.show_image_offset(-1),
            width=12,
            fg=TEXT_PRIMARY,
            bg=ACCENT_RED,
            activebackground=ACCENT_RED_HOVER,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("Bahnschrift", 11),
        )
        self.back_button.pack(side="left")

        self.next_button = tk.Button(
            navigation_bar,
            text="Next",
            command=lambda: self.show_image_offset(1),
            width=12,
            fg=TEXT_PRIMARY,
            bg=ACCENT_RED,
            activebackground=ACCENT_RED_HOVER,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("Bahnschrift", 11),
        )
        self.next_button.pack(side="left", padx=(8, 0))

        self.index_label = tk.Label(
            navigation_bar,
            text="0 / 0",
            bg=BG_SURFACE,
            fg=TEXT_MUTED,
            font=("Bahnschrift", 11),
        )
        self.index_label.pack(side="left", padx=12)

        right_panel = tk.Frame(body, bg=BG_SURFACE, width=560)
        right_panel.pack(side="right", fill="y")
        right_panel.pack_propagate(False)

        self.records_title = tk.Label(
            right_panel,
            text="Accident History",
            bg=BG_SURFACE,
            fg=TEXT_PRIMARY,
            font=("Bahnschrift SemiBold", 14),
        )
        self.records_title.pack(side="top", anchor="w", padx=14, pady=(14, 8))

        self.history_frame = tk.Frame(right_panel, bg=BG_SURFACE)
        self.history_frame.pack(side="top", fill="both", expand=True, padx=12)

        self.history_tree = ttk.Treeview(
            self.history_frame,
            columns=("timestamp", "source", "email", "sms"),
            show="headings",
            style="Records.Treeview",
            selectmode="browse",
        )
        self.history_tree.heading("timestamp", text="Timestamp")
        self.history_tree.heading("source", text="Source")
        self.history_tree.heading("email", text="Email")
        self.history_tree.heading("sms", text="SMS")
        self.history_tree.column("timestamp", width=145, anchor="w")
        self.history_tree.column("source", width=140, anchor="w")
        self.history_tree.column("email", width=125, anchor="w")
        self.history_tree.column("sms", width=125, anchor="w")
        self.history_tree.pack(side="left", fill="both", expand=True)

        history_scrollbar = ttk.Scrollbar(self.history_frame, orient="vertical", command=self.history_tree.yview)
        history_scrollbar.pack(side="right", fill="y")
        self.history_tree.configure(yscrollcommand=history_scrollbar.set)
        self.history_tree.bind("<<TreeviewSelect>>", self.on_history_select)

        self.history_tree.tag_configure("ok", background="#14362f", foreground=TEXT_PRIMARY)
        self.history_tree.tag_configure("warn", background="#3b2f12", foreground=TEXT_PRIMARY)
        self.history_tree.tag_configure("fail", background="#4a1c24", foreground=TEXT_PRIMARY)

        self.images_frame = tk.Frame(right_panel, bg=BG_SURFACE)

        self.images_listbox = tk.Listbox(
            self.images_frame,
            bg=BG_PANEL,
            fg=TEXT_PRIMARY,
            selectbackground=ACCENT_RED,
            selectforeground=TEXT_PRIMARY,
            highlightthickness=0,
            relief="flat",
            font=("Bahnschrift", 10),
        )
        self.images_listbox.pack(side="left", fill="both", expand=True)
        self.images_listbox.bind("<<ListboxSelect>>", self.on_image_select)

        images_scrollbar = tk.Scrollbar(self.images_frame, orient="vertical", command=self.images_listbox.yview)
        images_scrollbar.pack(side="right", fill="y")
        self.images_listbox.configure(yscrollcommand=images_scrollbar.set)

        actions_bar = tk.Frame(right_panel, bg=BG_SURFACE)
        actions_bar.pack(side="top", fill="x", padx=12, pady=(10, 8))

        self.show_frame_button = tk.Button(
            actions_bar,
            text="View Frame",
            command=lambda: self.show_selected_record_image("frame"),
            width=14,
            fg=TEXT_PRIMARY,
            bg=ACCENT_RED,
            activebackground=ACCENT_RED_HOVER,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("Bahnschrift", 10),
        )
        self.show_frame_button.pack(side="left")

        self.show_label_button = tk.Button(
            actions_bar,
            text="View Label",
            command=lambda: self.show_selected_record_image("label"),
            width=14,
            fg=TEXT_PRIMARY,
            bg=ACCENT_RED,
            activebackground=ACCENT_RED_HOVER,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("Bahnschrift", 10),
        )
        self.show_label_button.pack(side="left", padx=(8, 0))

        self.details_text = tk.Text(
            right_panel,
            height=10,
            bg=BG_PANEL,
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            relief="flat",
            padx=10,
            pady=10,
            wrap="word",
            font=("Consolas", 10),
        )
        self.details_text.pack(side="top", fill="x", padx=12, pady=(0, 12))
        self.details_text.configure(state="disabled")

        self.status_label = tk.Label(
            self.content,
            text="",
            bg=BG_PRIMARY,
            fg=TEXT_PRIMARY,
            font=("Bahnschrift", 11),
        )
        self.status_label.pack(side="bottom", anchor="w", padx=28, pady=(0, 12))

        self._set_record_buttons_state(enabled=False)
        self._render_placeholder("Choose a record to preview")

    def _build_metric(self, parent, label_text, value_text):
        card = tk.Frame(parent, bg=BG_PANEL, padx=14, pady=8)
        card.pack(side="left", padx=5)
        tk.Label(
            card,
            text=label_text,
            bg=BG_PANEL,
            fg=TEXT_MUTED,
            font=("Bahnschrift", 9),
        ).pack(anchor="w")
        value_label = tk.Label(
            card,
            text=value_text,
            bg=BG_PANEL,
            fg=TEXT_PRIMARY,
            font=("Bahnschrift SemiBold", 14),
        )
        value_label.pack(anchor="w")
        return value_label

    def _configure_ttk_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "TCombobox",
            fieldbackground=BG_PANEL,
            background=BG_PANEL,
            foreground=TEXT_PRIMARY,
            selectbackground=BG_PANEL,
            selectforeground=TEXT_PRIMARY,
            arrowcolor=TEXT_PRIMARY,
            borderwidth=0,
            relief="flat",
        )
        style.configure(
            "Records.Treeview",
            background=BG_PANEL,
            foreground=TEXT_PRIMARY,
            fieldbackground=BG_PANEL,
            borderwidth=0,
            rowheight=26,
            font=("Bahnschrift", 10),
        )
        style.configure(
            "Records.Treeview.Heading",
            background="#263342",
            foreground=TEXT_PRIMARY,
            relief="flat",
            font=("Bahnschrift SemiBold", 10),
        )
        style.map(
            "Records.Treeview",
            background=[("selected", ACCENT_RED)],
            foreground=[("selected", TEXT_PRIMARY)],
        )

    def _add_sidebar_hover(self, button):
        button.bind("<Enter>", lambda _event: button.config(bg="#223041"))
        button.bind("<Leave>", lambda _event: button.config(bg=BG_PANEL))

    def _set_status(self, text):
        self.status_label.config(text=text)

    def _render_placeholder(self, message):
        self.preview_canvas.delete("all")
        self.preview_canvas.create_rectangle(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT, fill=BG_STAGE, outline=BG_STAGE)
        self.preview_canvas.create_text(
            CANVAS_WIDTH // 2,
            CANVAS_HEIGHT // 2,
            text=message,
            fill=TEXT_MUTED,
            font=("Bahnschrift", 16),
        )
        self.current_canvas_image = None

    def _show_image(self, image_path):
        if not image_path or not os.path.exists(image_path):
            self._render_placeholder("Image not found on disk")
            return False
        try:
            image = Image.open(image_path).convert("RGB")
        except Exception:
            self._render_placeholder("Unable to read selected image")
            return False

        image.thumbnail((CANVAS_WIDTH, CANVAS_HEIGHT), Image.Resampling.LANCZOS)
        background = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), BG_STAGE)
        offset_x = (CANVAS_WIDTH - image.width) // 2
        offset_y = (CANVAS_HEIGHT - image.height) // 2
        background.paste(image, (offset_x, offset_y))

        preview = ImageTk.PhotoImage(background)
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(0, 0, anchor=tk.NW, image=preview)
        self.current_canvas_image = preview
        return True

    def _set_record_buttons_state(self, enabled):
        state = "normal" if enabled else "disabled"
        self.show_frame_button.config(state=state)
        self.show_label_button.config(state=state)

    def _update_details(self, text):
        self.details_text.configure(state="normal")
        self.details_text.delete("1.0", tk.END)
        self.details_text.insert("1.0", text)
        self.details_text.configure(state="disabled")

    def _compact_status(self, status_text):
        status_text = str(status_text or "Unknown")
        if len(status_text) <= 36:
            return status_text
        return status_text[:33] + "..."

    def _update_metrics(self, records):
        total = len(records)
        email_sent = sum(1 for r in records if str(r.get("email_status", "")).lower().startswith("email sent"))
        email_failed = sum(1 for r in records if "failed" in str(r.get("email_status", "")).lower())
        self.total_count_label.config(text=str(total))
        self.email_sent_label.config(text=str(email_sent))
        self.email_failed_label.config(text=str(email_failed))

    def _record_row_tag(self, record):
        email_status = str(record.get("email_status", "")).lower()
        sms_status = str(record.get("sms_status", "")).lower()
        if "failed" in email_status or "failed" in sms_status:
            return "fail"
        if email_status.startswith("email sent"):
            return "ok"
        return "warn"

    def _format_source(self, source_value):
        source_text = str(source_value or "Unknown")
        if source_text == "0":
            return "Live-Camera"
        if "/" in source_text or "\\" in source_text:
            return os.path.basename(source_text)
        return source_text

    def _set_history_mode(self):
        self.images_frame.pack_forget()
        self.history_frame.pack(side="top", fill="both", expand=True, padx=12)
        self.records_title.config(text="Accident History")
        self.back_button.config(state="disabled")
        self.next_button.config(state="disabled")
        self.index_label.config(text="History mode")

    def _set_images_mode(self, title_text):
        self.history_frame.pack_forget()
        self.images_frame.pack(side="top", fill="both", expand=True, padx=12)
        self.records_title.config(text=title_text)
        self.back_button.config(state="normal")
        self.next_button.config(state="normal")
        self._set_record_buttons_state(enabled=False)

    def handle_combobox(self, _event):
        self.refresh_current_view()

    def on_search(self, _event):
        self.refresh_current_view()

    def refresh_current_view(self):
        mode = self.combo_box.get()
        search_text = self.search_var.get().strip().lower()

        if mode == "Accident History":
            self._set_history_mode()
            self.load_history_records(search_text)
            return

        if mode == "Frame Images":
            self._set_images_mode("Frame Images")
            self.load_image_directory(FRAME_DIR, search_text)
            return

        self._set_images_mode("Inside Label Images")
        self.load_image_directory(LABEL_DIR, search_text)

    def load_history_records(self, filter_text=""):
        self.history_tree.delete(*self.history_tree.get_children())
        self.history_row_map = {}
        self.history_records = []
        self.selected_record = None
        self._set_record_buttons_state(enabled=False)

        if not os.path.exists(HISTORY_FILE):
            self._update_metrics([])
            self._update_details("No accident history file found yet.")
            self._render_placeholder("No history records available")
            self._set_status("No accident history found")
            return

        with open(HISTORY_FILE, "r", encoding="utf-8") as history_file:
            for raw_line in history_file:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    self.history_records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        self.history_records.reverse()
        self._update_metrics(self.history_records)

        visible_count = 0
        for record in self.history_records:
            ts = str(record.get("timestamp", "Unknown Time"))
            src = self._format_source(record.get("source", "Unknown Source"))
            email_status = str(record.get("email_status", "Pending"))
            sms_status = str(record.get("sms_status", "Pending"))

            searchable = f"{ts} {src} {email_status} {sms_status}".lower()
            if filter_text and filter_text not in searchable:
                continue

            row_id = self.history_tree.insert(
                "",
                "end",
                values=(
                    ts,
                    src,
                    self._compact_status(email_status),
                    self._compact_status(sms_status),
                ),
                tags=(self._record_row_tag(record),),
            )
            self.history_row_map[row_id] = record
            visible_count += 1

        if visible_count == 0:
            self._update_details("No records match your current filter.")
            self._render_placeholder("No matching records")
            self._set_status("Filter returned 0 records")
            return

        first_row = self.history_tree.get_children()[0]
        self.history_tree.selection_set(first_row)
        self.history_tree.focus(first_row)
        self.on_history_select(None)
        self._set_status(f"History loaded: {visible_count} records")

    def on_history_select(self, _event):
        selection = self.history_tree.selection()
        if not selection:
            return

        row_id = selection[0]
        record = self.history_row_map.get(row_id)
        if not record:
            return

        self.selected_record = record
        self._set_record_buttons_state(enabled=True)
        self.show_selected_record_image("frame")

        details = [
            "Selected Record",
            f"Timestamp: {record.get('timestamp', 'Unknown')}",
            f"Source: {record.get('source', 'Unknown')}",
            f"Email Status: {record.get('email_status', 'Unknown')}",
            f"SMS Status: {record.get('sms_status', 'Unknown')}",
            "",
            "Paths",
            f"Frame: {record.get('frame_image', 'Not available')}",
            f"Inside Label: {record.get('inside_label_image', 'Not available')}",
            f"Video: {record.get('detection_video', 'Not available')}",
        ]
        self._update_details("\n".join(details))

    def show_selected_record_image(self, image_type):
        if not self.selected_record:
            self._set_status("Select a record first")
            return

        key = "inside_label_image" if image_type == "label" else "frame_image"
        image_path = self.selected_record.get(key, "")
        if self._show_image(image_path):
            timestamp = self.selected_record.get("timestamp", "Unknown")
            view_name = "Inside Label" if image_type == "label" else "Frame"
            self._set_status(f"Showing {view_name} image for {timestamp}")
        else:
            self._set_status(f"Selected {image_type} image is missing")

    def load_image_directory(self, directory_path, filter_text=""):
        self.images_listbox.delete(0, tk.END)
        self.image_paths = []
        self.current_image_index = -1
        self._update_details("Image mode selected. Pick any file from the list to preview.")

        if not os.path.exists(directory_path):
            self._render_placeholder("Folder does not exist")
            self.index_label.config(text="0 / 0")
            self._set_status(f"Missing folder: {directory_path}")
            return

        entries = []
        for name in os.listdir(directory_path):
            if not name.lower().endswith((".png", ".jpg", ".jpeg")):
                continue
            if filter_text and filter_text not in name.lower():
                continue

            full_path = os.path.join(directory_path, name)
            if not os.path.isfile(full_path):
                continue
            entries.append((full_path, os.path.getmtime(full_path)))

        entries.sort(key=lambda item: item[1], reverse=True)

        for idx, (image_path, modified_ts) in enumerate(entries):
            self.image_paths.append(image_path)
            modified_text = self._format_mtime(modified_ts)
            display_name = os.path.basename(image_path)
            self.images_listbox.insert(tk.END, f"{idx + 1:03d}  {display_name}  ({modified_text})")

        if not self.image_paths:
            self._render_placeholder("No images found for this view")
            self.index_label.config(text="0 / 0")
            self._set_status("No images available")
            return

        self.images_listbox.selection_set(0)
        self.images_listbox.activate(0)
        self.on_image_select(None)
        self._set_status(f"Loaded {len(self.image_paths)} images")

    def _format_mtime(self, timestamp):
        try:
            return datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
        except Exception:
            return "Unknown"

    def on_image_select(self, _event):
        selected = self.images_listbox.curselection()
        if not selected:
            return

        index = selected[0]
        if index < 0 or index >= len(self.image_paths):
            return

        self.current_image_index = index
        image_path = self.image_paths[index]
        self._show_image(image_path)
        self.index_label.config(text=f"{index + 1} / {len(self.image_paths)}")
        self._set_status(f"Image: {os.path.basename(image_path)}")

    def show_image_offset(self, offset):
        if not self.image_paths:
            return

        next_index = self.current_image_index + offset
        next_index = max(0, min(next_index, len(self.image_paths) - 1))
        self.images_listbox.selection_clear(0, tk.END)
        self.images_listbox.selection_set(next_index)
        self.images_listbox.activate(next_index)
        self.images_listbox.see(next_index)
        self.on_image_select(None)

    def open_vcd(self):
        self.root.withdraw()
        vcd_window = tk.Toplevel(self.root)
        vcd_window.title("VCD")
        from vcd_ui import VcdUI

        VcdUI(vcd_window)

        def on_vcd_close():
            vcd_window.destroy()
            self.root.deiconify()

        vcd_window.protocol("WM_DELETE_WINDOW", on_vcd_close)

    def on_close(self):
        parent = self.root.master
        self.root.destroy()
        if parent is not None:
            try:
                parent.deiconify()
            except Exception:
                pass


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageViewer(root)
    root.mainloop()
