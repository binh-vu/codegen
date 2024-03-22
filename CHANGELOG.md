# Changelog

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
