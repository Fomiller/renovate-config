{
  description = "renovate-config: Renovate presets and the promoted versions they read";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem
      (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          python = pkgs.python3.withPackages (p: [ p.pytest p.google-re2 p.pyyaml ]);
        in
        {
          checks.tests = pkgs.runCommand "renovate-config-tests"
            { nativeBuildInputs = [ python ]; }
            ''
              cp -r ${./.} src && chmod -R +w src && cd src
              pytest tests -q
              touch $out
            '';

          devShells.default = pkgs.mkShell { packages = [ python ]; };
        });
}
