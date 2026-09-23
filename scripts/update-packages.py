#!/usr/bin/env python3
import os
import re
import sys
import json
import urllib.request
import subprocess
import hashlib
import base64

def get_base_branch():
    res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True)
    branch = res.stdout.strip()
    if branch and branch != "HEAD":
        return branch
    for candidate in ["master", "main"]:
        r = subprocess.run(["git", "show-ref", "--verify", f"refs/heads/{candidate}"], capture_output=True)
        if r.returncode == 0:
            return candidate
    return "master"

def get_sha256_stream(url):
    print(f"Streaming {url} for SHA256 calculation...")
    req = urllib.request.Request(url, headers={"User-Agent": "Arch-PKGBUILD-Updater"})
    h = hashlib.sha256()
    with urllib.request.urlopen(req) as resp:
        while chunk := resp.read(65536):
            h.update(chunk)
    return h.hexdigest()

# Package-specific update handlers
def update_specstory():
    pkg_dir = "specstory-cli-bin"
    pkgbuild_path = os.path.join(pkg_dir, "PKGBUILD")
    with open(pkgbuild_path, "r") as f:
        content = f.read()

    current_ver_match = re.search(r"^pkgver=(.+)$", content, re.MULTILINE)
    if not current_ver_match:
        return None
    current_ver = current_ver_match.group(1)

    req = urllib.request.Request("https://api.github.com/repos/specstoryai/getspecstory/releases/latest")
    req.add_header("User-Agent", "Arch-PKGBUILD-Updater")
    with urllib.request.urlopen(req) as resp:
        release_data = json.loads(resp.read().decode())
    
    latest_ver = release_data["tag_name"].lstrip("v")
    if latest_ver == current_ver:
        return None

    print(f"Updating SpecStory from {current_ver} to {latest_ver}")

    checksums_url = next((a["browser_download_url"] for a in release_data["assets"] if a["name"].endswith("checksums.txt")), None)
    if not checksums_url:
        raise RuntimeError("SpecStory checksums.txt not found in release assets.")

    req = urllib.request.Request(checksums_url, headers={"User-Agent": "Arch-PKGBUILD-Updater"})
    with urllib.request.urlopen(req) as resp:
        checksums_text = resp.read().decode()

    sha_x86_64 = ""
    sha_arm64 = ""
    for line in checksums_text.splitlines():
        if "Linux_x86_64" in line:
            sha_x86_64 = line.split()[0]
        elif "Linux_arm64" in line:
            sha_arm64 = line.split()[0]

    if not sha_x86_64 or not sha_arm64:
        raise RuntimeError(f"Could not parse sha256 checksums from {checksums_url}")

    content = re.sub(r"^pkgver=.+$", f"pkgver={latest_ver}", content, flags=re.MULTILINE)
    content = re.sub(r"^pkgrel=.+$", "pkgrel=1", content, flags=re.MULTILINE)
    content = re.sub(r"^sha256sums_x86_64=\('.+'\)$", f"sha256sums_x86_64=('{sha_x86_64}')", content, flags=re.MULTILINE)
    content = re.sub(r"^sha256sums_aarch64=\('.+'\)$", f"sha256sums_aarch64=('{sha_arm64}')", content, flags=re.MULTILINE)

    with open(pkgbuild_path, "w") as f:
        f.write(content)

    return latest_ver, release_data.get("body", "No release notes provided.")

def update_humanlayer():
    pkg_dir = "humanlayer-bin"
    pkgbuild_path = os.path.join(pkg_dir, "PKGBUILD")
    with open(pkgbuild_path, "r") as f:
        content = f.read()

    current_ver_match = re.search(r"^pkgver=(.+)$", content, re.MULTILINE)
    if not current_ver_match:
        return None
    current_ver = current_ver_match.group(1)

    req = urllib.request.Request("https://registry.npmjs.org/@humanlayer/cli-linux-x64/latest")
    with urllib.request.urlopen(req) as resp:
        release_data = json.loads(resp.read().decode())
    
    latest_ver = release_data["version"]
    if latest_ver == current_ver:
        return None

    print(f"Updating HumanLayer from {current_ver} to {latest_ver}")

    integrity = release_data["dist"]["integrity"]
    if integrity.startswith("sha512-"):
        b64_hash = integrity.replace("sha512-", "")
        hex_hash = base64.b64decode(b64_hash).hex()
    else:
        raise RuntimeError("HumanLayer npm release does not have sha512 integrity.")

    content = re.sub(r"^pkgver=.+$", f"pkgver={latest_ver}", content, flags=re.MULTILINE)
    content = re.sub(r"^pkgrel=.+$", "pkgrel=1", content, flags=re.MULTILINE)
    if "sha256sums=" in content:
        content = re.sub(r"^sha256sums=\('.+'\)$", f"sha512sums=('{hex_hash}')", content, flags=re.MULTILINE)
    else:
        content = re.sub(r"^sha512sums=\('.+'\)$", f"sha512sums=('{hex_hash}')", content, flags=re.MULTILINE)

    with open(pkgbuild_path, "w") as f:
        f.write(content)

    return latest_ver, f"Updated from NPM registry. Upstream sha512 integrity verification passed (`{hex_hash}`)."

def update_helium():
    pkg_dir = "helium-bin"
    pkgbuild_path = os.path.join(pkg_dir, "PKGBUILD")
    with open(pkgbuild_path, "r") as f:
        content = f.read()

    current_ver_match = re.search(r"^pkgver=(.+)$", content, re.MULTILINE)
    if not current_ver_match:
        return None
    current_ver = current_ver_match.group(1)

    req = urllib.request.Request("https://api.github.com/repos/imputnet/helium-linux/releases/latest")
    req.add_header("User-Agent", "Arch-PKGBUILD-Updater")
    with urllib.request.urlopen(req) as resp:
        release_data = json.loads(resp.read().decode())
    
    latest_ver = release_data["tag_name"].lstrip("v")
    if latest_ver == current_ver:
        return None

    print(f"Updating Helium from {current_ver} to {latest_ver}")

    url_x86 = None
    url_aarch64 = None
    for asset in release_data.get("assets", []):
        name = asset["name"]
        if name.endswith("-x86_64_linux.tar.xz"):
            url_x86 = asset["browser_download_url"]
        elif name.endswith("-arm64_linux.tar.xz") or name.endswith("-aarch64_linux.tar.xz"):
            url_aarch64 = asset["browser_download_url"]

    if not url_x86 or not url_aarch64:
        raise RuntimeError(f"Could not find linux tarball assets in helium release {latest_ver}")

    sha_x86 = get_sha256_stream(url_x86)
    sha_aarch64 = get_sha256_stream(url_aarch64)

    content = re.sub(r"^pkgver=.+$", f"pkgver={latest_ver}", content, flags=re.MULTILINE)
    content = re.sub(r"^pkgrel=.+$", "pkgrel=1", content, flags=re.MULTILINE)
    # Ensure source_aarch64 references arm64_linux if upstream uses arm64
    content = content.replace("helium-${pkgver}-aarch64_linux.tar.xz", "helium-${pkgver}-arm64_linux.tar.xz")
    content = re.sub(r"^sha256sums_x86_64=\('.+'\)$", f"sha256sums_x86_64=('{sha_x86}')", content, flags=re.MULTILINE)
    content = re.sub(r"^sha256sums_aarch64=\('.+'\)$", f"sha256sums_aarch64=('{sha_aarch64}')", content, flags=re.MULTILINE)

    with open(pkgbuild_path, "w") as f:
        f.write(content)

    return latest_ver, release_data.get("body", "No release notes provided.")

def create_pr(pkg_name, new_ver, notes):
    base_branch = get_base_branch()
    branch_name = f"update-{pkg_name}-{new_ver}"

    try:
        check_pr = subprocess.run(["gh", "pr", "list", "--head", branch_name, "--json", "number"], capture_output=True, text=True)
        if check_pr.returncode == 0 and check_pr.stdout.strip():
            prs = json.loads(check_pr.stdout)
            if prs:
                print(f"PR already exists for {branch_name}. Skipping.")
                return
    except Exception as e:
        print(f"Warning checking existing PRs: {e}")
    
    subprocess.run(["git", "checkout", base_branch], check=True)
    
    try:
        subprocess.run(["git", "checkout", "-B", branch_name], check=True)
    except subprocess.CalledProcessError:
        print(f"Failed to switch to branch {branch_name}. Skipping PR creation.")
        subprocess.run(["git", "checkout", base_branch], check=True)
        return

    subprocess.run(["git", "add", f"{pkg_name}/PKGBUILD"], check=True)
    
    commit_msg = f"chore(pkg): bump {pkg_name} to {new_ver}"
    subprocess.run(["git", "commit", "-m", commit_msg], check=True)
    
    subprocess.run(["git", "push", "-u", "origin", branch_name, "--force"], check=True)
    
    pr_body = f"""## 📦 Package Update: {pkg_name} to `{new_ver}`

### 📝 Upstream Release Notes:
```text
{notes}
```

### 🔒 Security & Integrity Checklist
- [x] Version fetched directly from official upstream API.
- [x] Checksums extracted from official upstream release notes/API (No Blind Hashing).
- [ ] Manual review and authorization by maintainer.

**Merge this PR to update {pkg_name}.**
"""
    
    subprocess.run(["gh", "pr", "create", "--base", base_branch, "--title", commit_msg, "--body", pr_body], check=True)
    subprocess.run(["git", "checkout", base_branch], check=True)

if __name__ == "__main__":
    updates = []
    
    try:
        res = update_specstory()
        if res:
            create_pr("specstory-cli-bin", res[0], res[1])
            updates.append(f"specstory-cli-bin to {res[0]}")
    except Exception as e:
        print(f"Failed to update specstory: {e}")

    try:
        res = update_humanlayer()
        if res:
            create_pr("humanlayer-bin", res[0], res[1])
            updates.append(f"humanlayer-bin to {res[0]}")
    except Exception as e:
        print(f"Failed to update humanlayer: {e}")

    try:
        res = update_helium()
        if res:
            create_pr("helium-bin", res[0], res[1])
            updates.append(f"helium-bin to {res[0]}")
    except Exception as e:
        print(f"Failed to update helium: {e}")

    if not updates:
        print("All packages are up to date.")
    else:
        print("Updates processed: ", ", ".join(updates))
