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
            # 1) Parseo robusto del JSON
            try:
                data = json.loads(json_text)
            except json.JSONDecodeError as e:
                st.error(
                    "❌ No pude leer el JSON. Revisa comillas, comas y corchetes.\n\n"
                    "Formato esperado (lista/array):\n"
                    "`[{\"id\": 1, \"name\": \"Ana\"}, {\"id\": 2, \"name\": \"Bruno\"}]`\n\n"
                    f"Detalle técnico: {e}"
                )
                st.stop()

            # 2) Validaciones de tipo/estructura
            if not isinstance(data, list):
                st.error(
                    "❌ El JSON debe ser una **lista de objetos** (array).\n\n"
                    "Ejemplo válido:\n"
                    "`[{\"id\": 1, \"name\": \"Ana\"}, {\"id\": 2, \"name\": \"Bruno\"}]`"
                )
                st.stop()

            if len(data) == 0:
                st.warning("La lista está vacía. Agrega al menos un objeto JSON.")
                st.stop()

            # (Opcional) Validar que cada elemento sea un dict
            non_dicts = [i for i, x in enumerate(data) if not isinstance(x, dict)]
            if non_dicts:
                st.error(
                    "❌ Todos los elementos dentro de la lista deben ser **objetos JSON** (diccionarios).\n"
                    f"Elementos problemáticos (índices): {non_dicts}"
                )
                st.stop()

            # 3) Normalización
            df_raw = pd.json_normalize(data, sep=".")

            # --- Análisis de esquema / nulos (ANTES de convertir listas/dicts a string) ---
            detected_columns = df_raw.columns.tolist()
            total_nulls = int(df_raw.isna().sum().sum())

            # 4) Mejor display en tabla: convertir listas/dicts a texto (para que no se “rompa” la vista)
            def to_displayable(x):
                if isinstance(x, (list, dict)):
                    return json.dumps(x, ensure_ascii=False)
                return x

            df = df_raw.applymap(to_displayable)

            # 5) Render tabla
            st.dataframe(df, use_container_width=True)
            st.caption(f"Filas: {df.shape[0]} | Columnas: {df.shape[1]}")

            # 6) Descarga CSV (opcional)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Descargar CSV",
                csv,
                file_name="datamorph.json_normalized.csv",
                mime="text/csv"
            )

            # 7) Sección de análisis automático del esquema
            st.divider()
            st.subheader("3) Análisis automático del esquema")
            st.markdown("**Columnas detectadas:**")
            st.write(detected_columns)

            st.markdown(f"**Valores nulos (NaN) totales:** `{total_nulls}`")

            if total_nulls > 0:
                st.warning(
                    "Se detectaron valores nulos (NaN). En un modelo relacional (SQL), "
                    "muchas columnas con NULL pueden ser **ineficientes** (esquemas rígidos, "
                    "más checks/joins y datos con muchos huecos). En cambio, en NoSQL es común "
                    "tener datos **dispersos (Sparse Data)**: documentos con campos opcionales, "
                    "y eso es normal."
                )
            else:
                st.success("No se detectaron valores nulos. El esquema está completo para este conjunto de registros.")

            # 8) Expansor final: explicación SQL vs NoSQL
            st.divider()
            with st.expander("📌 Esquema Fijo (SQL) vs Esquema Flexible (NoSQL)", expanded=False):
                st.markdown(
                    """
                    **Esquema Fijo (SQL / Relacional)**  
                    - Defines tablas con columnas y tipos (ej.: `clientes(id INT, email VARCHAR, ...)`).  
                    - Los datos deben ajustarse a esa estructura (si falta un campo, suele ser `NULL`).  
                    - Ventajas: integridad, constraints, joins potentes, consistencia y analítica estructurada.  
                    - Coste: cambiar el esquema puede implicar migraciones; muchos `NULL` pueden indicar un modelo poco natural.

                    **Esquema Flexible (NoSQL / Documentos)**  
                    - No obliga a que todos los documentos tengan los mismos campos.  
                    - Es común que unos registros tengan `phone` y otros `email` sin “rellenar” columnas.  
                    - Ventajas: evolución rápida del modelo, datos semi-estructurados, evita tablas con muchos huecos.  
                    - Coste: validación e integridad suelen moverse a la aplicación; consultas complejas pueden ser distintas a SQL.

                    **Idea clave:**  
                    - Si tu dataset tiene campos muy variables, NoSQL suele encajar mejor (sparse data).  
                    - Si necesitas relaciones fuertes, reglas e integridad, SQL suele ser mejor.
                    """
                )

        except Exception as e:
            # Catch-all: evita que la app se caiga ante cualquier caso inesperado
            st.error(
                "⚠️ Ocurrió un error inesperado procesando los datos. "
                "Verifica que el JSON sea una lista de objetos y que los campos tengan formatos coherentes."
            )
            st.caption(f"Detalle técnico: {e}")
