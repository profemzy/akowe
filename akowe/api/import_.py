"""Import API for financial data."""

import os
from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from akowe.services.import_service import ImportService

bp = Blueprint("import", __name__, url_prefix="/import")


@bp.route("/", methods=["GET"])
@login_required
def index():
    """Show the unified import page."""
    return render_template("import/index.html")


@bp.route("/all_transactions", methods=["POST"])
@login_required
def import_all_transactions():
    """Import all transactions from a CSV file."""
    if "file" not in request.files:
        flash("No file part", "error")
        return redirect(url_for("import.index"))

    file = request.files["file"]

    if file.filename == "":
        flash("No selected file", "error")
        return redirect(url_for("import.index"))

    if file:
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.instance_path, filename)
            file.save(filepath)

            results, count = ImportService.import_all_transactions_csv(filepath)

            # Clean up the file
            os.remove(filepath)

            flash(
                f"Successfully imported {count} transactions "
                f"({results['income_count']} income, {results['expense_count']} expenses)!",
                "success"
            )
            return render_template(
                "import/import_success.html", 
                results=results, 
                count=count
            )
        except Exception as e:
            current_app.logger.error(f"Error importing transactions: {str(e)}")
            flash(f"Error importing file: {str(e)}", "error")

    return redirect(url_for("import.index"))


@bp.route("/income", methods=["POST"])
@login_required
def import_income():
    """Import income transactions from a CSV file."""
    if "file" not in request.files:
        flash("No file part", "error")
        return redirect(url_for("import.index"))

    file = request.files["file"]

    if file.filename == "":
        flash("No selected file", "error")
        return redirect(url_for("import.index"))

    if file:
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.instance_path, filename)
            file.save(filepath)

            records, count = ImportService.import_income_csv(filepath)

            # Clean up the file
            os.remove(filepath)

            flash(f"Successfully imported {count} income records!", "success")
            return render_template("income/import_success.html", records=records, count=count)
        except Exception as e:
            flash(f"Error importing file: {str(e)}", "error")

    return redirect(url_for("import.index"))


@bp.route("/expense", methods=["POST"])
@login_required
def import_expense():
    """Import expense transactions from a CSV file."""
    if "file" not in request.files:
        flash("No file part", "error")
        return redirect(url_for("import.index"))

    file = request.files["file"]

    if file.filename == "":
        flash("No selected file", "error")
        return redirect(url_for("import.index"))

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

    return redirect(url_for("import.index"))