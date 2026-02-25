"""Complete build script for DadoBounce."""

import argparse
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

APP_EXE = "dadobounce.exe"
ENTRY_SCRIPT = "main.py"
DATA_FILE = "dado.gif"


def pretty_path(path: Path | str) -> str:
    """Return a cleaner path for console output."""
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(resolved)


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def get_version() -> str:
    """Read version from pyproject.toml."""
    try:
        with open("pyproject.toml", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("version = "):
                    return line.split('"')[1]
    except Exception as e:
        print(f"⚠️  Could not read version from pyproject.toml: {e}")
    return "0.0.0"


def build_app(mode: str):
    """Build the Python application using Nuitka."""
    print_section("Building DadoBounce")

    if not Path(DATA_FILE).exists():
        print(f"❌ {DATA_FILE} not found.")
        return False

    # Clean previous builds
    for folder in ["build", "dist", "main.build", "main.dist", "main.onefile-build"]:
        path = Path(folder)
        if path.exists():
            print(f"Cleaning {folder}/...")
            shutil.rmtree(path)

    dist_dir = Path("dist")
    dist_dir.mkdir(exist_ok=True)

    cmd = [
        "uv",
        "run",
        "--group",
        "dev",
        "python",
        "-m",
        "nuitka",
        "--windows-console-mode=disable",
        "--assume-yes-for-downloads",
        f"--include-data-files={DATA_FILE}={DATA_FILE}",
        "--output-dir=dist",
        f"--output-filename={APP_EXE}",
        "--remove-output",
    ]

    if mode == "standalone":
        cmd.append("--standalone")
    elif mode == "onefile":
        cmd.append("--onefile")
    else:
        print(f"❌ Unsupported build mode: {mode}")
        return False

    cmd.append(ENTRY_SCRIPT)

    print(f"Running Nuitka ({mode})...")
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print("❌ Build failed!")
        return False

    exe_path = dist_dir / APP_EXE
    if not exe_path.exists():
        for candidate in sorted(dist_dir.glob("*.dist")):
            preferred = candidate / APP_EXE
            if preferred.exists():
                exe_path = preferred
                break
            fallback = sorted(candidate.glob("*.exe"))
            if fallback:
                exe_path = fallback[0]
                break

    if not exe_path.exists():
        print("❌ Build completed but executable not found in dist/")
        return False

    if mode == "standalone":
        runtime_dirs = sorted(dist_dir.glob("*.dist"))
        if not runtime_dirs:
            print("❌ Standalone runtime directory not found in dist/")
            return False

    size_mb = exe_path.stat().st_size / (1024 * 1024)
    print(f"✓ Build successful! ({size_mb:.1f} MB)")
    return True


def create_zip_release():
    """Create a release ZIP."""
    print_section("Creating Release ZIP")

    dist_dir = Path("dist")
    if not dist_dir.exists():
        print("❌ Dist directory not found!")
        return False

    version = get_version()
    zip_name = f"DadoBounce-v{version}"
    print(f"Creating {zip_name}.zip...")

    runtime_dir = dist_dir / "main.dist"
    if not runtime_dir.exists():
        runtime_candidates = sorted(dist_dir.glob("*.dist"))
        if runtime_candidates:
            runtime_dir = runtime_candidates[0]
    onefile_exe = dist_dir / APP_EXE

    zip_path = Path(f"{zip_name}.zip")
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        if runtime_dir.exists() and runtime_dir.is_dir():
            print(f"Adding runtime folder to ZIP: {pretty_path(runtime_dir)}")
            for path in runtime_dir.rglob("*"):
                if path.is_file():
                    archive.write(path, path.relative_to(runtime_dir))
        elif onefile_exe.exists():
            print(f"Adding onefile exe to ZIP: {pretty_path(onefile_exe)}")
            archive.write(onefile_exe, APP_EXE)
        else:
            print("⚠️  No build artifacts found in dist/")
            return False

    if zip_path.exists():
        size_mb = zip_path.stat().st_size / (1024 * 1024)
        print(f"✓ Release ZIP created: {pretty_path(zip_path)} ({size_mb:.1f} MB)")
        return True

    return False


def create_installer():
    """Create installer using Inno Setup."""
    print_section("Creating Installer")

    iss_file = Path("installer.iss")
    if not iss_file.exists():
        print("❌ installer.iss not found!")
        return False

    print("Running Inno Setup compiler...")
    result = subprocess.run(["iscc", str(iss_file)])

    if result.returncode != 0:
        print("❌ Installer creation failed!")
        return False

    output_dir = Path("installer_output")
    if output_dir.exists():
        installers = list(output_dir.glob("*.exe"))
        if installers:
            installer = max(installers, key=lambda p: p.stat().st_mtime)
            size_mb = installer.stat().st_size / (1024 * 1024)
            print(f"✓ Installer created: {pretty_path(installer)} ({size_mb:.1f} MB)")
            return True

    print("⚠️  Installer may have been created but could not be verified")
    return False


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Build DadoBounce artifacts")
    parser.add_argument(
        "--mode",
        choices=["standalone", "onefile"],
        default="onefile",
        help="Python packaging mode for Nuitka (default: onefile)",
    )
    parser.add_argument(
        "--py",
        action="store_true",
        help="Build Python app",
    )
    parser.add_argument(
        "--inno",
        action="store_true",
        help="Build Inno Setup installer",
    )
    return parser.parse_args()


def main():
    """Main build process."""
    args = parse_args()

    print_section("DadoBounce - Build Script")

    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    print(f"Working directory: {script_dir}")

    selected = []
    if args.py:
        selected.append("py")
    if args.inno:
        selected.append("inno")

    if not selected:
        selected = ["py", "inno"]

    success = True

    # Step 1: Build application
    if "py" in selected:
        if not build_app(args.mode):
            print("\n❌ Build process stopped due to build failure.")
            sys.exit(1)

    # Step 2: Create release ZIP
    if "py" in selected:
        create_zip_release()

    # Step 3: Create installer (optional)
    if "inno" in selected:
        if not create_installer():
            success = False

    # Summary
    print_section("Build Summary")

    dist_dir = Path("dist")
    if dist_dir.exists():
        print("Built files in dist/:")
        for item in sorted(dist_dir.iterdir()):
            if item.is_file():
                size = item.stat().st_size
                if size > 1024 * 1024:
                    size_str = f"{size / (1024 * 1024):.1f} MB"
                else:
                    size_str = f"{size / 1024:.1f} KB"
                print(f"  • {item.name} ({size_str})")
            elif item.is_dir():
                print(f"  • {item.name}/")

    print("\n" + "=" * 70)
    if success:
        print("✓ Build process completed successfully!")
    else:
        print("⚠️  Build completed with warnings.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Build cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
