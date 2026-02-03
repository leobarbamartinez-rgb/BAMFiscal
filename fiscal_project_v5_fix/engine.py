import json
import os

class FiscalEngine:
    def __init__(self, data_path="tax_data.json"):
        with open(data_path, 'r') as f:
            self.data = json.load(f)

    def _calculate_progressive_tax(self, base, table):
        """Calcula el impuesto basado en una tabla progresiva."""
        tax = 0
        remaining_base = base
        previous_limit = 0
        
        for bracket in table:
            if "hasta" in bracket:
                limit = bracket["hasta"]
                rate = bracket["tipo"]
                taxable_amount = min(remaining_base, limit - previous_limit)
                
                if taxable_amount <= 0:
                    break
                    
                tax += taxable_amount * rate
                remaining_base -= taxable_amount
                previous_limit = limit
                
                if remaining_base <= 0:
                    break
            elif "mas_de" in bracket:
                # Tramo superior
                rate = bracket["tipo"]
                tax += remaining_base * rate
                
        return tax

    def calculate_irpf(self, gross_salary, region="Madrid"):
        """
        Calcula el IRPF.
        Simplificación: IRPF Total = Tabla Estatal * 2 (Asumiendo que la Autonómica iguala a la Estatal).
        En la realidad, cada comunidad tiene su propia tabla.
        """
        # Deducción SS básica empleado (aprox 6.35% del bruto).
        ss_employee = gross_salary * 0.0635 
        
        # Reducciones del trabajo (Reducción estándar 2000)
        net_taxable_base = gross_salary - ss_employee - 2000
        if net_taxable_base < 0: net_taxable_base = 0
        
        if net_taxable_base < 0: net_taxable_base = 0
        
        # 1. State Tax
        state_tax = self._calculate_progressive_tax(net_taxable_base, self.data["irpf_table_estatal"])
        
        # 2. Regional Tax
        # Get table for Region, fallback to "Otros" (Generic) if not found
        regional_table_name = region
        if regional_table_name not in self.data["irpf_tables_autonomicas"]:
            regional_table_name = "Otros (Ceuta/Melilla/Resto)"
            
        regional_tax = self._calculate_progressive_tax(net_taxable_base, self.data["irpf_tables_autonomicas"][regional_table_name])

        total_tax = state_tax + regional_tax
        
        return total_tax, ss_employee

    def calculate_reta(self, net_yield_estimated):
        """Calcula la cuota mensual RETA basada en ingresos reales."""
        # Buscar tramo
        monthly_yield = net_yield_estimated / 12
        quota = 0
        
        tramos = self.data["reta_2026_provisional"]["tramos"]
        
        for tramo in tramos:
            if tramo["ingresos_min"] <= monthly_yield <= tramo["ingresos_max"]:
                quota = tramo["cuota"] if isinstance(tramo["cuota"], (int, float)) else 590 # fallback
                break
        
        if quota == 0:
             # Fallback si supera el rango máximo
             quota = 590

        return quota * 12

    def calculate_savings_tax(self, amount):
        """Calcula el impuesto sobre el ahorro (Dividendos)."""
        return self._calculate_progressive_tax(amount, self.data["ahorro_table"])

    def run_simulation(self, 
                       employee_gross: float, 
                       employee_ss: float,
                       company_ss: float,
                       employee_personal_expenses: float, # New param
                       autonomo_gross: float, 
                       autonomo_expenses: float, 
                       region: str = "Madrid", 
                       is_new_company: bool = False):
        """
        Compara los 3 regímenes: Asalariado, Autónomo, SL.
        """
        
        # 1. Asalariado
        # Neto = Sueldo Base - Cotizaciones Trabajador - IRPF
        # Base Imponible IRPF = Sueldo Base - Cotizaciones Trabajador - 2000 (Reducción standard)
        
        net_taxable_base_employee = employee_gross - employee_ss - 2000
        if net_taxable_base_employee < 0: net_taxable_base_employee = 0
        
        state_tax_employee = self._calculate_progressive_tax(net_taxable_base_employee, self.data["irpf_table_estatal"])
        
        regional_tbl = region if region in self.data["irpf_tables_autonomicas"] else "Otros (Ceuta/Melilla/Resto)"
        regional_tax_employee = self._calculate_progressive_tax(net_taxable_base_employee, self.data["irpf_tables_autonomicas"][regional_tbl])
        
        
        irpf_employee = state_tax_employee + regional_tax_employee
        net_employee_official = employee_gross - employee_ss - irpf_employee
        
        # Apply "Fair Comparison": Subtract expenses that employee pays but cannot deduct
        net_employee_pocket = net_employee_official - employee_personal_expenses
        
        # 2. Autónomo
        # Base Imponible = Ingresos - Gastos - RETA
        # RETA se basa en Rendimiento Neto (Ingreso - Gasto)
        
        # 2. Autónomo
        # Base Imponible = Ingresos - Gastos - RETA
        
        net_yield_pre_reta = autonomo_gross - autonomo_expenses
        reta_annual = self.calculate_reta(net_yield_pre_reta)
        
        # IRPF Autónomo: Misma escala que Empleado (Base General)
        # 1. Aplicar Gastos de Difícil Justificación (7% del Rendimiento Neto previo, tope 2000€)
        # Rendimiento previo = Ingresos - Gastos (deductibles) - RETA
        # NOTA: RETA es gasto deducible. 
        # La norma suele ser: (Ingresos - Gastos) -> Restar 7% -> Restar RETA? 
        # NO: RETA es un gasto más para el rendimiento neto.
        # Orden: (Ingresos - Gastos - RETA) = Rendimiento Neto Previo.
        # Reducción 7% sobre (Ingresos - Gastos - RETA positives).
        
        # Reducción 7% sobre (Ingresos - Gastos - RETA positives).
        
        net_yield_before_reduction = net_yield_pre_reta - reta_annual
        
        difficult_justification_expenses = net_yield_before_reduction * 0.07
        if difficult_justification_expenses > 2000:
            difficult_justification_expenses = 2000
            
        base_imponible_autonomo = net_yield_before_reduction - difficult_justification_expenses
        
        if base_imponible_autonomo < 0: base_imponible_autonomo = 0
        
        state_tax_auto = self._calculate_progressive_tax(base_imponible_autonomo, self.data["irpf_table_estatal"])
        
        # Look up regional table again
        regional_table_name_auto = region
        if regional_table_name_auto not in self.data["irpf_tables_autonomicas"]:
             regional_table_name_auto = "Otros (Ceuta/Melilla/Resto)"
             
        regional_tax_auto = self._calculate_progressive_tax(base_imponible_autonomo, self.data["irpf_tables_autonomicas"][regional_table_name_auto])
        
        irpf_autonomo = state_tax_auto + regional_tax_auto
        
        net_autonomo = base_imponible_autonomo - irpf_autonomo
        
        # 3. Sociedad Limitada (SL)
        # Beneficio = Ingresos - Gastos - SalarioAdmin - SS_Societario
        # Asumimos coste fijo SS Societario ~ 4500/año
        
        ss_societario = 4500
        
        # Admin Salary strategy:
        # Prompt: "Neto = SalarioAdministrador(Neto) + [Beneficio x (1-IS) x (1-Dividendo)]"
        # We need to decide SalarioAdministrador.
        # Strategy: Set Salary to 0 to test specific 'Dividend' efficiency?
        # Or set Salary = 20,000 as base living?
        # Let's assume Salary = 0 for pure contrast, acknowledging the risk.
        # Or better, Salary = 25% of Profit?
        # To make it deterministic for the user prompt which didn't specify:
        # We will assume Administrator Salary = 0 (Pure Capital gain focus) OR
        # We will assume a minimal salary.
        # Let's set admin_salary = 0 for this version, maximizing the IS+Dividend route difference.
        
        admin_salary_gross = 0
        admin_salary_net = 0 # If 0 gross
        
        admin_salary_gross = 0
        admin_salary_net = 0 # If 0 gross
        
        corporate_profit_base = autonomo_gross - autonomo_expenses - admin_salary_gross - ss_societario
        
        is_rate = self.data["is_rates"]["new_entity"] if is_new_company else self.data["is_rates"]["general"]
        
        corporate_tax = corporate_profit_base * is_rate
        if corporate_tax < 0: corporate_tax = 0
        
        net_profit_available = corporate_profit_base - corporate_tax
        
        # Dividends
        dividend_gross = net_profit_available
        dividend_tax = self.calculate_savings_tax(dividend_gross)
        dividend_net = dividend_gross - dividend_tax
        
        net_sl = admin_salary_net + dividend_net
        
        return {
            "inputs": {
                "employee_gross": employee_gross,
                "autonomo_gross": autonomo_gross,
                "region": region
            },
            "results": {
                "asalariado": {
                    "neto": round(net_employee_pocket, 2),
                    "irpf": round(irpf_employee, 2),
                    "ss": round(employee_ss, 2),
                    "details": {
                        "bruto": employee_gross,
                        "ss_cuota": employee_ss,
                        "reduccion_trabajo": 2000,
                        "base_imponible": net_taxable_base_employee,
                        "cuota_estatal": state_tax_employee,
                        "cuota_autonomica": regional_tax_employee,
                        "total_irpf": irpf_employee,
                        "neto_oficial": net_employee_official,
                        "gastos_personales_asumidos": employee_personal_expenses
                    }
                },
                "autonomo": {
                    "neto": round(net_autonomo, 2),
                    "irpf": round(irpf_autonomo, 2),
                    "reta": round(reta_annual, 2),
                    "details": {
                        "ingresos": autonomo_gross,
                        "gastos": autonomo_expenses,
                        "reta_anual": reta_annual,
                        "rendimiento_neto_previo": net_yield_before_reduction,
                        "reduccion_7_porciento": difficult_justification_expenses,
                        "base_imponible": base_imponible_autonomo,
                        "cuota_estatal": state_tax_auto,
                        "cuota_autonomica": regional_tax_auto,
                        "total_irpf": irpf_autonomo
                    }
                },
                "sociedad_limitada": {
                    "neto": round(net_sl, 2),
                    "is": round(corporate_tax, 2),
                    "dividend_tax": round(dividend_tax, 2),
                    "ss_societario": ss_societario,
                    "admin_salary_net": admin_salary_net,
                    "details": {
                        "ingresos": autonomo_gross,
                        "gastos": autonomo_expenses,
                        "ss_societario": ss_societario,
                        "base_imponible_is": corporate_profit_base,
                        "tipo_is": is_rate,
                        "cuota_is": corporate_tax,
                        "dividendo_bruto": dividend_gross,
                        "retencion_dividendo": dividend_tax,
                        "dividendo_neto": dividend_net
                    }
                }
            }
        }

if __name__ == "__main__":
    # Quick Test
    engine = FiscalEngine()
    print(json.dumps(engine.run_simulation(60000, 5000), indent=2))
