import re
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).parents[1]
SKILL_DIR = ROOT / ".agents" / "skills" / "setup-git-ci-skills"
INITIALIZER = SKILL_DIR / "SKILL.md"
SEED = SKILL_DIR / "project-skill.md"
README = ROOT / "README.md"
ADR = ROOT / "docs" / "adr" / "0001-logical-node-identities-and-public-private-split.md"
DELIVERED = (INITIALIZER, SEED, README, ADR)


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
        self.assertEqual(
            initializer["description"],
            "Set up or maintain project-local Git and CI guidance.",
        )
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
        self.assertIn((README, ".agents/skills/setup-git-ci-skills/"), links)
        self.assertIn((INITIALIZER, "./project-skill.md"), links)

    def test_delivered_files_have_no_machine_paths_or_credential_urls(self):
        for path in DELIVERED:
            text = path.read_text(encoding="utf-8")
            self.assertNotRegex(text, r"(?:^|[\s`'(\"])/(?:home|Users|tmp|var|opt)/")
            self.assertNotRegex(text, r"https?://[^\s/@:]+:[^\s/@]+@")

    def test_initializer_structurally_covers_workflow(self):
        text = INITIALIZER.read_text(encoding="utf-8").lower()
        required = (
            "if both exist",
            "if neither exists",
            "ask the user which file",
            "complete proposed diff",
            "full diff and base revision",
            "before each write",
            "head` still equals the approved base revision",
            "unchanged rerun performs no writes regardless of missing provenance",
            "before forming an upgrade or removal diff",
            "multiple unresolved current records stop",
            "explicit supersedes chain",
            "repo-relative target path",
            "full-file sha-256 digest",
            "exact pointer line and containing heading",
            "link to the approved diff",
            "exact post-write provenance tracker comment or update",
            "tracker publication requires explicit permission",
            "workflow changes",
            "previous record it supersedes",
            "removal, record a tombstone",
            "tracker update fails",
            "do not claim success",
            "writes are individual, not atomic",
            "prompt instructions are neither a deterministic installer nor proof of runtime isolation",
        )
        self.assertEqual([], [phrase for phrase in required if phrase not in text])

    def test_seed_structurally_covers_policy(self):
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
            "issue-owned branch",
            "approved internal jobs",
            "fabric validation alone",
            "retained backups from live mirrors",
            "do not delete",
        )
        self.assertEqual([], [phrase for phrase in required if phrase not in text])


if __name__ == "__main__":
    unittest.main()
