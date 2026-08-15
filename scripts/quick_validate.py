#!/usr/bin/env python3
"""
Validate an Agent Skills folder before it gets packaged into a .skill file.

package_skill.py has always imported `validate_skill` from here, but this module
was never shipped with the repo — it was a sibling utility in whatever tree the
packaging script was originally lifted from. The result was a release workflow
that could not run at all: `ModuleNotFoundError: No module named 'quick_validate'`,
ten seconds into every tagged build.

Deliberately stdlib-only. The release workflow does no `pip install`, so pulling in
PyYAML here would trade one import error for another. The frontmatter block is a
small, flat key/value map, so a hand parser is honest rather than clever — but it
only accepts that shape, and says so plainly when it sees something else.

Contract expected by package_skill.py:
    validate_skill(path) -> (ok: bool, message: str)
"""
from pathlib import Path
import re
import sys

# Anthropic's published ceiling for the description field. A skill whose description
# is truncated at load time gets matched against a sentence that is not what the
# author wrote, so this is a hard failure rather than a warning.
MAX_DESCRIPTION = 1024
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _parse_frontmatter(text):
    """Return (dict, error). Only a flat `key: value` block between --- fences."""
    if not text.startswith("---"):
        return None, "SKILL.md does not open with a --- frontmatter fence"
    end = text.find("\n---", 3)
    if end == -1:
        return None, "frontmatter fence is never closed"
    body = text[3:end].strip("\n")
    meta = {}
    for line in body.split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[:1] in (" ", "\t"):
            return None, ("frontmatter contains an indented line — nested YAML is not "
                          "supported here, keep it to flat key: value pairs")
        if ":" not in line:
            return None, f"frontmatter line is not key: value → {line[:60]!r}"
        k, v = line.split(":", 1)
        meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta, None


def validate_skill(skill_path):
    skill_path = Path(skill_path)
    skill_md = skill_path / "SKILL.md"

    if not skill_md.exists():
        return False, f"SKILL.md not found in {skill_path}"

    try:
        text = skill_md.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        return False, f"SKILL.md is not valid UTF-8 ({e})"

    meta, err = _parse_frontmatter(text)
    if err:
        return False, err

    for field in ("name", "description"):
        if not meta.get(field):
            return False, f"frontmatter is missing a non-empty `{field}`"

    name = meta["name"]
    if not SLUG.match(name):
        return False, (f"`name` must be a lowercase hyphenated slug, got {name!r}")
    if name != skill_path.name:
        return False, (f"`name` is {name!r} but the folder is {skill_path.name!r} — "
                       "they must match or the packaged skill installs under the wrong id")

    desc = meta["description"]
    if len(desc) > MAX_DESCRIPTION:
        return False, (f"`description` is {len(desc)} chars, over the {MAX_DESCRIPTION} "
                       "limit — it would be truncated at load time")

    # Body after the frontmatter is what the model actually reads. An empty body
    # packages and installs cleanly while doing nothing, which is the worst outcome.
    if not text[text.find("\n---", 3) + 4:].strip():
        return False, "SKILL.md has frontmatter but no body content"

    extras = sum(1 for p in skill_path.rglob("*") if p.is_file() and p.name != "SKILL.md")
    return True, f"{name} — frontmatter valid, {extras} supporting file(s)"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: quick_validate.py <path/to/skill-folder>")
    ok, msg = validate_skill(sys.argv[1])
    print(("✅ " if ok else "❌ ") + msg)
    sys.exit(0 if ok else 1)
