{
  description = "NixOS VM approximating SEED Labs Ubuntu 24.04 lab setup";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
  };

  outputs =
    { self, nixpkgs, ... }:
    let
      system = "aarch64-linux";

      mkSeedVm =
        hostName:
        nixpkgs.lib.nixosSystem {
          inherit system;
          modules = [
            (
              {
                config,
                pkgs,
                lib,
                ...
              }:
              {
                # VM-friendly boot (per nix.dev NixOS VM guidance)
                boot.loader.grub.enable = false;
                boot.loader.generic-extlinux-compatible.enable = true;

                networking.hostName = hostName;
                networking.useDHCP = lib.mkDefault true;

                time.timeZone = "UTC";
                i18n.defaultLocale = "en_US.UTF-8";

                # User similar to many SEED lab VMs
                users.users.seed = {
                  isNormalUser = true;
                  description = "seed";
                  extraGroups = [
                    "wheel"
                    "networkmanager"
                    "docker"
                    "wireshark"
                  ];
                  initialPassword = "seed";
                };
                security.sudo.wheelNeedsPassword = false;

                services.openssh = {
                  enable = true;
                  settings = {
                    PermitRootLogin = "no";
                    PasswordAuthentication = true;
                  };
                };
                networking.firewall.allowedTCPPorts = [ 22 ];

                # Desktop environment (common in lab VMs)
                services.xserver.enable = true;
                services.xserver.xkb.layout = "us";
                services.xserver.displayManager.lightdm.enable = true;
                services.xserver.desktopManager.xfce.enable = true;

                # Lab-style tooling (extend to match the SEED Ubuntu script exactly)
                environment.systemPackages = with pkgs; [
                  git
                  vim
                  nano
                  curl
                  wget
                  unzip
                  gnumake
                  cmake
                  gcc
                  gdb
                  binutils
                  python3
                  python3Packages.pip
                  openssl
                  pkg-config
                  iproute2
                  nettools
                  dnsutils
                  tcpdump
                  wireshark-cli
                  nmap
                  socat
                  strace
                  ltrace
                  tmux
                  htop
                ];

                programs.wireshark.enable = true;

                # Docker (often used in SEED labs)
                virtualisation.docker.enable = true;

                # Better behavior when run under QEMU
                services.qemuGuest.enable = true;

                # VM run defaults when using system.build.vm
                virtualisation.vmVariant = {
                  virtualisation.memorySize = 4096; # MB
                  virtualisation.cores = 2;
                  virtualisation.diskSize = 20000; # MB
                  virtualisation.graphics = true;
                };

                system.stateVersion = "25.11";
              }
            )
          ];
        };
    in
    {
      # Primary config name (VM)
      nixosConfigurations.seed-labs-ubuntu24-vm = mkSeedVm "seed-vm";

      # Convenience alias for hosts whose hostname is "nixos"
      nixosConfigurations.nixos = mkSeedVm "nixos";
    };
}
