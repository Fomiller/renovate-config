# renovate-config

Shared Renovate config for Fomiller repos. It pins each repo's flake-hub packs
to a version that someone has promoted.

## How a release flows

- A pack is tagged in flake-hub, for example `golden-base-0.6.0`.
- Kargo sees the tag and creates freight in that pack's warehouse.
- Someone promotes the freight to the `release` stage.
- The promotion commits the tag to `versions/nix-flakes/<pack>.yaml` on `main`.
- Renovate reads that file and opens a PR in each consumer repo.

Nothing reaches a consumer until the promotion.

## Promote a pack

```sh
kargo promote --project renovate-config --stage release --freight <id>
```

The Kargo UI does the same thing.

## Add a pack

- Add `versions/nix-flakes/<pack>.yaml` with `version` and the other keys from
  an existing file.
- In `argocd/overlays/prod/values.kargo.yaml`, add an entry named `<pack>` to
  `gitRepos` and `warehouses`.
- Add the pack to the `release` stage's `warehouses`.

The tests fail if the version files and warehouses do not match.

## Why only `custom.regex` runs

`default.json` sets `enabledManagers` to `custom.regex`. Any other manager
would edit files the generator owns, and the drift check would fail. The Nix
manager is off for the same reason.

## Why `version` is the full tag

The pins in `flake.nix` use `ref=refs/tags/<pack>-<x.y.z>`. Storing the whole
tag lets Renovate write it back without rebuilding the name.

## Validate locally

```sh
nix flake check
npx --yes --package renovate@44.171.8 -- renovate-config-validator --strict default.json presets/nix-flakes/packs.json
```
