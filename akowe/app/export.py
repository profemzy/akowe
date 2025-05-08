"""Export API for financial data."""

from flask import Blueprint, request, send_file, current_app, render_template
from flask_login import login_required

from akowe.services.export_service import ExportService

bp = Blueprint("export", __name__, url_prefix="/export")


@bp.route("/", methods=["GET"])
@login_required
def index():
    """Show the export interface."""
    return render_template("export/index.html")


@bp.route("/income", methods=["GET"])
@login_required
def export_income():
    """Export income data to CSV.

    Query Parameters:
        year (int): Optional year to filter income records
    """
    # Get the year parameter, if provided
    year = request.args.get("year", type=int)

    try:
        # Generate the CSV file
        csv_data, filename = ExportService.export_income_csv(year)

        # Send the file to the client
        return send_file(csv_data, as_attachment=True, download_name=filename, mimetype="text/csv")
    except Exception as e:
        current_app.logger.error(f"Error exporting income: {str(e)}")
        return {"error": "Failed to export income data"}, 500


@bp.route("/expense", methods=["GET"])
@login_required
def export_expense():
    """Export expense data to CSV.

    Query Parameters:
        year (int): Optional year to filter expense records
        category (str): Optional category to filter expense records
    """
    # Get the parameters, if provided
    year = request.args.get("year", type=int)
    category = request.args.get("category")

    try:
        # Generate the CSV file
        csv_data, filename = ExportService.export_expense_csv(year, category)

        # Send the file to the client
        return send_file(csv_data, as_attachment=True, download_name=filename, mimetype="text/csv")
    except Exception as e:
        current_app.logger.error(f"Error exporting expenses: {str(e)}")
        return {"error": "Failed to export expense data"}, 500


@bp.route("/all", methods=["GET"])
@login_required
def export_all():
    """Export all transactions to CSV.

    Query Parameters:
        year (int): Optional year to filter transactions
    """
    # Get the year parameter, if provided
    year = request.args.get("year", type=int)

    try:
        # Generate the CSV file
        csv_data, filename = ExportService.export_all_transactions_csv(year)

        # Send the file to the client
        return send_file(csv_data, as_attachment=True, download_name=filename, mimetype="text/csv")
    except Exception as e:
        current_app.logger.error(f"Error exporting transactions: {str(e)}")
        return {"error": "Failed to export transaction data"}, 500
