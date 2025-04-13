# CLAUDE.md - Project Guidelines

## Project: Akowe Financial Tracker

### Commands
- Data Processing: Use Python with pandas for CSV operations
- Tests: pytest tests/ -v
- Single Test: pytest tests/test_file.py::test_function -v
- Linting: flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
- Type Check: mypy --strict .

### Code Style Guidelines
- Python 3.10+ for all scripts
- Use type hints for all functions and variables
- Follow PEP 8 for code formatting
- Use pandas for all CSV data manipulation
- Class names: CamelCase
- Functions/variables: snake_case
- Constants: UPPER_CASE
- Group imports: stdlib, 3rd-party, local
- Error handling: Use context-specific exceptions with descriptive messages
- Documentation: Docstrings for all functions and classes
- Financial data precision: Use Decimal type for monetary values, not float
- Date format: ISO 8601 (YYYY-MM-DD)