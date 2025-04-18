# Flask Template Testing Guide

## Issue 
When running Flask tests with pytest, you might encounter template errors like:
```
jinja2.exceptions.TemplateNotFound: dashboard/index.html
```

This happens because, by default, Flask looks for templates in a specific directory relative to the app, and in test environments these paths might not be correctly configured.

## Solutions

We implemented several solutions:

### 1. Basic Approach: Configure Template Paths

```python
@pytest.fixture
def app():
    # Configure path to templates folder
    template_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "akowe", "templates"))
    
    app = create_app({
        "TEMPLATE_FOLDER": template_path,
    })
    
    # Explicitly set the template folder on the app
    app.template_folder = template_path
    
    return app
```

### 2. Advanced Approach: Template Mocking

This approach avoids the need to access actual template files by mocking the template rendering:

```python
@pytest.fixture
def app():
    app = create_app({"TESTING": True})
    
    # Define a function that mocks render_template
    def mock_render_template(template_name, **kwargs):
        if template_name == 'auth/login.html':
            return render_template_string('<html><h1>Login</h1></html>', **kwargs)
        # Add more template mocks as needed
    
    # Apply the mock during tests
    with patch('flask.render_template', side_effect=mock_render_template):
        yield app
```

### 3. Comprehensive Solution: Template Dictionary

For larger applications with many templates, use a dictionary to store mock templates:

```python
# Template mocking setup
TEMPLATE_MOCKS = {
    'auth/login.html': '<html><h1>Sign in</h1></html>',
    'dashboard/index.html': '<html><h1>Dashboard</h1></html>',
    # Add more templates as needed
}

def mock_render_template(template_name, **kwargs):
    if template_name in TEMPLATE_MOCKS:
        return render_template_string(TEMPLATE_MOCKS[template_name], **kwargs)
    else:
        # Generic fallback template
        return render_template_string(
            f'<html><h1>{template_name}</h1><p>Template mocked for testing</p></html>',
            **kwargs
        )
```

## Testing Strategy

### 1. Skip Template Tests
For API endpoints that return JSON, just test the API functionality without worrying about templates:

```python
def test_ping_route(client):
    response = client.get('/ping')
    assert response.status_code == 200
    assert response.json == {"status": "ok"}
```

### 2. Test Response Codes Without Content
For simple page tests, you can just verify response codes without checking content:

```python
def test_dashboard_access(client, auth):
    auth.login()
    response = client.get("/")
    assert response.status_code == 200
```

### 3. Test With Mocked Templates
For pages where content verification is important:

```python
def test_login_page(client_with_mocks):
    response = client_with_mocks.get("/login")
    assert response.status_code == 200
    assert b"Sign in" in response.data
```

## Best Practices

1. **Use the Right Tool**: Choose between direct template path configuration and mocking based on your needs
2. **Match URLs Correctly**: Ensure test URLs match the actual application routes
3. **Check Appropriate Content**: Look for content that will actually be present in the response
4. **Separate API Tests**: Keep API endpoint tests separate from UI/template tests
5. **Mock at the Appropriate Level**: Mock the template rendering, not the entire route handler

## Implementation Files
- `conftest_with_mocks.py`: Complete fixture setup with template mocking
- `test_with_mocks.py`: Test examples using the mock templates
- `test_app.py`: Basic tests that don't require templates