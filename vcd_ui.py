import os
import tkinter as tk
from PIL import Image
from PIL import ImageTk
from PIL.ImageTk import PhotoImage
from tkinter import ttk, filedialog
import vehicle_crash_detection
import ctypes

ctypes.windll.shcore.SetProcessDpiAwareness(1)

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

class VcdUI:
    def __init__(self, root):
        self.root = root
        self.root.state('zoomed')
        self.root.title("Vehicle Crash Detector")
        self.root.config(bg=BG_PRIMARY)
        self.title_bar_icon = PhotoImage(file=os.path.join(_BASE_DIR, "resources/icon/vehicle_crash_black.png"))
        self.root.iconphoto(False, self.title_bar_icon)

        self.content = tk.Frame(root, bg=BG_PRIMARY)
        self.content.pack(side='right', fill='both', expand=True)

        self.icon_white = Image.open(os.path.join(_BASE_DIR, "resources/icon/vehicle_crash_white.png")).resize((60, 60))
        self.icon_white = ImageTk.PhotoImage(self.icon_white)
        self.icon_black = Image.open(os.path.join(_BASE_DIR, "resources/icon/vehicle_crash_black._32.png")).resize((60, 60))
        self.icon_black = ImageTk.PhotoImage(self.icon_black)

        self.source = "No Video Source Selected"

        self.sidebar = tk.Frame(root, bg=BG_PANEL, width=290)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)

        self.border_frame = tk.Frame(self.sidebar, bg=ACCENT_RED, width=3)
        self.border_frame.pack(side='right', fill='y')

        self.sidebar_icon_label = tk.Label(self.sidebar, image=self.icon_white, bg=BG_PANEL)
        self.sidebar_icon_label.pack(side='top', pady=(20, 8))

        self.brand_title = tk.Label(
            self.sidebar,
            text="VEHICLE CRASH",
            bg=BG_PANEL,
            fg=TEXT_PRIMARY,
            font=('Bahnschrift SemiBold', 16)
        )
        self.brand_title.pack(side="top", padx=16)

        self.brand_subtitle = tk.Label(
            self.sidebar,
            text="Detector Console",
            bg=BG_PANEL,
            fg=TEXT_MUTED,
            font=('Bahnschrift', 11)
        )
        self.brand_subtitle.pack(side="top", pady=(0, 26), padx=16)

        self.sidebar_button1 = tk.Button(
            self.sidebar,
            text='Crash Detection',
            width=24,
            height=2,
            fg=TEXT_PRIMARY,
            bg=BG_PANEL,
            activebackground=ACCENT_RED,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=('Bahnschrift', 12)
        )
        self.sidebar_button1.pack(padx=18, pady=6)

        self.sidebar_button2 = tk.Button(
            self.sidebar,
            text='Records',
            command=self.open_image_viewer,
            width=24,
            height=2,
            fg=TEXT_PRIMARY,
            bg=BG_PANEL,
            activebackground=ACCENT_RED,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=('Bahnschrift', 12)
        )

        self.sidebar_button2.pack(padx=18, pady=6)
        self._add_sidebar_hover(self.sidebar_button1)
        self._add_sidebar_hover(self.sidebar_button2)

        self.sidebar_tip = tk.Label(
            self.sidebar,
            text="Tip: Select a source, then enable detection.",
            wraplength=230,
            justify="left",
            bg=BG_PANEL,
            fg=TEXT_MUTED,
            font=('Bahnschrift', 10)
        )
        self.sidebar_tip.pack(side="bottom", padx=16, pady=20)

        self.header_card = tk.Frame(self.content, bg=BG_SURFACE, height=120)
        self.header_card.pack(side="top", fill="x", padx=24, pady=(22, 14))
        self.header_card.pack_propagate(False)

        self.header_left = tk.Frame(self.header_card, bg=BG_SURFACE)
        self.header_left.pack(side="left", fill="both", expand=True, padx=20)

        self.title_label = tk.Label(
            self.header_left,
            text="Vehicle Crash Detector",
            bg=BG_SURFACE,
            font=('Bahnschrift SemiBold', 26),
            fg=TEXT_PRIMARY,
            compound="left",
            image=self.icon_black
        )
        self.title_label.pack(side="top", anchor="w", pady=(12, 4))

        self.subtitle_label = tk.Label(
            self.header_left,
            text="Real-time monitoring with automated emergency alerts",
            bg=BG_SURFACE,
            fg=TEXT_MUTED,
            font=('Bahnschrift', 12)
        )
        self.subtitle_label.pack(side="top", anchor="w")

        self.source_tag = tk.Label(
            self.header_card,
            text="SOURCE: NOT SELECTED",
            bg=ACCENT_RED,
            fg=TEXT_PRIMARY,
            font=('Bahnschrift SemiBold', 10),
            padx=16,
            pady=8
        )
        self.source_tag.pack(side="right", padx=20, pady=18)

        self.control_panel = tk.Frame(self.content, bg=BG_SURFACE, height=98)
        self.control_panel.pack(side="top", fill="x", padx=24, pady=(0, 14))
        self.control_panel.pack_propagate(False)

        self.combo_label = tk.Label(
            self.control_panel,
            text="Select a Video Source:",
            fg=TEXT_MUTED,
            bg=BG_SURFACE,
            font=('Bahnschrift', 12)
        )
        self.combo_label.pack(side="left", padx=(20, 12), pady=20)

        combo_style = ttk.Style()
        combo_style.theme_use("clam")
        combo_style.configure(
            "TCombobox",
            fieldbackground=BG_PANEL,
            background=BG_PANEL,
            foreground=TEXT_PRIMARY,
            selectbackground=BG_PANEL,
            selectforeground=TEXT_PRIMARY,
            arrowcolor=TEXT_PRIMARY,
            borderwidth=0,
            relief="flat"
        )

        self.combo_box = ttk.Combobox(
            self.control_panel,
            values=["Video File", "Live-Camera"],
            state="readonly",
            width=22,
            font=('Bahnschrift', 11)
        )
        self.combo_box.set("Select an option")
        self.combo_box.pack(side="left", pady=20)
        self.combo_box.bind("<<ComboboxSelected>>", self.handle_combobox)

        self.var = tk.BooleanVar()
        self.button1 = tk.Button(
            self.control_panel,
            text="Detection \nOFF",
            width=16,
            height=2,
            fg=TEXT_DARK,
            bg=ACCENT_TEAL,
            activebackground="#30c7bc",
            activeforeground=TEXT_DARK,
            relief="flat",
            bd=0,
            highlightthickness=0,
            command=self.toggle,
            font=('Bahnschrift SemiBold', 11)
        )
        self.button1.pack(side="right", padx=22, pady=16)

        self.detections_update_label = tk.Label(
            self.control_panel,
            text="",
            bg=BG_SURFACE,
            font=('Bahnschrift', 11),
            fg=TEXT_PRIMARY
        )
        self.detections_update_label.pack(side="right", padx=8)

        self.feed_shell = tk.Frame(self.content, bg=BG_SURFACE)
        self.feed_shell.pack(side="top", fill="both", expand=True, padx=24, pady=(0, 20))

        self.feed_title = tk.Label(
            self.feed_shell,
            text="Live Monitoring Stage",
            bg=BG_SURFACE,
            fg=TEXT_PRIMARY,
            font=('Bahnschrift SemiBold', 14)
        )
        self.feed_title.pack(side="top", anchor="w", padx=16, pady=(14, 6))

        self.feed_hint = tk.Label(
            self.feed_shell,
            text="Your model preview and loading progress appear here.",
            bg=BG_SURFACE,
            fg=TEXT_MUTED,
            font=('Bahnschrift', 11)
        )
        self.feed_hint.pack(side="top", anchor="w", padx=16, pady=(0, 8))

        self.feed_area = tk.Frame(self.feed_shell, bg=BG_STAGE)
        self.feed_area.pack(side="top", fill="both", expand=True, padx=16, pady=(0, 16))

        # Show team details splash inside feed_area during loading
        self.splash_frame = self._build_splash(self.feed_area)
        self.splash_frame.place(relx=0.5, rely=0.4, anchor="center")

        self.vc = vehicle_crash_detection.VehicleCrash(self.detections_update_label, self.feed_area, self.button1)
        self.vc.load_model()

        # Remove splash after model is loaded
        self.splash_frame.destroy()

    def _build_splash(self, parent):
        """Build team details splash overlay shown during model loading."""
        frame = tk.Frame(parent, bg=BG_STAGE)

        # ── Project Title ──
        tk.Label(
            frame, text="CrashGuard",
            bg=BG_STAGE, fg=ACCENT_RED,
            font=('Bahnschrift SemiBold', 36)
        ).pack(pady=(0, 2))

        tk.Label(
            frame, text="Vehicle Crash Detection System",
            bg=BG_STAGE, fg=TEXT_MUTED,
            font=('Bahnschrift', 13)
        ).pack(pady=(0, 20))

        # ── Accent Divider ──
        tk.Frame(frame, bg=ACCENT_TEAL, height=3, width=320).pack(pady=(0, 20))

        # ── Project Info ──
        info_items = [
            ("College",    "Hindustan College of Science & Technology"),
            ("Department", "B.Tech \u2014 Computer Science & Engineering"),
            ("Batch",      "2022 \u2013 2026"),
            ("Group",      "G-32"),
        ]

        for label_text, value_text in info_items:
            row = tk.Frame(frame, bg=BG_STAGE)
            row.pack(fill="x", pady=2)
            tk.Label(
                row, text=f"{label_text}:", width=12, anchor="e",
                bg=BG_STAGE, fg=TEXT_MUTED,
                font=('Bahnschrift', 11)
            ).pack(side="left")
            tk.Label(
                row, text=value_text, anchor="w",
                bg=BG_STAGE, fg=TEXT_PRIMARY,
                font=('Bahnschrift', 11)
            ).pack(side="left", padx=(8, 0))

        # ── Divider ──
        tk.Frame(frame, bg=BG_PANEL, height=1, width=320).pack(pady=16)

        # ── Team Members ──
        tk.Label(
            frame, text="TEAM MEMBERS",
            bg=BG_STAGE, fg=ACCENT_TEAL,
            font=('Bahnschrift SemiBold', 11)
        ).pack(pady=(0, 10))

        members = [
            "Kavyansh Sharma",
            "Manish Singh",
            "Rohit Rajput",
            "Saksham Jain",
        ]
        accent_colors = [ACCENT_RED, ACCENT_TEAL, "#e67e22", "#8e44ad"]

        for i, name in enumerate(members):
            member_row = tk.Frame(frame, bg=BG_STAGE)
            member_row.pack(fill="x", pady=3)

            # Color dot
            dot = tk.Canvas(
                member_row, width=10, height=10,
                bg=BG_STAGE, highlightthickness=0
            )
            dot.pack(side="left", padx=(40, 8), pady=2)
            dot.create_oval(1, 1, 9, 9, fill=accent_colors[i], outline="")

            tk.Label(
                member_row, text=name,
                bg=BG_STAGE, fg=TEXT_PRIMARY,
                font=('Bahnschrift', 12), anchor="w"
            ).pack(side="left")

            tk.Label(
                member_row, text=f"  \u2022  Member {i + 1}",
                bg=BG_STAGE, fg=TEXT_MUTED,
                font=('Bahnschrift', 10), anchor="w"
            ).pack(side="left")

        return frame

    def _add_sidebar_hover(self, button):
        button.bind("<Enter>", lambda _event: button.config(bg="#223041"))
        button.bind("<Leave>", lambda _event: button.config(bg=BG_PANEL))

    def _refresh_source_tag(self):
        tag_text = "SOURCE: LIVE-CAMERA" if self.source == 0 else f"SOURCE: {self.source}"
        self.source_tag.config(text=tag_text)

    def _update_detection_button(self):
        if self.var.get():
            self.button1.config(
                text="Detection \nON",
                bg=ACCENT_RED,
                fg=TEXT_PRIMARY,
                activebackground=ACCENT_RED_HOVER,
                activeforeground=TEXT_PRIMARY
            )
        else:
            self.button1.config(
                text="Detection \nOFF",
                bg=ACCENT_TEAL,
                fg=TEXT_DARK,
                activebackground="#30c7bc",
                activeforeground=TEXT_DARK
            )

    def _set_status(self, text):
        self.detections_update_label.configure(text=text)

    def open_file(self):
        file_path = filedialog.askopenfilename(
            title="Select video file",
            filetypes=[("Video Files", "*.mp4 *.avi *.mov *.mkv"), ("All Files", "*.*")]
        )
        if not file_path:
            self._set_status("No file selected")
            return None
        self.source = str(file_path)
        self.vc.set_source(self.source)
        self._refresh_source_tag()
        self._set_status("Video source selected")
        return self.source

    def open_camera(self):
        self.source = 0
        self.vc.set_source(self.source)
        self._refresh_source_tag()
        self._set_status("Live camera selected")
        return self.source

    def handle_combobox(self, event):
        value = event.widget.get()
        if value == "Video File":
            self.open_file()
        elif value == "Live-Camera":
            self.open_camera()

    def clear_frame(self):
        for widget in self.feed_area.winfo_children():
            if isinstance(widget, (tk.Canvas, ttk.Progressbar)):
                widget.destroy()

    def toggle(self):
        self.var.set(not self.var.get())
        self._update_detection_button()
        if self.var.get():
            self._set_status("Starting detection...")
            self.vc.run_detection()
        else:
            self.vc.stop_detection()
            self._set_status("")
            self.clear_frame()

    def open_image_viewer(self):
        self.root.withdraw()
        image_viewer_window = tk.Toplevel(self.root)
        image_viewer_window.title("Image Viewer")
        from image_data_viewer import ImageViewer
        ImageViewer(image_viewer_window)

if __name__ == '__main__':
    root = tk.Tk()
    app = VcdUI(root)
    root.mainloop()
