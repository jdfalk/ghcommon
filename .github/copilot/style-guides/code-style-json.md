<!-- file: copilot/code-style-json.md -->
<!-- version: 1.0.0 -->
<!-- guid: 7b2e1c3d-4f5a-6b7c-8d9e-0a1b2c3d4e5f -->

<!-- Google JSON Style Guide Summary -->
<!-- Source: https://google.github.io/styleguide/jsoncstyleguide.xml -->

# JSON Style Guide (Google)

This document summarizes Google's JSON style guide for use in code generation and review.

## Core Principles

- **Consistency**: Follow the same conventions throughout all JSON files
- **Readability**: Format JSON to be easily readable by humans
- **Validity**: Ensure all JSON is well-formed and valid
- **Clarity**: Use meaningful property names and structure
- **Simplicity**: Keep JSON structure as simple as possible

## General Guidelines

### JSON Format

- Use proper JSON syntax as defined by RFC 7159
- JSON must be valid and well-formed
- Use UTF-8 encoding

### Property Names

- Property names must be camelCase
- Property names should be meaningful and descriptive
- Avoid abbreviations unless they're widely understood

```json
{
  "firstName": "John",
  "lastName": "Doe",
  "emailAddress": "john.doe@example.com",
  "phoneNumber": "+1-555-123-4567"
}
```

### Reserved Names

- Avoid using JavaScript reserved words as property names
- Don't use property names that could conflict with standard methods

```json
// Good
{
  "itemType": "book",
  "dataValue": 42,
  "identifier": "abc123"
}

// Avoid
{
  "class": "book",
  "function": 42,
  "constructor": "abc123"
}
```

## Property Value Guidelines

### Property Value Format

- Use appropriate JSON data types (string, number, boolean, array, object, null)
- Be consistent with data types across similar properties

```json
{
  "id": 12345,
  "name": "Example Item",
  "isActive": true,
  "price": 29.99,
  "tags": ["electronics", "gadget"],
  "metadata": {
    "createdAt": "2023-12-01T10:00:00Z",
    "updatedAt": "2023-12-01T15:30:00Z"
  },
  "description": null
}
```

### Property Value Data Types

#### Strings

- Use double quotes for all strings
- Escape special characters properly
- Use meaningful string values

```json
{
  "message": "Hello, \"world\"!",
  "path": "/api/v1/users",
  "htmlContent": "<p>This is a paragraph</p>",
  "unicodeText": "こんにちは"
}
```

#### Numbers

- Use appropriate numeric format (integer or decimal)
- Don't use leading zeros for decimals
- Use scientific notation for very large or small numbers when appropriate

```json
{
  "count": 42,
  "price": 19.99,
  "percentage": 0.75,
  "largeNumber": 1.23e10,
  "smallNumber": 1.23e-5
}
```

#### Booleans

- Use true/false (lowercase)
- Use booleans for binary states

```json
{
  "isEnabled": true,
  "hasPermission": false,
  "isVisible": true
}
```

#### Arrays

- Use arrays for ordered collections
- Keep array elements consistent in type when logical
- Use meaningful names for array properties

```json
{
  "userIds": [1, 2, 3, 4, 5],
  "tags": ["json", "style", "guide"],
  "coordinates": [40.7128, -74.006],
  "mixedArray": ["text", 42, true, null]
}
```

#### Objects

- Use objects for structured data
- Keep object structure consistent across similar items
- Nest objects when it makes logical sense

```json
{
  "user": {
    "id": 12345,
    "profile": {
      "firstName": "John",
      "lastName": "Doe",
      "avatar": {
        "url": "https://example.com/avatar.jpg",
        "width": 200,
        "height": 200
      }
    },
    "preferences": {
      "theme": "dark",
      "language": "en-US",
      "notifications": {
        "email": true,
        "push": false
      }
    }
  }
}
```

#### Null Values

- Use null for explicitly empty values
- Consider omitting properties instead of setting to null when appropriate

```json
{
  "name": "John Doe",
  "middleName": null,
  "nickname": "Johnny"
}
```

## Property Value Formatting

### Empty/Null/Missing Properties

#### Null

- Use null to represent an explicitly empty value
- Use null when the property exists but has no value

```json
{
  "firstName": "John",
  "middleName": null,
  "lastName": "Doe"
}
```

#### Empty Strings

- Use empty strings when a string property exists but is empty
- Distinguish between null (no value) and empty string (empty value)

```json
{
  "title": "Document Title",
  "subtitle": "",
  "description": null
}
```

#### Empty Arrays

- Use empty arrays when a collection exists but contains no items
- Distinguish between null (no collection) and empty array (empty collection)

```json
{
  "primaryTags": ["important", "urgent"],
  "secondaryTags": [],
  "archivedTags": null
}
```

#### Missing Properties

- Omit properties that don't apply or aren't available
- Document which properties are optional vs required

```json
{
  "id": 12345,
  "name": "John Doe",
  "email": "john@example.com"
  // phoneNumber omitted because not available
}
```

## Formatting and Whitespace

### Indentation

- Use 2 spaces for indentation
- Be consistent throughout the file
- Don't use tabs

```json
{
  "user": {
    "profile": {
      "name": "John Doe",
      "settings": {
        "theme": "dark"
      }
    }
  }
}
```

### Line Breaks and Spacing

- Put opening braces on the same line
- Put closing braces on their own line
- Use consistent spacing around colons and commas

```json
{
  "firstName": "John",
  "lastName": "Doe",
  "contacts": {
    "email": "john@example.com",
    "phone": "+1-555-123-4567"
  },
  "addresses": [
    {
      "type": "home",
      "street": "123 Main St",
      "city": "Anytown"
    },
    {
      "type": "work",
      "street": "456 Business Ave",
      "city": "Corporate City"
    }
  ]
}
```

### Array Formatting

#### Short Arrays

- Keep short arrays on a single line when readable

```json
{
  "coordinates": [40.7128, -74.006],
  "colors": ["red", "green", "blue"],
  "flags": [true, false, true]
}
```

#### Long Arrays

- Break long arrays across multiple lines
- Each element on its own line for complex objects

```json
{
  "users": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com"
    },
    {
      "id": 2,
      "name": "Jane Smith",
      "email": "jane@example.com"
    }
  ],
  "simpleList": ["item1", "item2", "item3", "item4"]
}
```

## Comments

### Standard JSON

- Standard JSON does not support comments
- Use external documentation for explanations
- Consider using a separate schema file for documentation

### JSON with Comments (JSONC)

- When using JSON with Comments (like in VS Code settings):
  - Use `//` for single-line comments
  - Use `/* */` for multi-line comments
  - Keep comments meaningful and concise

```jsonc
{
  // User configuration settings
  "user": {
    "name": "John Doe",
    /*
     * Email notifications are enabled by default
     * Can be disabled in user preferences
     */
    "notifications": {
      "email": true,
      "push": false, // Push notifications require mobile app
    },
  },
}
```

## Common JSON Patterns

### API Responses

```json
{
  "status": "success",
  "data": {
    "user": {
      "id": 12345,
      "username": "johndoe",
      "email": "john@example.com",
      "createdAt": "2023-01-15T10:30:00Z"
    }
  },
  "metadata": {
    "requestId": "req_abc123",
    "timestamp": "2023-12-01T15:30:00Z",
    "version": "1.0"
  }
}
```

### Error Responses

```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": [
      {
        "field": "email",
        "message": "Email format is invalid"
      },
      {
        "field": "age",
        "message": "Age must be between 13 and 120"
      }
    ]
  },
  "metadata": {
    "requestId": "req_xyz789",
    "timestamp": "2023-12-01T15:30:00Z"
  }
}
```

### Pagination

```json
{
  "data": [
    { "id": 1, "name": "Item 1" },
    { "id": 2, "name": "Item 2" },
    { "id": 3, "name": "Item 3" }
  ],
  "pagination": {
    "currentPage": 2,
    "totalPages": 10,
    "pageSize": 20,
    "totalItems": 200,
    "hasNextPage": true,
    "hasPreviousPage": true
  }
}
```

### Configuration Files

```json
{
  "application": {
    "name": "MyApp",
    "version": "1.2.3",
    "environment": "production"
  },
  "database": {
    "host": "localhost",
    "port": 5432,
    "name": "myapp_db",
    "ssl": true,
    "connectionPool": {
      "min": 5,
      "max": 20,
      "idleTimeout": 30000
    }
  },
  "logging": {
    "level": "info",
    "format": "json",
    "outputs": ["console", "file"]
  },
  "features": {
    "enableCache": true,
    "enableMetrics": true,
    "enableDebugMode": false
  }
}
```

## Validation and Tools

### JSON Schema

- Use JSON Schema to define and validate JSON structure
- Document required vs optional properties
- Specify data types and constraints

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100
    },
    "age": {
      "type": "integer",
      "minimum": 0,
      "maximum": 120
    },
    "email": {
      "type": "string",
      "format": "email"
    }
  },
  "required": ["name", "email"],
  "additionalProperties": false
}
```

### Linting and Formatting

- Use JSON linters to validate syntax
- Use formatters to ensure consistent style
- Consider tools like `jq` for command-line JSON processing

### Performance Considerations

- Keep JSON structure as flat as reasonable
- Avoid deeply nested objects when possible
- Use appropriate data types (don't stringify numbers)
- Consider compression for large JSON files

```json
// Good - appropriate nesting
{
  "user": {
    "id": 12345,
    "name": "John Doe"
  },
  "order": {
    "id": 67890,
    "total": 99.99
  }
}

// Avoid - unnecessary deep nesting
{
  "data": {
    "user": {
      "information": {
        "personal": {
          "name": {
            "first": "John",
            "last": "Doe"
          }
        }
      }
    }
  }
}
```

## Security Considerations

- Validate all JSON input
- Sanitize values that will be used in HTML contexts
- Be careful with user-generated content
- Don't include sensitive information in JSON logs

```json
// Good - safe structure
{
  "userId": 12345,
  "displayName": "John D.",
  "publicProfile": true
}

// Avoid - sensitive information
{
  "userId": 12345,
  "password": "secret123",
  "creditCardNumber": "1234-5678-9012-3456"
}
```

This style guide should be used as the foundation for all JSON formatting and structure decisions.
