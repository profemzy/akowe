from flask import Flask, render_template
import os

# Create a simple Flask app for testing template resolution
app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(__file__), "akowe", "templates"))


@app.route("/test")
def test():
    try:
        return render_template("dashboard/index.html", 
                               all_time_income=0,
                               all_time_expense=0,
                               all_time_profit=0,
                               year_income=0,
                               year_expense=0,
                               year_profit=0,
                               recent_income=[],
                               recent_expenses=[],
                               months=[],
                               monthly_income_data=[],
                               monthly_expense_data=[],
                               category_labels=[],
                               category_data=[],
                               selected_year=2025,
                               available_years=[])
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    # Print the template path
    print(f"Template folder: {app.template_folder}")
    print(f"Dashboard template exists: {os.path.exists(os.path.join(app.template_folder, 'dashboard', 'index.html'))}")
    
    # Run the test server
    app.run(debug=True, port=5001)