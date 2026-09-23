#!/usr/bin/env bash
set -euo pipefail

# ANSI color codes
BOLD="\033[1m"
GREEN="\033[1;32m"
BLUE="\033[1;34m"
YELLOW="\033[1;33m"
CYAN="\033[1;36m"
RED="\033[1;31m"
RESET="\033[0m"

info() {
    printf "${BLUE}::${RESET} ${BOLD}%s${RESET}\n" "$1"
}

success() {
    printf "${GREEN}==>${RESET} ${BOLD}%s${RESET}\n" "$1"
}

warn() {
    printf "${YELLOW}==> WARNING:${RESET} %s\n" "$1"
}

error() {
    printf "${RED}==> ERROR:${RESET} %s\n" "$1" >&2
    exit 1
}

# 1. Determine target directory
TARGET_DIR=""
if [ $# -ge 1 ]; then
    TARGET_DIR="$1"
elif [ -f "PKGBUILD" ]; then
    TARGET_DIR="."
else
    # Find package directories with PKGBUILDs in current repo
    PACKAGES=($(find . -maxdepth 2 -name PKGBUILD -printf '%h\n' | sed 's|^\./||' | sort))
    echo -e "${BOLD}Usage:${RESET} $0 <package-dir>"
    echo -e "\nAvailable packages:"
    for pkg in "${PACKAGES[@]}"; do
        echo -e "  - ${CYAN}${pkg}${RESET}"
    done
    exit 1
fi

if [ ! -f "${TARGET_DIR}/PKGBUILD" ]; then
    error "No PKGBUILD found in '${TARGET_DIR}'"
fi

cd "${TARGET_DIR}"
PKG_DIR=$(pwd)

# Parse metadata
PKGNAME=$(bash -c 'source PKGBUILD; echo "$pkgname"')
PKGVER=$(bash -c 'source PKGBUILD; echo "$pkgver"')
PKGREL=$(bash -c 'source PKGBUILD; echo "$pkgrel"')
CARCH=$(uname -m)

echo ""
printf "${CYAN}╔═══════════════════════════════════════════════════════════╗${RESET}\n"
printf "${CYAN}║${RESET} ${BOLD}Packaging:${RESET} %-48s ${CYAN}║${RESET}\n" "${PKGNAME} ${PKGVER}-${PKGREL} (${CARCH})"
printf "${CYAN}╚═══════════════════════════════════════════════════════════╝${RESET}\n"
echo ""

# 2. Build the package
info "Cleaning previous build artifacts and compiling with makepkg..."
makepkg -Ccf

# 3. Locate the built package
PKGFILE=$(find . -maxdepth 1 -name "${PKGNAME}-${PKGVER}-${PKGREL}-${CARCH}.pkg.tar.zst" -o -name "${PKGNAME}-${PKGVER}-${PKGREL}-any.pkg.tar.zst" | head -n 1)

if [ -z "${PKGFILE}" ] || [ ! -f "${PKGFILE}" ]; then
    # Fallback search for any matching .pkg.tar.zst generated right now
    PKGFILE=$(ls -t *.pkg.tar.zst 2>/dev/null | grep -v 'debug' | head -n 1 || true)
fi

if [ -z "${PKGFILE}" ] || [ ! -f "${PKGFILE}" ]; then
    error "Build finished but could not locate generated .pkg.tar.zst file."
fi

FULL_PKG_PATH="$(realpath "${PKGFILE}")"

# 4. Inspect payload
echo ""
success "Build complete! Inspecting package payload:"
printf "${CYAN}-------------------------------------------------------------${RESET}\n"
pacman -Qlp "${PKGFILE}"
printf "${CYAN}-------------------------------------------------------------${RESET}\n"

# 5. Handoff command
INSTALL_CMD="sudo pacman -U ${FULL_PKG_PATH}"

# Copy to clipboard if wl-copy or xclip is available
COPIED=false
if command -v wl-copy >/dev/null 2>&1; then
    printf "%s" "${INSTALL_CMD}" | wl-copy
    COPIED=true
elif command -v xclip >/dev/null 2>&1; then
    printf "%s" "${INSTALL_CMD}" | xclip -selection clipboard
    COPIED=true
fi

echo ""
printf "${GREEN}╔═══════════════════════════════════════════════════════════╗${RESET}\n"
printf "${GREEN}║${RESET}                  ${BOLD}Ready for Installation${RESET}                   ${GREEN}║${RESET}\n"
printf "${GREEN}╚═══════════════════════════════════════════════════════════╝${RESET}\n"
echo ""
echo -e "To install this package, run:"
echo ""
echo -e "  ${BOLD}${YELLOW}${INSTALL_CMD}${RESET}"
echo ""

if [ "$COPIED" = true ]; then
    printf "${GREEN}✔${RESET} Command has been copied to your clipboard (paste with Ctrl+V or Ctrl+Shift+V).\n\n"
fi
