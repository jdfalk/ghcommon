<!-- file: copilot/code-style-swift.md -->
<!-- version: 1.0.0 -->
<!-- guid: 5d4c3b2a-1e0f-9d8c-7b6a-5c4d3e2f1a0b -->

<!-- Google Swift Style Guide Summary -->
<!-- Source: https://google.github.io/swift/ -->

# Swift Style Guide (Google)

This document summarizes Google's Swift style guide for use in code generation and review.

## Core Principles

- **Clarity**: Code should be clear and self-documenting
- **Consistency**: Follow established patterns throughout the codebase
- **Brevity**: Be concise without sacrificing clarity
- **Convention**: Follow Swift community conventions
- **Performance**: Write efficient code that performs well

## General Formatting

### Whitespace and Indentation

- Use 2 spaces for indentation
- No trailing whitespace
- File should end with a single newline
- Use single spaces around operators and after commas

```swift
// Good
let sum = a + b
let array = [1, 2, 3, 4]
func calculate(x: Int, y: Int) -> Int {
  return x + y
}

// Avoid
let sum=a+b
let array=[1,2,3,4]
func calculate(x:Int,y:Int)->Int{
    return x+y
}
```

### Line Length

- Prefer 100 characters or fewer per line
- Break long lines at natural boundaries

```swift
// Good
let message = "This is a long message that should be broken up " +
  "into multiple lines for better readability"

// Acceptable when breaking would reduce clarity
let url = URL(string: "https://api.example.com/v1/users/12345/profile/settings")
```

### Braces

- Opening braces on the same line
- Closing braces on their own line, aligned with opening statement

```swift
// Good
if condition {
  doSomething()
} else {
  doSomethingElse()
}

class MyClass {
  func myMethod() {
    // implementation
  }
}
```

## Naming Conventions

### Types

- Use PascalCase for types (classes, structs, enums, protocols)
- Use descriptive names

```swift
class UserManager {}
struct NetworkResponse {}
enum ConnectionState {}
protocol DataSource {}
```

### Variables and Functions

- Use camelCase for variables, functions, and parameters
- Use descriptive names that indicate purpose

```swift
let userName = "john_doe"
var isUserLoggedIn = false
let maxRetryCount = 3

func calculateTotalPrice(items: [Item], taxRate: Double) -> Double {
  // implementation
}

func validateEmailAddress(_ email: String) -> Bool {
  // implementation
}
```

### Constants

- Use camelCase for constants
- Group related constants in enums or structs

```swift
let defaultTimeout: TimeInterval = 30.0
let maxPasswordLength = 128

enum Constants {
  static let apiBaseURL = "https://api.example.com"
  static let defaultPageSize = 20
}
```

### Enums

- Use PascalCase for enum names
- Use camelCase for enum cases

```swift
enum UserRole {
  case guest
  case user
  case administrator
  case superAdmin
}

enum NetworkError {
  case noConnection
  case timeout
  case invalidResponse(String)
  case serverError(code: Int, message: String)
}
```

## Code Organization

### Import Statements

- Group imports logically
- Sort alphabetically within groups
- Use specific imports when possible

```swift
// System frameworks
import Foundation
import UIKit

// Third-party frameworks
import Alamofire
import SwiftyJSON

// Local modules
import Authentication
import Networking
```

### Type Declaration Order

1. Properties (stored, then computed)
2. Initializers
3. Type methods
4. Instance methods
5. Extensions (in separate extension blocks)

```swift
class UserProfileViewController: UIViewController {
  // MARK: - Properties

  // Stored properties
  private let userManager: UserManager
  private var currentUser: User?

  // Computed properties
  private var isUserLoggedIn: Bool {
    return currentUser != nil
  }

  // MARK: - Initialization

  init(userManager: UserManager) {
    self.userManager = userManager
    super.init(nibName: nil, bundle: nil)
  }

  required init?(coder: NSCoder) {
    fatalError("init(coder:) has not been implemented")
  }

  // MARK: - View Lifecycle

  override func viewDidLoad() {
    super.viewDidLoad()
    setupUI()
  }

  // MARK: - Private Methods

  private func setupUI() {
    // UI setup code
  }
}

// MARK: - UserProfileViewController Extensions

extension UserProfileViewController: UITableViewDataSource {
  // UITableViewDataSource implementation
}
```

## Functions and Methods

### Function Declarations

- Use clear, descriptive parameter labels
- Omit redundant type information when it can be inferred

```swift
// Good - clear parameter labels
func move(from startPoint: CGPoint, to endPoint: CGPoint) {
  // implementation
}

func download(fileAt url: URL, completion: @escaping (Result<Data, Error>) -> Void) {
  // implementation
}

// Use default parameter values appropriately
func createUser(name: String, age: Int = 18, isActive: Bool = true) -> User {
  // implementation
}
```

### Closures

- Use trailing closure syntax when appropriate
- Use shorthand argument names ($0, $1) for simple closures

```swift
// Trailing closure syntax
users.filter { $0.isActive }
  .map { $0.name }
  .sorted()

// Multiple trailing closures (Swift 5.3+)
UIView.animate(withDuration: 0.3) {
  view.alpha = 0.0
} completion: { _ in
  view.removeFromSuperview()
}

// Explicit closure for complex logic
let validUsers = users.filter { user in
  return user.isActive &&
         user.age >= 18 &&
         user.emailVerified
}
```

## Types and Declarations

### Properties

- Use `let` for immutable values, `var` for mutable
- Use computed properties for derived values
- Use property observers when needed

```swift
class CircleView: UIView {
  // Stored properties
  private let radius: CGFloat
  private var fillColor: UIColor = .blue {
    didSet {
      setNeedsDisplay()
    }
  }

  // Computed properties
  var diameter: CGFloat {
    return radius * 2
  }

  var area: CGFloat {
    return .pi * radius * radius
  }
}
```

### Optionals

- Use optionals appropriately to represent absence of value
- Prefer optional binding over force unwrapping
- Use nil-coalescing operator for default values

```swift
// Optional binding
if let user = currentUser {
  displayUserProfile(user)
} else {
  showLoginScreen()
}

// Guard statements for early returns
guard let validUser = currentUser else {
  showErrorMessage("User not found")
  return
}

// Nil-coalescing for defaults
let displayName = user.name ?? "Anonymous"
let timeout = config.timeout ?? 30.0

// Optional chaining
let streetAddress = user.address?.street?.uppercased()
```

### Enums

- Use enums for related constants and state representation
- Add associated values when needed
- Implement CaseIterable for complete enums

```swift
enum NetworkState: CaseIterable {
  case disconnected
  case connecting
  case connected
  case failed(Error)

  var displayText: String {
    switch self {
    case .disconnected:
      return "Disconnected"
    case .connecting:
      return "Connecting..."
    case .connected:
      return "Connected"
    case .failed(let error):
      return "Failed: \(error.localizedDescription)"
    }
  }
}
```

### Structs vs Classes

- Prefer structs for simple data types
- Use classes when reference semantics are needed
- Make structs conform to appropriate protocols

```swift
// Struct for simple data
struct Point {
  let x: Double
  let y: Double

  func distance(to other: Point) -> Double {
    let dx = x - other.x
    let dy = y - other.y
    return sqrt(dx * dx + dy * dy)
  }
}

// Class for complex objects with reference semantics
class NetworkManager: ObservableObject {
  @Published var connectionState: NetworkState = .disconnected
  private let session: URLSession

  init(session: URLSession = .shared) {
    self.session = session
  }
}
```

## Error Handling

### Error Types

- Define custom error types when appropriate
- Use Result type for functions that can fail
- Handle errors gracefully

```swift
enum UserValidationError: LocalizedError {
  case emptyName
  case invalidEmail
  case ageTooYoung(minimumAge: Int)

  var errorDescription: String? {
    switch self {
    case .emptyName:
      return "Name cannot be empty"
    case .invalidEmail:
      return "Please enter a valid email address"
    case .ageTooYoung(let minimumAge):
      return "Must be at least \(minimumAge) years old"
    }
  }
}

func validateUser(_ user: User) -> Result<Void, UserValidationError> {
  guard !user.name.isEmpty else {
    return .failure(.emptyName)
  }

  guard user.email.contains("@") else {
    return .failure(.invalidEmail)
  }

  guard user.age >= 13 else {
    return .failure(.ageTooYoung(minimumAge: 13))
  }

  return .success(())
}
```

### Throwing Functions

```swift
func loadUser(withID id: String) throws -> User {
  guard !id.isEmpty else {
    throw UserValidationError.emptyName
  }

  // Load user logic
  guard let user = database.user(with: id) else {
    throw DatabaseError.userNotFound(id: id)
  }

  return user
}

// Usage
do {
  let user = try loadUser(withID: userID)
  displayUser(user)
} catch let error as UserValidationError {
  showValidationError(error)
} catch {
  showGenericError(error)
}
```

## Protocols and Extensions

### Protocol Design

- Keep protocols focused and cohesive
- Use protocol composition when appropriate
- Provide default implementations in extensions

```swift
protocol Identifiable {
  var id: String { get }
}

protocol Timestamped {
  var createdAt: Date { get }
  var updatedAt: Date? { get }
}

// Protocol composition
typealias Entity = Identifiable & Timestamped

// Default implementations
extension Timestamped {
  var age: TimeInterval {
    return Date().timeIntervalSince(createdAt)
  }

  var isRecent: Bool {
    return age < 3600 // Less than 1 hour old
  }
}
```

### Extensions

- Use extensions to organize code and add functionality
- Group related functionality in extensions
- Use MARK comments to organize extension sections

```swift
// MARK: - UITableViewDataSource
extension UserListViewController: UITableViewDataSource {
  func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
    return users.count
  }

  func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
    // Implementation
  }
}

// MARK: - UserManagerDelegate
extension UserListViewController: UserManagerDelegate {
  func userManager(_ manager: UserManager, didUpdateUser user: User) {
    DispatchQueue.main.async {
      self.refreshUserDisplay()
    }
  }
}
```

## SwiftUI Specific Guidelines

### View Structure

- Keep view bodies simple and focused
- Extract complex views into separate components
- Use view modifiers appropriately

```swift
struct UserProfileView: View {
  let user: User
  @State private var isEditing = false

  var body: some View {
    VStack(alignment: .leading, spacing: 16) {
      userInfoSection
      actionButtons
    }
    .padding()
    .navigationTitle("Profile")
    .navigationBarTitleDisplayMode(.large)
  }

  private var userInfoSection: some View {
    VStack(alignment: .leading, spacing: 8) {
      Text(user.name)
        .font(.title)
        .fontWeight(.bold)

      Text(user.email)
        .font(.subheadline)
        .foregroundColor(.secondary)
    }
  }

  private var actionButtons: some View {
    HStack {
      Button("Edit") {
        isEditing = true
      }
      .buttonStyle(.borderedProminent)

      Button("Share") {
        shareUser()
      }
      .buttonStyle(.bordered)
    }
  }

  private func shareUser() {
    // Share implementation
  }
}
```

### State Management

- Use appropriate property wrappers for state
- Keep state as local as possible
- Use ObservableObject for complex shared state

```swift
class UserStore: ObservableObject {
  @Published var users: [User] = []
  @Published var isLoading = false

  func loadUsers() async {
    isLoading = true
    defer { isLoading = false }

    do {
      users = try await userService.fetchUsers()
    } catch {
      print("Failed to load users: \(error)")
    }
  }
}

struct UserListView: View {
  @StateObject private var userStore = UserStore()
  @State private var searchText = ""

  var filteredUsers: [User] {
    if searchText.isEmpty {
      return userStore.users
    }
    return userStore.users.filter { $0.name.localizedCaseInsensitiveContains(searchText) }
  }

  var body: some View {
    NavigationView {
      List(filteredUsers) { user in
        UserRowView(user: user)
      }
      .searchable(text: $searchText)
      .refreshable {
        await userStore.loadUsers()
      }
    }
    .task {
      await userStore.loadUsers()
    }
  }
}
```

## Concurrency

### Async/Await

- Use async/await for asynchronous operations
- Handle errors appropriately in async contexts
- Use Task for concurrent operations

```swift
// Async function
func fetchUserProfile(id: String) async throws -> User {
  let url = URL(string: "\(baseURL)/users/\(id)")!
  let (data, _) = try await URLSession.shared.data(from: url)
  return try JSONDecoder().decode(User.self, from: data)
}

// Using async functions
func loadUserData() async {
  do {
    let user = try await fetchUserProfile(id: currentUserID)
    await MainActor.run {
      self.currentUser = user
    }
  } catch {
    await MainActor.run {
      self.showError(error)
    }
  }
}

// Concurrent operations
func loadAllData() async {
  async let users = fetchUsers()
  async let settings = fetchSettings()
  async let notifications = fetchNotifications()

  do {
    let (loadedUsers, loadedSettings, loadedNotifications) = try await (users, settings, notifications)
    // Process loaded data
  } catch {
    handleError(error)
  }
}
```

## Comments and Documentation

### Documentation Comments

- Use /// for documentation comments
- Document public APIs thoroughly
- Include parameter and return value descriptions

```swift
/// Calculates the distance between two points in 2D space.
///
/// This function uses the Euclidean distance formula to compute
/// the straight-line distance between two points.
///
/// - Parameters:
///   - point1: The first point
///   - point2: The second point
/// - Returns: The distance between the points as a Double
/// - Complexity: O(1)
func distance(from point1: Point, to point2: Point) -> Double {
  let dx = point1.x - point2.x
  let dy = point1.y - point2.y
  return sqrt(dx * dx + dy * dy)
}
```

### MARK Comments

- Use MARK comments to organize code sections
- Follow consistent MARK patterns

```swift
class UserViewController: UIViewController {
  // MARK: - Properties

  private let userManager: UserManager

  // MARK: - Initialization

  init(userManager: UserManager) {
    self.userManager = userManager
    super.init(nibName: nil, bundle: nil)
  }

  // MARK: - View Lifecycle

  override func viewDidLoad() {
    super.viewDidLoad()
    setupUI()
  }

  // MARK: - Private Methods

  private func setupUI() {
    // Implementation
  }
}
```

## Testing

### Unit Tests

- Write clear, descriptive test names
- Follow Arrange-Act-Assert pattern
- Use appropriate XCTest methods

```swift
class UserValidatorTests: XCTestCase {
  var validator: UserValidator!

  override func setUp() {
    super.setUp()
    validator = UserValidator()
  }

  override func tearDown() {
    validator = nil
    super.tearDown()
  }

  func testValidateUser_withValidData_returnsSuccess() {
    // Arrange
    let user = User(name: "John Doe", email: "john@example.com", age: 25)

    // Act
    let result = validator.validate(user)

    // Assert
    XCTAssertTrue(result.isSuccess)
  }

  func testValidateUser_withEmptyName_returnsFailure() {
    // Arrange
    let user = User(name: "", email: "john@example.com", age: 25)

    // Act
    let result = validator.validate(user)

    // Assert
    XCTAssertFalse(result.isSuccess)
    XCTAssertEqual(result.error, .emptyName)
  }
}
```

This style guide should be used as the foundation for all Swift code generation and formatting decisions.
