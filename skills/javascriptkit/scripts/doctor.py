#!/usr/bin/env python3

import json
import subprocess
import sys
import shutil

def check_cmd(cmd, name):
    path = shutil.which(cmd)
    if path:
        print(f"[OK] {name} found")
        return True
    else:
        print(f"[ERROR] {name} not found ({cmd})")
        return False

def get_target_info():
    try:
        output = subprocess.check_output(["swiftc", "-print-target-info"], stderr=subprocess.DEVNULL).decode("utf-8")
        return json.loads(output)
    except Exception:
        return None

def main():
    print("Checking environment for Swift WebAssembly development...")
    print("")

    # 1. Verify Swift Toolchain
    if not check_cmd("swiftc", "Swift compiler"):
        print("   Please install Swift from https://www.swift.org/install/ or via 'swiftly'.")
        sys.exit(1)

    # 2. Verify OSS Toolchain
    info = get_target_info()
    if not info:
        print("[ERROR] Failed to get Swift target info.")
        sys.exit(1)

    compiler_tag = info.get("swiftCompilerTag", "")
    if compiler_tag.startswith("swiftlang-"):
        print(f"[ERROR] Detected Xcode toolchain ({compiler_tag}).")
        print("   Swift SDK for WebAssembly requires an OSS toolchain from swift.org.")
        print("   Please use 'swiftly use' or select an OSS toolchain in your environment.")
        sys.exit(1)
    elif compiler_tag:
        print(f"[OK] OSS toolchain detected ({compiler_tag})")
    else:
        print("[WARNING] Could not determine Swift compiler tag. Assuming OSS toolchain.")

    # 3. Verify Node.js and npm
    check_cmd("node", "Node.js")
    check_cmd("npm", "npm")

    # 4. Verify Swift SDK for WebAssembly
    try:
        sdk_list = subprocess.check_output(["swift", "sdk", "list"], stderr=subprocess.DEVNULL).decode("utf-8")
    except Exception:
        sdk_list = ""

    # Extract the core part of the tag for matching (e.g., 6.2.3 or DEVELOPMENT-SNAPSHOT-...)
    # This matches the logic in install-sdk.py
    tag_core = compiler_tag.replace("swift-", "").replace("-RELEASE", "")

    if not tag_core:
        # Fallback to general wasm check
        if "wasm" in sdk_list.lower():
            print("[OK] Swift SDK for WebAssembly detected (general check)")
        else:
            print("[ERROR] Swift SDK for WebAssembly not found.")
            print("   Please run './scripts/install-sdk.py' to install it.")
            sys.exit(1)
    else:
        # Precise check: does the SDK list contain the current toolchain's tag?
        if tag_core in sdk_list:
            print(f"[OK] Matching Swift SDK for WebAssembly found ({tag_core})")
        else:
            print(f"[ERROR] No matching Swift SDK for WebAssembly found for toolchain {compiler_tag}.")
            print("   Please run './scripts/install-sdk.py' to automatically install the matching SDK.")
            sys.exit(1)

    print("")
    print("Environment is ready for Swift WebAssembly development!")

if __name__ == "__main__":
    main()

