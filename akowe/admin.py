from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from akowe.decorators import admin_required
from akowe.forms import RegistrationForm, UserEditForm
from akowe.models import db
from akowe.models.user import User

bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.route('/')
@login_required
@admin_required
def index():
    return render_template('admin/index.html', title='Admin Dashboard')


@bp.route('/users')
@login_required
@admin_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', users=users, title='User Management')


@bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_user():
    form = RegistrationForm()
    
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            is_admin=form.is_admin.data
        )
        user.password = form.password.data
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'User {user.username} has been created.', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/new_user.html', form=form, title='Create User')


@bp.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(id):
    user = User.query.get_or_404(id)
    
    # Don't allow editing the initial admin user
    if user.id == 1 and current_user.id != 1:
        flash('You cannot edit the primary admin user.', 'danger')
        return redirect(url_for('admin.users'))
    
    form = UserEditForm(user=user)
    
    if request.method == 'GET':
        form.email.data = user.email
        form.first_name.data = user.first_name
        form.last_name.data = user.last_name
        form.is_admin.data = user.is_admin
        form.is_active.data = user.is_active
    
    if form.validate_on_submit():
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.is_admin = form.is_admin.data
        user.is_active = form.is_active.data
        
        db.session.commit()
        
        flash(f'User {user.username} has been updated.', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/edit_user.html', form=form, user=user, title='Edit User')


@bp.route('/users/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    
    # Don't allow deleting the initial admin user
    if user.id == 1:
        flash('You cannot delete the primary admin user.', 'danger')
        return redirect(url_for('admin.users'))
    
    # Don't allow users to delete themselves
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.users'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {username} has been deleted.', 'success')
    return redirect(url_for('admin.users'))


@bp.route('/users/<int:id>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_password(id):
    user = User.query.get_or_404(id)
    
    # Generate a temporary password
    temp_password = 'Temporary123'
    user.password = temp_password
    db.session.commit()
    
    flash(f'Password for {user.username} has been reset to: {temp_password}', 'success')
    return redirect(url_for('admin.edit_user', id=user.id))
