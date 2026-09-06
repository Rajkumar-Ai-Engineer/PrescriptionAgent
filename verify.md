You are a senior software architect and security engineer. Perform a thorough **Security Audit** and **Modular Structure Review** on the provided codebase. Be precise, actionable, and prioritize findings by severity.

---

## PART 1: SECURITY AUDIT

### 1.1 Authentication & Authorization
- Are authentication mechanisms properly implemented (JWT, OAuth, session tokens)?
- Is authorization enforced at every endpoint/route (role-based or attribute-based access control)?
- Are there any broken access control issues (e.g., IDOR, privilege escalation)?
- Is token expiration and refresh handled correctly?

### 1.2 Input Validation & Sanitization
- Is all user input validated on the server side (never trust client-side only)?
- Are there any injection vulnerabilities: SQL injection, NoSQL injection, command injection, LDAP injection?
- Is output properly encoded to prevent XSS (Cross-Site Scripting)?
- Are file uploads validated for type, size, and content?

### 1.3 Data Protection
- Is sensitive data (passwords, PII, API keys) encrypted at rest and in transit (HTTPS/TLS)?
- Are secrets/credentials hardcoded anywhere in the codebase or committed to version control?
- Are environment variables used correctly for configuration?
- Is password hashing done with a secure algorithm (bcrypt, argon2, scrypt)?

### 1.4 API Security
- Are API endpoints protected against rate limiting and brute force attacks?
- Is CORS configured correctly and not overly permissive?
- Are HTTP security headers set (CSP, HSTS, X-Frame-Options, X-Content-Type-Options)?
- Is CSRF protection implemented for state-changing requests?

### 1.5 Dependency & Supply Chain Security
- Are any dependencies outdated or known to have CVEs?
- Are dependency versions pinned to avoid unexpected updates?
- Is there a process for auditing third-party packages?

### 1.6 Error Handling & Logging
- Are sensitive details (stack traces, DB errors, internal paths) exposed in error responses?
- Is logging implemented for security events (failed logins, access violations)?
- Are logs sanitized to avoid leaking sensitive information?

### 1.7 Session Management
- Are session IDs sufficiently random and regenerated after login?
- Is there a proper session timeout and invalidation on logout?
- Are cookies marked as HttpOnly and Secure?

### 1.8 Cryptography
- Are weak algorithms (MD5, SHA1, DES, RC4) used anywhere?
- Are random values generated using a cryptographically secure RNG?
- Is encryption implemented correctly (not rolling custom crypto)?

---

## PART 2: MODULAR STRUCTURE REVIEW

### 2.1 Separation of Concerns
- Is business logic separated from presentation/UI logic?
- Are controllers, services, repositories/DAOs, and models clearly separated?
- Is there any direct database access from controllers or UI layers?

### 2.2 Single Responsibility Principle (SRP)
- Does each module/class/function have one clear responsibility?
- Are there any "god objects" or monolithic functions doing too many things?
- Are utilities and helpers logically grouped?

### 2.3 Dependency Management
- Are dependencies injected (DI pattern) rather than hardcoded?
- Are circular dependencies present between modules?
- Is the dependency graph clean and acyclic?

### 2.4 Reusability & DRY (Don't Repeat Yourself)
- Is there duplicated logic that should be extracted into shared utilities?
- Are common patterns abstracted into reusable components or functions?
- Are there copy-pasted code blocks that indicate missing abstractions?

### 2.5 Module Boundaries & Encapsulation
- Are module internals properly encapsulated (private vs public interfaces)?
- Is the public API of each module clearly defined and minimal?
- Do modules expose only what consumers need?

### 2.6 Scalability & Extensibility
- Is it easy to add new features without modifying existing modules (Open/Closed Principle)?
- Are interfaces/abstractions used to decouple implementations?
- Are there hardcoded assumptions that would make scaling difficult?

### 2.7 Configuration & Environment Management
- Are environment-specific configs separated from code?
- Is there a single source of truth for configuration?
- Are feature flags or toggles modular and maintainable?

### 2.8 Testing & Testability
- Are modules designed to be unit-testable in isolation?
- Is there excessive coupling that makes mocking difficult?
- Are side effects isolated from pure logic?

### 2.9 Naming & Directory Structure
- Are naming conventions consistent across the codebase?
- Does the folder/file structure clearly reflect the domain and architecture?
- Are there misplaced files or logically inconsistent groupings?

### 2.10 Documentation & Contracts
- Are module interfaces and public APIs documented?
- Are complex functions and business rules explained with comments?
- Is there an architectural overview or README for the module structure?

---

## OUTPUT FORMAT

For each finding, provide:

| # | Category | Severity (Critical/High/Medium/Low/Info) | File/Module | Issue Description | Recommendation |
|---|----------|------------------------------------------|-------------|-------------------|----------------|

Then provide:
1. **Executive Summary** — overall health rating (1–10) for Security and Modularity separately, with a 2–3 sentence assessment.
2. **Top 5 Priority Fixes** — ranked by risk/impact, with specific file references if available.
3. **Positive Observations** — things done well that should be preserved.

---

[PASTE YOUR CODE OR DESCRIBE YOUR PROJECT STRUCTURE BELOW]