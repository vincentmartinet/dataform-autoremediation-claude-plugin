# ADR-0009: Migrating to Object-Oriented Service Architecture with Dependency Injection

## Status
Accepted

## Context
After splitting the Scout Daemon into multiple modular files (ADR-0008), the system still relied on module-level functions and global state variables (`_token_cache`, `_recent_failures`, etc.). This imperative approach made testing difficult, as each test required extensive `unittest.mock.patch` decorators, leading to brittle tests that were tightly coupled to the implementation details of module imports. Additionally, state management across different areas of the application was opaque.

## Decision
We decided to refactor the core modules into an Object-Oriented (OO) architecture using the Inversion of Control (IoC) principle through Dependency Injection.
- We created service classes for each domain: `GCPApiClient`, `GitOpsService`, `ErrorClassifier`, `ClaudeInvokerService`, and `NotificationService`.
- Global state was moved to instance variables within their respective service classes.
- The `ScoutDaemon` class was updated to accept instances of these services in its constructor, removing hard-coded dependencies.

## Consequences
**Positive:**
- **Improved Testability:** Unit tests no longer rely heavily on `patch`. Mocks can be passed directly as constructor arguments, significantly reducing test fragility and improving readability.
- **Better State Management:** Global variables are eliminated; state is securely encapsulated within class instances.
- **Maintainability:** Clear boundaries and responsibilities for each service.

**Negative:**
- **Complexity:** Introduces slightly more boilerplate code for class instantiation and dependency passing at application startup.
