import os
from datetime import datetime
from decimal import Decimal
from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename

from akowe.models import db
from akowe.models.income import Income
from akowe.services.import_service import ImportService

bp = Blueprint("income", __name__, url_prefix="/income")


@bp.route("/", methods=["GET"])
def index():
    incomes = Income.query.order_by(Income.date.desc()).all()
    return render_template("income/index.html", incomes=incomes)


@bp.route("/new", methods=["GET", "POST"])
def new():
    if request.method == "POST":
        try:
            date = datetime.strptime(request.form["date"], "%Y-%m-%d").date()
            amount = Decimal(request.form["amount"])
            client = request.form["client"]
            project = request.form["project"]
            invoice = request.form["invoice"]

            income = Income(
                date=date, amount=amount, client=client, project=project, invoice=invoice
            )

            db.session.add(income)
            db.session.commit()

            flash("Income record added successfully!", "success")
            return redirect(url_for("income.index"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding income record: {str(e)}", "error")

    return render_template("income/new.html")


@bp.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    income = Income.query.get_or_404(id)

    if request.method == "POST":
        try:
            income.date = datetime.strptime(request.form["date"], "%Y-%m-%d").date()
            income.amount = Decimal(request.form["amount"])
            income.client = request.form["client"]
            income.project = request.form["project"]
            income.invoice = request.form["invoice"]

            db.session.commit()

            flash("Income record updated successfully!", "success")
            return redirect(url_for("income.index"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating income record: {str(e)}", "error")

    return render_template("income/edit.html", income=income)


@bp.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    income = Income.query.get_or_404(id)

    try:
        db.session.delete(income)
        db.session.commit()
        flash("Income record deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting income record: {str(e)}", "error")

    return redirect(url_for("income.index"))


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

                records, count = ImportService.import_income_csv(filepath)

                # Clean up the file
                os.remove(filepath)

                flash(f"Successfully imported {count} income records!", "success")
                return render_template("income/import_success.html", records=records, count=count)
            except Exception as e:
                flash(f"Error importing file: {str(e)}", "error")

    return render_template("income/import.html")
