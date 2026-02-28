"""
Build script for MedusaAbsolute.

Usage:
    uv run python scripts/build.py
    uv run python scripts/build.py --onedir
    uv run python scripts/build.py --console
"""

import os
import subprocess
import sys
import platform
import argparse
import sysconfig
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MAIN_SCRIPT = PROJECT_ROOT / "main.py"
APP_NAME = "MedusaAbsolute"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"


def find_binaries():
    """Find platform-specific binaries that PyInstaller misses."""
    binaries = []
    system = platform.system()

    if system == "Windows":
        # PyInstaller + uv часто не находит SSL DLL из uv-шного Python
        # Ищем в нескольких местах
        search_dirs = set()

        # stdlib DLLs dir
        stdlib_dir = sysconfig.get_path("stdlib")
        if stdlib_dir:
            search_dirs.add(Path(stdlib_dir).parent / "DLLs")

        # Рядом с интерпретатором
        exe_dir = Path(sys.executable).parent
        search_dirs.add(exe_dir)
        search_dirs.add(exe_dir.parent / "DLLs")

        # uv python dir (через sys.base_prefix)
        base = Path(sys.base_prefix)
        search_dirs.add(base / "DLLs")

        needed_dlls = [
            "libssl-3-x64.dll",
            "libcrypto-3-x64.dll",
            "_ssl.pyd",
        ]

        for dll_name in needed_dlls:
            for search_dir in search_dirs:
                dll_path = search_dir / dll_name
                if dll_path.exists():
                    binaries.append((str(dll_path), "."))
                    print(f"  Found: {dll_path}")
                    break
            else:
                print(f"  WARNING: {dll_name} not found!")

    return binaries


def get_platform_args():
    """Platform-specific PyInstaller arguments."""
    system = platform.system()
    args = []

    if system == "Windows":
        args.append("--icon=NONE")  # TODO: добавить иконку .ico
    elif system == "Darwin":
        args.append("--icon=NONE")  # TODO: добавить иконку .icns
        args.append("--osx-bundle-identifier=com.medusaabsolute.app")
    elif system == "Linux":
        pass  # TODO: добавить .desktop файл, иконку

    return args


def kill_running_exe():
    """Kill the running exe if it exists (Windows only)."""
    if platform.system() != "Windows":
        return
    exe_path = DIST_DIR / f"{APP_NAME}.exe"
    if not exe_path.exists():
        return
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", f"{APP_NAME}.exe"],
            capture_output=True,
        )
        print(f"  Killed running {APP_NAME}.exe")
    except Exception:
        pass


def build(onefile=True, console=False):
    kill_running_exe()

    print("Collecting binaries...")
    binaries = find_binaries()

    cmd = [
        sys.executable, "-m", "PyInstaller",
        str(MAIN_SCRIPT),
        f"--name={APP_NAME}",
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR}",
        "--clean",
        "--noconfirm",
    ]

    if onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")

    if not console:
        cmd.append("--windowed")
    else:
        cmd.append("--console")

    # Hidden imports для yt-dlp и PySide6
    hidden = [
        "yt_dlp",
        "requests",
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
    ]
    for h in hidden:
        cmd.extend(["--hidden-import", h])

    for src, dst in binaries:
        cmd.extend(["--add-binary", f"{src}{os.pathsep}{dst}"])

    cmd.extend(get_platform_args())

    print(f"\nBuilding {APP_NAME} for {platform.system()}...")
    print(f"Mode: {'onefile' if onefile else 'onedir'}, Console: {console}")
    print(f"Command: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd=PROJECT_ROOT)

    if result.returncode == 0:
        print(f"\nBuild successful! Output: {DIST_DIR}")
    else:
        print(f"\nBuild failed with code {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser(description=f"Build {APP_NAME} executable")
    parser.add_argument(
        "--onedir", action="store_true",
        help="Build as directory instead of single file (faster startup)"
    )
    parser.add_argument(
        "--console", action="store_true",
        help="Keep console window visible (useful for debugging)"
    )
    args = parser.parse_args()

    build(onefile=not args.onedir, console=args.console)


if __name__ == "__main__":
    main()
