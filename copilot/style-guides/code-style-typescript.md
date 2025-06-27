# file: copilot/code-style-typescript.md

<!-- Google TypeScript/JavaScript Style Guide Summary -->
<!-- Source: https://google.github.io/styleguide/tsguide.html -->
<!-- Source: https://google.github.io/styleguide/jsguide.html -->

# TypeScript/JavaScript Style Guide (Google)

This document summarizes Google's TypeScript and JavaScript style guides for use in code generation and review.

## Core Principles

- **Readability**: Code should be clear and understandable
- **Consistency**: Follow established patterns and conventions
- **Type Safety**: Use TypeScript features to catch errors at compile time
- **Simplicity**: Prefer simple, straightforward solutions

## File Organization

### File Extensions

- Use `.ts` for TypeScript files
- Use `.js` for JavaScript files
- Use `.tsx` for TypeScript files with JSX
- Use `.jsx` for JavaScript files with JSX

### Import/Export Style

```typescript
// Named imports (preferred)
import { Component, OnInit } from "@angular/core";

// Default imports
import React from "react";

// Namespace imports (when many symbols are used)
import * as fs from "fs";

// Export syntax
export class MyComponent {}
export { MyFunction, MyVariable };
export default MyClass;
```

### File Structure

- License header (if required)
- ES6 imports
- File's primary export
- Implementation

## Naming Conventions

### Variables and Functions

```typescript
// Use camelCase for variables and functions
const userName = "john";
const maxRetryCount = 3;

function calculateTotal(items: Item[]): number {
  // implementation
}

// Use descriptive names
const isUserLoggedIn = checkAuthStatus();
const userPreferences = getUserPreferences();
```

### Classes and Interfaces

```typescript
// Use PascalCase for classes and interfaces
class UserService {
  private readonly apiUrl: string;

  constructor(apiUrl: string) {
    this.apiUrl = apiUrl;
  }
}

interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
}

// Prefix interfaces with 'I' is discouraged in TypeScript
// Use descriptive names instead
interface UserSettings {
  theme: "light" | "dark";
  notifications: boolean;
}
```

### Constants

```typescript
// Use SCREAMING_SNAKE_CASE for module-level constants
const MAX_RETRY_ATTEMPTS = 3;
const API_BASE_URL = "https://api.example.com";

// Use camelCase for local constants
const defaultTimeout = 5000;
```

### Enums

```typescript
// Use PascalCase for enum names and members
enum HttpStatus {
  Ok = 200,
  BadRequest = 400,
  Unauthorized = 401,
  NotFound = 404,
  InternalServerError = 500,
}

// Prefer string enums for better debugging
enum Theme {
  Light = "light",
  Dark = "dark",
  Auto = "auto",
}
```

## Type Annotations

### Function Types

```typescript
// Always annotate function parameters and return types
function processUser(user: User, options: ProcessOptions): Promise<Result> {
  // implementation
}

// Use arrow functions for short functions
const isEven = (num: number): boolean => num % 2 === 0;

// Generic functions
function identity<T>(arg: T): T {
  return arg;
}
```

### Variable Types

```typescript
// Let TypeScript infer simple types
const message = "Hello, world!"; // string inferred
const count = 42; // number inferred

// Annotate when inference isn't clear
const users: User[] = [];
const config: Partial<Config> = {};

// Use explicit types for complex objects
const apiResponse: ApiResponse<User[]> = {
  data: users,
  status: 200,
  message: "Success",
};
```

## Code Formatting

### Line Length

- Maximum 80 characters per line
- Break long lines at logical points

### Indentation

- Use 2 spaces for indentation
- No tabs

### Semicolons

- Always use semicolons to terminate statements

```typescript
const message = "Hello, world!";
doSomething();
```

### Quotes

- Use single quotes for strings
- Use template literals for string interpolation

```typescript
const name = "John";
const greeting = `Hello, ${name}!`;
```

### Trailing Commas

- Use trailing commas in multiline structures

```typescript
const config = {
  apiUrl: "https://api.example.com",
  timeout: 5000,
  retries: 3, // trailing comma
};

const items = [
  "apple",
  "banana",
  "cherry", // trailing comma
];
```

## Type Definitions

### Interface vs Type

```typescript
// Use interfaces for object shapes that might be extended
interface User {
  id: string;
  name: string;
  email: string;
}

interface AdminUser extends User {
  permissions: string[];
}

// Use type aliases for unions, primitives, or computed types
type Status = "pending" | "approved" | "rejected";
type EventHandler<T> = (event: T) => void;
type UserKeys = keyof User;
```

### Generic Constraints

```typescript
// Use extends for generic constraints
interface Identifiable {
  id: string;
}

function updateEntity<T extends Identifiable>(
  entity: T,
  updates: Partial<T>,
): T {
  return { ...entity, ...updates };
}
```

### Utility Types

```typescript
// Use built-in utility types
type PartialUser = Partial<User>;
type RequiredUser = Required<User>;
type UserEmail = Pick<User, "email">;
type UserWithoutId = Omit<User, "id">;
```

## Error Handling

### Error Types

```typescript
// Create custom error classes
class ValidationError extends Error {
  constructor(
    message: string,
    public readonly field: string,
  ) {
    super(message);
    this.name = "ValidationError";
  }
}

// Use Result pattern for explicit error handling
type Result<T, E = Error> =
  | { success: true; data: T }
  | { success: false; error: E };

async function fetchUser(id: string): Promise<Result<User>> {
  try {
    const user = await apiClient.getUser(id);
    return { success: true, data: user };
  } catch (error) {
    return { success: false, error: error as Error };
  }
}
```

## Best Practices

### Null and Undefined

```typescript
// Use strict null checks
// Prefer undefined over null
function findUser(id: string): User | undefined {
  return users.find((user) => user.id === id);
}

// Use optional chaining and nullish coalescing
const userName = user?.profile?.name ?? "Anonymous";
```

### Array and Object Manipulation

```typescript
// Use array methods instead of loops
const activeUsers = users.filter((user) => user.isActive);
const userNames = users.map((user) => user.name);
const totalAge = users.reduce((sum, user) => sum + user.age, 0);

// Use object spread for copying
const updatedUser = { ...user, lastLogin: new Date() };

// Use destructuring for extraction
const { name, email } = user;
const [first, second, ...rest] = items;
```

### Async/Await

```typescript
// Prefer async/await over promises
async function processUsers(): Promise<void> {
  try {
    const users = await fetchUsers();
    await Promise.all(users.map((user) => processUser(user)));
  } catch (error) {
    logger.error("Failed to process users:", error);
    throw error;
  }
}

// Handle multiple async operations
async function loadData(): Promise<[User[], Post[]]> {
  const [users, posts] = await Promise.all([fetchUsers(), fetchPosts()]);
  return [users, posts];
}
```

### Function Design

```typescript
// Keep functions small and focused
function validateEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

// Use pure functions when possible
function calculateTax(amount: number, rate: number): number {
  return amount * rate;
}

// Use function overloads for different signatures
function createElement(tag: "div"): HTMLDivElement;
function createElement(tag: "span"): HTMLSpanElement;
function createElement(tag: string): HTMLElement {
  return document.createElement(tag);
}
```

## Testing

### Test Structure

```typescript
describe("UserService", () => {
  let userService: UserService;

  beforeEach(() => {
    userService = new UserService();
  });

  describe("validateUser", () => {
    it("should return true for valid user", () => {
      const user = { id: "1", name: "John", email: "john@example.com" };
      expect(userService.validateUser(user)).toBe(true);
    });

    it("should return false for invalid email", () => {
      const user = { id: "1", name: "John", email: "invalid-email" };
      expect(userService.validateUser(user)).toBe(false);
    });
  });
});
```

## Comments and Documentation

### JSDoc Comments

```typescript
/**
 * Calculates the total price including tax.
 * @param basePrice - The base price before tax
 * @param taxRate - The tax rate as a decimal (e.g., 0.1 for 10%)
 * @returns The total price including tax
 * @throws {ValidationError} When basePrice or taxRate is negative
 */
function calculateTotalPrice(basePrice: number, taxRate: number): number {
  if (basePrice < 0 || taxRate < 0) {
    throw new ValidationError("Price and tax rate must be non-negative");
  }
  return basePrice * (1 + taxRate);
}
```

### Inline Comments

```typescript
// Use comments to explain why, not what
const retryDelay = 1000; // Wait 1 second between retries to avoid rate limiting

// Explain complex logic
if (user.lastLogin && Date.now() - user.lastLogin.getTime() > SESSION_TIMEOUT) {
  // Session has expired, redirect to login
  redirectToLogin();
}
```

## Tools and Configuration

### ESLint Configuration

- Use `@typescript-eslint/parser`
- Enable strict type checking rules
- Configure for Google style preferences

### Prettier Configuration

- Single quotes
- No semicolons (if preferred)
- Trailing commas
- 80-character line length

### TypeScript Configuration

```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "noImplicitReturns": true,
    "noImplicitThis": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  }
}
```

This style guide should be used as the foundation for all TypeScript and JavaScript code generation and formatting decisions.
