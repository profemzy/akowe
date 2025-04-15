import os
from datetime import datetime
from decimal import Decimal

from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename

from akowe.models import db
from akowe.models.expense import Expense
from akowe.services.import_service import ImportService
from akowe.services.storage_service import StorageService

bp = Blueprint("expense", __name__, url_prefix="/expense")

PAYMENT_METHODS = ["credit_card", "debit_card", "bank_transfer", "cash", "other"]
STATUSES = ["paid", "pending", "cancelled"]
CATEGORIES = [
    "hardware",
    "software",
    "rent",
    "utilities",
    "travel",
    "food",
    "entertainment",
    "professional_services",
    "office_supplies",
    "marketing",
    "maintenance",
    "taxes",
    "insurance",
    "other",
]
RECEIPT_CONTAINER = "receipts"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf"}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route("/", methods=["GET"])
def index():
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    return render_template("expense/index.html", expenses=expenses)


@bp.route("/new", methods=["GET", "POST"])
def new():
    if request.method == "POST":
        try:
            date = datetime.strptime(request.form["date"], "%Y-%m-%d").date()
            title = request.form["title"]
            amount = Decimal(request.form["amount"])
            category = request.form["category"]
            payment_method = request.form["payment_method"]
            status = request.form["status"]
            vendor = request.form["vendor"]

            expense = Expense(
                date=date,
                title=title,
                amount=amount,
                category=category,
                payment_method=payment_method,
                status=status,
                vendor=vendor if vendor else None,
            )

            # Handle receipt upload
            receipt_file = request.files.get("receipt")
            if receipt_file and receipt_file.filename and allowed_file(receipt_file.filename):
                try:
                    # Check file size (max 5MB)
                    receipt_file.seek(0, os.SEEK_END)
                    file_size = receipt_file.tell()
                    receipt_file.seek(0)

                    if file_size > MAX_CONTENT_LENGTH:
                        flash("Receipt file is too large. Maximum size is 5MB.", "error")
                        return render_template(
                            "expense/new.html",
                            payment_methods=PAYMENT_METHODS,
                            statuses=STATUSES,
                            categories=CATEGORIES,
                        )

                    # Upload file to Azure Blob Storage
                    blob_name, blob_url = StorageService.upload_file(
                        receipt_file, RECEIPT_CONTAINER
                    )

                    # Store blob info in the expense record
                    expense.receipt_blob_name = blob_name
                    expense.receipt_url = blob_url

                except Exception as e:
                    flash(f"Error uploading receipt: {str(e)}", "error")

            db.session.add(expense)
            db.session.commit()

            flash("Expense record added successfully!", "success")
            return redirect(url_for("expense.index"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding expense record: {str(e)}", "error")

    return render_template(
        "expense/new.html",
        payment_methods=PAYMENT_METHODS,
        statuses=STATUSES,
        categories=CATEGORIES,
    )


@bp.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    expense = Expense.query.get_or_404(id)

    if request.method == "POST":
        try:
            expense.date = datetime.strptime(request.form["date"], "%Y-%m-%d").date()
            expense.title = request.form["title"]
            expense.amount = Decimal(request.form["amount"])
            expense.category = request.form["category"]
            expense.payment_method = request.form["payment_method"]
            expense.status = request.form["status"]
            expense.vendor = request.form["vendor"] if request.form["vendor"] else None

            # Handle receipt upload
            receipt_file = request.files.get("receipt")
            if receipt_file and receipt_file.filename and allowed_file(receipt_file.filename):
                try:
                    # Check file size (max 5MB)
                    receipt_file.seek(0, os.SEEK_END)
                    file_size = receipt_file.tell()
                    receipt_file.seek(0)

                    if file_size > MAX_CONTENT_LENGTH:
                        flash("Receipt file is too large. Maximum size is 5MB.", "error")
                        return render_template(
                            "expense/edit.html",
                            expense=expense,
                            payment_methods=PAYMENT_METHODS,
                            statuses=STATUSES,
                            categories=CATEGORIES,
                        )

                    # Delete old receipt if it exists
                    if expense.receipt_blob_name:
                        try:
                            StorageService.delete_file(expense.receipt_blob_name, RECEIPT_CONTAINER)
                        except Exception as e:
                            current_app.logger.error(f"Error deleting old receipt: {str(e)}")

                    # Upload new file to Azure Blob Storage
                    blob_name, blob_url = StorageService.upload_file(
                        receipt_file, RECEIPT_CONTAINER
                    )

                    # Store blob info in the expense record
                    expense.receipt_blob_name = blob_name
                    expense.receipt_url = blob_url

                except Exception as e:
                    flash(f"Error uploading receipt: {str(e)}", "error")

            db.session.commit()

            flash("Expense record updated successfully!", "success")
            return redirect(url_for("expense.index"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating expense record: {str(e)}", "error")

    return render_template(
        "expense/edit.html",
        expense=expense,
        payment_methods=PAYMENT_METHODS,
        statuses=STATUSES,
        categories=CATEGORIES,
    )


@bp.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    expense = Expense.query.get_or_404(id)

    try:
        # Delete receipt if it exists
        if expense.receipt_blob_name:
            try:
                StorageService.delete_file(expense.receipt_blob_name, RECEIPT_CONTAINER)
            except Exception as e:
                current_app.logger.error(f"Error deleting receipt: {str(e)}")

        db.session.delete(expense)
        db.session.commit()
        flash("Expense record deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting expense record: {str(e)}", "error")

    return redirect(url_for("expense.index"))


@bp.route("/view-receipt/<int:id>", methods=["GET"])
def view_receipt(id):
    expense = Expense.query.get_or_404(id)

    if not expense.receipt_blob_name or not expense.receipt_url:
        flash("No receipt found for this expense", "error")
        return redirect(url_for("expense.edit", id=id))

    try:
        # Generate a SAS URL for temporary access
        sas_url = StorageService.generate_sas_url(expense.receipt_blob_name, RECEIPT_CONTAINER)
        return redirect(sas_url)
    except Exception as e:
        flash(f"Error accessing receipt: {str(e)}", "error")
        return redirect(url_for("expense.edit", id=id))


@bp.route("/delete-receipt/<int:id>", methods=["POST"])
def delete_receipt(id):
    expense = Expense.query.get_or_404(id)

    if not expense.receipt_blob_name:
        flash("No receipt found for this expense", "error")
        return redirect(url_for("expense.edit", id=id))

    try:
        # Delete receipt from storage
        StorageService.delete_file(expense.receipt_blob_name, RECEIPT_CONTAINER)

        # Update expense record
        expense.receipt_blob_name = None
        expense.receipt_url = None

        db.session.commit()
        flash("Receipt deleted successfully", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting receipt: {str(e)}", "error")

    return redirect(url_for("expense.edit", id=id))


@bp.route("/import", methods=["GET", "POST"])
def import_csv():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part", "error")
            return redirect(request.url)

        file = request.files["file"]

        if file.filename == "":
            flash("No selected file", "error")
            return redirect(request.url)

        if file:
            try:
                filename = secure_filename(file.filename)
                filepath = os.path.join(current_app.instance_path, filename)
                file.save(filepath)

                records, count = ImportService.import_expense_csv(filepath)

                # Clean up the file
                os.remove(filepath)

                flash(f"Successfully imported {count} expense records!", "success")
                return render_template("expense/import_success.html", records=records, count=count)
            except Exception as e:
                flash(f"Error importing file: {str(e)}", "error")

    return render_template("expense/import.html")
