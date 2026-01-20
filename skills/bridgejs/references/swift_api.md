# BridgeJS Swift API Reference

## Type Mapping

| TypeScript | Swift |
|:-----------|:------|
| `number` | `Int`, `Float`, `Double` |
| `string` | `String` |
| `boolean` | `Bool` |
| `T \| null` | `Optional<T>` |
| `Promise<T>` | `async` functions |
| `object` | `JSObject` |
| `(args) => T` | `@escaping` closures |

## Type Bridging and Performance

| Type | Strategy | Crossing Cost | Best For |
|:-----|:---------|:--------------|:---------|
| Classes | Reference (pointer) | Low | Stateful objects, frequent method calls |
| Structs | Copy (serialize) | Medium | Small immutable data, infrequent passing |
| Enums (simple) | Copy (integer/string) | Very low | Flags, options |
| Enums (associated) | Copy (serialize payload) | Medium | Result types, variants |
| Closures | Boxed/retained | Medium | Callbacks, transforms |
| Primitives | Direct | Very low | Frequent access |
| Strings | Copy (UTF-8) | Medium | Text data |

**Classes** use `FinalizationRegistry` for automatic cleanup when JS garbage collects. Call `release()` for deterministic cleanup in performance-critical code.

**Structs/Enums** are value types - data is copied across the boundary. No shared state between Swift and JS.

**Tip:** Prefer classes for objects with many method calls. Use structs for data transfer objects passed once.

---

## Functions

```swift
import JavaScriptKit

@JS func calculateTotal(price: Double, quantity: Int) -> Double {
    return price * Double(quantity)
}

@JS func findUser(id: Int) throws(JSException) -> String {
    guard id > 0 else {
        throw JSException(JSError(message: "Invalid ID").jsValue)
    }
    return "User_\(id)"
}

@JS func fetchData(endpoint: String) async -> String {
    try? await Task.sleep(nanoseconds: 50_000_000)
    return "Data from \(endpoint)"
}

@JS func greet(name: String, greeting: String = "Hello") -> String {
    return "\(greeting), \(name)!"
}
```

**JavaScript:**

```javascript
const total = exports.calculateTotal(19.99, 3);

try {
    const user = exports.findUser(42);
} catch (e) {
    console.error(e);
}

const data = await exports.fetchData("/api");

exports.greet("World");         // "Hello, World!"
exports.greet("World", "Hi");   // "Hi, World!"
```

| Feature | Status |
|:--------|:-------|
| Primitives, String params/returns | Supported |
| `@JS class`, `@JS enum` params/returns | Supported |
| `throws(JSException)` | Supported |
| `throws` (any error) | Not supported |
| `async` | Supported |
| Default parameter values | Supported |
| Generics, opaque types | Not supported |

---

## Classes

```swift
@JS class Counter {
    @JS var count = 0
    @JS var doubled: Int { count * 2 }

    @JS init() {}

    @JS init(start: Int) throws(JSException) {
        guard start >= 0 else {
            throw JSException(JSError(message: "Start must be positive").jsValue)
        }
        self.count = start
    }

    @JS func increment() { count += 1 }
    @JS func add(_ amount: Int) { count += amount }

    @JS static var instanceCount = 0
    @JS static func resetAll() { instanceCount = 0 }
}
```

**JavaScript:**

```javascript
const counter = new exports.Counter();
counter.increment();
console.log(counter.count);     // 1
console.log(counter.doubled);   // 2
counter.release();  // explicit cleanup (optional but recommended)

// Static members
console.log(exports.Counter.instanceCount);
exports.Counter.resetAll();

// Throwing initializer
try {
    const c = new exports.Counter(-1);
} catch (e) {
    console.error(e);  // "Start must be positive"
}
```

**Generated TypeScript:**

```typescript
export interface SwiftHeapObject {
    release(): void;
}

export interface Counter extends SwiftHeapObject {
    count: number;
    readonly doubled: number;
    increment(): void;
    add(amount: number): void;
}

export type Exports = {
    Counter: {
        new(): Counter;
        new(start: number): Counter;
        instanceCount: number;
        resetAll(): void;
    };
}
```

| Feature | Status |
|:--------|:-------|
| `init()` | Supported |
| `init() throws(JSException)` | Supported |
| `init() throws` (any error) | Not supported |
| `init() async` | Not supported |
| Stored properties (`var`, `let`) | Supported |
| Computed properties | Supported |
| Instance methods | Supported |
| Static properties/methods | Supported |
| `deinit` | Supported |
| Subscripts | Not supported |
| Generics | Not supported |

---

## Structs

Structs are value types - data is copied across the Swift-JS boundary (no shared state).

```swift
@JS struct Point {
    @JS var x: Double
    @JS var y: Double
    @JS var label: String?

    @JS init(x: Double, y: Double, label: String? = nil) {
        self.x = x
        self.y = y
        self.label = label
    }
}

@JS func movePoint(_ point: Point, dx: Double, dy: Double) -> Point {
    return Point(x: point.x + dx, y: point.y + dy, label: point.label)
}

@JS struct AppConfig {
    @JS static let version = "1.0.0"
    @JS static var debugMode = false
    @JS static func reset() { debugMode = false }
}
```

**JavaScript:**

```javascript
// Structs are created via init function, returned as plain JS objects
const point = exports.Point.init(10.0, 20.0, "origin");
console.log(point.x, point.y);  // 10.0, 20.0

// Passing to Swift copies the data
const moved = exports.movePoint(point, 5.0, 5.0);
console.log(moved.x, moved.y);  // 15.0, 25.0

// Static members
console.log(exports.AppConfig.version);  // "1.0.0"
exports.AppConfig.debugMode = true;
exports.AppConfig.reset();
```

| Feature | Status |
|:--------|:-------|
| Stored properties | Supported |
| Optional properties | Supported |
| Nested structs | Supported |
| Class properties in structs | Supported |
| Static properties/methods | Supported |
| Instance methods | Not supported |
| Computed properties | Not supported |
| Generics | Not supported |

---

## Enums

### Simple Case Enums

```swift
@JS enum Direction {
    case north, south, east, west
}

@JS func setDirection(_ direction: Direction) { /* ... */ }
@JS func getDirection() -> Direction { /* ... */ }
```

**JavaScript:**

```javascript
exports.setDirection(exports.Direction.North);  // passes integer 0
const dir = exports.getDirection();
if (dir === exports.Direction.North) { /* ... */ }
```

### Raw Value Enums

```swift
@JS enum Theme: String {
    case light = "light"
    case dark = "dark"
    case system = "system"
}

@JS enum HttpStatus: Int {
    case ok = 200
    case notFound = 404
    case serverError = 500
}
```

**JavaScript:**

```javascript
exports.setTheme(exports.Theme.Dark);      // passes "dark"
exports.setStatus(exports.HttpStatus.Ok);  // passes 200
```

### Associated Value Enums

```swift
@JS enum APIResult {
    case success(String)
    case failure(Int)
    case loading
}

@JS func handleResult(_ result: APIResult) { /* ... */ }
@JS func getResult() -> APIResult { /* ... */ }
```

**JavaScript:**

```javascript
// Create with associated values
const success = { tag: exports.APIResult.Tag.Success, param0: "Data loaded" };
const failure = { tag: exports.APIResult.Tag.Failure, param0: 404 };
const loading = { tag: exports.APIResult.Tag.Loading };

exports.handleResult(success);

// Pattern match on result
const result = exports.getResult();
switch (result.tag) {
    case exports.APIResult.Tag.Success:
        console.log("Data:", result.param0);
        break;
    case exports.APIResult.Tag.Failure:
        console.log("Error code:", result.param0);
        break;
    case exports.APIResult.Tag.Loading:
        console.log("Loading...");
        break;
}
```

| Associated Value Type | Status |
|:----------------------|:-------|
| `String`, `Int`, `Bool`, `Float`, `Double` | Supported |
| Classes, structs | Not supported |
| Other enums | Not supported |
| Arrays/Collections | Not supported |
| Optionals | Not supported |

---

## Closures

Closures can be passed in both directions between Swift and JavaScript.

```swift
@JS class DataProcessor {
    @JS init() {}

    // Accept JS callback
    @JS func process(items: String, transform: @escaping (String) -> String) -> String {
        return transform(items)
    }

    // Accept callback with enum parameter
    @JS func filterDirections(callback: @escaping (Direction) -> Bool) {
        let directions: [Direction] = [.north, .south, .east, .west]
        for dir in directions {
            if callback(dir) { print("Accepted: \(dir)") }
        }
    }

    // Return Swift closure to JS
    @JS func makeMultiplier(factor: Int) -> (Int) -> Int {
        return { value in value * factor }
    }

    // Return closure with optional parameter
    @JS func makeFormatter() -> (String?) -> String {
        return { input in input ?? "N/A" }
    }
}
```

**JavaScript:**

```javascript
const processor = new exports.DataProcessor();

// Pass JS function to Swift
const result = processor.process("hello", (s) => s.toUpperCase());
console.log(result);  // "HELLO"

// Callback with enum
processor.filterDirections((dir) => dir === exports.Direction.North);

// Get Swift closure
const triple = processor.makeMultiplier(3);
console.log(triple(5));  // 15

const format = processor.makeFormatter();
console.log(format(null));    // "N/A"
console.log(format("test"));  // "test"
```

| Feature | Status |
|:--------|:-------|
| `(T) -> U` | Supported |
| `(T, U) -> V` (multiple params) | Supported |
| `(T?) -> U` (optional params) | Supported |
| `(T) -> U?` (optional return) | Supported |
| Enum parameters | Supported |
| Class parameters | Supported |
| `@escaping` | Required |
| `async` closures | Not supported |
| `throws` closures | Not supported |

---

## Protocols

Protocols enable duck-typed interoperability - JavaScript objects can implement Swift protocol requirements.

```swift
@JS protocol DataDelegate {
    var processedCount: Int { get set }
    var delegateName: String { get }

    func onDataReceived(_ data: String)
    func shouldProcess(_ item: Int) -> Bool
}

@JS class DataManager {
    private var delegate: DataDelegate

    @JS init(delegate: DataDelegate) {
        self.delegate = delegate
    }

    @JS func processItem(_ item: Int) {
        if delegate.shouldProcess(item) {
            delegate.processedCount += 1
            delegate.onDataReceived("Processed: \(item)")
        }
    }
}
```

**JavaScript:**

```javascript
// JS object implementing the protocol
const myDelegate = {
    processedCount: 0,
    delegateName: "MyDelegate",

    onDataReceived(data) {
        console.log("Received:", data);
    },
    shouldProcess(item) {
        return item > 0;
    }
};

const manager = new exports.DataManager(myDelegate);
manager.processItem(42);
console.log(myDelegate.processedCount);  // 1
```

| Feature | Status |
|:--------|:-------|
| Properties (`get`, `get set`) | Supported |
| Optional properties | Supported |
| Methods | Supported |
| Methods with return values | Supported |
| Enum parameters/returns | Supported |
| Class parameters/returns | Supported |
| Associated types | Not supported |
| Protocol inheritance | Not supported |

---

## Namespaces

### Using `@JS(namespace:)`

```swift
@JS(namespace: "MyApp.Utils")
func formatDate(timestamp: Double) -> String { /* ... */ }

@JS(namespace: "MyApp.Models")
class User {
    @JS var name: String
    @JS init(name: String) { self.name = name }
}
```

**JavaScript:**

```javascript
exports.MyApp.Utils.formatDate(Date.now());
const user = new exports.MyApp.Models.User("Alice");
```

### Using Empty Enums

```swift
@JS enum MyApp {
    @JS enum Models {
        @JS class User {
            @JS var name: String
            @JS init(name: String) { self.name = name }
        }
    }
}
```

**JavaScript:**

```javascript
const user = new exports.MyApp.Models.User("Alice");
```

**Note:** Only empty enums (no cases) work as namespaces. Nested items cannot use `@JS(namespace:)`.

---

## Importing TypeScript into Swift

Create `bridge-js.d.ts` in your target source directory:

```typescript
export function consoleLog(message: string): void;

interface Document {
    title: string;
    readonly body: HTMLElement;
    getElementById(id: string): HTMLElement;
    createElement(tagName: string): HTMLElement;
}

interface HTMLElement {
    innerText: string;
    appendChild(child: HTMLElement): void;
}

export function getDocument(): Document;
```

**Generated Swift** (all imported functions/methods throw `JSException`):

```swift
func consoleLog(_ message: String) throws(JSException)

struct Document {
    var title: String { get throws(JSException) }
    func setTitle(_ value: String) throws(JSException)
    var body: HTMLElement { get throws(JSException) }
    func getElementById(_ id: String) throws(JSException) -> HTMLElement
    func createElement(_ tagName: String) throws(JSException) -> HTMLElement
}

struct HTMLElement {
    var innerText: String { get throws(JSException) }
    func setInnerText(_ value: String) throws(JSException)
    func appendChild(_ child: HTMLElement) throws(JSException)
}

func getDocument() throws(JSException) -> Document
```

**Usage in Swift:**

```swift
@JS func setupUI() throws(JSException) {
    try consoleLog("Setting up UI")

    let doc = try getDocument()
    try doc.setTitle("My App")

    let button = try doc.createElement("button")
    try button.setInnerText("Click Me")

    let container = try doc.getElementById("app")
    try container.appendChild(button)
}
```

**Inject JS implementations:**

```javascript
const { exports } = await init({
    getImports: () => ({
        consoleLog: (msg) => console.log(msg),
        getDocument: () => document,
    })
});

exports.setupUI();
```

---

## Configuration

Create `bridge-js.config.json` in your target directory:

```json
{
    "exposeToGlobal": false,
    "tools": {
        "node": "/usr/local/bin/node"
    }
}
```

- **`exposeToGlobal`**: When `true`, exports available on `globalThis`. Default: `false`.
- **`tools.node`**: Custom path to Node.js executable.

Create `bridge-js.config.local.json` for local overrides (add to `.gitignore`).
