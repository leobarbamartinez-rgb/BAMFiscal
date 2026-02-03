import functions_framework
from google.cloud import bigquery
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional
import json
import logging

# Import local modules
from engine import FiscalEngine
from dgt_classifier import DGTAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)

# Pydantic Models for Validation
class ExpenseItem(BaseModel):
    description: str
    amount: float = Field(..., gt=0, description="Amount in EUR")

class SimulationRequest(BaseModel):
    gross_income: float = Field(..., gt=0, description="Annual Gross Income")
    expenses: List[ExpenseItem] = []
    region: str = "Madrid"
    cnae: str = Field(..., description="CNAE Activity Code")
    is_new_company: bool = False

# BigQuery Client (Global for reuse)
# client = bigquery.Client() # Commented out to prevent errors in local env without creds

def get_tax_data_from_bq():
    """
    Fetches tax data from BigQuery. 
    Fallbacks to local JSON if BQ fails or not configured.
    """
    try:
        # client = bigquery.Client()
        # query = "SELECT * FROM `project.dataset.tax_tables_2026`"
        # results = client.query(query).result()
        # ... logic to parse results ...
        logging.info("Attempting BigQuery connection...")
        raise Exception("BQ Credentials not found (Mock)")
    except Exception as e:
        logging.warning(f"BigQuery fetch failed: {e}. Using local tax_data.json")
        return "tax_data.json" # Return path to local file for Engine to load

@functions_framework.http
def fiscal_navigator_api(request):
    """HTTP Cloud Function entry point."""
    
    # CORS Headers
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)

    headers = {'Access-Control-Allow-Origin': '*'}

    # Parsing Request
    try:
        request_json = request.get_json(silent=True)
        if not request_json:
            return ({"error": "Invalid JSON"}, 400, headers)
            
        # Validation with Pydantic
        data = SimulationRequest(**request_json)
        
    except ValidationError as e:
        return ({"error": "Validation Error", "details": e.errors()}, 400, headers)
    except Exception as e:
        return ({"error": f"Bad Request: {str(e)}"}, 400, headers)

    try:
        # 1. Initialize Engines
        # In a real cold-start, we might load data here.
        data_source = get_tax_data_from_bq()
        engine = FiscalEngine(data_source)
        dgt = DGTAnalyzer()
        
        # 2. Process Expenses (Module 2)
        # We process expenses first to determine deductible amount
        dgt_result = dgt.process_expenses([e.dict() for e in data.expenses], data.cnae)
        
        deductible_expenses = dgt_result["total_deductible_suggested"]
        
        # 3. Process Calculation (Module 1)
        # We pass the calculated deductible expenses to the engine
        calc_result = engine.run_simulation(
            gross_income=data.gross_income,
            deductibles=deductible_expenses,
            region=data.region,
            is_new_company=data.is_new_company
        )
        
        # 4. Construct Final Response
        response = {
            "status": "success",
            "dgt_analysis": {
                "risk_score": dgt_result["fiscal_risk_score"],
                "details": dgt_result["analyzed_expenses"],
                "total_deductible": deductible_expenses
            },
            "financial_simulation": calc_result["results"],
            "inputs": calc_result["inputs"]
        }
        
        return (json.dumps(response), 200, headers)

    except Exception as e:
        logging.error(f"Internal Error: {e}")
        return ({"error": str(e)}, 500, headers)
