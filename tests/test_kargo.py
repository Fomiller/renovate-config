import yaml

from conftest import ROOT

VALUES = yaml.safe_load((ROOT / "argocd/overlays/prod/values.kargo.yaml").read_text())
PACKS = sorted(p.stem for p in (ROOT / "versions/nix-flakes").glob("*.yaml"))


def test_every_warehouse_has_a_version_file_and_back():
    assert sorted(w["name"] for w in VALUES["warehouses"]) == PACKS


def test_each_warehouse_writes_only_its_own_file():
    for w in VALUES["warehouses"]:
        assert w["gitRepos"] == [w["name"]]
        assert w["updatePaths"] == [{
            "path": f"versions/nix-flakes/{w['name']}.yaml",
            "rootRelative": True,
            "updates": [{"key": "version", "source": w["name"]}],
        }]


def test_each_git_source_sees_only_its_own_tags():
    """Every pack is tagged on one repo. Without the anchor a warehouse would
    see every pack's tags."""
    for g in VALUES["gitRepos"]:
        assert g["git"]["repoURL"] == "https://github.com/Fomiller/flake-hub.git"
        assert g["git"]["allowTags"] == f"^{g['name']}-"
        assert g["git"]["commitSelectionStrategy"] == "NewestTag"


def test_one_release_stage_promoted_by_hand():
    (stage,) = VALUES["stages"]
    assert stage["name"] == "release"
    assert sorted(stage["warehouses"]) == PACKS
    assert "autoPromotion" not in stage
    assert "argocd" not in stage
