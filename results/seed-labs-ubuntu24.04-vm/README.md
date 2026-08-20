# seed-labs-ubuntu24.04-vm

A small **Nix flake** that builds a **NixOS QEMU VM** intended to *approximate* a typical **SEED Labs Ubuntu 24.04** lab setup.

## What’s included

- Desktop: **XFCE + LightDM**
- User: **`seed` / `seed`** (passwordless sudo; groups include `docker` + `wireshark`)
- Services: **OpenSSH** (port 22 open inside the VM), **Docker**, **QEMU guest**
- Tools: git, compilers/debuggers, networking tools (iproute2/nettools/dnsutils), tcpdump/nmap, wireshark-cli, etc.
- VM defaults (via `virtualisation.vmVariant`): **4GB RAM**, **2 cores**, **20GB disk**, graphics enabled

## Build + run

From this directory:

```bash
nix build .#nixosConfigurations.seed-labs-ubuntu24-vm.config.system.build.vm
./result/bin/run-*-vm
```

## Using this flake with `nixos-rebuild`

This configuration is embedded in `flake.nix` (there is no separate `configuration.nix`).

- If the machine’s hostname is `nixos`, use the convenience output:

  ```bash
  sudo nixos-rebuild boot --flake .#nixos
  # or
  sudo nixos-rebuild switch --flake .#nixos
  ```

- Otherwise, use:

  ```bash
  sudo nixos-rebuild boot --flake .#seed-labs-ubuntu24-vm
  # or
  sudo nixos-rebuild switch --flake .#seed-labs-ubuntu24-vm
  ```

Login with:

- username: `seed`
- password: `seed`

## Caveats

- This is **NixOS**, not a byte-for-byte Ubuntu 24.04 image; labs that depend on SEED’s exact Ubuntu install scripts may need extra packages/services/kernel tweaks in `flake.nix`.
- The flake targets **`aarch64-linux`**; building on other systems may require an appropriate builder.
