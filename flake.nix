{
  description = "nixos-drift-detector — audit runtime state vs /run/current-system";

  inputs = {
    nixpkgs.url     = "github:NixOS/nixpkgs/nixos-24.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    let
      pyproject = builtins.fromTOML (builtins.readFile ./pyproject.toml);
    in
    flake-utils.lib.eachDefaultSystem (system:
      let pkgs = nixpkgs.legacyPackages.${system};
      in {
        packages.default = pkgs.python3Packages.buildPythonApplication {
          pname   = "nixos-drift-detector";
          version = pyproject.project.version;
          src     = ./.;
          format  = "pyproject";
          nativeBuildInputs    = with pkgs.python3Packages; [ setuptools wheel ];
          pythonImportsCheck   = [ "drift_detector" ];
          meta.mainProgram     = "nixos-drift-detect";
        };

        apps.default = {
          type    = "app";
          program = "${self.packages.${system}.default}/bin/nixos-drift-detect";
        };

        devShells.default = pkgs.mkShell {
          packages = [ pkgs.python3 pkgs.jq ];
        };
      }
    ) // {
      # NixOS VM tests only run on Linux
      checks.x86_64-linux.vm-test = nixpkgs.legacyPackages.x86_64-linux.nixosTest {
        name = "drift-detector";

        nodes.machine = { pkgs, ... }: {
          services.nginx.enable      = true;
          environment.systemPackages = [ self.packages.x86_64-linux.default ];
        };

        testScript = builtins.readFile ./nix/test.py;
      };
    };
}
