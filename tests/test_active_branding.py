"""Red Team guard against obsolete branding on active public surfaces."""

from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ACTIVE_PUBLIC_FILES = (
    Path("README.md"),
    Path("streamlit_app.py"),
    Path("docs/architecture.md"),
)
PROHIBITED_PHRASES = (
    "Kaggle",
    "capstone",
    "Course concepts demonstrated",
)


def test_active_public_files_do_not_use_obsolete_branding() -> None:
    """Report every obsolete phrase remaining on the selected active surfaces."""

    violations: list[str] = []

    for relative_path in ACTIVE_PUBLIC_FILES:
        file_path = REPOSITORY_ROOT / relative_path
        lines = file_path.read_text(encoding="utf-8").splitlines()

        for line_number, line in enumerate(lines, start=1):
            casefolded_line = line.casefold()
            for phrase in PROHIBITED_PHRASES:
                if phrase.casefold() in casefolded_line:
                    violations.append(
                        f"{relative_path.as_posix()}:{line_number}: "
                        f"{phrase!r}: {line}"
                    )

    assert not violations, (
        "Obsolete active branding found:\n" + "\n".join(violations)
    )
