{
  description = "NMLinux — Network Manager for Linux";

  inputs = {
    nixpkgs.url     = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs   = nixpkgs.legacyPackages.${system};
        python = pkgs.python313;

        nmlinux = python.pkgs.buildPythonApplication {
          pname   = "nmlinux";
          version = "0.1.0";
          src     = ./.;
          format  = "pyproject";

          nativeBuildInputs = [ python.pkgs.hatchling ];

          propagatedBuildInputs = with python.pkgs; [
            pyside6
            dnspython
            paramiko
            netaddr
          ];
        };
      in {
        packages.default = nmlinux;

        apps.default = {
          type    = "app";
          program = "${nmlinux}/bin/nmlinux";
        };

        devShells.default = pkgs.mkShell {
          packages = [
            (python.withPackages (ps: with ps; [
              pyside6 dnspython paramiko netaddr
            ]))
          ];
        };
      }
    );
}
