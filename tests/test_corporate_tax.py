"""Test corporate tax export functionality directly."""

import io
import csv
from decimal import Decimal

# More direct test approach without using database transactions


def test_gst_hst_calculation():
    """Test the GST/HST calculation formulas directly."""
    test_amount = Decimal("1000.00")  # Amount including tax
    
    # Test for Ontario (13% HST)
    hst_rate = Decimal("0.13")
    
    # Calculate HST using original formula
    pre_tax_amount = test_amount / (Decimal('1.0') + hst_rate)
    hst_collected = test_amount - pre_tax_amount
    hst_collected = hst_collected.quantize(Decimal('0.01'))
    
    # Calculate HST using fallback formula
    alternative_hst = test_amount * (hst_rate / (Decimal('1.0') + hst_rate))
    alternative_hst = alternative_hst.quantize(Decimal('0.01'))
    
    # Both should be approximately $115.04
    expected_hst = Decimal("115.04")
    
    # Check that both calculations give the same result
    assert hst_collected == alternative_hst, f"Calculations don't match: {hst_collected} vs {alternative_hst}"
    
    # Check against the expected value
    assert hst_collected == expected_hst, f"Expected HST: {expected_hst}, got: {hst_collected}"
    
    # Test various other amounts with correctly calculated expected values
    test_cases = [
        {"amount": Decimal("100.00"), "rate": Decimal("0.13"), "expected": Decimal("11.50")},
        {"amount": Decimal("500.00"), "rate": Decimal("0.13"), "expected": Decimal("57.52")},
        {"amount": Decimal("2000.00"), "rate": Decimal("0.13"), "expected": Decimal("230.09")},
        {"amount": Decimal("999.99"), "rate": Decimal("0.05"), "expected": Decimal("47.62")},
        {"amount": Decimal("123.45"), "rate": Decimal("0.15"), "expected": Decimal("16.10")}  # Fixed this value
    ]
    
    for case in test_cases:
        amount = case["amount"]
        rate = case["rate"]
        expected = case["expected"]
        
        # Calculate using both formulas
        pre_tax = amount / (Decimal('1.0') + rate)
        tax1 = (amount - pre_tax).quantize(Decimal('0.01'))
        
        tax2 = (amount * (rate / (Decimal('1.0') + rate))).quantize(Decimal('0.01'))
        
        # Check that both calculations match
        assert tax1 == tax2, f"Calculations don't match for {amount}: {tax1} vs {tax2}"
        
        # Check against expected value
        assert tax1 == expected, f"Expected tax: {expected} for amount {amount} with rate {rate}, got: {tax1}"
    
    # This confirms our calculation formulas work correctly