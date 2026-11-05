#!/usr/bin/env python3
"""Read-only checks for frontend module directory capacity and source size."""

from __future__ import annotations

import argparse
import fnmatch
import os
from collections import defaultdict
from pathlib import Path


TARGET_FILES = 8
MAX_FILES = 10
MAX_VUE_LINES = 250
MAX_SOURCE_LINES = 300
SOURCE_EXTENSIONS = {
    '.vue', '.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs', '.mts', '.cts',
    '.css', '.scss', '.sass', '.less',
}
IGNORED_DIRECTORIES = {
    '.git', 'node_modules', 'dist', 'build', 'coverage', '__pycache__', '.next', '.nuxt',
}


def excluded(path: Path, root: Path, patterns: list[str]) -> bool:
    relative = path.relative_to(root).as_posix()
    return any(fnmatch.fnmatchcase(relative, pattern) for pattern in patterns)


def collect_sources(root: Path, patterns: list[str]) -> list[Path]:
    sources: list[Path] = []

    def fail_walk(error: OSError) -> None:
        raise error

    for directory, directories, names in os.walk(root, onerror=fail_walk):
        folder = Path(directory)
        directories[:] = sorted(
            name for name in directories
            if name not in IGNORED_DIRECTORIES
            and not (folder / name).is_symlink()
            and not excluded(folder / name, root, patterns)
        )
        for name in sorted(names):
            source = folder / name
            if source.suffix.lower() in SOURCE_EXTENSIONS and not excluded(source, root, patterns):
                sources.append(source)
    return sources


def audit(root: Path, patterns: list[str]) -> tuple[list[str], list[str], int, int]:
    sources = collect_sources(root, patterns)
    folders: dict[Path, list[Path]] = defaultdict(list)
    errors: list[str] = []
    warnings: list[str] = []
    for source in sources:
        folders[source.parent].append(source)
        lines = len(source.read_text(encoding='utf-8').splitlines())
        limit = MAX_VUE_LINES if source.suffix.lower() == '.vue' else MAX_SOURCE_LINES
        if lines > limit:
            errors.append(f'{source.relative_to(root)}: {lines} lines > {limit}')

    for directory, members in sorted(folders.items()):
        relative = directory.relative_to(root)
        if len(members) > MAX_FILES:
            errors.append(f'{relative}/: {len(members)} direct source files > {MAX_FILES}')
        elif len(members) > TARGET_FILES:
            warnings.append(
                f'{relative}/: {len(members)} direct source files; review ownership '
                f'(target {TARGET_FILES}, maximum {MAX_FILES})'
            )
    return errors, warnings, len(sources), len(folders)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('module', type=Path, help='Business module directory to inspect recursively')
    parser.add_argument(
        '--exclude', action='append', default=[], metavar='GLOB',
        help='Exclude a confirmed generated path relative to the module; repeat as needed',
    )
    args = parser.parse_args()
    root = args.module.resolve()
    if not root.is_dir():
        parser.error(f'Not a directory: {root}')
    try:
        errors, warnings, files, folders = audit(root, args.exclude)
    except (OSError, UnicodeError) as error:
        print(f'ERROR: Cannot inspect module: {error}')
        return 2
    for pattern in args.exclude:
        print(f'EXCLUDE: {pattern}')
    for warning in warnings:
        print(f'REVIEW: {warning}')
    for error in errors:
        print(f'ERROR: {error}')
    print(f'Scanned {files} source files in {folders} directories: '
          f'{len(errors)} violations, {len(warnings)} ownership reviews.')
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
