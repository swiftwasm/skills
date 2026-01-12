#!/usr/bin/env python3

import json
import re
import subprocess
import sys
import urllib.request

def get_swift_version():
    try:
        # Try -print-target-info first, as it provides the most accurate tag for snapshots
        target_info = subprocess.check_output(["swiftc", "-print-target-info"]).decode("utf-8")
        info = json.loads(target_info)
        if "swiftCompilerTag" in info:
            return info["swiftCompilerTag"]
    except Exception:
        pass

    try:
        output = subprocess.check_output(["swiftc", "--version"]).decode("utf-8")
        # Example: Swift version 6.0.3 (swift-6.0.3-RELEASE)
        # Example: Swift version 6.1-dev (swift-6.1-DEVELOPMENT-SNAPSHOT-2024-10-23-a)
        match = re.search(r"\((swift-[^)]+)\)", output)
        if match:
            return match.group(1)
        
        # Fallback for some environments
        match = re.search(r"Swift version ([0-9.]+)", output)
        if match:
            return match.group(1)
            
        return None
    except Exception:
        return None

def fetch_json(url):
    try:
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def find_release_sdk(version_id):
    # version_id is like '6.2.3' or 'swift-6.2.3-RELEASE'
    releases = fetch_json("https://www.swift.org/api/v1/install/releases.json")
    if not releases:
        return None

    # Normalize version_id to '6.2.3' style for matching 'name'
    norm_version = version_id
    if version_id.startswith("swift-") and version_id.endswith("-RELEASE"):
        norm_version = version_id[6:-8]

    for release in releases:
        if release["name"] == norm_version or release["tag"] == version_id:
            for platform in release.get("platforms", []):
                if platform["platform"] == "wasm-sdk":
                    tag = release["tag"]
                    version = release["name"]
                    url = f"https://download.swift.org/swift-{version}-release/wasm-sdk/{tag}/{tag}_wasm.artifactbundle.tar.gz"
                    return {
                        "url": url,
                        "checksum": platform["checksum"]
                    }
    return None

def find_dev_sdk(version_id):
    # version_id is like 'swift-6.2-DEVELOPMENT-SNAPSHOT-2024-12-10-a'
    # We need to find the branch. Usually it's in the ID.
    match = re.match(r"swift-([0-9.]+)-DEVELOPMENT", version_id)
    branch = "main"
    if match:
        branch = f"swift-{match.group(1)}-branch"
    
    # Try the guessed branch, then fall back to main
    branches_to_try = [branch, "main"]
    if "DEVELOPMENT" in version_id:
        # Check if it's a specific release branch like 6.2
        m = re.match(r"swift-([0-9.]+)", version_id)
        if m:
            branches_to_try.insert(0, f"swift-{m.group(1)}-release")

    for b in branches_to_try:
        url = f"https://www.swift.org/api/v1/install/dev/{b}/wasm-sdk.json"
        snapshots = fetch_json(url)
        if not snapshots:
            continue
        
        for snap in snapshots:
            # snap["dir"] is like 'swift-DEVELOPMENT-SNAPSHOT-2024-12-10-a'
            # version_id might be exactly that or prefixed with swift-<version>-
            if snap["dir"] in version_id or version_id in snap["dir"]:
                download_url = f"https://download.swift.org/development/wasm-sdk/{snap['dir']}/{snap['download']}"
                return {
                    "url": download_url,
                    "checksum": snap["checksum"]
                }
    return None

def main():
    version_id = get_swift_version()
    if not version_id:
        print("Could not determine Swift version from 'swiftc'")
        sys.exit(1)

    # Check for Xcode toolchain
    if version_id.startswith("swiftlang-"):
        print(f"Error: Detected Xcode toolchain ({version_id}).")
        print("Swift SDK for WebAssembly requires an OSS toolchain from swift.org.")
        print("Please install one via 'swiftly' or from the swift.org download page.")
        sys.exit(1)

    print(f"Detected Swift version ID: {version_id}")

    sdk_info = None
    if "-RELEASE" in version_id or re.match(r"^[0-9.]+$", version_id):
        sdk_info = find_release_sdk(version_id)
    else:
        sdk_info = find_dev_sdk(version_id)

    if not sdk_info:
        print(f"Could not find a matching Wasm SDK for version {version_id}")
        # Try one last fallback: if it's a version number, try release search anyway
        if not sdk_info and re.search(r"[0-9.]+", version_id):
            sdk_info = find_release_sdk(version_id)
            
    if sdk_info:
        print(f"Found Wasm SDK:")
        print(f"  URL: {sdk_info['url']}")
        print(f"  Checksum: {sdk_info['checksum']}")
        
        cmd = ["swift", "sdk", "install", sdk_info["url"], "--checksum", sdk_info["checksum"]]
        print(f"Running: {' '.join(cmd)}")
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode("utf-8")
            print(output)
            print("Successfully installed Swift SDK for WebAssembly.")
        except subprocess.CalledProcessError as e:
            output = e.output.decode("utf-8")
            if "already installed" in output:
                print(output)
                print("Swift SDK for WebAssembly is already installed.")
            else:
                print(f"Error installing SDK: {output}")
                sys.exit(1)
    else:
        print("No matching SDK found. Please install manually from https://www.swift.org/download/")
        sys.exit(1)

if __name__ == "__main__":
    main()

