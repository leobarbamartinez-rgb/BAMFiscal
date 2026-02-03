from engine import FiscalEngine
from dgt_classifier import DGTAnalyzer
import json

def test_full_flow():
    print("--- Starting Fiscal Navigator Simulation Test ---")
    
    # Setup
    try:
        engine = FiscalEngine("tax_data.json")
        dgt = DGTAnalyzer()
    except Exception as e:
        print(f"Error initializing: {e}")
        return
    
    # Scenario: Senior Dev
    gross_income = 65000
    cnae = "6201" # Programming
    
    # Expenses (some good, some bad)
    expenses = [
        {"description": "MacBook Pro M4", "amount": 3500}, # Green
        {"description": "Silla Herman Miller", "amount": 1200}, # Green/Partial depending on logic (furniture often partial if home)
        {"description": "Cena Navidad", "amount": 200}, # Red
        {"description": "Internet Casa", "amount": 600} # Yellow
    ]
    
    print(f"Scenario: Income {gross_income} EUR, Expenses: {len(expenses)} items totaling {sum(e['amount'] for e in expenses)}")
    
    # Module 2: Analysis
    processed_expenses = dgt.process_expenses(expenses, cnae)
    deductible = processed_expenses["total_deductible_suggested"]
    print(f"\n[DGT Module] Analysis Risk Score: {processed_expenses['fiscal_risk_score']}/10")
    print(f"[DGT Module] Total Deductible Suggested: {deductible:.2f} EUR")
    
    # Module 1: Engine
    # Module 1: Engine
    simulation = engine.run_simulation(
        employee_gross=gross_income,
        employee_ss=gross_income*0.0635, # Estimating for test
        company_ss=gross_income*0.299,
        employee_personal_expenses=2000, # Testing the new subtraction logic
        autonomo_gross=gross_income,
        autonomo_expenses=deductible,
        region="Madrid"
    )
    
    print("\n--- RESULTS (Net Pocket) ---")
    results = simulation["results"]
    print(f"Asalariado Net: {results['asalariado']['neto']} EUR  (IRPF: {results['asalariado']['irpf']})")
    print(f"Autonomo Net:   {results['autonomo']['neto']} EUR  (RETA: {results['autonomo']['reta']}, IRPF: {results['autonomo']['irpf']})")
    print(f"SL Net:         {results['sociedad_limitada']['neto']} EUR  (IS: {results['sociedad_limitada']['is']}, DivTax: {results['sociedad_limitada']['dividend_tax']})")
    
    # Comparison
    best_option = max(results, key=lambda k: results[k]['neto'])
    print(f"\n>>> FINAL WINNER: {best_option.upper()} <<<")
    
    # Check assertions (Basic logic checks)
    if results['sociedad_limitada']['neto'] > results['asalariado']['neto']:
        print("Verification: SL beats Asalariado for high income (Expected).")
    else:
        print("Verification: SL did not beat Asalariado (Suggests low income or overheads).")

if __name__ == "__main__":
    test_full_flow()
