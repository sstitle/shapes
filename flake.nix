{
  description = "Flake with default shell and Python main.py execution";

  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs";

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        devShell = pkgs.mkShell {
          buildInputs = [ pkgs.python3 ];
        };

        packages = rec {
          default = pkgs.writeShellScriptBin "run-main" ''
            #!${pkgs.python3}/bin/python3
            exec python3 main.py
          '';
        };

        apps = rec {
          default = flake-utils.lib.mkApp {
            drv = self.packages.${system}.default;
          };
        };
      }
    );
}
