# Custom PKGBUILDs

This repository tracks custom Arch Linux packages I maintain locally. It currently includes builds for `humanlayer-bin` and `specstory-cli-bin`.

## How to use

Clone the repository.

```sh
git clone https://github.com/username/custom-pkgbuilds.git
cd custom-pkgbuilds
```

Navigate to the package you want to install.

```sh
cd humanlayer-bin
```

Build and install the package with `makepkg`.

```sh
makepkg -si
```

The `-s` flag installs missing dependencies. The `-i` flag installs the package after a successful build.

## Packages

### humanlayer-bin

This package installs the precompiled Humanlayer CLI. It pulls the binary directly from upstream releases. Use it to interact with the Humanlayer API from your terminal.

### specstory-cli-bin

This package installs the Specstory CLI. It pulls the precompiled binary and sets up the environment for Specstory.
