# Changelog

## [2.1.3] - 2024-04-12

### Fixed

- Fixed keep NoStatement (don't ignore it)

### Added

- Added `to_wrapped_python` to detect when we need to wrap an expression in `()`

## [2.1.2] - 2024-04-12

### Fixed

- Fix `AST.find_ast_to`

## [2.1.1] - 2024-04-10

### Fixed

- Fix wrapping complex expression in `()`
- Fix checking else\_ statement

## [2.1.0] - 2024-03-21

### Added

- Add back NoStatement class

## [2.0.0] - 2024-03-21

### Added

- Add item_setter expression
- Add PythonStatement
- We can force name of a variable (for embedding python code).

### Changed

- Make it clear if we are import a module or an attribute of a module
- Refactor variable creation (use DeferredVar pattern) and scoping
- Replace Memory class with VarRegisters class and hide it from the users of the library
- Change BlockStatement to not hold a list of statements but act as a unit of code as it should be.
