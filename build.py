#!/usr/bin/env python
# Iris — Email Sender
# Copyright (C) 2026 Marco Lombardo
#
# SPDX-License-Identifier: AGPL-3.0-or-later
# Distributed WITHOUT ANY WARRANTY; see LICENSE for the full terms.
# A commercial licence, without the AGPL's obligations, is available for use
# in proprietary or closed-source products — see COMMERCIAL-LICENSE.md.

"""Build the Iris executable with PyInstaller.

Usage::

    python build.py            build the executable
    python build.py --clean    remove build/ and dist/ only
"""

import argparse
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from iris.version import APP_TITLE, __version__  # noqa: E402

APP_NAME = "Iris"
MAIN_SCRIPT = "main.py"
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

#: Files that must exist for the build to run.
REQUIRED_FILES = (MAIN_SCRIPT, os.path.join("iris", "gui.py"), os.path.join("iris", "__init__.py"))

#: Resources bundled with the executable, when present: (source, destination).
OPTIONAL_DATA = (
    (os.path.join("assets", "app_icon.ico"), "assets"),
    (os.path.join("assets", "app_icon.png"), "assets"),
)

HIDDEN_IMPORTS = [
    "tkinter",
    "tkinter.ttk",
    "tkinter.filedialog",
    "tkinter.messagebox",
    "tkinter.scrolledtext",
    "pypdf",
    "openpyxl",
    "xlrd",
    "docx",
    "PIL",
    "PIL.Image",
    "PIL.ImageTk",
    # Required at runtime by PIL.ImageTk. Without it ttkbootstrap cannot build
    # its theme and every "bootstyle" widget raises, so the app fails to start.
    "PIL._tkinter_finder",
    "ttkbootstrap",
    "iris.gui",
    "iris",
    "iris.config_store",
    "iris.i18n",
    "iris.mailer",
    "iris.msgwriter",
    "iris.parsers",
    "iris.paths",
    "iris.version",
]

#: Windows only: .msg generation through Outlook.
WINDOWS_HIDDEN_IMPORTS = [
    "win32com",
    "win32com.client",
    "win32com.client.gencache",
    "pythoncom",
    "win32timezone",
]

EXCLUDES = [
    "matplotlib",
    "numpy",
    "pandas",
    "scipy",
    "PyQt5",
    "PyQt6",
    "PySide2",
    "PySide6",
    "jupyter",
    "IPython",
    "sphinx",
    "pytest",
]


def log(message):
    print(message, flush=True)


def check_prerequisites():
    """Check the interpreter, PyInstaller and the required files."""
    log("Checking prerequisites...")
    log(f"  Python: {sys.version.split()[0]} ({sys.executable})")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "PyInstaller", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        log(f"  ERROR: could not run PyInstaller: {exc}")
        return False

    if result.returncode != 0:
        log("  PyInstaller not found, installing...")
        install = subprocess.run(
            [sys.executable, "-m", "pip", "install", "pyinstaller"],
            capture_output=True,
            text=True,
            check=False,
        )
        if install.returncode != 0:
            log(f"  ERROR installing PyInstaller: {install.stderr.strip()}")
            return False
        log("  PyInstaller installed")
    else:
        log(f"  PyInstaller: {result.stdout.strip()}")

    missing = [
        name for name in REQUIRED_FILES if not os.path.exists(os.path.join(PROJECT_DIR, name))
    ]
    if missing:
        log(f"  ERROR: required files not found: {', '.join(missing)}")
        return False
    log("  Project files present")

    # config.ini is NOT required: the application creates it on the first save
    # and it is excluded from the repository because it holds credentials.
    if not os.path.exists(os.path.join(PROJECT_DIR, "config.ini")):
        log("  Note: config.ini missing (it is created on first run)")
    return True


def clean_temp_directories():
    """Remove the artefacts of a previous build."""
    log("Cleaning temporary directories...")
    for name in ("build", "dist", "__pycache__"):
        path = os.path.join(PROJECT_DIR, name)
        if not os.path.exists(path):
            continue
        try:
            shutil.rmtree(path)
            log(f"  {name} removed")
        except Exception as exc:
            log(f"  Could not remove {name}: {exc}")


def build_command():
    """Assemble the PyInstaller command line."""
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--windowed",
        "--noconfirm",
        f"--name={APP_NAME}",
        # The auto-generated .spec holds absolute paths of the build machine:
        # write it into build/ so the versioned, portable Iris.spec is
        # never overwritten.
        "--specpath",
        os.path.join(PROJECT_DIR, "build"),
    ]

    icon = os.path.join(PROJECT_DIR, "assets", "app_icon.ico")
    if os.path.exists(icon):
        command.append(f"--icon={icon}")

    hidden_imports = list(HIDDEN_IMPORTS)
    if sys.platform.startswith("win"):
        hidden_imports += WINDOWS_HIDDEN_IMPORTS
    for name in hidden_imports:
        command += ["--hidden-import", name]

    try:
        import ttkbootstrap  # noqa: F401

        command += ["--collect-all", "ttkbootstrap"]
    except ImportError:
        log("  Note: ttkbootstrap not installed, the build will use the standard ttk theme")

    # The --add-data separator is platform dependent.
    for name, destination in OPTIONAL_DATA:
        path = os.path.join(PROJECT_DIR, name)
        if os.path.exists(path):
            command += ["--add-data", f"{path}{os.pathsep}{destination}"]

    for name in EXCLUDES:
        command += ["--exclude-module", name]

    command.append(os.path.join(PROJECT_DIR, MAIN_SCRIPT))
    return command


def build_executable():
    """Run PyInstaller and return the path of the produced executable."""
    log(f"Building {APP_NAME} {__version__}...")
    command = build_command()
    try:
        result = subprocess.run(command, cwd=PROJECT_DIR, check=False, timeout=1800)
    except subprocess.TimeoutExpired:
        log("ERROR: build timed out (>30 minutes)")
        return None

    if result.returncode != 0:
        log(f"ERROR: PyInstaller exited with code {result.returncode}")
        return None

    suffix = ".exe" if sys.platform.startswith("win") else ""
    exe_path = os.path.join(PROJECT_DIR, "dist", f"{APP_NAME}{suffix}")
    if not os.path.exists(exe_path):
        log(f"ERROR: executable not found at {exe_path}")
        return None

    size_mb = os.path.getsize(exe_path) / (1024 * 1024)
    log(f"Executable created: {exe_path} ({size_mb:.1f} MB)")
    return exe_path


def create_distribution():
    """Prepare the dist/ folder for distribution."""
    log("Preparing the distribution folder...")
    dist_dir = os.path.join(PROJECT_DIR, "dist")
    os.makedirs(os.path.join(dist_dir, "logs"), exist_ok=True)

    example_config = os.path.join(PROJECT_DIR, "config.ini.example")
    if os.path.exists(example_config):
        shutil.copy2(example_config, os.path.join(dist_dir, "config.ini.example"))
        log("  config.ini.example copied to dist/")
    return True


def main():
    parser = argparse.ArgumentParser(description="Build the Iris executable")
    parser.add_argument("--clean", action="store_true", help="remove build/ and dist/ only")
    args = parser.parse_args()

    log("=" * 50)
    log(f"   {APP_TITLE.upper()} {__version__} - BUILD")
    log("=" * 50)

    if args.clean:
        clean_temp_directories()
        return 0

    if not check_prerequisites():
        log("BUILD FAILED: prerequisites not met")
        return 1

    clean_temp_directories()

    if not build_executable():
        log("BUILD FAILED: error during compilation")
        return 1

    create_distribution()
    log("=" * 50)
    log("   BUILD COMPLETED SUCCESSFULLY")
    log("=" * 50)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        log("Interrupted by the user")
        sys.exit(1)
