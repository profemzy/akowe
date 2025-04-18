# Flask Testing Guide for Akowe

This guide explains how to properly test Flask applications, especially when dealing with templates and other resources.

## Common Issues and Solutions

### 1. Template Not Found Errors

When running tests, you might encounter errors like:
```
jinja2.exceptions.TemplateNotFound: auth/login.html
```

**Solution**: Use one of these approaches:

1. **Explicitly Set Template Path**: Update `conftest.py` to provide the absolute path to templates:
   ```python
   template_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "akowe", "templates"))
   app.template_folder = template_path
   ```

2. **Mock Templates**: Use Flask's `render_template_string` with unittest.mock to avoid template loading:
   ```python
   with patch('flask.render_template', side_effect=mock_render_template):
       yield app  # Test fixture
   ```

### 2. Database Connection Issues

For tests requiring database access:

1. **Use In-Memory SQLite**: For tests, configure an in-memory SQLite database:
   ```python
   app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
   ```

2. **Temporary File Database**: For more persistence during a test:
   ```python
   db_fd, db_path = tempfile.mkstemp()
   app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
   ```

### 3. Test Types

#### Basic API Tests
For simple API endpoints that return JSON:

```python
def test_ping_route(client):
    response = client.get('/ping')
    assert response.status_code == 200
    assert response.json == {"status": "ok", "message": "Akowe is running"}
```

#### Template Tests with Mocks
For pages that render templates but you don't need to check exact HTML:

```python
@pytest.fixture
def app_with_mocks(app):
    def mock_render_template(template_name, **kwargs):
        if template_name == 'auth/login.html':
            return render_template_string('<html><h1>Login</h1></html>', **kwargs)
        # Add more template mocks as needed
        
    with patch('flask.render_template', side_effect=mock_render_template):
        yield app
```

#### Authentication Tests
For testing login/logout functionality:

```python
def test_login_success(client, auth):
    response = auth.login()
    # Check for success indicators
    assert response.headers["Location"] == "/"
```

## Best Practices

1. **Keep Tests Isolated**: Each test should run independently
2. **Use Fixtures**: Create pytest fixtures for common test setups
3. **Mock External Services**: Use unittest.mock for external APIs
4. **Test Different Response Types**: Test JSON APIs differently from rendered templates
5. **Test Auth Workflows**: Ensure authentication and authorization work properly

## Recommended Test Structure

```
tests/
├── conftest.py               # Common fixtures
├── test_api.py               # API endpoint tests
├── test_auth.py              # Authentication tests
├── test_models.py            # Database model tests
└── test_with_templates.py    # Tests with template mocking
```