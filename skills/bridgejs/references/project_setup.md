# BridgeJS Project Setup

Complete guide to setting up a Swift project with BridgeJS for WebAssembly development.

## Prerequisites

- **Swift Toolchain**: Swift 6.1 or later (Swift 6.2+ recommended)
- **Swift SDK for WebAssembly**: Matching your toolchain version
- **Node.js**: Required for TypeScript processing and serving

## 1. Install Swift Toolchain

The recommended way to install Swift is using [`swiftly`](https://www.swift.org/install/):

```bash
# Install swiftly (follow instructions for your platform)
# Then install Swift 6.2.3 (or latest)
swiftly install 6.2.3
swiftly use 6.2.3
```

### Verify Installation

Ensure you're using an **OSS Swift toolchain**, not the Xcode-bundled one:

```bash
which swiftc
swiftc --version
```

If `which swiftc` shows `/usr/bin/swiftc` or a path inside `Xcode.app`, you need to install and select an OSS toolchain.

## 2. Install Swift SDK for WebAssembly

Find the matching SDK on the [Swift download page](https://www.swift.org/download/) and install:

```bash
# Example for Swift 6.2.3
swift sdk install https://download.swift.org/swift-6.2.3-release/wasm-sdk/swift-6.2.3-RELEASE/swift-6.2.3-RELEASE_wasm.artifactbundle.tar.gz
```

Verify installation:

```bash
swift sdk list
```

Note the **Swift SDK ID** (e.g., `swift-6.2.3-RELEASE_wasm`). Set it as an environment variable:

```bash
export SWIFT_SDK_ID="swift-6.2.3-RELEASE_wasm"
```

## 3. Create a New Swift Package

```bash
swift package init --name MyApp --type executable
cd MyApp
```

## 4. Configure Package.swift

### Option A: Build Plugin (Simplest)

The build plugin processes `@JS` annotations during each build:

```swift
// swift-tools-version:6.0

import PackageDescription

let package = Package(
    name: "MyApp",
    dependencies: [
        .package(url: "https://github.com/swiftwasm/JavaScriptKit.git", from: "0.22.0")
    ],
    targets: [
        .executableTarget(
            name: "MyApp",
            dependencies: ["JavaScriptKit"],
            swiftSettings: [
                // Required for BridgeJS generated code
                .enableExperimentalFeature("Extern")
            ],
            plugins: [
                // Process @JS annotations and generate bindings
                .plugin(name: "BridgeJS", package: "JavaScriptKit")
            ]
        )
    ]
)
```

### Option B: Ahead-of-Time Generation (Faster Builds)

For larger projects, generate code once and commit it:

```swift
// swift-tools-version:6.0

import PackageDescription

let package = Package(
    name: "MyApp",
    dependencies: [
        .package(url: "https://github.com/swiftwasm/JavaScriptKit.git", from: "0.22.0")
    ],
    targets: [
        .executableTarget(
            name: "MyApp",
            dependencies: ["JavaScriptKit"],
            swiftSettings: [
                .enableExperimentalFeature("Extern")
            ]
            // No BridgeJS plugin - using AOT generation
        )
    ]
)
```

Create config file:

```bash
echo "{}" > Sources/MyApp/bridge-js.config.json
```

Generate code:

```bash
swift package plugin bridge-js --target MyApp
```

This creates `Sources/MyApp/Generated/` with:

- `BridgeJS.swift` - Generated Swift glue code
- `BridgeJS.Macros.swift` - Macro-annotated declarations for TypeScript imports (if using `bridge-js.d.ts`)
- `JavaScript/BridgeJS.json` - Unified skeleton for JS runtime

Commit generated files:

```bash
git add Sources/MyApp/Generated
git commit -m "Add generated BridgeJS code"
```

## 5. Write Swift Code with @JS

Create `Sources/MyApp/main.swift`:

```swift
import JavaScriptKit

@JS class Counter {
    private var count = 0

    @JS init() {}

    @JS func increment() {
        count += 1
    }

    @JS func getValue() -> Int {
        return count
    }
}

@JS func greet(name: String) -> String {
    return "Hello, \(name)!"
}
```

## 6. Build for WebAssembly

```bash
swift package --swift-sdk $SWIFT_SDK_ID js
```

This compiles Swift to WebAssembly and generates JavaScript bindings in:

```
.build/plugins/PackageToJS/outputs/Package/
├── index.js          # Entry point
├── index.d.ts        # TypeScript declarations
└── MyApp.wasm        # WebAssembly binary
```

### Build Options

```bash
# Debug build (default)
swift package --swift-sdk $SWIFT_SDK_ID js

# Release build
swift package --swift-sdk $SWIFT_SDK_ID js -c release

# Use CDN for JavaScriptKit runtime
swift package --swift-sdk $SWIFT_SDK_ID js --use-cdn
```

## 7. Create HTML Entry Point

Create `index.html` in project root:

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>MyApp</title>
    <script type="module">
        import { init } from "./.build/plugins/PackageToJS/outputs/Package/index.js";

        const { exports } = await init({});

        // Use your Swift exports
        console.log(exports.greet("World"));

        const counter = new exports.Counter();
        counter.increment();
        console.log(counter.getValue());
    </script>
</head>
<body>
    <h1>MyApp</h1>
</body>
</html>
```

## 8. Serve and Test

```bash
npx serve
```

Open `http://localhost:3000` in your browser.

## Project Structure

Recommended structure for a BridgeJS project:

```
MyApp/
├── Package.swift
├── index.html
├── Sources/
│   └── MyApp/
│       ├── main.swift              # Entry point with @JS exports
│       ├── Models.swift            # @JS classes
│       ├── Functions.swift         # @JS functions
│       ├── bridge-js.config.json   # BridgeJS configuration
│       ├── bridge-js.d.ts          # TypeScript imports (optional)
│       └── Generated/              # AOT-generated code (if using Option B)
└── Tests/
    └── MyAppTests/                 # Swift tests
```

## Configuration Files

### bridge-js.config.json

Place in your target directory:

```json
{
  "exposeToGlobal": false,
  "tools": {
    "node": "/usr/local/bin/node"
  }
}
```

### bridge-js.config.local.json

For local overrides (add to `.gitignore`):

```json
{
  "tools": {
    "node": "/opt/homebrew/bin/node"
  }
}
```

## When to Use Each Approach

**Build Plugin** when:

- Developing small projects or prototypes
- Frequently changing API boundaries
- Want simplest setup

**AOT Generation** when:

- Developing larger projects
- Build time is a concern
- Want to inspect/version control generated code
- Working in teams needing consistent builds

## Updating Generated Code (AOT)

When you change Swift code or TypeScript definitions:

```bash
swift package plugin bridge-js
git add Sources/MyApp/Generated
git commit -m "Update generated BridgeJS code"
```

## Troubleshooting

### "Extern" Feature Error

Ensure `Package.swift` includes:

```swift
swiftSettings: [
    .enableExperimentalFeature("Extern")
]
```

### Node.js Not Found

Set custom path in `bridge-js.config.json`:

```json
{
  "tools": {
    "node": "/path/to/node"
  }
}
```

Or set environment variable:

```bash
export JAVASCRIPTKIT_NODE_EXEC=/path/to/node
```

### Xcode Toolchain Issues

BridgeJS requires an OSS Swift toolchain. In Xcode:

1. Xcode > Toolchains > select your installed OSS toolchain
2. Or use command line with explicit toolchain path
