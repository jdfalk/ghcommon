<!-- file: copilot/code-style-csharp.md -->
<!-- version: 1.0.0 -->
<!-- guid: 123e4567-e89b-12d3-a456-426614174000 -->

# C# Coding Style Guide (Google Style)

This guide is based on the [Google C# Style Guide](https://google.github.io/styleguide/csharp-style.html) and provides comprehensive guidelines for writing clean, consistent C# code.

## Naming Conventions

### Code Elements

- **Classes, methods, enumerations, public fields, public properties, namespaces**: `PascalCase`
- **Local variables, parameters**: `camelCase`
- **Private, protected, internal fields and properties**: `_camelCase` (underscore prefix)
- **Interfaces**: Start with `I`, e.g., `IInterface`
- **Constants**: Naming convention unaffected by `const`, `static`, `readonly` modifiers

### Files and Directories

- **Filenames and directory names**: `PascalCase`, e.g., `MyFile.cs`
- **File naming**: Prefer file name matches main class name, e.g., `MyClass.cs`
- **Class organization**: Generally prefer one core class per file

## Formatting Guidelines

### Whitespace Rules

- **Indentation**: 2 spaces, no tabs
- **Column limit**: 100 characters
- **Statement structure**: Maximum one statement per line
- **Assignment structure**: Maximum one assignment per statement
- **Braces**:
  - No line break before opening brace
  - No line break between closing brace and `else`
  - Use braces even when optional
- **Spacing**:
  - Space after `if`/`for`/`while` etc., and after commas
  - No space after opening parenthesis or before closing parenthesis
  - No space between unary operator and operand
  - One space between operator and each operand for binary operators

### Line Wrapping

- **Continuations**: Generally indented 4 spaces
- **Function arguments**:
  - If arguments don't fit on one line, align with first argument
  - If alignment doesn't fit, place on subsequent lines with 4-space indent
- **Braces**: Line breaks with braces (list initializers, lambdas, object initializers) don't count as continuations

### Code Organization

- **Modifier order**: `public protected internal private new abstract virtual override sealed static readonly extern unsafe volatile async`
- **Using statements**:
  - Go at the top, before namespaces
  - Alphabetical order, except `System` imports first
- **Class member ordering**:
  1. Nested classes, enums, delegates, events
  2. Static, const, readonly fields
  3. Fields and properties
  4. Constructors and finalizers
  5. Methods
- **Access modifier ordering**: public → internal → protected internal → protected → private
- **Interface implementations**: Group together when possible

## C# Coding Guidelines

### Variables and Fields

- **Constants**: Variables and fields that can be `const` should always be `const`
- **Readonly**: Use `readonly` when `const` isn't possible
- **Named constants**: Prefer named constants over magic numbers
- **Field initializers**: Generally encouraged

### Collections and Containers

- **Input parameters**: Use most restrictive collection type (`IReadOnlyCollection`/`IReadOnlyList`/`IEnumerable`)
- **Output parameters**: Prefer `IList` when transferring ownership, most restrictive option otherwise
- **Arrays vs List**:
  - Prefer `List<>` for public variables, properties, return types
  - Use `List<>` when size can change
  - Use arrays when size is fixed and known at construction
  - Use arrays for multidimensional arrays

### Properties and Methods

- **Property styles**:
  - Single-line read-only properties: prefer expression body (`=>`)
  - Everything else: use `{ get; set; }` syntax
- **Expression body syntax**:
  - Use judiciously in lambdas and properties
  - Don't use on method definitions
  - Align closing with first character of opening brace line

### Classes and Structs

- **Default choice**: Almost always use a class
- **Struct usage**: Consider when type can be treated like value types (small, short-lived, or embedded)
- **Good struct examples**: Vector3, Quaternion, Bounds

### Advanced Features

#### Extension Methods

- Only use when source of original class unavailable or changing source not feasible
- Only for 'core' general features appropriate for original class
- Only in core libraries available everywhere
- Be aware they obfuscate code - err on side of not adding

#### LINQ

- Prefer single-line LINQ calls and imperative code over long chains
- Prefer member extension methods over SQL-style keywords
- Avoid `Container.ForEach(...)` for anything longer than single statement

#### ref and out Parameters

- Use `out` for returns that aren't also inputs
- Place `out` parameters after all other parameters
- Use `ref` rarely, only when mutating input is necessary
- Don't use `ref` for optimization or passing modifiable containers

### String Handling

- **String operations**: Use whatever is easiest to read
- **Performance**: Be aware chained `operator+` is slower and causes memory churn
- **Multiple concatenations**: Use `StringBuilder` when performance matters
- **String interpolation**: Generally preferred for readability

### Variable Declaration

- **var keyword usage**:
  - **Encouraged**: When type is obvious or for transient variables
  - **Discouraged**: With basic types or when users benefit from knowing type
- **Examples**:

  ```csharp
  var apple = new Apple();           // Good - obvious type
  var request = Factory.Create();    // Good - obvious from method
  var item = GetItem();              // Good - transient variable

  int success = true;                // Bad - should be bool
  float number = 12 * ReturnsFloat(); // Bad - unclear numeric type
  ```

### Object Construction

- **Object initializer syntax**: Fine for 'plain old data' types
- **Avoid with constructors**: Don't use for classes/structs with constructors
- **Multi-line formatting**: Indent one block level when splitting across lines

### Error Handling and Null Values

- **Struct returns**: Prefer returning success boolean and struct `out` value
- **Nullable structs**: Acceptable when performance isn't concern and improves readability
- **Delegate calls**: Use `Invoke()` with null conditional operator: `SomeDelegate?.Invoke()`

### Code Documentation

- **Attributes**: Appear on line above associated member, separated by newline
- **Multiple attributes**: Separate by newlines for easier maintenance
- **Argument clarity**: Use named constants, enums, named variables, or Named Arguments for unclear parameters

## Example Code Structure

```csharp
using System;                                       // using goes at top, outside namespace

namespace MyNamespace {                             // Namespaces are PascalCase
  public interface IMyInterface {                   // Interfaces start with 'I'
    public int Calculate(float value, float exp);   // Methods are PascalCase
  }

  public enum MyEnum {                              // Enumerations are PascalCase
    Yes,                                            // Enumerators are PascalCase
    No,
  }

  public class MyClass {                            // Classes are PascalCase
    public int Foo = 0;                             // Public members are PascalCase
    public bool NoCounting = false;                 // Field initializers encouraged
    private int _results;                           // Private members are _camelCase
    private const int _bar = 100;                   // const doesn't affect naming

    private int[] _someTable = {                    // Container initializers use 2
      2, 3, 4,                                      // space indent
    }

    public MyClass() {
      _results = new Results {
        NumNegativeResults = 1,                     // Object initializers use 2
        NumPositiveResults = 1,                     // space indent
      };
    }

    public int CalculateValue(int mulNumber) {      // No line break before opening brace
      var resultValue = Foo * mulNumber;            // Local variables are camelCase
      Foo += _bar;

      if (!NoCounting) {                            // Space after 'if', braces always used
        if (resultValue < 0) {                      // Spaces around comparison operators
          _results.NumNegativeResults++;
        } else if (resultValue > 0) {               // No newline between brace and else
          _results.NumPositiveResults++;
        }
      }

      return resultValue;
    }

    void DoNothing() {}                             // Empty blocks may be concise

    // Function arguments - align with first argument when possible
    void AVeryLongFunctionName(int longArgumentName,
                              int p1, int p2) {}

    // Or wrap all arguments with 4-space indent when alignment doesn't fit
    void AnotherLongFunctionName(
        int longArgumentName, int longArgumentName2, int longArgumentName3) {}
  }
}
```

## Best Practices Summary

1. **Follow naming conventions** consistently (PascalCase for public, \_camelCase for private)
2. **Use 2-space indentation** and 100-character line limit
3. **Prefer explicit types** except when `var` improves readability
4. **Use `const` and `readonly`** appropriately
5. **Choose appropriate collection types** based on usage
6. **Keep classes focused** - prefer composition over large inheritance hierarchies
7. **Use meaningful names** and avoid abbreviations
8. **Document non-obvious code** with clear comments
9. **Follow consistent organization** of class members
10. **Prefer simple, readable code** over clever optimizations

This style guide ensures consistency with Google's broader style guidelines while maintaining C#-specific best practices and .NET conventions.
