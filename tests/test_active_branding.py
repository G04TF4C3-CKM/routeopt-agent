"""Red Team guard against obsolete course artifacts in tracked files."""

from pathlib import Path
import subprocess


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
THIS_TEST = Path("tests/test_active_branding.py")
EXCLUDED_TOP_LEVEL_DIRECTORIES = frozenset({"archive", "legacy_audit"})
TEXT_SUFFIXES = frozenset(
    {
        ".md",
        ".py",
        ".txt",
        ".toml",
        ".yaml",
        ".yml",
        ".json",
        ".rst",
    }
)
PROHIBITED_PHRASES = (
    "Kaggle",
    "capstone",
    "5-Day AI Agents",
    "5-Day Vibe Coding",
    "Vibe Coding Course",
    "Agents for Business",
    "capstone-ready",
    "Course concepts demonstrated",
    "Antigravity",
    "agy CLI",
    "Kaggle judge",
    "Kaggle submission",
)
PROHIBITED_PATH_FRAGMENTS = (
    "kaggle",
    "capstone",
    "agy_capstone",
)


def _tracked_paths() -> list[Path]:
    """Return repository-relative paths reported by ``git ls-files -z``."""

    result = subprocess.run(
        ("git", "ls-files", "-z"),
        cwd=REPOSITORY_ROOT,
        check=True,
        stdout=subprocess.PIPE,
    )
    return [
        Path(raw_path.decode("utf-8"))
        for raw_path in result.stdout.split(b"\0")
        if raw_path
    ]


def _is_excluded(relative_path: Path) -> bool:
    """Return whether a tracked path is outside the active branding guard."""

    if relative_path == THIS_TEST:
        return True
    return bool(
        relative_path.parts
        and relative_path.parts[0].casefold() in EXCLUDED_TOP_LEVEL_DIRECTORIES
    )


def _read_tracked_text(relative_path: Path) -> str | None:
    """Decode supported or extensionless tracked text, skipping binary data."""

    if relative_path.suffix and relative_path.suffix.casefold() not in TEXT_SUFFIXES:
        return None

    raw_content = (REPOSITORY_ROOT / relative_path).read_bytes()
    if b"\0" in raw_content:
        return None

    try:
        return raw_content.decode("utf-8")
    except UnicodeDecodeError:
        return None


def test_tracked_repository_has_no_obsolete_course_artifacts() -> None:
    """Aggregate obsolete content and path names across active tracked text."""

    violations: list[str] = []

    for relative_path in _tracked_paths():
        if _is_excluded(relative_path):
            continue

        display_path = relative_path.as_posix()
        casefolded_path = display_path.casefold()
        for fragment in PROHIBITED_PATH_FRAGMENTS:
            if fragment.casefold() in casefolded_path:
                violations.append(
                    f"{display_path}: prohibited path fragment {fragment!r}"
                )

        text = _read_tracked_text(relative_path)
        if text is None:
            continue

        for line_number, line in enumerate(text.splitlines(), start=1):
            casefolded_line = line.casefold()
            for phrase in PROHIBITED_PHRASES:
                if phrase.casefold() in casefolded_line:
                    violations.append(
                        f"{display_path}:{line_number}: {phrase!r}: {line}"
                    )

    assert not violations, (
        "Obsolete course artifacts found:\n" + "\n".join(violations)
    )
