import json

import re2
import yaml

from conftest import ROOT

PACKS = sorted(p.stem for p in (ROOT / "versions/nix-flakes").glob("*.yaml"))
PRESET = json.loads((ROOT / "presets/nix-flakes/packs.json").read_text())
VERSIONING = PRESET["customManagers"][0]["versioningTemplate"].removeprefix("regex:")


def load(pack):
    return yaml.safe_load((ROOT / f"versions/nix-flakes/{pack}.yaml").read_text())


def test_every_pack_has_a_version_file():
    assert PACKS == [
        "golden-argocd", "golden-base", "golden-docs", "golden-engine",
        "golden-github", "golden-infra", "golden-service",
    ]


def test_every_version_file_has_the_fields_the_transform_reads():
    for pack in PACKS:
        assert load(pack) == {
            "repo": "github.com/Fomiller/flake-hub",
            "dir": pack,
            "sourceUrl": "https://github.com/Fomiller/flake-hub",
            "version": load(pack)["version"],
        }


def test_version_file_tag_matches_its_file_name():
    for pack in PACKS:
        m = re2.match(VERSIONING, load(pack)["version"])
        assert m is not None, pack
        assert m.group("compatibility") == pack


def test_every_version_file_says_kargo_owns_it():
    for pack in PACKS:
        text = (ROOT / f"versions/nix-flakes/{pack}.yaml").read_text()
        assert "Kargo writes `version`" in text.splitlines()[0]
