#!/usr/bin/env python3
"""Build Go binaries for multiple platforms with checksums."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Platform configurations for cross-compilation
PLATFORMS = [
    {"goos": "windows", "goarch": "amd64", "ext": ".exe"},
    {"goos": "windows", "goarch": "arm64", "ext": ".exe"},
    {"goos": "linux", "goarch": "amd64", "ext": ""},
    {"goos": "linux", "goarch": "arm64", "ext": ""},
    {"goos": "darwin", "goarch": "amd64", "ext": ""},
    {"goos": "darwin", "goarch": "arm64", "ext": ""},
]


def calculate_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with file_path.open("rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_binary_name(module_path: Path | None = None) -> str:
    """Get the binary name from go.mod or use directory name."""
    if module_path is None:
        module_path = Path.cwd()

    go_mod = module_path / "go.mod"
    if go_mod.exists():
        content = go_mod.read_text(encoding="utf-8")
        for line in content.splitlines():
            if line.startswith("module "):
                # Extract last component of module path
                module_name = line.split()[-1].strip()
                return module_name.split("/")[-1]

    # Fallback to directory name
    return module_path.name


def build_binary(
    goos: str,
    goarch: str,
    output_dir: Path,
    binary_name: str,
    ext: str,
    ldflags: str = "",
    version: str = "",
) -> Path | None:
    """Build a Go binary for a specific platform."""
    output_name = f"{binary_name}-{goos}-{goarch}{ext}"
    output_path = output_dir / output_name

    env = os.environ.copy()
    env["GOOS"] = goos
    env["GOARCH"] = goarch
    env["CGO_ENABLED"] = "0"  # Static binaries

    # Build ldflags
    ldflags_parts = ["-s", "-w"]  # Strip debug info and symbol table
    if version:
        # Try multiple common version variable locations
        ldflags_parts.append(f"-X main.version={version}")
        # Some projects use package-level variables
        if binary_name:
            ldflags_parts.append(f"-X {binary_name}.version={version}")
    if ldflags:
        ldflags_parts.append(ldflags)
    ldflags_str = " ".join(ldflags_parts)

    cmd = [
        "go",
        "build",
        "-v",
        "-ldflags",
        ldflags_str,
        "-o",
        str(output_path),
    ]

    print(f"Building {output_name}...")
    print(f"  Command: {' '.join(cmd)}")
    print(f"  GOOS={goos} GOARCH={goarch}")

    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            print(f"❌ Build failed for {goos}/{goarch}")
            print(f"  stdout: {result.stdout}")
            print(f"  stderr: {result.stderr}")
            return None

        if not output_path.exists():
            print(f"❌ Output file not created: {output_path}")
            return None

        file_size = output_path.stat().st_size / (1024 * 1024)  # MB
        print(f"✅ Built {output_name} ({file_size:.2f} MB)")
        return output_path

    except Exception as e:
        print(f"❌ Exception building {goos}/{goarch}: {e}")
        return None


def create_checksum_file(binary_path: Path) -> Path:
    """Create a SHA256 checksum file for the binary."""
    checksum = calculate_checksum(binary_path)
    checksum_path = binary_path.with_suffix(binary_path.suffix + ".sha256")

    # Format: checksum  filename (two spaces, like sha256sum command)
    checksum_content = f"{checksum}  {binary_path.name}\n"
    checksum_path.write_text(checksum_content, encoding="utf-8")

    print(f"  Checksum: {checksum}")
    return checksum_path


def build_all_platforms(
    output_dir: Path,
    binary_name: str,
    ldflags: str = "",
    version: str = "",
    platforms: list[dict] | None = None,
) -> dict[str, dict[str, str]]:
    """Build binaries for all platforms and generate checksums."""
    if platforms is None:
        platforms = PLATFORMS

    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}
    successful_builds = []
    failed_builds = []

    for platform_config in platforms:
        goos = platform_config["goos"]
        goarch = platform_config["goarch"]
        ext = platform_config["ext"]

        binary_path = build_binary(
            goos=goos,
            goarch=goarch,
            output_dir=output_dir,
            binary_name=binary_name,
            ext=ext,
            ldflags=ldflags,
            version=version,
        )

        if binary_path:
            checksum_path = create_checksum_file(binary_path)
            platform_key = f"{goos}-{goarch}"
            results[platform_key] = {
                "binary": str(binary_path.name),
                "checksum": str(checksum_path.name),
                "size": binary_path.stat().st_size,
            }
            successful_builds.append(platform_key)
        else:
            failed_builds.append(f"{goos}-{goarch}")

    # Write build manifest
    manifest_path = output_dir / "build-manifest.json"
    manifest_data = {
        "binary_name": binary_name,
        "version": version or "unknown",
        "platforms": results,
        "successful_builds": successful_builds,
        "failed_builds": failed_builds,
        "total_platforms": len(platforms),
        "successful_count": len(successful_builds),
        "failed_count": len(failed_builds),
    }
    manifest_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
    print(f"\n📋 Build manifest: {manifest_path}")

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"Build Summary: {len(successful_builds)}/{len(platforms)} successful")
    print(f"{'=' * 60}")
    if successful_builds:
        print("✅ Successful builds:")
        for platform in successful_builds:
            print(f"  - {platform}")
    if failed_builds:
        print("❌ Failed builds:")
        for platform in failed_builds:
            print(f"  - {platform}")
    print(f"{'=' * 60}\n")

    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build Go binaries for multiple platforms with checksums"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("dist"),
        help="Output directory for binaries",
    )
    parser.add_argument(
        "--binary-name",
        type=str,
        help="Binary name (auto-detected from go.mod if not provided)",
    )
    parser.add_argument(
        "--ldflags",
        type=str,
        default="",
        help="Additional ldflags for go build",
    )
    parser.add_argument(
        "--version",
        type=str,
        default="",
        help="Version string to embed in binary",
    )
    parser.add_argument(
        "--platforms",
        type=str,
        help="Comma-separated list of platforms (e.g., 'windows-amd64,linux-amd64')",
    )

    args = parser.parse_args()

    # Check if Go is available
    if not shutil.which("go"):
        print("❌ Go is not installed or not in PATH", file=sys.stderr)
        return 1

    # Check if go.mod exists
    if not Path("go.mod").exists():
        print("❌ go.mod not found in current directory", file=sys.stderr)
        return 1

    # Get binary name
    binary_name = args.binary_name or get_binary_name()
    print(f"Binary name: {binary_name}")

    # Parse platforms if specified
    platforms = PLATFORMS
    if args.platforms:
        platform_list = [p.strip() for p in args.platforms.split(",")]
        platforms = []
        for platform_str in platform_list:
            parts = platform_str.split("-")
            if len(parts) != 2:
                print(
                    f"⚠️  Invalid platform format: {platform_str}",
                    file=sys.stderr,
                )
                continue
            goos, goarch = parts
            ext = ".exe" if goos == "windows" else ""
            platforms.append({"goos": goos, "goarch": goarch, "ext": ext})

    # Download dependencies first
    print("Downloading Go dependencies...")
    result = subprocess.run(["go", "mod", "download"], check=False, capture_output=True, text=True)
    if result.returncode != 0:
        print(
            f"❌ Failed to download dependencies: {result.stderr}",
            file=sys.stderr,
        )
        return 1

    # Build all platforms
    results = build_all_platforms(
        output_dir=args.output_dir,
        binary_name=binary_name,
        ldflags=args.ldflags,
        version=args.version,
        platforms=platforms,
    )

    if not results:
        print("❌ No binaries were built successfully", file=sys.stderr)
        return 1

    print(f"✅ Binaries and checksums written to: {args.output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
