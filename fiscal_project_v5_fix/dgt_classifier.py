from typing import List, Dict
import random
import json

class DGTAnalyzer:
    """
    Module 2: El Cerebro DGT (Análisis de Deducibilidad).
    Uses a (mocked) LLM to analyze expenses based on CNAE and description.
    """
    
    def __init__(self, api_key: str = None, rules_path: str = "rules.json"):
        self.api_key = api_key
        # In a real scenario, we would initialize Vertex AI or Gemini client here.
        try:
            with open(rules_path, 'r', encoding='utf-8') as f:
                self.rules = json.load(f)
        except Exception:
            # Fallback si no encuentra el archivo (para tests rápidos)
            self.rules = {
                "deduccion_total_keywords": ["server", "cloud", "software", "ordinador", "licencia"],
                "deduccion_parcial_keywords": ["luz", "agua", "internet", "casa", "alquiler"],
                "deduccion_conflictiva_keywords": ["comida", "restaurante", "viaje", "ropa", "traje"]
            }
        
    def _mock_llm_classification(self, expense_desc: str, cnae: str) -> Dict:
        """
        Simula la respuesta de Gemini 1.5 Pro usando reglas cargadas.
        """
        expense_lower = expense_desc.lower()
        
        # Heurística basada en JSON
        if any(x in expense_lower for x in self.rules["deduccion_total_keywords"]):
            return {"category": "DEDUCCIÓN_TOTAL", "reason": "Coincidencia con lista verde (Tecnología/Directo).", "confidence": 0.95}
        
        elif any(x in expense_lower for x in self.rules["deduccion_parcial_keywords"]):
            return {"category": "DEDUCCIÓN_PARCIAL", "reason": "Coincidencia con lista amarilla (Suministros/Vivienda).", "confidence": 0.8}
            
        elif any(x in expense_lower for x in self.rules["deduccion_conflictiva_keywords"]):
            return {"category": "DEDUCCIÓN_CONFLICTIVA", "reason": "Coincidencia con lista roja (Ocio/Personal).", "confidence": 0.6}
            
        else:
            return {"category": "DEDUCCIÓN_PARCIAL", "reason": "No encontrado en listas. Revisión manual requerida.", "confidence": 0.5}

    def analyze_expense(self, expense: Dict, cnae: str) -> Dict:
        """
        Analyzes a single expense.
        expense: {"description": "...", "amount": ...}
        """
        # Call LLM (Mocked)
        analysis = self._mock_llm_classification(expense["description"], cnae)
        
        result = {
            "description": expense["description"],
            "amount": expense["amount"],
            "category": analysis["category"], # VERDE (Total), AMARILLA (Parcial), ROJA (Conflictiva)
            "reason": analysis["reason"],
            "deductible_amount": 0
        }
        
        # Apply logic based on Category
        # UPDATE: User requested NO proration. If entered, it is 100% deductible.
        # Classification remains for "Risk Info", but value is taken fully.
        result["deductible_amount"] = expense["amount"]
            
        return result

    def calculate_risk_score(self, analyzed_expenses: List[Dict]) -> int:
        """
        Calcula un 'Score de Riesgo Fiscal' del 1 (Seguro) al 10 (Alto Riesgo).
        Basado en el ratio de gastos Conflictivos/Parciales reclamados.
        """
        total_claimed = 0
        risk_weighted_sum = 0
        
        for exp in analyzed_expenses:
            amount = exp["amount"]
            cat = exp["category"]
            
            # Si el usuario lo reclama (asumiendo que intenta reclamar logicamente)
            # Aquí calculamos el riesgo de la estrategia.
            
            total_claimed += amount
            
            if cat == "DEDUCCIÓN_CONFLICTIVA":
                risk_weighted_sum += amount * 10 # Alto riesgo
            elif cat == "DEDUCCIÓN_PARCIAL":
                risk_weighted_sum += amount * 5 # Riesgo medio
            else:
                risk_weighted_sum += amount * 1 # Riesgo bajo
                
        if total_claimed == 0:
            return 1
            
        avg_risk = risk_weighted_sum / total_claimed
        return min(10, max(1, int(avg_risk)))

    def process_expenses(self, expenses: List[Dict], cnae: str) -> Dict:
        """
        Punto de entrada principal para el módulo 2.
        """
        analyzed = [self.analyze_expense(e, cnae) for e in expenses]
        risk_score = self.calculate_risk_score(analyzed)
        
        total_deductible = sum(e["deductible_amount"] for e in analyzed)
        
        return {
            "analyzed_expenses": analyzed,
            "fiscal_risk_score": risk_score,
            "total_deductible_suggested": total_deductible
        }

if __name__ == "__main__":
    dgt = DGTAnalyzer()
    expenses = [
        {"description": "AWS Hosting", "amount": 200},
        {"description": "Comida Cliente", "amount": 150},
        {"description": "Factura Luz Casa", "amount": 100}
    ]
    print(dgt.process_expenses(expenses, "6201"))
