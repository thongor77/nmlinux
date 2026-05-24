{
  description = "NMLinux — Network Manager GUI for Linux";

  inputs = {
    nixpkgs.url     = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs   = nixpkgs.legacyPackages.${system};
        python = pkgs.python3;

        systemTools = with pkgs; [
          networkmanager   # nmcli
          iproute2         # ip
          iputils          # ping
          nmap
          whois
          net-snmp         # snmpwalk / snmpget
          bind             # dig
          traceroute
          mtr
          curl
          kdePackages.breeze-icons
          hicolor-icon-theme
        ];

        nmlinux = python.pkgs.buildPythonApplication {
          pname   = "nmlinux";
          version = "1.2.6";
          src     = ./.;
          format  = "pyproject";

          nativeBuildInputs = with python.pkgs; [ hatchling ];

          propagatedBuildInputs = with python.pkgs; [
            pyside6
            ptyprocess
            pyte
          ];

          makeWrapperArgs = [
            "--prefix PATH : ${pkgs.lib.makeBinPath systemTools}"
            "--prefix XDG_DATA_DIRS : ${pkgs.kdePackages.breeze-icons}/share"
            "--prefix XDG_DATA_DIRS : ${pkgs.hicolor-icon-theme}/share"
            "--set-default QT_QPA_PLATFORMTHEME kde"
            "--set NMLINUX_ICON_PATH ${pkgs.kdePackages.breeze-icons}/share/icons"
          ];

          meta = {
            description = "A free Linux adaptation of NETworkManager";
            homepage    = "https://github.com/thongor77/nmlinux";
            license     = pkgs.lib.licenses.gpl2Only;
            platforms   = pkgs.lib.platforms.linux;
          };
        };
      in {
        packages.default = nmlinux;

        apps.default = {
          type    = "app";
          program = "${nmlinux}/bin/nmlinux";
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [
            (python.withPackages (ps: with ps; [
              pyside6
              ptyprocess
              pyte
            ]))
          ] ++ systemTools;
        };
      }
    );
}
