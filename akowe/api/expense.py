import os
from datetime import datetime
from decimal import Decimal
from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename

from akowe.models import db
from akowe.models.expense import Expense
from akowe.services.import_service import ImportService

bp = Blueprint('expense', __name__, url_prefix='/expense')

PAYMENT_METHODS = ['credit_card', 'debit_card', 'bank_transfer', 'cash', 'other']
STATUSES = ['paid', 'pending', 'cancelled']
CATEGORIES = ['hardware', 'software', 'rent', 'utilities', 'travel', 'food', 
              'entertainment', 'professional_services', 'office_supplies', 
              'marketing', 'maintenance', 'taxes', 'insurance', 'other']

@bp.route('/', methods=['GET'])
def index():
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    return render_template('expense/index.html', expenses=expenses)

@bp.route('/new', methods=['GET', 'POST'])
def new():
    if request.method == 'POST':
        try:
            date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            title = request.form['title']
            amount = Decimal(request.form['amount'])
            category = request.form['category']
            payment_method = request.form['payment_method']
            status = request.form['status']
            vendor = request.form['vendor']
            
            expense = Expense(
                date=date,
                title=title,
                amount=amount,
                category=category,
                payment_method=payment_method,
                status=status,
                vendor=vendor if vendor else None
            )
            
            db.session.add(expense)
            db.session.commit()
            
            flash('Expense record added successfully!', 'success')
            return redirect(url_for('expense.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding expense record: {str(e)}', 'error')
    
    return render_template('expense/new.html', 
                          payment_methods=PAYMENT_METHODS,
                          statuses=STATUSES,
                          categories=CATEGORIES)

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    expense = Expense.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            expense.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            expense.title = request.form['title']
            expense.amount = Decimal(request.form['amount'])
            expense.category = request.form['category']
            expense.payment_method = request.form['payment_method']
            expense.status = request.form['status']
            expense.vendor = request.form['vendor'] if request.form['vendor'] else None
            
            db.session.commit()
            
            flash('Expense record updated successfully!', 'success')
            return redirect(url_for('expense.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating expense record: {str(e)}', 'error')
    
    return render_template('expense/edit.html', 
                          expense=expense,
                          payment_methods=PAYMENT_METHODS,
                          statuses=STATUSES,
                          categories=CATEGORIES)

@bp.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    expense = Expense.query.get_or_404(id)
    
    try:
        db.session.delete(expense)
        db.session.commit()
        flash('Expense record deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting expense record: {str(e)}', 'error')
    
    return redirect(url_for('expense.index'))

@bp.route('/import', methods=['GET', 'POST'])
def import_csv():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        
        if file:
            try:
                filename = secure_filename(file.filename)
                filepath = os.path.join(current_app.instance_path, filename)
                file.save(filepath)
                
                records, count = ImportService.import_expense_csv(filepath)
                
                # Clean up the file
                os.remove(filepath)
                
                flash(f'Successfully imported {count} expense records!', 'success')
                return render_template('expense/import_success.html', records=records, count=count)
            except Exception as e:
                flash(f'Error importing file: {str(e)}', 'error')
    
    return render_template('expense/import.html')