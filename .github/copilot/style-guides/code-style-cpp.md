<!-- file: copilot/code-style-cpp.md -->
<!-- version: 1.0.0 -->
<!-- guid: 6c5d4e3f-2b1a-0c9d-8e7f-6a5b4c3d2e1f -->

<!-- Google C++ Style Guide Summary -->
<!-- Source: https://google.github.io/styleguide/cppguide.html -->

# C++ Style Guide (Google)

This document summarizes Google's C++ style guide for use in code generation and review.

## Core Principles

- **Optimize for the reader, not the writer**: Code should be clear and maintainable
- **Be consistent with existing code**: Follow established patterns within the codebase
- **Be consistent with the broader C++ community when appropriate**: Use standard idioms
- **Avoid surprising or dangerous constructs**: Prefer safe, well-understood patterns
- **Be mindful of scale**: Consider the impact across large codebases

## C++ Version

- Target C++20, avoid C++23 features
- Do not use non-standard extensions
- Consider portability when using newer features

## Header Files

### Self-contained Headers

- Header files should be self-contained and compile on their own
- Use `.h` extension for headers, `.cc` for source files
- Include all dependencies needed for the header

### Header Guards

```cpp
#ifndef PROJECT_PATH_FILE_H_
#define PROJECT_PATH_FILE_H_
// ...
#endif  // PROJECT_PATH_FILE_H_
```

### Include Order

1. Related header
2. Blank line
3. C system headers
4. Blank line
5. C++ standard library headers
6. Blank line
7. Other libraries' headers
8. Blank line
9. Your project's headers

```cpp
#include "foo/server/fooserver.h"

#include <sys/types.h>
#include <unistd.h>

#include <string>
#include <vector>

#include "base/basictypes.h"
#include "foo/server/bar.h"
```

## Naming Conventions

### Types

- Use PascalCase for classes, structs, enums, type aliases
- Examples: `MyExcitingClass`, `UrlTable`, `PropertiesMap`

```cpp
class UrlTable { ... };
struct UrlTableProperties { ... };
enum class UrlTableError { ... };
using PropertiesMap = hash_map<UrlTableProperties*, std::string>;
```

### Variables

- Use snake_case for variables and function parameters
- Class data members have trailing underscore
- Struct data members do not have trailing underscore

```cpp
std::string table_name;           // Local variable
std::string table_name_;          // Class member
std::string name;                 // Struct member
```

### Constants

- Use leading 'k' followed by PascalCase
- Apply to variables with static storage duration

```cpp
const int kDaysInAWeek = 7;
const int kAndroid8_0_0 = 24;
```

### Functions

- Use PascalCase for regular functions
- Accessors/mutators may use snake_case

```cpp
AddTableEntry()
DeleteUrl()
OpenFileOrDie()

// Accessors/mutators
int count() const { return count_; }
void set_count(int count) { count_ = count; }
```

### Namespaces

- Use snake_case for namespace names
- Keep names short and descriptive

```cpp
namespace url_table_errors {
namespace internal {
// Implementation details
}
}
```

## Code Organization

### Namespaces

- Place code in namespaces to avoid global scope pollution
- Do not use `using namespace` directives
- Terminate with comments

```cpp
namespace mynamespace {

// All declarations within namespace scope
class MyClass {
  // ...
};

}  // namespace mynamespace
```

### Classes

#### Access Control

- Make data members private unless they are constants
- Use public/protected/private sections in that order

#### Declaration Order

1. Types and type aliases
2. Static constants
3. Factory functions
4. Constructors and assignment operators
5. Destructor
6. Other functions
7. Data members

```cpp
class MyClass : public OtherClass {
 public:  // 1 space indent
  MyClass();  // 2 space indent
  explicit MyClass(int var);
  ~MyClass() {}

  void SomeFunction();
  void set_some_var(int var) { some_var_ = var; }
  int some_var() const { return some_var_; }

 private:
  bool SomeInternalFunction();
  int some_var_;
  int some_other_var_;
};
```

### Functions

#### Function Design

- Keep functions short and focused (aim for ~40 lines)
- Use clear parameter names
- Prefer return values over output parameters

```cpp
// Good - clear purpose and parameters
std::unique_ptr<Foo> CreateFoo(const Config& config);

// Avoid - unclear output parameters
void CreateFoo(const Config& config, Foo** result);
```

#### Function Declarations

```cpp
ReturnType ClassName::FunctionName(Type par_name1, Type par_name2) {
  DoSomething();
  // ...
}

// Long parameter lists
ReturnType ClassName::ReallyLongFunctionName(
    Type par_name1,  // 4 space indent
    Type par_name2,
    Type par_name3) {
  DoSomething();  // 2 space indent
  // ...
}
```

## Type System and Safety

### Type Annotations

- Use exact-width integer types from `<stdint.h>`
- Prefer `int64_t` over `long`, `int16_t` over `short`
- Use `int` for loop counters and small values

```cpp
int count = 0;                    // OK for small values
int64_t large_number = 1000000;   // Use for large values
uint32_t flags = 0;               // OK for bit patterns
```

### Const Usage

- Use `const` liberally in APIs
- Mark methods `const` when they don't modify object state
- Use const references for non-optional input parameters

```cpp
class Calculator {
 public:
  int Add(int a, int b) const;                    // Doesn't modify state
  void ProcessItems(const std::vector<Item>& items) const;  // Const reference

 private:
  mutable int cache_hits_;  // Can be modified in const methods
};
```

### Smart Pointers

- Prefer `std::unique_ptr` for single ownership
- Use `std::shared_ptr` sparingly for shared ownership
- Avoid raw pointers for ownership

```cpp
// Good - clear ownership transfer
std::unique_ptr<Foo> CreateFoo();
void ProcessFoo(std::unique_ptr<Foo> foo);

// Use shared_ptr only when necessary
std::shared_ptr<const Foo> GetSharedFoo();
```

## Modern C++ Features

### Auto and Type Deduction

- Use `auto` when it makes code clearer or safer
- Avoid `auto` when the type provides important information

```cpp
// Good uses of auto
auto widget = std::make_unique<WidgetWithBellsAndWhistles>(arg1, arg2);
auto it = my_map.find(key);

// Provide explicit types when clarity is important
const std::string user_name = GetUserName();  // Clear intent
```

### Range-based for Loops

```cpp
// Prefer range-based loops
for (const auto& item : container) {
  ProcessItem(item);
}

// Use references to avoid copies
for (auto& item : mutable_container) {
  item.Update();
}
```

### Lambda Expressions

- Use lambda expressions for short, local functions
- Prefer explicit captures over default captures
- Use explicit capture when lambda may escape scope

```cpp
// Good - explicit capture
std::sort(vec.begin(), vec.end(), [](const Item& a, const Item& b) {
  return a.priority() > b.priority();
});

// Good - explicit capture when escaping scope
executor->Schedule([foo = std::move(foo)] { ProcessFoo(foo); });
```

## Error Handling

### Return Values vs Exceptions

- Google codebase does not use exceptions
- Use return values or output parameters for error handling
- Consider using `absl::Status` or similar for error reporting

```cpp
// Good - clear error handling
absl::StatusOr<std::string> ReadFile(const std::string& filename);

// Alternative approach
enum class ReadResult { kSuccess, kFileNotFound, kPermissionDenied };
ReadResult ReadFile(const std::string& filename, std::string* content);
```

## Formatting Rules

### Line Length

- Maximum 80 characters per line
- Break at logical points when necessary

### Indentation

- Use 2 spaces for indentation
- Use spaces, not tabs

### Braces

- Opening brace on same line as declaration
- Closing brace on its own line

```cpp
if (condition) {
  DoSomething();
} else {
  DoSomethingElse();
}

class MyClass {
 public:
  MyClass() {}
};
```

### Spacing

```cpp
// Spaces around operators
int result = a + b * c;

// No space around member access
obj.method();
ptr->member;

// Space after keywords
if (condition) {}
for (int i = 0; i < n; ++i) {}
```

## Comments and Documentation

### Function Comments

- Document what the function does, not how
- Include parameter descriptions for non-obvious cases
- Document ownership and lifetime requirements

```cpp
// Returns an iterator positioned at the first entry lexically greater
// than or equal to start_word. If no such entry exists, returns nullptr.
// The caller must not use the iterator after the underlying table
// has been destroyed.
std::unique_ptr<Iterator> GetIterator(absl::string_view start_word) const;
```

### Class Comments

- Describe the purpose and usage of the class
- Include example usage when helpful
- Document thread safety requirements

```cpp
// Iterates over the contents of a GargantuanTable.
// Example:
//   std::unique_ptr<GargantuanTableIterator> iter = table->NewIterator();
//   for (iter->Seek("foo"); !iter->done(); iter->Next()) {
//     process(iter->key(), iter->value());
//   }
class GargantuanTableIterator {
  // ...
};
```

### TODO Comments

```cpp
// TODO: bug 12345678 - Remove this after the 2047q4 compatibility window
// TODO(username): Use a "*" here for concatenation operator
```

## Best Practices

### Performance

- Profile before optimizing
- Prefer value semantics when appropriate
- Use move semantics for expensive-to-copy objects

### Thread Safety

- Document thread safety assumptions
- Use appropriate synchronization primitives
- Prefer immutable objects when possible

### Testing

- Write comprehensive tests for new functionality
- Use descriptive test names
- Follow the same style rules in test code

## Prohibited Features

- Do not use exceptions
- Avoid RTTI (dynamic_cast, typeid)
- Do not use `using namespace` directives
- Avoid multiple inheritance (except for interfaces)
- Do not use GNU-style variadic macros

## Tools and Enforcement

### Recommended Tools

- Use `clang-format` for automatic formatting
- Use `cpplint.py` for style checking
- Enable appropriate compiler warnings (-Wall, -Wextra)

### Build Configuration

- Treat warnings as errors in production code
- Use static analysis tools when available
- Enable address sanitizer and other debugging tools during development

This style guide should be used as the foundation for all C++ code generation and formatting decisions.
