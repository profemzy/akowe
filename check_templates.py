#!/usr/bin/env python3
"""
Template verification script for Akowe.
This script checks that templates can be found correctly.
"""

import os
from akowe.akowe import create_app


def check_templates():
    """Check if all critical templates can be found."""
    app = create_app()
    
    # Get the template folder path
    template_path = os.path.join(app.root_path, app.template_folder)
    print(f"Template folder path: {template_path}")
    
    # List of critical templates to check
    critical_templates = [
        "dashboard/index.html",
        "layouts/base.html",
        "auth/login.html",
        "admin/index.html",
    ]
    
    # Check each template
    for template in critical_templates:
        template_file = os.path.join(template_path, template)
        exists = os.path.exists(template_file)
        status = "✅ FOUND" if exists else "❌ MISSING"
        print(f"{status}: {template}")
        
    print("\nIf all templates are found, the app should work correctly.")
    print("If any templates are missing, check your installation and file paths.")


if __name__ == "__main__":
    check_templates()