# CLAUDE.md - Project Guidelines

## Project: Akowe Financial Tracker

### Commands
- Data Processing: Use Python with pandas for CSV operations
- Tests: pytest tests/ -v
- Single Test: pytest tests/test_file.py::test_function -v
- Linting: flake8 .
- Type Check: mypy akowe
- Format: black .
- Run All Checks: make check
- Run Application: make run
- Setup Database: make setup

### Code Style Guidelines
- Python 3.10+ for all scripts
- Use type hints for all functions and variables
- Follow PEP 8 for code formatting (enforced by black with 100 char line length)
- Use pandas for all CSV data manipulation
- Class names: CamelCase
- Functions/variables: snake_case
- Constants: UPPER_CASE
- Group imports: stdlib, 3rd-party, local
- Error handling: Use context-specific exceptions with descriptive messages
- Documentation: Docstrings for all functions and classes
- Financial data precision: Use Decimal type for monetary values, not float
- Date format: ISO 8601 (YYYY-MM-DD)

### Testing Guidelines
- All new features must have accompanying tests
- Maintain minimum 80% test coverage
- Use pytest fixtures for common setup
- Mock external dependencies in tests
- Create both unit and integration tests