---
inclusion: manual
---

# Coding Conventions

## Code Style

Follow [Google TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html) with these specifics:
- **Line length**: 100 characters maximum
- **Formatting**: Prettier (enforced by CI) - run `pnpm ng-dev format changed`
- **Indentation**: Managed by Prettier

## Commit Messages

Strict format required for changelog generation:

```
<type>(<scope>): <short summary>

<body>

<footer>
```

### Types
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation only
- `refactor` - Code change that neither fixes a bug nor adds a feature
- `perf` - Performance improvement
- `test` - Adding or correcting tests
- `build` - Build system or external dependencies
- `ci` - CI configuration changes

### Scopes
Use package names: `core`, `common`, `compiler`, `router`, `forms`, `animations`, `platform-browser`, `platform-server`, `compiler-cli`, `language-service`, `devtools`, etc.

### Summary
- Use imperative, present tense: "change" not "changed"
- Don't capitalize first letter
- No period at the end

### Body
- Mandatory for all commits except `docs`
- Minimum 20 characters
- Explain the "why" not the "what"

## Naming Conventions

### Classes
- PascalCase
- Don't suffix with `Impl`

### Interfaces
- PascalCase
- No `I` prefix
- No `Interface` suffix

### Functions and Methods
- camelCase
- Name should describe the action performed, not when it's called
- Example: `activateRipple()` not `handleClick()`

### Constants and Injection Tokens
- UPPER_SNAKE_CASE

### Boolean Properties
- Use `is` or `has` prefix (except for `@Input()` properties)
- JsDoc: "Whether..." not "True if..."

### Observables
- Don't suffix with `$`

### Variables
- Prefer `const` over `let`
- Never use `var` unless absolutely necessary

## TypeScript Practices

### Type Safety
- Avoid `any` - use generics or `unknown` instead
- Use `readonly` wherever possible
- Enable all strict flags

### Getters and Setters
- Only use for `@Input` properties or API compatibility
- Keep logic simple (max 3 lines)
- Prefer `readonly` properties over getters without setters
- Apply decorators to getter, not setter

### Iteration
- Prefer `for` or `for of` over `Array.prototype.forEach`

### Try-Catch
- Only for legitimately unexpected errors
- Must include comment explaining the specific error and why it can't be prevented
- Don't use to avoid null checks or bounds checking

### RxJS
- Import `of` as `observableOf`: `import {of as observableOf} from 'rxjs';`

## Comments

### JsDoc
- Required for all public APIs
- Recommended for most private/internal APIs
- Properties: Concise description of what it means
- Methods: Describe what it does, document parameters and return value

### Inline Comments
- Use `//` for explanations and background info
- Explain "why" not "what"
- Valuable comments explain why code exists or why it's done a certain way

## API Design

### Boolean Arguments
- Avoid boolean flags that mean "do something extra"
- Prefer separate functions instead

### Optional Arguments
- Only use when it makes sense for the API or required for performance
- Don't use merely for implementation convenience

## Testing

### Test Names
- Descriptive, read like sentences
- Often "it should..." format
- Example: `it('should not reuse routes upon location change', ...)`

### Test Classes
- Give meaningful, descriptive names
- Example: `FormGroupWithCheckboxAndRadios` not `Comp`

## File Organization

### Public APIs
- All features/bug fixes must be tested
- All public API methods must be documented
- Changes tracked in golden files

### Imports
- Use path mappings defined in tsconfig
- Example: `@angular/core` not relative paths for framework packages

## Pull Request Requirements

- Sign CLA before submitting
- Include appropriate test cases
- Follow commit message conventions
- Run full test suite: `pnpm test //packages/...`
- Format code: `pnpm ng-dev format changed`
- All tests must pass
- Code must be properly formatted
