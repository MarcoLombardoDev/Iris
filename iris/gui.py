# -*- coding: utf-8 -*-
#
# Iris - Email Sender
# Copyright (C) 2026 Marco Lombardo
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version. It is distributed WITHOUT ANY WARRANTY; see the
# GNU Affero General Public License in LICENSE for details.
#
# A commercial licence, without the AGPL obligations, is available for use in
# proprietary or closed-source products - see COMMERCIAL-LICENSE.md.
"""Graphical interface of Iris - Email Sender.

The application logic (document parsing, message composition and sending,
configuration handling) lives in the :mod:`iris` package; this module
only contains the Tkinter layer.
"""

import datetime
import logging
import os
import queue
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, simpledialog, ttk

from iris import config_store, i18n, mailer, msgwriter, paths
from iris.i18n import t
from iris.parsers import (
    SUPPORTED_EXTENSIONS,
    Recipient,
    UnsupportedFormatError,
    extract_from_file,
)
from iris.version import APP_NAME, APP_TITLE, __version__

# ttkbootstrap is optional: without it the standard ttk theme is used.
BOOTSTRAP_ERROR = None
try:
    import ttkbootstrap as tb

    BOOTSTRAP_AVAILABLE = True
except Exception as exc:  # pragma: no cover - depends on the environment
    tb = None
    BOOTSTRAP_AVAILABLE = False
    BOOTSTRAP_ERROR = str(exc)

THEME_NAME = "flatly"

#: Translation key for each connection type shown in the combo box.
CONNECTION_KEYS = {
    mailer.CONNECTION_SSL: "connection.ssl",
    mailer.CONNECTION_STARTTLS: "connection.starttls",
    mailer.CONNECTION_NONE: "connection.none",
}


class IrisApp:
    """Main application window."""

    def __init__(self, root):
        self.root = root

        # Variables bound to the widgets.
        self.file_path = tk.StringVar()
        self.sender_email = tk.StringVar()
        self.smtp_server = tk.StringVar()
        self.smtp_port = tk.StringVar()
        self.smtp_user = tk.StringVar()
        self.smtp_password = tk.StringVar()
        self.connection_type = tk.StringVar(value=mailer.CONNECTION_STARTTLS)
        self.connection_display = tk.StringVar()
        self.language_display = tk.StringVar()
        self.subject_template = tk.StringVar()
        self.body_template = tk.StringVar()
        self.attachment_path = tk.StringVar()
        self.send_delay = tk.StringVar(value="0")
        self.profile_display = tk.StringVar()
        self.template_display = tk.StringVar()

        #: Recipients currently listed.
        self.actions = []

        #: Saved sender profiles and email templates, read from config.ini.
        self.profiles = []
        self.templates = []

        self.operation_in_progress = False
        self.cancel_requested = False
        self._status_reset_job = None
        self._ui_queue_job = None
        self._closing = False
        self._action_buttons = []
        self._icon_photo = None

        self.ui_queue = queue.Queue()
        self.bootstyle_available = BOOTSTRAP_AVAILABLE

        self.setup_logging()
        if not self.bootstyle_available and BOOTSTRAP_ERROR:
            self.log(t("log.bootstrap_missing", error=BOOTSTRAP_ERROR), level=logging.WARNING)

        # The language must be known before any widget is created.
        self.load_config(apply_to_widgets=False)

        self.root.title(f"{APP_TITLE} {__version__}")
        self.root.geometry("900x800")
        self.root.minsize(820, 700)
        self._set_window_icon()

        if self.bootstyle_available:
            try:
                self.style = tb.Style(THEME_NAME)
                self.log(t("log.bootstrap_active", theme=THEME_NAME))
            except Exception as exc:
                self.bootstyle_available = False
                self.log(t("log.bootstrap_fallback", error=exc), level=logging.WARNING)
        else:
            self.log(t("log.bootstrap_unavailable"), level=logging.WARNING)

        self.create_widgets()
        self.apply_config_to_widgets()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.process_ui_queue()

    # ------------------------------------------------------------------
    # Infrastructure
    # ------------------------------------------------------------------
    def _set_window_icon(self):
        """Set the window icon, without ever blocking start-up on failure."""
        try:
            ico_path = paths.resource_path(os.path.join("assets", "app_icon.ico"))
            if os.name == "nt" and os.path.exists(ico_path):
                self.root.iconbitmap(ico_path)
                return
            png_path = paths.resource_path(os.path.join("assets", "app_icon.png"))
            if os.path.exists(png_path):
                self._icon_photo = tk.PhotoImage(file=png_path)
                self.root.iconphoto(True, self._icon_photo)
        except Exception as exc:
            self.log(t("log.icon_error", error=exc), level=logging.WARNING)

    def setup_logging(self):
        """Configure file logging."""
        self.logger = logging.getLogger("iris")
        self.logger.setLevel(logging.INFO)
        if self.logger.handlers:
            return

        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        try:
            log_dir = os.path.join(paths.writable_app_dir(), "logs")
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(
                log_dir, f"{APP_NAME.lower()}_{datetime.datetime.now().strftime('%Y%m%d')}.log"
            )
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            self.log(t("log.logging_ready", path=log_file))
        except Exception as exc:  # pragma: no cover - depends on permissions
            print(f"Could not configure file logging: {exc}")
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def process_ui_queue(self):
        """Run, on the main thread, the UI updates requested by workers."""
        try:
            while True:
                try:
                    update = self.ui_queue.get_nowait()
                except queue.Empty:
                    break
                try:
                    update()
                except Exception as exc:
                    self.logger.error("Error while updating the UI: %s", exc)
        finally:
            if self._closing:
                self._ui_queue_job = None
                return
            try:
                self._ui_queue_job = self.root.after(100, self.process_ui_queue)
            except tk.TclError:
                self._ui_queue_job = None  # window closed

    def run_on_ui(self, callback):
        """Schedule ``callback`` to run on the GUI thread."""
        self.ui_queue.put(callback)

    def button(self, parent, text, command, style=None, **kwargs):
        """Create a button using ttkbootstrap when available, else plain ttk.

        The ``bootstyle`` option only exists on ttkbootstrap widgets: passing
        it to a standard ``ttk.Button`` raises
        ``TclError: unknown option "-bootstyle"``.
        """
        if self.bootstyle_available:
            themed_kwargs = dict(kwargs)
            if style:
                themed_kwargs["bootstyle"] = style
            try:
                return tb.Button(parent, text=text, command=command, **themed_kwargs)
            except Exception as exc:
                # For instance a theme that failed to build: fall back to the
                # standard widgets instead of failing to start.
                self.bootstyle_available = False
                self.log(t("log.buttons_fallback", error=exc), level=logging.WARNING)
        return ttk.Button(parent, text=text, command=command, **kwargs)

    def update_status_bar(self, message):
        """Update the status bar (main thread only)."""
        if not hasattr(self, "status_label"):
            return
        self.status_label.config(text=message)
        self._cancel_status_reset()
        self._status_reset_job = self.root.after(15000, self._reset_status_bar)

    def _cancel_status_reset(self):
        if self._status_reset_job is None:
            return
        try:
            self.root.after_cancel(self._status_reset_job)
        except Exception:
            pass
        self._status_reset_job = None

    def _reset_status_bar(self):
        self._status_reset_job = None
        if hasattr(self, "status_label"):
            try:
                self.status_label.config(text=t("status.ready"))
            except tk.TclError:
                pass

    def log(self, message, level=logging.INFO):
        """Write a message to the LOG tab and to the log file (thread-safe)."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {message}"

        if threading.current_thread() is threading.main_thread():
            self._append_log_line(line)
        else:
            self.ui_queue.put(lambda text=line: self._append_log_line(text))

        if hasattr(self, "logger"):
            self.logger.log(level, message)

    def _append_log_line(self, text):
        if not hasattr(self, "log_text"):
            return
        try:
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, text + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        except tk.TclError:
            pass

    def on_close(self):
        """Orderly shutdown: stop any running operation first."""
        if self.operation_in_progress:
            if not messagebox.askyesno(t("dialog.closing_title"), t("dialog.closing_body")):
                return
            self.cancel_requested = True
        self.shutdown()

    def shutdown(self):
        """Cancel pending timers and destroy the window.

        Without the explicit cancellation the ``after`` callbacks keep firing
        on a destroyed Tk interpreter ("invalid command name ...").
        """
        self._closing = True
        self.cancel_requested = True
        for job in (self._ui_queue_job, self._status_reset_job):
            if job is None:
                continue
            try:
                self.root.after_cancel(job)
            except Exception:
                pass
        self._ui_queue_job = None
        self._status_reset_job = None

        # Release the icon image while still on the main thread:
        # PhotoImage.__del__ talks to Tk and would hang if the garbage
        # collector ran it inside a worker thread.
        self._icon_photo = None

        try:
            self.root.destroy()
        except tk.TclError:
            pass

    # ------------------------------------------------------------------
    # Widget construction
    # ------------------------------------------------------------------
    def create_widgets(self):
        self.notebook_container = ttk.Frame(self.root)
        self.notebook_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.notebook = ttk.Notebook(self.notebook_container)
        try:
            ttk.Style(self.root).configure("TNotebook.Tab", padding=[10, 3])
        except Exception as exc:
            self.log(t("log.tab_style_error", error=exc), level=logging.WARNING)

        self.notebook.pack(fill=tk.BOTH, expand=True)

        version_label = ttk.Label(
            self.notebook_container,
            text=f"{APP_TITLE.upper()}  ·  " + t("app.version_label", version=__version__),
            font=("Arial", 8),
        )
        version_label.place(relx=1.0, y=2, anchor=tk.NE, x=-5)

        actions_frame = ttk.Frame(self.notebook)
        self.notebook.add(actions_frame, text=t("tab.processing"))

        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text=t("tab.log"))

        config_frame = ttk.Frame(self.notebook)
        self.notebook.add(config_frame, text=t("tab.configuration"))

        self.setup_config_tab(config_frame)
        self.setup_actions_tab(actions_frame)
        self.setup_logs_tab(logs_frame)

        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=(0, 10))
        self.status_label = ttk.Label(
            self.status_frame, text=t("status.ready"), anchor=tk.W, borderwidth=0, relief=tk.FLAT
        )
        self.status_label.pack(fill=tk.X)

        self.footer_label = ttk.Label(
            self.status_frame,
            text=t("footer.copyright", app=APP_NAME),
            anchor=tk.CENTER,
            font=("Arial", 8),
            foreground="#888888",
        )
        self.footer_label.pack(fill=tk.X, pady=(4, 0))

    def setup_config_tab(self, parent):
        email_frame = ttk.LabelFrame(parent, text=t("config.sender_frame"))
        email_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        ttk.Label(email_frame, text=t("config.profile")).grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=3
        )
        self.profile_combo = self._build_library_row(
            email_frame,
            row=0,
            variable=self.profile_display,
            names=self._profile_names(),
            on_selected=self.on_profile_selected,
            on_save=self.save_profile_as,
            on_delete=self.delete_profile,
        )

        ttk.Label(email_frame, text=t("config.email")).grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=3
        )
        self.sender_email_entry = ttk.Entry(email_frame, textvariable=self.sender_email, width=45)
        self.sender_email_entry.grid(row=1, column=1, padx=5, pady=3, sticky=tk.W)

        ttk.Label(email_frame, text=t("config.server")).grid(
            row=2, column=0, sticky=tk.W, padx=5, pady=3
        )
        self.smtp_server_entry = ttk.Entry(email_frame, textvariable=self.smtp_server, width=45)
        self.smtp_server_entry.grid(row=2, column=1, padx=5, pady=3, sticky=tk.W)

        ttk.Label(email_frame, text=t("config.port")).grid(
            row=3, column=0, sticky=tk.W, padx=5, pady=3
        )
        self.smtp_port_entry = ttk.Entry(email_frame, textvariable=self.smtp_port, width=45)
        self.smtp_port_entry.grid(row=3, column=1, padx=5, pady=3, sticky=tk.W)

        ttk.Label(email_frame, text=t("config.connection")).grid(
            row=4, column=0, sticky=tk.W, padx=5, pady=3
        )
        self.connection_labels = {code: t(key) for code, key in CONNECTION_KEYS.items()}
        self.connection_reverse = {label: code for code, label in self.connection_labels.items()}
        self.connection_combo = ttk.Combobox(
            email_frame,
            textvariable=self.connection_display,
            values=list(self.connection_labels.values()),
            state="readonly",
            width=42,
        )
        self.connection_combo.grid(row=4, column=1, padx=5, pady=3, sticky=tk.W)
        self.connection_combo.bind("<<ComboboxSelected>>", self.on_connection_type_change)
        self._set_connection_display(self.connection_type.get())

        ttk.Label(email_frame, text=t("config.username")).grid(
            row=5, column=0, sticky=tk.W, padx=5, pady=3
        )
        self.smtp_user_entry = ttk.Entry(email_frame, textvariable=self.smtp_user, width=45)
        self.smtp_user_entry.grid(row=5, column=1, padx=5, pady=3, sticky=tk.W)

        ttk.Label(email_frame, text=t("config.password")).grid(
            row=6, column=0, sticky=tk.W, padx=5, pady=3
        )
        self.smtp_password_entry = ttk.Entry(
            email_frame, textvariable=self.smtp_password, width=45, show="*"
        )
        self.smtp_password_entry.grid(row=6, column=1, padx=5, pady=3, sticky=tk.W)

        ttk.Label(
            email_frame,
            text=t("config.auth_note"),
            font=("Arial", 8),
            foreground="#1a5fb4",
            wraplength=520,
            justify="left",
        ).grid(row=7, column=0, columnspan=2, sticky=tk.W, padx=5, pady=(0, 5))

        template_frame = ttk.LabelFrame(parent, text=t("config.template_frame"))
        template_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        library_frame = ttk.Frame(template_frame)
        library_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(library_frame, text=t("config.template"), width=12).pack(
            side=tk.LEFT, padx=(0, 10)
        )
        self.template_combo = self._build_library_row(
            library_frame,
            row=None,
            variable=self.template_display,
            names=self._template_names(),
            on_selected=self.on_template_selected,
            on_save=self.save_template_as,
            on_delete=self.delete_template,
        )

        subject_frame = ttk.Frame(template_frame)
        subject_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(subject_frame, text=t("config.subject"), width=12).pack(side=tk.LEFT, padx=(0, 10))
        self.subject_template_entry = ttk.Entry(subject_frame, textvariable=self.subject_template)
        self.subject_template_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(
            subject_frame,
            text=t("config.variables", placeholder=mailer.COMPANY_PLACEHOLDERS[0]),
            font=("Arial", 8),
        ).pack(side=tk.LEFT, padx=(10, 0))

        body_frame = ttk.Frame(template_frame)
        body_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        ttk.Label(body_frame, text=t("config.message"), width=12).pack(
            side=tk.LEFT, padx=(0, 10), anchor=tk.N
        )
        entry_font = ttk.Style(self.root).lookup("TEntry", "font") or "TkDefaultFont"
        self.body_text = tk.Text(body_frame, height=5, wrap=tk.WORD, font=entry_font, undo=True)
        self.body_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        body_scroll = ttk.Scrollbar(body_frame, orient=tk.VERTICAL, command=self.body_text.yview)
        self.body_text.configure(yscrollcommand=body_scroll.set)
        body_scroll.pack(side=tk.LEFT, fill=tk.Y)

        attachment_frame = ttk.Frame(template_frame)
        attachment_frame.pack(fill=tk.X, padx=5, pady=(0, 10))
        attachment_frame.columnconfigure(1, weight=1)

        ttk.Label(attachment_frame, text=t("config.attachment"), width=12).grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10)
        )
        attachment_style = ttk.Style(self.root)
        attachment_style.configure("Attachment.TEntry", fieldbackground="white")
        attachment_style.map("Attachment.TEntry", fieldbackground=[("readonly", "white")])
        self.attachment_entry = ttk.Entry(
            attachment_frame,
            textvariable=self.attachment_path,
            state="readonly",
            style="Attachment.TEntry",
        )
        self.attachment_entry.grid(row=0, column=1, sticky=tk.EW, padx=(0, 5))
        self.button(
            attachment_frame,
            t("config.select_file"),
            self.browse_attachment_file,
            style="info-outline",
        ).grid(row=0, column=2, sticky=tk.E, padx=(0, 5))
        self.button(
            attachment_frame,
            t("config.remove"),
            self.clear_attachment_file,
            style="danger-outline",
            width=10,
        ).grid(row=0, column=3, sticky=tk.E)

        # A Text widget has no textvariable: keep it in sync manually.
        self.body_text.bind("<KeyRelease>", self.update_body_template)
        self.body_text.bind("<FocusOut>", self.update_body_template)

        options_frame = ttk.LabelFrame(parent, text=t("config.options_frame"))
        options_frame.pack(fill=tk.X, padx=10, pady=5)

        options_row = ttk.Frame(options_frame)
        options_row.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(options_row, text=t("config.send_delay")).pack(side=tk.LEFT, padx=(0, 10))
        self.send_delay_entry = ttk.Entry(options_row, textvariable=self.send_delay, width=8)
        self.send_delay_entry.pack(side=tk.LEFT)
        ttk.Label(
            options_row,
            text=t("config.send_delay_hint"),
            font=("Arial", 8),
            foreground="#666666",
        ).pack(side=tk.LEFT, padx=(8, 0))

        ttk.Label(options_row, text=t("config.language")).pack(side=tk.LEFT, padx=(30, 10))
        self.language_names = {code: name for code, name in i18n.language_choices()}
        self.language_codes = {name: code for code, name in self.language_names.items()}
        self.language_combo = ttk.Combobox(
            options_row,
            textvariable=self.language_display,
            values=list(self.language_names.values()),
            state="readonly",
            width=16,
        )
        self.language_combo.pack(side=tk.LEFT)
        self.language_combo.bind("<<ComboboxSelected>>", self.on_language_change)
        self.language_display.set(i18n.language_name(i18n.get_language()))

        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        self.button(button_frame, t("config.save"), self.save_config, style="success").pack(
            side=tk.RIGHT, padx=5
        )
        self.button(
            button_frame, t("config.test_connection"), self.test_connection, style="info-outline"
        ).pack(side=tk.RIGHT, padx=5)

    def _build_library_row(self, parent, row, variable, names, on_selected, on_save, on_delete):
        """Build a "saved items" row: combo box, SAVE AS... and DELETE.

        ``row`` places the row in a grid; pass ``None`` when ``parent`` is
        already a packed row of its own. Returns the combo box.
        """
        container = ttk.Frame(parent)
        if row is None:
            container.pack(side=tk.LEFT, fill=tk.X, expand=True)
        else:
            container.grid(row=row, column=1, padx=5, pady=3, sticky=tk.W)

        combo = ttk.Combobox(
            container, textvariable=variable, values=names, state="readonly", width=24
        )
        combo.pack(side=tk.LEFT)
        combo.bind("<<ComboboxSelected>>", on_selected)
        self.button(container, t("config.save_as"), on_save, style="info-outline", width=13).pack(
            side=tk.LEFT, padx=(6, 0)
        )
        self.button(container, t("config.delete"), on_delete, style="danger-outline", width=9).pack(
            side=tk.LEFT, padx=(6, 0)
        )
        return combo

    # ------------------------------------------------------------------
    # Saved sender profiles and email templates
    # ------------------------------------------------------------------
    def _profile_names(self):
        return [profile.name for profile in self.profiles]

    def _template_names(self):
        return [template.name for template in self.templates]

    def _find_profile(self, name):
        wanted = config_store.clean_name(name).lower()
        return next((item for item in self.profiles if item.name.lower() == wanted), None)

    def _find_template(self, name):
        wanted = config_store.clean_name(name).lower()
        return next((item for item in self.templates if item.name.lower() == wanted), None)

    def _refresh_library_choices(self):
        """Re-publish the saved names into the two combo boxes."""
        for combo, names in (
            (getattr(self, "profile_combo", None), self._profile_names()),
            (getattr(self, "template_combo", None), self._template_names()),
        ):
            if combo is None:
                continue
            try:
                combo.config(values=names)
            except tk.TclError:
                pass

    def _ask_name(self, title_key, body_key, current):
        """Ask for a name, returning it cleaned up — or ``None`` to give up."""
        answer = simpledialog.askstring(
            t(title_key), t(body_key), parent=self.root, initialvalue=current
        )
        if answer is None:
            return None
        name = config_store.clean_name(answer)
        if not name:
            messagebox.showerror(t("dialog.error"), t("dialog.name_required"))
            return None
        return name

    def _library_error(self, key, exc):
        detail = t(key, error=exc)
        self.log(detail, level=logging.ERROR)
        messagebox.showerror(t("dialog.error"), detail)

    def _announce(self, key, name):
        message = t(key, name=name)
        self.log(message)
        self.update_status_bar(message)

    def on_profile_selected(self, event=None):
        """Copy the selected sender profile into the configuration fields."""
        profile = self._find_profile(self.profile_display.get())
        if profile is None:
            return
        self.sender_email.set(profile.sender_email)
        self.smtp_server.set(profile.smtp_server)
        self.smtp_port.set(profile.smtp_port)
        self.smtp_user.set(profile.smtp_user)
        self.smtp_password.set(profile.smtp_password)
        self._set_connection_display(profile.connection_type)
        self._announce("log.profile_loaded", profile.name)

    def save_profile_as(self):
        """Store the sender fields as a named profile."""
        name = self._ask_name(
            "dialog.profile_name_title", "dialog.profile_name_body", self.profile_display.get()
        )
        if name is None:
            return
        if self._find_profile(name) is not None and not messagebox.askyesno(
            t("dialog.confirm"), t("dialog.profile_overwrite", name=name)
        ):
            return

        profile = config_store.SenderProfile(
            name=name,
            sender_email=self.sender_email.get().strip(),
            smtp_server=self.smtp_server.get().strip(),
            smtp_port=self.smtp_port.get().strip(),
            smtp_user=self.smtp_user.get(),
            smtp_password=self.smtp_password.get(),
            connection_type=self.connection_type.get(),
        )
        try:
            config_store.save_profile(profile)
        except Exception as exc:
            self._library_error("log.profile_error", exc)
            return

        self.profiles = [item for item in self.profiles if item.name.lower() != name.lower()]
        self.profiles.append(profile)
        self.profiles.sort(key=lambda item: item.name.lower())
        self.profile_display.set(name)
        self._refresh_library_choices()
        self._announce("log.profile_saved", name)

    def delete_profile(self):
        """Remove the selected sender profile."""
        name = config_store.clean_name(self.profile_display.get())
        if not name or self._find_profile(name) is None:
            messagebox.showinfo(t("dialog.info"), t("dialog.select_profile"))
            return
        if not messagebox.askyesno(
            t("dialog.confirm"), t("dialog.confirm_delete_profile", name=name)
        ):
            return
        try:
            config_store.delete_profile(name)
        except Exception as exc:
            self._library_error("log.profile_error", exc)
            return

        self.profiles = [item for item in self.profiles if item.name.lower() != name.lower()]
        self.profile_display.set("")
        self._refresh_library_choices()
        self._announce("log.profile_deleted", name)

    def on_template_selected(self, event=None):
        """Copy the selected template into the subject, message and attachment."""
        template = self._find_template(self.template_display.get())
        if template is None:
            return
        self.subject_template.set(template.email_subject)
        self._set_body_text(template.email_body)
        self.attachment_path.set(template.attachment_path)
        self._announce("log.template_loaded", template.name)

    def save_template_as(self):
        """Store subject, message and attachment as a named template."""
        name = self._ask_name(
            "dialog.template_name_title", "dialog.template_name_body", self.template_display.get()
        )
        if name is None:
            return
        if self._find_template(name) is not None and not messagebox.askyesno(
            t("dialog.confirm"), t("dialog.template_overwrite", name=name)
        ):
            return

        self.update_body_template()
        template = config_store.MessageTemplate(
            name=name,
            email_subject=self.subject_template.get(),
            email_body=self.body_template.get(),
            attachment_path=self.attachment_path.get().strip(),
        )
        try:
            config_store.save_template(template)
        except Exception as exc:
            self._library_error("log.template_error", exc)
            return

        self.templates = [item for item in self.templates if item.name.lower() != name.lower()]
        self.templates.append(template)
        self.templates.sort(key=lambda item: item.name.lower())
        self.template_display.set(name)
        self._refresh_library_choices()
        self._announce("log.template_saved", name)

    def delete_template(self):
        """Remove the selected template."""
        name = config_store.clean_name(self.template_display.get())
        if not name or self._find_template(name) is None:
            messagebox.showinfo(t("dialog.info"), t("dialog.select_template"))
            return
        if not messagebox.askyesno(
            t("dialog.confirm"), t("dialog.confirm_delete_template", name=name)
        ):
            return
        try:
            config_store.delete_template(name)
        except Exception as exc:
            self._library_error("log.template_error", exc)
            return

        self.templates = [item for item in self.templates if item.name.lower() != name.lower()]
        self.template_display.set("")
        self._refresh_library_choices()
        self._announce("log.template_deleted", name)

    def setup_actions_tab(self, parent):
        file_frame = ttk.LabelFrame(parent, text=t("actions.file_frame"))
        file_frame.pack(fill=tk.X, padx=10, pady=10)

        self._register_button(
            self.button(
                file_frame,
                t("actions.select_file"),
                self.browse_and_analyze_file,
                style="info-outline",
            )
        ).pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(
            file_frame,
            text=t("actions.criteria"),
            font=("Arial", 8),
            foreground="#666666",
            wraplength=780,
            justify="left",
        ).pack(fill=tk.X, padx=10, pady=(0, 10))

        actions_list_frame = ttk.LabelFrame(parent, text=t("actions.list_frame"))
        actions_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("company", "email")
        self.actions_tree = ttk.Treeview(
            actions_list_frame, columns=columns, show="headings", selectmode="extended"
        )
        self.actions_tree.heading("company", text=t("actions.col_company"))
        self.actions_tree.heading("email", text=t("actions.col_email"))
        self.actions_tree.column("company", width=300)
        self.actions_tree.column("email", width=300)

        scrollbar = ttk.Scrollbar(
            actions_list_frame, orient=tk.VERTICAL, command=self.actions_tree.yview
        )
        self.actions_tree.configure(yscroll=scrollbar.set)
        self.actions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)

        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        left_button_frame = ttk.Frame(button_frame)
        left_button_frame.pack(side=tk.LEFT)
        self._register_button(
            self.button(
                left_button_frame, t("actions.send_selected"), self.send_selected_email,
                style="success",
            )
        ).pack(side=tk.LEFT, padx=5)
        self._register_button(
            self.button(
                left_button_frame,
                t("actions.delete_selected"),
                self.delete_selected_action,
                style="danger-outline",
            )
        ).pack(side=tk.LEFT, padx=5)

        right_button_frame = ttk.Frame(button_frame)
        right_button_frame.pack(side=tk.RIGHT)
        self._register_button(
            self.button(
                right_button_frame,
                t("actions.create_only"),
                self.generate_email_files,
                style="info-outline",
            )
        ).pack(side=tk.RIGHT, padx=5)
        self._register_button(
            self.button(right_button_frame, t("actions.send_all"), self.send_all_emails,
                        style="success")
        ).pack(side=tk.RIGHT, padx=5)

    def _register_button(self, button):
        """Register a button to be disabled while a long operation runs."""
        self._action_buttons.append(button)
        return button

    def _set_buttons_enabled(self, enabled):
        state = tk.NORMAL if enabled else tk.DISABLED
        for button in self._action_buttons:
            try:
                button.config(state=state)
            except tk.TclError:
                pass

    def setup_logs_tab(self, parent):
        events_frame = ttk.LabelFrame(parent, text=t("logs.frame"))
        events_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.log_text = scrolledtext.ScrolledText(events_frame, width=80, height=30, font=("Arial", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.log_text.config(state=tk.DISABLED)

        self.button(events_frame, t("logs.clear"), self.clear_logs, style="danger-outline").pack(
            side=tk.RIGHT, padx=10, pady=5
        )

    # ------------------------------------------------------------------
    # Language
    # ------------------------------------------------------------------
    def on_language_change(self, event=None):
        """Apply, persist and redraw the interface in the chosen language."""
        code = self.language_codes.get(self.language_display.get())
        if not code or code == i18n.get_language():
            return

        i18n.set_language(code)
        try:
            config_store.update_language(code)
        except Exception as exc:
            self.log(t("log.config_save_error", error=exc), level=logging.ERROR)

        self.rebuild_ui()
        self.log(t("log.language_changed", language=i18n.language_name(code)))

    def rebuild_ui(self):
        """Rebuild every widget, preserving the current content."""
        rows = [self.actions_tree.item(item, "values") for item in self.actions_tree.get_children()]
        selected_tab = self.notebook.index(self.notebook.select())
        log_lines = self.log_text.get("1.0", tk.END).rstrip("\n")
        self.update_body_template()
        body = self.body_template.get()

        self._cancel_status_reset()
        for child in self.root.winfo_children():
            child.destroy()
        self._action_buttons = []

        self.create_widgets()

        self._set_body_text(body)
        self._set_connection_display(self.connection_type.get())
        self.language_display.set(i18n.language_name(i18n.get_language()))
        for row in rows:
            self.actions_tree.insert("", tk.END, values=row)
        if log_lines:
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert("1.0", log_lines + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        try:
            self.notebook.select(selected_tab)
        except tk.TclError:
            pass

    # ------------------------------------------------------------------
    # Document analysis
    # ------------------------------------------------------------------
    def browse_and_analyze_file(self):
        patterns = " ".join(f"*{extension}" for extension in SUPPORTED_EXTENSIONS)
        file_path = filedialog.askopenfilename(
            title=t("filedialog.recipients"),
            filetypes=[
                (t("filetype.all_supported"), patterns),
                (t("filetype.pdf"), "*.pdf"),
                (t("filetype.excel"), "*.xlsx *.xlsm *.xls"),
                (t("filetype.csv"), "*.csv"),
                (t("filetype.word"), "*.docx"),
                (t("filetype.text"), "*.txt"),
                (t("filetype.all"), "*.*"),
            ],
        )
        if file_path:
            self.file_path.set(file_path)
            self.log(t("log.file_selected", path=file_path))
            self.analyze_file(file_path)

    def analyze_file(self, file_path=None):
        """Analyse the file on a worker thread so the interface stays responsive."""
        if self.operation_in_progress:
            self.update_status_bar(t("status.operation_running"))
            return

        file_path = file_path or self.file_path.get()
        if not file_path:
            messagebox.showerror(t("dialog.error"), t("dialog.select_file_first"))
            return
        if not os.path.exists(file_path):
            messagebox.showerror(t("dialog.error"), t("dialog.file_missing", path=file_path))
            return

        self.log(t("log.start_analysis", path=file_path))
        self._begin_operation(t("status.analyzing"))

        def worker():
            try:
                recipients = extract_from_file(file_path, log=self.log)
            except (UnsupportedFormatError, FileNotFoundError) as exc:
                # The message must be read here: Python deletes the ``exc``
                # name when the except block ends, so a lambda referencing it
                # would fail once executed on the UI thread.
                detail = str(exc)
                self.run_on_ui(lambda: self._analysis_failed(detail, show_dialog=True))
                return
            except Exception as exc:
                detail = t("log.analysis_error", error=exc)
                self.run_on_ui(lambda: self._analysis_failed(detail, show_dialog=True))
                return
            self.run_on_ui(lambda: self._analysis_completed(recipients))

        threading.Thread(target=worker, daemon=True, name="analyze-file").start()

    def _analysis_completed(self, recipients):
        self._update_actions_list(recipients)
        if recipients:
            self.log(t("log.analysis_done", count=len(recipients)))
            self._end_operation(t("status.analysis_done", count=len(recipients)))
        else:
            self.log(t("log.analysis_none"), level=logging.WARNING)
            self._end_operation(t("status.analysis_none"))
            messagebox.showwarning(
                t("dialog.no_recipients_title"), t("dialog.no_recipients_body")
            )

    def _analysis_failed(self, detail, show_dialog=False):
        self.log(detail, level=logging.ERROR)
        self._end_operation(t("status.analysis_error"))
        if show_dialog:
            messagebox.showerror(t("dialog.error"), detail)

    def _update_actions_list(self, recipients):
        for item in self.actions_tree.get_children():
            self.actions_tree.delete(item)
        self.actions = list(recipients)
        for recipient in self.actions:
            self.actions_tree.insert("", tk.END, values=(recipient.company, recipient.email))

    def _selected_recipients(self):
        """Selected recipients, read on the main thread."""
        return [
            (item, Recipient(*self.actions_tree.item(item, "values")))
            for item in self.actions_tree.selection()
        ]

    def _all_recipients(self):
        return [
            (item, Recipient(*self.actions_tree.item(item, "values")))
            for item in self.actions_tree.get_children()
        ]

    # ------------------------------------------------------------------
    # Current configuration
    # ------------------------------------------------------------------
    def current_settings(self):
        return mailer.SmtpSettings(
            host=self.smtp_server.get().strip(),
            port=mailer.parse_port(self.smtp_port.get()),
            connection_type=self.connection_type.get(),
            username=self.smtp_user.get(),
            password=self.smtp_password.get(),
            send_delay=mailer.parse_delay(self.send_delay.get()),
        )

    def current_template(self):
        self.update_body_template()
        attachment = self.attachment_path.get().strip()
        return mailer.EmailTemplate(
            sender=self.sender_email.get().strip(),
            subject=self.subject_template.get(),
            body=self.body_template.get(),
            attachments=[attachment] if attachment else [],
        )

    def validate_email_config(self, require_template=True):
        """Validate the configuration, showing every problem found."""
        settings = self.current_settings()
        template = self.current_template()
        errors = mailer.validate_settings(settings, template)
        if not require_template:
            skipped = {t("validate.subject_missing"), t("validate.body_missing")}
            errors = [error for error in errors if error not in skipped]
        if errors:
            for error in errors:
                self.log(t("log.invalid_config", error=error), level=logging.ERROR)
            messagebox.showerror(t("dialog.invalid_config"), "\n\n".join(errors))
            return False
        return True

    # ------------------------------------------------------------------
    # Operation state
    # ------------------------------------------------------------------
    def _begin_operation(self, status_message):
        self.operation_in_progress = True
        self.cancel_requested = False
        self._set_buttons_enabled(False)
        self.update_status_bar(status_message)

    def _end_operation(self, status_message):
        self.operation_in_progress = False
        self._set_buttons_enabled(True)
        self.update_status_bar(status_message)

    # ------------------------------------------------------------------
    # Sending
    # ------------------------------------------------------------------
    def test_connection(self):
        """Check the SMTP connection (and authentication, when configured)."""
        if self.operation_in_progress:
            self.update_status_bar(t("status.operation_running"))
            return
        if not self.validate_email_config(require_template=False):
            return

        settings = self.current_settings()
        self._begin_operation(t("status.testing"))

        def worker():
            try:
                with mailer.SmtpSession(settings, log=self.log) as session:
                    session.connect()
                    authenticated = session.authenticated
                message = t("mailer.test_ok_auth") if authenticated else t("mailer.test_ok")
                self.run_on_ui(lambda: self._connection_test_done(True, message))
            except Exception as exc:
                detail = mailer.describe_smtp_error(exc)
                self.run_on_ui(lambda: self._connection_test_done(False, detail))

        threading.Thread(target=worker, daemon=True, name="smtp-test").start()

    def _connection_test_done(self, success, message):
        self.log(message, level=logging.INFO if success else logging.ERROR)
        self._end_operation(message if success else t("status.test_failed"))
        if success:
            messagebox.showinfo(t("dialog.test_title"), message)
        else:
            messagebox.showerror(t("dialog.test_title"), message)

    def send_selected_email(self):
        """Send the email to the selected recipients."""
        if self.operation_in_progress:
            self.update_status_bar(t("status.operation_running"))
            return

        selection = self._selected_recipients()
        if not selection:
            self.update_status_bar(t("status.select_recipient"))
            messagebox.showinfo(t("dialog.info"), t("dialog.select_recipient"))
            return
        if not self.validate_email_config():
            return
        self._start_send(selection)

    def send_all_emails(self):
        """Send the email to every recipient in the list."""
        if self.operation_in_progress:
            self.update_status_bar(t("status.operation_running"))
            return

        entries = self._all_recipients()
        if not entries:
            self.update_status_bar(t("status.no_recipients"))
            return
        if not self.validate_email_config():
            return
        if not messagebox.askyesno(
            t("dialog.confirm"), t("dialog.confirm_send_all", count=len(entries))
        ):
            return
        self._start_send(entries)

    def _start_send(self, entries):
        """Start the background send, reusing a single SMTP connection."""
        settings = self.current_settings()
        template = self.current_template()
        total = len(entries)
        item_by_email = {recipient.email: item for item, recipient in entries}
        recipients = [recipient for _, recipient in entries]

        self._begin_operation(t("status.sending", count=total))

        def worker():
            progress = {"done": 0}

            def on_result(recipient, success, detail):
                progress["done"] += 1
                done = progress["done"]
                if success:
                    item = item_by_email.get(recipient.email)
                    self.run_on_ui(lambda: self._remove_tree_item(item))
                self.run_on_ui(
                    lambda: self.update_status_bar(
                        t("status.send_progress", done=done, total=total)
                    )
                )

            try:
                result = mailer.send_bulk(
                    settings,
                    template,
                    recipients,
                    log=self.log,
                    on_result=on_result,
                    should_stop=lambda: self.cancel_requested,
                )
            except Exception as exc:
                detail = mailer.describe_smtp_error(exc)
                self.run_on_ui(lambda: self._send_failed(detail))
                return
            self.run_on_ui(lambda: self._send_completed(result))

        threading.Thread(target=worker, daemon=True, name="send-emails").start()

    def _remove_tree_item(self, item):
        if not item:
            return
        try:
            self.actions_tree.delete(item)
        except tk.TclError:
            pass

    def _send_failed(self, detail):
        self.log(detail, level=logging.ERROR)
        self._end_operation(t("status.send_error"))
        messagebox.showerror(t("dialog.error"), detail)

    def _send_completed(self, result):
        sent, errors = result.sent_count, result.error_count
        if sent and not errors:
            summary = t("log.send_summary_ok", count=sent)
            self.log(summary)
        elif sent and errors:
            summary = t("log.send_summary_mixed", sent=sent, errors=errors)
            self.log(summary, level=logging.WARNING)
        elif errors:
            summary = t("log.send_summary_failed", errors=errors)
            self.log(summary, level=logging.ERROR)
        else:
            summary = t("log.send_summary_none")
            self.log(summary, level=logging.WARNING)

        self._end_operation(summary)
        if errors:
            first_errors = "\n".join(
                f"• {recipient.email}: {detail}" for recipient, detail in result.failed[:5]
            )
            extra = "\n..." if errors > 5 else ""
            messagebox.showwarning(
                t("dialog.send_done_errors"), f"{summary}\n\n{first_errors}{extra}"
            )
        elif sent:
            messagebox.showinfo(t("dialog.send_done"), summary)

    # ------------------------------------------------------------------
    # Email file generation
    # ------------------------------------------------------------------
    def generate_email_files(self):
        """Create the email files (.msg with Outlook, otherwise .eml), no sending."""
        if self.operation_in_progress:
            self.update_status_bar(t("status.operation_running"))
            return

        entries = self._all_recipients()
        if not entries:
            self.update_status_bar(t("status.no_recipients"))
            return
        if not self.validate_email_config():
            return

        use_outlook = msgwriter.outlook_available()
        output_format = "MSG (Outlook)" if use_outlook else "EML"
        if not messagebox.askyesno(
            t("dialog.confirm"),
            t("dialog.confirm_create", format=output_format, count=len(entries)),
        ):
            return

        template = self.current_template()
        recipients = [recipient for _, recipient in entries]
        output_dir = os.path.join(paths.writable_app_dir(), "emails")
        self._begin_operation(t("status.creating", count=len(recipients)))

        def worker():
            created, failed = [], []
            try:
                os.makedirs(output_dir, exist_ok=True)
                removed = msgwriter.clean_output_directory(output_dir, log=self.log)
                if removed:
                    self.log(t("log.emails_cleaned", count=removed))

                for recipient in recipients:
                    if self.cancel_requested:
                        self.log(t("log.create_stopped"))
                        break
                    try:
                        message = mailer.build_message(template, recipient, log=self.log)
                        path, output_type = msgwriter.save_message(
                            message,
                            output_dir,
                            recipient.company,
                            recipient.email,
                            attachments=template.attachments,
                            prefer_msg=use_outlook,
                            log=self.log,
                        )
                        created.append(path)
                        self.log(t("log.file_created", format=output_type.upper(), path=path))
                    except Exception as exc:
                        failed.append((recipient, str(exc)))
                        self.log(
                            t("log.create_error", email=recipient.email, error=exc),
                            level=logging.ERROR,
                        )
            except Exception as exc:
                detail = t("log.dir_error", path=output_dir, error=exc)
                self.run_on_ui(lambda: self._generation_failed(detail))
                return
            self.run_on_ui(lambda: self._generation_completed(created, failed, output_dir))

        threading.Thread(target=worker, daemon=True, name="generate-emails").start()

    def _generation_failed(self, detail):
        self.log(detail, level=logging.ERROR)
        self._end_operation(t("status.create_error"))
        messagebox.showerror(t("dialog.error"), detail)

    def _generation_completed(self, created, failed, output_dir):
        if created and not failed:
            summary = t("log.create_summary_ok", count=len(created), path=output_dir)
            self.log(summary)
            self._end_operation(summary)
            messagebox.showinfo(t("dialog.create_done"), summary)
        elif created and failed:
            summary = t("log.create_summary_mixed", count=len(created), errors=len(failed))
            self.log(summary, level=logging.WARNING)
            self._end_operation(summary)
            messagebox.showwarning(t("dialog.create_done_errors"), summary)
        else:
            summary = t("log.create_summary_failed", errors=len(failed))
            self.log(summary, level=logging.ERROR)
            self._end_operation(summary)
            messagebox.showerror(t("dialog.error"), summary)

    # ------------------------------------------------------------------
    # List actions
    # ------------------------------------------------------------------
    def delete_selected_action(self):
        selection = self._selected_recipients()
        if not selection:
            messagebox.showinfo(t("dialog.info"), t("dialog.select_recipient"))
            return
        for item, recipient in selection:
            self.actions_tree.delete(item)
            self.log(
                t("log.recipient_removed", company=recipient.company, email=recipient.email)
            )
        self.update_status_bar(t("status.removed", count=len(selection)))

    def clear_logs(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.log(t("logs.cleared"))

    # ------------------------------------------------------------------
    # Attachment and template
    # ------------------------------------------------------------------
    def browse_attachment_file(self):
        file_path = filedialog.askopenfilename(
            title=t("filedialog.attachment"),
            filetypes=[
                (t("filetype.all"), "*.*"),
                (t("filetype.pdf"), "*.pdf"),
                (t("filetype.word"), "*.docx"),
                (t("filetype.excel"), "*.xlsx *.xls"),
                (t("filetype.text"), "*.txt"),
            ],
        )
        if file_path:
            self.attachment_path.set(file_path)
            self.log(t("log.attachment_selected", path=file_path))

    def clear_attachment_file(self):
        if self.attachment_path.get():
            self.log(t("log.attachment_removed", path=self.attachment_path.get()))
        self.attachment_path.set("")

    def update_body_template(self, *args):
        """Keep the StringVar aligned with the Text widget content."""
        if not hasattr(self, "body_text"):
            return
        content = self.body_text.get("1.0", tk.END)
        if content.endswith("\n"):
            content = content[:-1]
        if content != self.body_template.get():
            self.body_template.set(content)

    def _set_body_text(self, value):
        """Write the template into the Text widget, keeping the StringVar in sync."""
        self.body_template.set(value)
        if hasattr(self, "body_text"):
            self.body_text.delete("1.0", tk.END)
            self.body_text.insert("1.0", value)

    def on_connection_type_change(self, event=None):
        selected = self.connection_display.get()
        if selected in self.connection_reverse:
            internal = self.connection_reverse[selected]
            self.connection_type.set(internal)
            self.log(t("log.connection_type", value=internal))
        else:
            self._set_connection_display(self.connection_type.get())

    def _set_connection_display(self, internal_value):
        if internal_value not in self.connection_labels:
            internal_value = mailer.CONNECTION_STARTTLS
        self.connection_type.set(internal_value)
        self.connection_display.set(self.connection_labels[internal_value])

    # ------------------------------------------------------------------
    # Configuration file
    # ------------------------------------------------------------------
    def save_config(self):
        self.update_body_template()
        config = config_store.AppConfig(
            sender_email=self.sender_email.get().strip(),
            smtp_server=self.smtp_server.get().strip(),
            smtp_port=self.smtp_port.get().strip(),
            smtp_user=self.smtp_user.get(),
            smtp_password=self.smtp_password.get(),
            connection_type=self.connection_type.get(),
            email_subject=self.subject_template.get(),
            email_body=self.body_template.get(),
            attachment_path=self.attachment_path.get().strip(),
            language=i18n.get_language(),
            send_delay=self.send_delay.get().strip() or "0",
            # Saving the whole configuration must not drop the saved
            # profiles and templates: they live in the same file.
            profiles=list(self.profiles),
            templates=list(self.templates),
        )
        try:
            config_path = config_store.save(config)
        except Exception as exc:
            detail = t("log.config_save_error", error=exc)
            self.log(detail, level=logging.ERROR)
            messagebox.showerror(t("dialog.error"), detail)
            return

        self.log(t("log.config_saved", path=config_path))
        self.update_status_bar(t("log.config_saved", path=config_path))
        messagebox.showinfo(t("dialog.info"), t("dialog.config_saved", path=config_path))

    def load_config(self, apply_to_widgets=True):
        """Load ``config.ini``; optionally populate the interface with it."""
        try:
            result = config_store.load()
        except Exception as exc:
            self.log(t("log.config_load_error", error=exc), level=logging.ERROR)
            self._loaded_config = None
            return

        for message in result.messages:
            self.log(message, level=logging.WARNING)
        self._loaded_config = result if result.found else None
        self.profiles = list(result.config.profiles)
        self.templates = list(result.config.templates)
        self._refresh_library_choices()

        if apply_to_widgets:
            self.apply_config_to_widgets()

    def apply_config_to_widgets(self):
        """Copy the loaded configuration into the interface."""
        result = getattr(self, "_loaded_config", None)
        if result is None:
            return

        config = result.config
        self.sender_email.set(config.sender_email)
        self.smtp_server.set(config.smtp_server)
        self.smtp_port.set(config.smtp_port)
        self.smtp_user.set(config.smtp_user)
        self.smtp_password.set(config.smtp_password)
        self.attachment_path.set(config.attachment_path)
        self.subject_template.set(config.email_subject)
        self.send_delay.set(config.send_delay or "0")
        self._set_body_text(config.email_body)
        self._set_connection_display(config.connection_type)
        self.language_display.set(i18n.language_name(i18n.get_language()))

        self.log(
            t(
                "log.config_loaded",
                path=result.path,
                encoding=result.encoding,
                sender=config.sender_email,
                server=config.smtp_server,
                port=config.smtp_port,
                connection=self.connection_type.get(),
            )
        )


def create_root():
    """Create the main window, using ttkbootstrap when available."""
    if BOOTSTRAP_AVAILABLE:
        try:
            return tb.Window(themename=THEME_NAME)
        except Exception:
            pass
    return tk.Tk()


def main():
    root = create_root()
    IrisApp(root)
    root.mainloop()


if __name__ == "__main__":
    sys.exit(main())
