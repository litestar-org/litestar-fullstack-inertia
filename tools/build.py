#!/usr/bin/env python
"""Build frontend assets with configurable JavaScript executor.

This script builds frontend assets using a specified JavaScript package manager.
It's designed for use in Docker builds where caching layers are important.

Usage:
    python tools/build.py --executor bun
    python tools/build.py --executor npm
    python tools/build.py --executor deno
    python tools/build.py --executor yarn
    python tools/build.py --executor pnpm
"""
from __future__ import annotations

import argparse
import logging
import platform
import shutil
import subprocess
import sys
from typing import Literal

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("build")

Executor = Literal["bun", "npm", "deno", "yarn", "pnpm"]

EXECUTOR_COMMANDS: dict[Executor, dict[str, list[str]]] = {
    "bun": {
        "install": ["bun", "install", "--frozen-lockfile"],
        "build": ["bun", "run", "build"],
    },
    "npm": {
        "install": ["npm", "ci"],
        "build": ["npm", "run", "build"],
    },
    "deno": {
        "install": ["deno", "install"],
        "build": ["deno", "task", "build"],
    },
    "yarn": {
        "install": ["yarn", "install", "--frozen-lockfile"],
        "build": ["yarn", "build"],
    },
    "pnpm": {
        "install": ["pnpm", "install", "--frozen-lockfile"],
        "build": ["pnpm", "build"],
    },
}


def is_executable(cmd: str) -> bool:
    """Check if a command exists and is executable."""
    return shutil.which(cmd) is not None


def run_command(cmd: list[str], description: str) -> None:
    """Run a command and handle errors."""
    logger.info("%s: %s", description, " ".join(cmd))
    shell = platform.system() == "Windows"
    result = subprocess.run(cmd, shell=shell, check=False)
    if result.returncode != 0:
        logger.error("%s failed with exit code %d", description, result.returncode)
        sys.exit(result.returncode)


def build_assets(executor: Executor, *, install: bool = False, build: bool = True) -> None:
    """Build frontend assets using the specified executor.

    Args:
        executor: The JavaScript package manager to use.
        install: Whether to install dependencies first.
        build: Whether to build assets.
    """
    if not is_executable(executor):
        logger.error("%s is not installed or not in PATH", executor)
        sys.exit(1)

    commands = EXECUTOR_COMMANDS[executor]

    if install:
        run_command(commands["install"], f"Installing dependencies with {executor}")

    if build:
        run_command(commands["build"], f"Building assets with {executor}")

    logger.info("Build completed successfully")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build frontend assets with configurable JavaScript executor.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python tools/build.py --executor bun
    python tools/build.py --executor npm --install
    python tools/build.py --executor bun --no-build --install
        """,
    )
    parser.add_argument(
        "--executor",
        "-e",
        type=str,
        choices=["bun", "npm", "deno", "yarn", "pnpm"],
        default="bun",
        help="JavaScript package manager to use (default: bun)",
    )
    parser.add_argument(
        "--install",
        "-i",
        action="store_true",
        default=False,
        help="Install dependencies before building",
    )
    parser.add_argument(
        "--no-build",
        action="store_true",
        default=False,
        help="Skip the build step (only install)",
    )

    args = parser.parse_args()

    build_assets(
        executor=args.executor,
        install=args.install,
        build=not args.no_build,
    )


if __name__ == "__main__":
    main()
