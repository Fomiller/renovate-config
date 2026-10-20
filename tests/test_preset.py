"""Renovate runs these patterns through RE2. Python's re accepts things RE2
rejects, and that gap already shipped one broken preset."""

import json

import re2

from conftest import ROOT

DEFAULT = json.loads((ROOT / "default.json").read_text())
PRESET = json.loads((ROOT / "presets/nix-flakes/packs.json").read_text())
MANAGER = PRESET["customManagers"][0]
DATASOURCE = PRESET["customDatasources"]["flake-hub-pack"]
VERSIONING = MANAGER["versioningTemplate"].removeprefix("regex:")

FLAKE = """{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    golden-engine.url = "github:Fomiller/flake-hub?dir=golden-engine&ref=refs/tags/golden-engine-0.1.0";
    golden-argocd.url = "github:Fomiller/flake-hub?dir=golden-argocd&ref=refs/tags/golden-argocd-0.20.0";
  };
}
"""


def deps():
    """Named groups first, then each *Template overwrites its field, the way
    Renovate builds a dep."""
    out = []
    for pattern in MANAGER["matchStrings"]:
        for m in re2.finditer(pattern, FLAKE):
            dep = dict(m.groupdict())
            for field in ("packageName", "datasource", "versioning"):
                template = MANAGER.get(f"{field}Template")
                if template is not None:
                    dep[field] = template.replace("{{{depName}}}", dep["depName"])
            out.append(dep)
    return out


def test_every_pattern_compiles_under_re2():
    for pattern in MANAGER["matchStrings"] + [VERSIONING]:
        re2.compile(pattern)


def test_every_pin_is_matched_with_its_full_tag():
    assert sorted((d["depName"], d["currentValue"]) for d in deps()) == [
        ("golden-argocd", "golden-argocd-0.20.0"),
        ("golden-engine", "golden-engine-0.1.0"),
    ]


def test_package_name_is_the_pack_so_the_url_is_per_pack():
    for dep in deps():
        assert dep["packageName"] == dep["depName"]
        url = DATASOURCE["defaultRegistryUrlTemplate"].replace("{{packageName}}", dep["packageName"])
        assert url == f"https://raw.githubusercontent.com/Fomiller/renovate-config/main/versions/nix-flakes/{dep['depName']}.yaml"


def test_datasource_reads_the_version_file_fields():
    assert MANAGER["datasourceTemplate"] == "custom.flake-hub-pack"
    assert DATASOURCE["format"] == "yaml"
    transform = DATASOURCE["transformTemplates"][0]
    for field in ("sourceUrl", "dir", "version"):
        assert field in transform


def test_another_packs_tag_is_never_compatible():
    compat = lambda tag: re2.match(VERSIONING, tag).group("compatibility")
    assert compat("golden-argocd-0.20.0") == "golden-argocd"
    assert compat("golden-infra-9.9.9") != compat("golden-github-1.2.3")


def test_only_the_custom_regex_manager_runs():
    """Any other manager edits files the generator owns and fails drift."""
    assert DEFAULT["enabledManagers"] == ["custom.regex"]
    assert DEFAULT["nix"]["enabled"] is False


def test_default_extends_the_preset_by_full_path():
    """Renovate has no directory default: //presets/nix-flakes would look for
    presets/nix-flakes.json."""
    assert DEFAULT["extends"] == ["github>Fomiller/renovate-config//presets/nix-flakes/packs"]


def test_regenerate_commits_do_not_stop_renovate_updating_its_pr():
    assert DEFAULT["gitIgnoredAuthors"] == ["41898282+github-actions[bot]@users.noreply.github.com"]


def test_one_open_pr_per_pack_always_fits():
    """Kargo promotion is the gate. A concurrent limit below the pack count
    would hold a promoted bump back behind the others for no reason."""
    packs = list((ROOT / "versions/nix-flakes").glob("*.yaml"))
    assert DEFAULT["prConcurrentLimit"] >= len(packs)
