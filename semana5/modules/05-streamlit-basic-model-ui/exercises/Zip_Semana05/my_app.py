
import streamlit as st
from model import predict

st.set_page_config(page_title="Churn de clientes", page_icon="📊")
st.title("Predicción de abandono de clientes")
st.caption("Ejemplo docente: el resultado es orientativo, no una probabilidad real.")

with st.form("churn_form"):
    col1, col2 = st.columns(2)

    with col1:
        tenure = st.number_input(
            "Antigüedad (meses)", min_value=0, max_value=120, value=2, step=1
        )
        spend = st.number_input(
            "Gasto mensual (€)", min_value=0.0, max_value=300.0, value=95.0, step=1.0
        )

    with col2:
        calls = st.number_input(
            "Llamadas a soporte", min_value=0, max_value=20, value=4, step=1
        )
        annual = st.checkbox("Contrato anual", value=False)

    submitted = st.form_submit_button("Calcular riesgo")

if submitted:
    try:
        result = predict(
            tenure_months=tenure,
            monthly_spend_eur=spend,
            support_calls=calls,
            has_annual_contract=annual,
        )
    except ValueError as error:
        st.error(f"No se ha podido calcular el riesgo: {error}")
    else:
        if result["will_churn"]:
            st.warning(result["label"])
        else:
            st.success(result["label"])

        st.metric("Score de riesgo (0 a 1)", f"{result['risk_score']:.2f}")
        st.progress(result["risk_score"])

        with st.expander("Ver explicación del resultado"):
            st.write(result["explanation"])
else:
    st.info("Introduce los datos y pulsa «Calcular riesgo».")
