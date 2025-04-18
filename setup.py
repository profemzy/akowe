from setuptools import setup, find_packages

setup(
    name="akowe",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "flask",
        "flask-sqlalchemy",
        "flask-migrate",
        "flask-login",
        "python-dotenv",
        "pandas",
        "azure-storage-blob",
        "openpyxl",
        "pdfkit",
        "pytz",
    ],
)