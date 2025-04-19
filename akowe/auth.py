from datetime import datetime
from urllib.parse import urlparse

from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user

from akowe.forms import LoginForm, PasswordChangeForm
from akowe.models import db
from akowe.models.user import User

bp = Blueprint("auth", __name__)

# Handle CSRF errors
from flask_wtf.csrf import CSRFError


@bp.errorhandler(CSRFError)
def handle_csrf_error(e):
    """Handle CSRF errors by returning to the login page with an error message."""
    flash("Security token expired or missing. Please fill out the form again.", "danger")
    # Create a fresh form with a new CSRF token
    form = LoginForm()
    return render_template("auth/login.html", form=form, title="Log In", csrf_error=True)


@bp.route("/login", methods=["GET", "POST"])
def login():
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        # Check if user exists and password is correct
        if user is None or not user.verify_password(form.password.data):
            flash("Invalid username or password", "danger")
            # Rather than redirecting, render the template with the form to show errors
            return render_template("auth/login.html", form=form, title="Log In", login_failed=True)

        # Check if user is active
        if not user.is_active:
            flash("Account is disabled. Please contact an administrator.", "warning")
            # Rather than redirecting, render the template with the form
            return render_template("auth/login.html", form=form, title="Log In", login_failed=True)

        # Log in the user and update last login timestamp
        # If remember_me is False, make session permanent but with config lifetime
        # This allows us to control session expiry even for non-remembered sessions
        if not form.remember_me.data:
            session.permanent = True  # This makes the session use PERMANENT_SESSION_LIFETIME
        
        login_user(user, remember=form.remember_me.data)
        
        # Set session security flags
        session.modified = True
        
        # Set initial activity time
        session['last_activity'] = datetime.utcnow().timestamp()
        
        # Update last login time
        user.last_login = datetime.utcnow()
        db.session.commit()

        # Redirect to the page the user was trying to access
        next_page = request.args.get("next")
        if not next_page or urlparse(next_page).netloc != "":
            next_page = url_for("dashboard.index")

        return redirect(next_page)

    return render_template("auth/login.html", form=form, title="Log In")


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = PasswordChangeForm()

    if form.validate_on_submit():
        if current_user.verify_password(form.current_password.data):
            current_user.password = form.new_password.data
            db.session.commit()
            flash("Your password has been updated.", "success")
            return redirect(url_for("dashboard.index"))
        else:
            flash("Invalid current password.", "danger")

    return render_template("auth/change_password.html", form=form, title="Change Password")
