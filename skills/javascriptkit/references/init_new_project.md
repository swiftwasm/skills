# Initializing a New JavaScriptKit Project

This guide walks you through setting up a new Swift project that uses JavaScriptKit to interact with JavaScript APIs from WebAssembly.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Swift Toolchain**: Swift 6.0 or later (with WebAssembly support). Swift 6.2 or later is recommended for the best experience.
- **Swift SDK for WebAssembly**: Matching your Swift toolchain version.
- **Node.js and npm**: Required for serving the application and managing JavaScript bindings.

### 1. Install Swift Toolchain and SDK

The recommended way to install and manage Swift toolchains is using [`swiftly`](https://www.swift.org/install/).

1.  **Install `swiftly`**: Follow the instructions on swift.org for your platform.
2.  **Install a supported toolchain** (e.g., Swift 6.2.3):
    ```bash
    swiftly install 6.2.3
    swiftly use 6.2.3
    ```
3.  **Install the Swift SDK for WebAssembly**:
    The easiest way is to use the supplemental script provided with this skill:
    ```bash
    ./scripts/install-sdk.py
    ```
    This script automatically detects your toolchain version and fetches the matching SDK. Alternatively, you can manually find the latest SDK artifact bundle URL on the [swift.org download page](https://www.swift.org/download/) and run:
    ```bash
    # Example for Swift 6.2.3
    swift sdk install https://download.swift.org/swift-6.2.3-release/wasm-sdk/swift-6.2.3-RELEASE/swift-6.2.3-RELEASE_wasm.artifactbundle.tar.gz
    ```
4.  **Verify installation**:
    ```bash
    swift sdk list
    ```
    Note the **Swift SDK ID** from the output (e.g., `swift-6.2.3-RELEASE_wasm`). You will need this for building.

### 2. Verify Your Environment

It is crucial to use an **OSS Swift toolchain** rather than the one bundled with Xcode.

> **Note**: AI should run the following commands to verify the environment. If `which swiftc` points to `/usr/bin/swiftc` (the Xcode stub) or a path inside `Xcode.app`, inform the user that they must install and select an OSS toolchain.

```bash
which swiftc
swiftc --version
```

Set the `SWIFT_SDK_ID` environment variable to your installed Swift SDK ID (e.g., `swift-6.2.3-RELEASE_wasm`).

```bash
export SWIFT_SDK_ID="your-sdk-id-here"
```

## 1. Create a New Swift Package

Start by creating a new Swift executable package.

> **Note**: Ask the user for their preferred project name before running these commands.

```bash
# Replace <PROJECT_NAME> with the project name provided by the user
swift package init --name <PROJECT_NAME> --type executable
```

## 2. Add JavaScriptKit Dependency

Add JavaScriptKit as a dependency to your `Package.swift` file. You can do this using the `swift package` command.

> **Note**: Always check for the latest release version of JavaScriptKit on GitHub (https://github.com/swiftwasm/JavaScriptKit/releases) and use it in the command below.

```bash
# Replace <LATEST_VERSION> with the actual latest version (e.g., 0.36.0)
swift package add-dependency https://github.com/swiftwasm/JavaScriptKit.git --from <LATEST_VERSION>
```

Then, add `JavaScriptKit` as a target dependency for your executable:

```bash
# Replace <PROJECT_NAME> with the project name provided by the user
swift package add-target-dependency --package JavaScriptKit JavaScriptKit <PROJECT_NAME>
```

## 3. Write Your Swift Code

Replace the contents of `Sources/main.swift` with the following code to manipulate the DOM:

```swift
import JavaScriptKit

let document = JSObject.global.document
let div = document.createElement("div")
div.innerText = "Hello from Swift!"
_ = document.body.appendChild(div)
```

## 4. Create an HTML Entry Point

Create an `index.html` file in the root directory of your project:

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>PROJECT_NAME</title>
    <script type="module">
        import { init } from "./.build/plugins/PackageToJS/outputs/Package/index.js";
        init();
    </script>
</head>
<body>
    <h1><PROJECT_NAME></h1>
</body>
</html>
```

## 5. Build and Run

Build your application for WebAssembly:

```bash
swift package --swift-sdk $SWIFT_SDK_ID js --use-cdn
```

This command compiles your Swift code to WebAssembly and uses the `PackageToJS` plugin to generate the necessary JavaScript bindings.

Start a local web server to view your application:

```bash
npx serve
```

Open your browser and navigate to the address provided by `serve` (usually `http://localhost:3000`). You should see your project title and "Hello from Swift!" on the page.

