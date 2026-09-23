# Custom PKGBUILDs

Personal Arch Linux packages maintained with upstream checksum verification and human review gates.

## Packages

- `helium-bin`: Lightweight Chromium derivative.
- `humanlayer-bin`: Daemon management and authentication CLI for HumanLayer.
- `specstory-cli-bin`: Claude Code wrapper that saves conversation history to markdown.

## Building and installing

Clone the repository:

```sh
git clone https://github.com/abstraction/custom-pkgbuilds.git
cd custom-pkgbuilds
```

Run the build helper:

```sh
./build.sh specstory-cli-bin
```

This runs `makepkg -Ccf` in a clean workspace, displays the package payload (`pacman -Qlp`) so you can verify file destinations, and copies the `sudo pacman -U` install command to your clipboard.

To install directly with standard `makepkg`:

```sh
cd specstory-cli-bin
makepkg -si
```

## Automated updates

A GitHub Actions workflow runs every Sunday at 02:00 UTC. It polls upstream GitHub and npm release APIs, extracts official checksums or integrity hashes, and opens a pull request with upstream release notes.

Merging a pull request approves the update. You can then pull the change and build the package locally with `./build.sh`.
