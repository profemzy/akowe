"""Export API for financial data and tax preparation formats."""

from flask import Blueprint, request, send_file, current_app, render_template
from flask_login import login_required

from akowe.services.export_service import ExportService
from akowe.services.tax_export_service import TaxExportService
from akowe.services.corporate_tax_export_service import CorporateTaxExportService
from akowe.app.tax_dashboard import GST_HST_RATES

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


@bp.route("/tax/t2125", methods=["GET"])
@login_required
def export_t2125():
    """Export data in CRA T2125 format.

    Query Parameters:
        year (int): Tax year to export (required)
        province (str): Province for GST/HST calculation (default: Ontario)
    """
    # Get the required year parameter
    year = request.args.get("year", type=int)
    if not year:
        return {"error": "Year parameter is required"}, 400

    # Get optional province parameter
    province = request.args.get("province", default="Ontario")

    try:
        # Generate the CSV file
        csv_data, filename = TaxExportService.export_t2125_format(year, province)

        # Send the file to the client
        return send_file(csv_data, as_attachment=True, download_name=filename, mimetype="text/csv")
    except Exception as e:
        current_app.logger.error(f"Error exporting T2125 data: {str(e)}")
        return {"error": "Failed to export T2125 data"}, 500


@bp.route("/tax/turbotax", methods=["GET"])
@login_required
def export_turbotax():
    """Export data in TurboTax format.

    Query Parameters:
        year (int): Tax year to export (required)
    """
    # Get the required year parameter
    year = request.args.get("year", type=int)
    if not year:
        return {"error": "Year parameter is required"}, 400

    try:
        # Get optional province parameter
        province = request.args.get("province", default="Ontario")

        # Generate the CSV file
        csv_data, filename = TaxExportService.export_turbotax_format(year, province)

        # Send the file to the client
        return send_file(csv_data, as_attachment=True, download_name=filename, mimetype="text/csv")
    except Exception as e:
        current_app.logger.error(f"Error exporting TurboTax data: {str(e)}")
        return {"error": "Failed to export TurboTax data"}, 500


@bp.route("/tax/wealthsimple", methods=["GET"])
@login_required
def export_wealthsimple():
    """Export data in Wealthsimple Tax format.

    Query Parameters:
        year (int): Tax year to export (required)
    """
    # Get the required year parameter
    year = request.args.get("year", type=int)
    if not year:
        return {"error": "Year parameter is required"}, 400

    try:
        # Get optional province parameter
        province = request.args.get("province", default="Ontario")

        # Generate the CSV file
        csv_data, filename = TaxExportService.export_wealthsimple_format(year, province)

        # Send the file to the client
        return send_file(csv_data, as_attachment=True, download_name=filename, mimetype="text/csv")
    except Exception as e:
        current_app.logger.error(f"Error exporting Wealthsimple Tax data: {str(e)}")
        return {"error": "Failed to export Wealthsimple Tax data"}, 500


@bp.route("/tax/corporate/t2gifi", methods=["GET"])
@login_required
def export_t2_gifi():
    """Export data in T2 GIFI format for corporate tax returns.

    Query Parameters:
        year (int): Tax year to export (required)
        province (str): Province for GST/HST calculation (default: Ontario)
    """
    # Get the required year parameter
    year = request.args.get("year", type=int)
    if not year:
        return {"error": "Year parameter is required"}, 400

    # Get optional province parameter
    province = request.args.get("province", default="Ontario")

    try:
        # Generate the CSV file
        csv_data, filename = CorporateTaxExportService.export_t2_gifi_format(year, province)

        # Send the file to the client
        return send_file(csv_data, as_attachment=True, download_name=filename, mimetype="text/csv")
    except Exception as e:
        current_app.logger.error(f"Error exporting T2 GIFI data: {str(e)}")
        return {"error": "Failed to export T2 GIFI data"}, 500


@bp.route("/tax/corporate/schedule8", methods=["GET"])
@login_required
def export_t2_schedule8():
    """Export data in T2 Schedule 8 format for corporate tax returns.

    Query Parameters:
        year (int): Tax year to export (required)
    """
    # Get the required year parameter
    year = request.args.get("year", type=int)
    if not year:
        return {"error": "Year parameter is required"}, 400

    try:
        # Generate the CSV file
        csv_data, filename = CorporateTaxExportService.export_t2_schedule8_format(year)

        # Send the file to the client
        return send_file(csv_data, as_attachment=True, download_name=filename, mimetype="text/csv")
    except Exception as e:
        current_app.logger.error(f"Error exporting T2 Schedule 8 data: {str(e)}")
        return {"error": "Failed to export T2 Schedule 8 data"}, 500


@bp.route("/tax/corporate/turbotax", methods=["GET"])
@login_required
def export_corporate_turbotax():
    """Export data in Corporate TurboTax format.

    Query Parameters:
        year (int): Tax year to export (required)
        province (str): Province for GST/HST calculation (default: Ontario)
    """
    # Get the required year parameter
    year = request.args.get("year", type=int)
    if not year:
        return {"error": "Year parameter is required"}, 400

    # Get optional province parameter
    province = request.args.get("province", default="Ontario")

    try:
        # Generate the CSV file
        csv_data, filename = CorporateTaxExportService.export_corporate_turbotax_format(year, province)

        # Send the file to the client
        return send_file(csv_data, as_attachment=True, download_name=filename, mimetype="text/csv")
    except Exception as e:
        current_app.logger.error(f"Error exporting Corporate TurboTax data: {str(e)}")
        return {"error": "Failed to export Corporate TurboTax data"}, 500
