import re
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).parents[1]
SKILL_DIR = ROOT / ".agents" / "skills" / "setup-git-ci-skills"
INITIALIZER = SKILL_DIR / "SKILL.md"
SEED = SKILL_DIR / "project-skill.md"
README = ROOT / "README.md"
DELIVERED = (INITIALIZER, SEED, README)


def metadata(path):
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) != 3 or parts[0].strip():
        raise AssertionError(f"invalid frontmatter delimiters: {path}")
    entries = {}
    for line in parts[1].splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"([a-z][a-z0-9-]*):\s*(.+)", line)
        if not match or match.group(1) in entries:
            raise AssertionError(f"invalid frontmatter entry: {path}: {line}")
        entries[match.group(1)] = match.group(2).strip().strip('"')
    return entries


class SetupGitCiSkillsTest(unittest.TestCase):
    def test_metadata_subset(self):
        initializer = metadata(INITIALIZER)
        seed = metadata(SEED)

        self.assertEqual(initializer["name"], "setup-git-ci-skills")
        self.assertTrue(initializer["description"])
        self.assertEqual(initializer["disable-model-invocation"], "true")
        self.assertEqual(seed["name"], "project-git-ci")
        self.assertRegex(seed["description"], r"^Use when ")
        self.assertNotIn("disable-model-invocation", seed)

    def test_local_markdown_links_resolve(self):
        links = []
        for path in DELIVERED:
            text = path.read_text(encoding="utf-8")
            for target in re.findall(r"(?<!!)\[[^]]*\]\(([^)]+)\)", text):
                target = target.strip().split(maxsplit=1)[0].strip("<>")
                parsed = urlsplit(target)
                if parsed.scheme or parsed.netloc or target.startswith("#"):
                    continue
                self.assertFalse(
                    target.startswith("/"), f"absolute link in {path}: {target}"
                )
                resolved = path.parent / unquote(parsed.path)
                self.assertTrue(resolved.exists(), f"broken link in {path}: {target}")
                links.append((path, target))
        self.assertIn((README, ".agents/skills/setup-git-ci-skills/SKILL.md"), links)
        self.assertIn((INITIALIZER, "./project-skill.md"), links)

    def test_delivered_files_have_no_machine_paths_or_credential_urls(self):
        for path in DELIVERED:
            text = path.read_text(encoding="utf-8")
            self.assertNotRegex(text, r"(?:^|[\s`'(\"])/(?:home|Users|tmp|var|opt)/")
            self.assertNotRegex(text, r"https?://[^\s/@:]+:[^\s/@]+@")

    def test_initializer_structurally_covers_contracts(self):
        text = INITIALIZER.read_text(encoding="utf-8").lower()
        required = (
            "complete proposed diff",
            "explicit approval",
            "unchanged rerun",
            "upgrade",
            "removal",
            "source recovery",
            "approved internal jobs",
            "empty or a capability is unsupported",
            "concurrent edits",
            "partial failure",
            "before each write",
            "prompt instructions are neither a deterministic installer nor proof of runtime isolation",
            "names and matching paths do not prove ownership",
            "sanitize remote urls",
        )
        self.assertEqual([], [phrase for phrase in required if phrase not in text])

    def test_seed_preserves_unknown_security_and_recovery_gates(self):
        text = SEED.read_text(encoding="utf-8").lower()
        for heading in (
            "ownership and publication",
            "verification",
            "ci trust",
            "source recovery",
        ):
            self.assertIn(f"## {heading}", text)
        required = (
            "unsupported or unknown",
            "safe next gate",
            "secrets",
            "userinfo",
            "do not delete",
        )
        self.assertEqual([], [phrase for phrase in required if phrase not in text])


if __name__ == "__main__":
    unittest.main()
