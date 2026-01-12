# Common Patterns and Best Practices

Practical patterns and common pitfalls when building applications with JavaScriptKit.

## Architectural Approaches

There are two primary ways to architect a WebAssembly application with JavaScriptKit, depending on how much of the web ecosystem you want to leverage.

### 1. Pure Swift (Full-Stack Swift)

In this approach, Swift handles everything: DOM manipulation, state management, and application logic.

- **How it works**: Swift uses JavaScriptKit to call DOM APIs directly (e.g., `document.createElement`, `addEventListener`).
- **Declarative Alternative**: Instead of raw DOM manipulation, you can use declarative UI libraries like [Elementary](https://elementary.codes/), which provides a more Swift-native way to build HTML components.
- **Best for**: Small to medium applications, developers who prefer staying entirely within Swift, or when porting existing Swift logic that heavily controls its own UI.
- **Data Flow**: Swift → JavaScript (DOM APIs).

### 2. Core Logic in Swift (Hybrid Approach)

In this approach, modern web frameworks (like React, Vue, or Svelte) handle the UI and state management, while Swift provides the heavy-duty business logic.

- **How it works**: Swift exposes specific functions or objects to the JavaScript `global` object. The JavaScript UI then calls into these Swift APIs.
- **Best for**: Applications requiring complex UIs, leveraging existing web components/libraries, or when Swift is only needed for specialized tasks (e.g., data processing, cryptography, shared logic with a mobile app).
- **Data Flow**: JavaScript (UI) → Swift (Core Logic).

#### Example: Exposing Swift API to JavaScript

```swift
// Swift side
let api = JSObject()
api.processData = JSClosure { args in
    let input = args[0].string ?? ""
    let result = HeavyLogic.process(input)
    return .string(result)
}
JSObject.global.mySwiftApp = .object(api)
```

```javascript
// JavaScript side (e.g., in a React component)
const result = window.mySwiftApp.processData("input data");
```

## Memory Management and Closures

JavaScript does not participate in Swift's Automatic Reference Counting (ARC). You must manually manage the lifetime of Swift objects and closures that are exposed to JavaScript.

### Retaining Closures

`JSClosure` instances must be retained by the Swift side as long as they are expected to be called by JavaScript. If a `JSClosure` is deallocated, any attempt by JavaScript to call it will result in a crash.

When using `[weak self]` in a closure, ensure the capturing object is also retained.

```swift
class UIManager {
    private var clickHandler: JSClosure?
    private let button: JSObject

    init(button: JSObject) {
        self.button = button
        
        // clickHandler must be stored as a property to be retained
        self.clickHandler = JSClosure { [weak self] _ in
            self?.handleClick()
            return .undefined
        }
        _ = button.addEventListener!("click", clickHandler!)
    }

    func handleClick() {
        // ...
    }
}
```

### Cleanup in `deinit`

When an object owning an event listener is deallocated, it is recommended to remove the event listener from the DOM to avoid memory leaks or attempts to call deallocated closures.

```swift
class UIManager {
    private var clickHandler: JSClosure?
    private let button: JSObject

    // ... init ...

    deinit {
        if let handler = clickHandler {
            _ = button.removeEventListener!("click", handler)
        }
    }
}
```

### Application Lifetime Objects

For root-level UI managers or state containers that should live for the duration of the application, store them in a static property in your `@main` entry point.

```swift
@main
struct MyApp {
    static nonisolated(unsafe) var ui: UIManager!

    static func main() {
        let ui = UIManager()
        ui.setup()
        Self.ui = ui // Retain for application lifetime
    }
}
```

## Event Handling Recipes

### Input Handling (Enter Key)

```swift
let input = document.getElementById!("text-input").object!
let closure = JSClosure { [weak self] args in
    guard let event = args.first?.object,
          event.key.string == "Enter" else { return .undefined }
    
    self?.handleSubmit()
    return .undefined
}
_ = input.addEventListener!("keydown", closure)
```

### Checkbox/Toggle

```swift
let checkbox = document.getElementById!("toggle").object!
let closure = JSClosure { [weak self] _ in
    let isChecked = checkbox.checked.boolean ?? false
    self?.updateToggleState(isChecked)
    return .undefined
}
_ = checkbox.addEventListener!("change", closure)
```

## Common Gotchas

### Property Assignment

Values must be converted to `JSValue` using `.jsValue` or explicit wrappers like `.string()`.

```swift
let text = "Hello"
// Correct
element.textContent = .string(text)
element.textContent = text.jsValue

// Incorrect
element.textContent = text
```

### Method Calls vs. Properties

Ensure you use `!` only for method calls that return an optional closure via Dynamic Member Lookup.

```swift
// Method call (requires !)
_ = document.createElement!("div")

// Property access (no !)
let body = document.body.object!
```

### Discarding Results

Many JavaScript methods return a value that Swift requires you to handle. Use `_ =` to silence warnings.

```swift
_ = document.body.object!.appendChild!(element)
```
