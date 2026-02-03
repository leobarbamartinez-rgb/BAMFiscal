import streamlit as st
import pandas as pd
from engine import FiscalEngine
from dgt_classifier import DGTAnalyzer

# Configuración de la página
st.set_page_config(page_title="Fiscal Navigator 2026", layout="wide")

st.title("🇪🇸 Fiscal Navigator Spain 2026")
st.markdown("Comparador de eficiencia fiscal: **Asalariado vs Autónomo vs Sociedad Limitada**")

# Sidebar: Configuración de Datos
st.sidebar.header("📍 Configuración General")
# Initialize engine to get available regions
engine = FiscalEngine() 
available_regions = list(engine.data["irpf_tables_autonomicas"].keys())
default_index = available_regions.index("Madrid") if "Madrid" in available_regions else 0
region = st.sidebar.selectbox("Comunidad Autónoma", available_regions, index=default_index)

st.sidebar.divider()

st.sidebar.header("👨‍💼 Datos Nómina (Asalariado)")
employee_gross = st.sidebar.number_input("Sueldo Bruto Anual (€)", min_value=12000, value=30000, step=1000)
employee_ss = st.sidebar.number_input("Cotizaciones Trabajador (€)", min_value=0, value=int(30000*0.0635), help="Aprox 6.35% del bruto")
company_ss = st.sidebar.number_input("Cotizaciones Empresa (€)", min_value=0, value=int(30000*0.299), help="Solo informativo (aprox 29.9% del bruto)")

st.sidebar.divider()

st.sidebar.header("💻 Datos Actividad (Autónomo/SL)")
autonomo_gross = st.sidebar.number_input("Facturación Bruta Anual (€)", min_value=0, value=45000, step=1000)
cnae = st.sidebar.text_input("Código CNAE", value="6201")

if "expenses" not in st.session_state:
    st.session_state.expenses = []

with st.sidebar.expander("Añadir Gastos Actividad", expanded=False):
    desc = st.text_input("Descripción", key="desc_input")
    amount = st.number_input("Importe Anual Deducible (€)", min_value=0, value=0, key="amount_input", help="Introduce el importe total anual que consideres deducible.")
    also_employee = st.checkbox("¿Gasto también incurrido como Asalariado?", help="Marca esto si es un gasto que pagarías igual siendo empleado (ej: internet, móvil, ordenador) pero sin poder deducirlo.")
    
    if st.button("Añadir"):
        if desc and amount > 0:
            st.session_state.expenses.append({
                "description": desc, 
                "amount": amount,
                "also_employee": also_employee
            })
            st.rerun()

    # Show list
    for i, e in enumerate(st.session_state.expenses):
        emp_tag = " (Paga también Asalariado)" if e.get("also_employee") else ""
        st.caption(f"{e['description']}: {e['amount']} €{emp_tag}")
    
    if st.button("Borrar Todos"):
        st.session_state.expenses = []
        st.rerun()

# Mostrar Gastos y Análisis
if st.session_state.expenses:
    dgt = DGTAnalyzer()
    processed = dgt.process_expenses(st.session_state.expenses, cnae)
    
    st.subheader("🕵️ Análisis de Inteligencia DGT")
    
    # Métricas de riesgo
    risk_score = processed["fiscal_risk_score"]
    color = "green" if risk_score < 4 else "orange" if risk_score < 7 else "red"
    st.metric("Score de Riesgo Fiscal", f"{risk_score}/10")
    
    # Tabla de gastos clasificados
    df_expenses = pd.DataFrame(processed["analyzed_expenses"])
    # Traducir columnas para visualización
    df_show = df_expenses[["description", "amount", "category", "reason", "deductible_amount"]]
    st.dataframe(df_show, use_container_width=True)
    
    total_deductible = processed["total_deductible_suggested"]
else:
    total_deductible = 0

# Simulación Principal
if st.button("🚀 Ejecutar Simulación Fiscal", type="primary"):
    engine = FiscalEngine()
    
    # Calculate total expenses from session
    # Note: engine expects 'autonomo_expenses'. 
    
    total_deductible = 0
    employee_personal_expenses = 0
    
    for e in st.session_state.expenses:
        total_deductible += e["amount"]
        if e.get("also_employee"):
            employee_personal_expenses += e["amount"]
    
    result = engine.run_simulation(
        employee_gross=employee_gross, 
        employee_ss=employee_ss,
        company_ss=company_ss,
        employee_personal_expenses=employee_personal_expenses,
        autonomo_gross=autonomo_gross, 
        autonomo_expenses=total_deductible, 
        region=region
    )
    
    res = result["results"]
    
    st.divider()
    
    # Tarjetas de Resultados
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.header("👨‍💼 Asalariado")
        st.metric("Neto en Bolsillo", f"{res['asalariado']['neto']:,.2f} €", help="Incluye resta de gastos personales no deducibles si los has marcado.")
        st.caption(f"IRPF pagado: {res['asalariado']['irpf']:,.2f} €")
        
    with c2:
        st.header("💻 Autónomo")
        st.metric("Neto en Bolsillo", f"{res['autonomo']['neto']:,.2f} €", 
                  delta=f"{res['autonomo']['neto'] - res['asalariado']['neto']:,.2f} € vs Asalariado")
        st.caption(f"Cuota RETA: {res['autonomo']['reta']:,.2f} €")
        
    with c3:
        st.header("🏢 Sociedad Limitada")
        st.metric("Neto en Bolsillo", f"{res['sociedad_limitada']['neto']:,.2f} €",
                  delta=f"{res['sociedad_limitada']['neto'] - res['asalariado']['neto']:,.2f} € vs Asalariado")
        st.caption(f"Impuesto Sociedades: {res['sociedad_limitada']['is']:,.2f} €")

    # Gráfica
    st.subheader("Comparativa Visual")
    chart_data = pd.DataFrame({
        "Régimen": ["Asalariado", "Autónomo", "Sociedad Limitada"],
        "Neto Anual": [res['asalariado']['neto'], res['autonomo']['neto'], res['sociedad_limitada']['neto']]
    })
    st.bar_chart(chart_data, x="Régimen", y="Neto Anual", color="Régimen")

    st.markdown("---")
    st.subheader("📝 Desglose de Cálculos")
    
    with st.expander("Ver detalle: Asalariado"):
        d = res['asalariado']['details']
        st.write(f"**Ingresos Brutos**: {d['bruto']:,.2f} €")
        st.write(f"- Seguridad Social (aprox 6.35%): {d['ss_cuota']:,.2f} €")
        st.write(f"- Reducción por Trabajo: {d['reduccion_trabajo']:,.2f} €")
        st.markdown(f"**= Base Liquidable IRPF**: `{d['base_imponible']:,.2f} €`")
        st.write(f"  * Cuota Estatal: {d['cuota_estatal']:,.2f} €")
        st.write(f"  * Cuota Autonómica ({region}): {d['cuota_autonomica']:,.2f} €")
        st.markdown(f"**Total IRPF**: `{d['total_irpf']:,.2f} €`")
        st.write("---")
        st.write(f"Neto en Nómina: {d['neto_oficial']:,.2f} €")
        if d['gastos_personales_asumidos'] > 0:
            st.write(f"- Gastos Personales (No Deducibles): {d['gastos_personales_asumidos']:,.2f} €")
            st.caption("Estos son gastos que has marcado como 'incurridos también por asalariado'.")
        st.success(f"**Neto Real en Bolsillo**: {res['asalariado']['neto']:,.2f} €")

    with st.expander("Ver detalle: Autónomo (Est. Directa Simplificada)"):
        d = res['autonomo']['details']
        st.write(f"**Ingresos**: {d['ingresos']:,.2f} €")
        st.write(f"- Gastos Deducibles: {d['gastos']:,.2f} €")
        st.write(f"- Cuota RETA Anual: {d['reta_anual']:,.2f} €")
        st.write(f"= Rendimiento Neto Previo: {d['rendimiento_neto_previo']:,.2f} €")
        st.write(f"- 7% Gastos Difícil Justificación (Tope 2k): {d['reduccion_7_porciento']:,.2f} €")
        st.markdown(f"**= Base Liquidable IRPF**: `{d['base_imponible']:,.2f} €`")
        st.write(f"  * Cuota Estatal: {d['cuota_estatal']:,.2f} €")
        st.write(f"  * Cuota Autonómica ({region}): {d['cuota_autonomica']:,.2f} €")
        st.markdown(f"**Total IRPF**: `{d['total_irpf']:,.2f} €`")
        st.success(f"**Neto Final**: {res['autonomo']['neto']:,.2f} €")

    with st.expander("Ver detalle: Sociedad Limitada"):
        d = res['sociedad_limitada']['details']
        st.write(f"**Ingresos**: {d['ingresos']:,.2f} €")
        st.write(f"- Gastos Deducibles: {d['gastos']:,.2f} €")
        st.write(f"- SS Societario / Admin: {d['ss_societario']:,.2f} €")
        st.markdown(f"**= Base Imponible IS**: `{d['base_imponible_is']:,.2f} €`")
        st.write(f"  * Tipo IS: {d['tipo_is']*100}%")
        st.markdown(f"**Cuota Impuesto Sociedades**: `{d['cuota_is']:,.2f} €`")
        st.write(f"Beneficio Distribuible: {d['dividendo_bruto']:,.2f} €")
        st.write(f"- Impuesto s/ Dividendos (Ahorro): {d['retencion_dividendo']:,.2f} €")
        st.success(f"**Neto Final (Dividendo + Sueldo)**: {res['sociedad_limitada']['neto']:,.2f} €")

st.markdown("---")
st.caption("Los datos impositivos se cargan desde `tax_data.json`. Las reglas de deducción se cargan desde `rules.json`.")
