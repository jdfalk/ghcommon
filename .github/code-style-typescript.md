# TypeScript Code Style Guide

This guide follows Google's TypeScript Style Guide, which builds upon the JavaScript style guide with TypeScript-specific additions.

## Core TypeScript Guidelines

- Use TypeScript strict mode (`"strict": true` in tsconfig.json)
- Prefer interfaces over type aliases for object types
- Use explicit type annotations for function returns when not obvious
- Use type inference for local variables when types are obvious

## Types and Interfaces

- Use PascalCase for type names and interface names
- Prefix interface names with `I` only in rare cases where required by frameworks
- Use descriptive names that reflect the purpose, not the structure
- Use readonly for immutable properties
- Mark optional properties with `?` suffix

```typescript
interface User {
  readonly id: string;
  name: string;
  email: string;
  phoneNumber?: string;
}
```

## Type Annotations

- Annotate function parameters and return types
- Avoid `any` type as much as possible
- Use union types instead of optional parameters when there's a logical distinction
- Use intersection types for composition

```typescript
function processUser(user: User): Promise<ProcessedUser> {
  // Implementation
}

// Union type example
function getId(user: User | number): string {
  // Implementation
}
```

## Generics

- Use descriptive generic type parameter names (e.g., `TValue` instead of just `T`)
- Constrain generic types when possible
- Keep generic functions simple and focused

```typescript
function getProperty<TObject, TKey extends keyof TObject>(obj: TObject, key: TKey): TObject[TKey] {
  return obj[key];
}
```

## Null and Undefined

- Use `undefined` for unintentional absence of value
- Use `null` only when explicitly required by APIs
- Use non-null assertion (`!`) only when you're certain a value cannot be null/undefined
- Use optional chaining (`?.`) for potentially undefined properties

## Async Code

- Use `async`/`await` over Promises with `.then`/`.catch`
- Always properly type Promise-returning functions
- Handle errors properly in async functions

```typescript
async function fetchUserData(userId: string): Promise<UserData> {
  try {
    const response = await fetch(`/api/users/${userId}`);
    if (!response.ok) {
      throw new Error(`HTTP error ${response.status}`);
    }
    return await response.json() as UserData;
  } catch (error) {
    console.error('Failed to fetch user data', error);
    throw error;
  }
}
```

## Classes

- Use parameter properties for simple class members
- Explicitly define access modifiers (public, private, protected)
- Prefer readonly for immutable properties
- Use private fields (#) for truly private members in newer code

```typescript
class UserService {
  readonly #apiClient: ApiClient;

  constructor(private readonly baseUrl: string) {
    this.#apiClient = new ApiClient(baseUrl);
  }

  public async getUser(id: string): Promise<User> {
    // Implementation
  }
}
```

## Imports and Exports

- Use ES module syntax (`import`/`export`)
- Use named exports over default exports
- Group and organize imports logically
- Don't use namespace imports (`import * as foo`)

## Tool Configuration

- Use tslint or eslint with typescript-eslint
- Enable strict type checking
- Configure formatting tools consistent with Google's style
- Include `noImplicitAny` and `strictNullChecks` in compiler options
