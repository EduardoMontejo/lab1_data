# app.py
import json
import pandas as pd
import streamlit as st

st.set_page_config(page_title="DataMorph JSON", layout="wide")
st.title("DataMorph JSON")

st.caption("Pega una **lista de objetos JSON** (array) y conviértela en una tabla con `pd.json_normalize`.")

# JSON de ejemplo: 3 personas con campos diferentes
example_json = [
    {
        "id": 1,
        "name": "Ana",
        "age": 29,
        "city": "Madrid",
        "contacts": {"email": "ana@example.com"},
        "skills": ["Python", "SQL"]
    },
    {
        "id": 2,
        "name": "Bruno",
        "country": "Germany",
        "is_active": True,
        "contacts": {"phone": "+49-111-222"},
        "projects": [{"name": "ETL", "status": "done"}, {"name": "Dashboard", "status": "wip"}]
    },
    {
        "id": 3,
        "name": "Carla",
        "age": 41,
        "city": "Zurich",
        "department": {"name": "Data", "level": "Senior"},
        "preferences": {"newsletter": False}
    }
]

# Layout en 2 columnas
left, right = st.columns(2, gap="large")

with left:
    st.subheader("1) Input JSON")
    st.write("Debe ser un **array** JSON: `[{...}, {...}, {...}]`")

    # Botón para cargar ejemplo
    if st.button("Cargar ejemplo"):
        st.session_state["json_input"] = json.dumps(example_json, indent=2, ensure_ascii=False)

    json_text = st.text_area(
        "Pega aquí tu JSON",
        height=420,
        key="json_input",
        placeholder='Ejemplo:\n[\n  {"id": 1, "name": "Ana"},\n  {"id": 2, "name": "Bruno"}\n]'
    )

with right:
    st.subheader("2) Tabla normalizada")
    if not json_text.strip():
        st.info("Pega un JSON válido en la izquierda (o pulsa **Cargar ejemplo**).")
    else:
        try:
            data = json.loads(json_text)

            if not isinstance(data, list):
                st.error("El JSON debe ser una **lista de objetos** (array). Ej: `[{...}, {...}]`")
            elif len(data) == 0:
                st.warning("La lista está vacía. Agrega al menos un objeto.")
            else:
                # Normalización principal
                df = pd.json_normalize(data, sep=".")

                # Opcional: convertir listas/dicts a texto para mostrar mejor en tabla
                def to_displayable(x):
                    if isinstance(x, (list, dict)):
                        return json.dumps(x, ensure_ascii=False)
                    return x

                df = df.applymap(to_displayable)

                st.dataframe(df, use_container_width=True)
                st.caption(f"Filas: {df.shape[0]} | Columnas: {df.shape[1]}")

                # Opcional: descarga a CSV
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("Descargar CSV", csv, file_name="datamorph.json_normalized.csv", mime="text/csv")

        except json.JSONDecodeError as e:
            st.error(f"JSON inválido: {e}")
        except Exception as e:
            st.error(f"Error procesando el JSON: {e}")

