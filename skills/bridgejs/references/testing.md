# Testing BridgeJS Projects

Overview of testing approaches for BridgeJS-based Swift WebAssembly projects.

## Testing Approaches

### Snapshot Testing

BridgeJS uses snapshot testing to verify generated code remains consistent. The tool generates:

- `BridgeJS.swift` - Swift glue code
- `BridgeJS.Macros.swift` - Macro-annotated declarations
- `JavaScript/BridgeJS.json` - Unified skeleton for JS runtime

Snapshot tests compare generated output against expected baselines, catching unintended changes to the binding generator.

### End-to-End Testing

End-to-end tests verify the complete Swift-JavaScript integration:

1. Swift code with `@JS` exports compiles to WebAssembly
2. JavaScript tests instantiate WASM and call the exported APIs
3. Assertions verify the bridged interface works correctly

## JavaScriptKit Test Infrastructure

JavaScriptKit uses a prelude pattern for end-to-end testing. The key components:

### Setup Function

```javascript
// Tests/prelude.mjs
export async function setupOptions(options, context) {
    return {
        ...options,
        getImports: (importsContext) => {
            // Provide JavaScript implementations for TypeScript imports
            return {
                jsRoundTripString: (v) => v,
                JsGreeter: class {
                    constructor(name, prefix) {
                        this.name = name;
                        this.prefix = prefix;
                    }
                    greet() {
                        return `${this.prefix}, ${this.name}!`;
                    }
                },
            };
        },
        addToCoreImports(importObject, importsContext) {
            // Register test hooks that Swift can call
            const { getExports } = importsContext;
            importObject["MyTests"] = {
                "runJsWorks": () => {
                    const exports = getExports();
                    runTests(exports);
                }
            };
        }
    }
}
```

### Test Function

```javascript
import assert from "node:assert";

function runTests(exports) {
    // Test primitives
    assert.equal(exports.roundTripString("Hello"), "Hello");
    assert.equal(exports.roundTripInt(42), 42);
    assert.equal(exports.roundTripBool(true), true);

    // Test classes
    const greeter = new exports.Greeter("World");
    assert.equal(greeter.greet(), "Hello, World!");
    assert.equal(greeter.name, "World");

    // Test property setters
    greeter.name = "Swift";
    assert.equal(greeter.greet(), "Hello, Swift!");

    // Test enums
    assert.equal(exports.Direction.North, 0);
    exports.setDirection(exports.Direction.South);

    // Clean up Swift objects
    greeter.release();
}
```

### Swift Test Entry Point

```swift
import XCTest

@_extern(wasm, module: "MyTests", name: "runJsWorks")
@_extern(c)
func runJsWorks() -> Void

class BridgeTests: XCTestCase {
    func testAll() {
        runJsWorks()
    }
}
```

## Running Tests

Build and run with the Swift test command:

```bash
swift package --swift-sdk $SWIFT_SDK_ID test
```

The test runner:

1. Builds Swift to WebAssembly
2. Starts a JavaScript runtime (Node.js)
3. Instantiates the WASM module with test hooks
4. Executes Swift tests that call back into JavaScript
5. Reports results

## Project Testing with Vitest

For testing BridgeJS in your own projects using Vitest:

### Setup

```bash
# In your project
mkdir -p tests && cd tests
npm init -y
npm install -D vitest vite-plugin-wasm typescript
```

**vitest.config.ts**:

```typescript
import { defineConfig } from "vitest/config";
import wasm from "vite-plugin-wasm";

export default defineConfig({
    test: { globals: true, environment: "node" },
    plugins: [wasm()],
});
```

**setup.ts**:

```typescript
import { instantiate } from "../.build/plugins/PackageToJS/outputs/Package/instantiate.js";
import { defaultNodeSetup } from "../.build/plugins/PackageToJS/outputs/Package/platforms/node.js";

export async function load() {
    const options = await defaultNodeSetup();
    return await instantiate({ ...options, getImports: () => ({}) });
}
```

### Example Test

```typescript
import { describe, expect, test } from "vitest";
import { load } from "./setup";

describe("MyApp", async () => {
    const { exports } = await load();

    test("greeter works", () => {
        const greeter = new exports.Greeter("World");
        expect(greeter.greet()).toBe("Hello, World!");
        greeter.name = "Swift";
        expect(greeter.greet()).toBe("Hello, Swift!");
        greeter.release();
    });

    test("enums work", () => {
        expect(exports.Direction.North).toBe(0);
        expect(exports.setDirection(exports.Direction.South)).toBe(exports.Direction.South);
    });

    test("optionals work", () => {
        expect(exports.roundTripOptionalString(null)).toBeNull();
        expect(exports.roundTripOptionalString("test")).toBe("test");
    });
});
```

### Run

```bash
# Build Swift first
swift package --swift-sdk $SWIFT_SDK_ID js

# Run tests
npx vitest run
```

## Tips

### Memory Management

Always call `release()` on Swift objects when done:

```javascript
const greeter = new exports.Greeter("Test");
// ... use greeter ...
greeter.release();
```
