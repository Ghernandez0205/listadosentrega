import streamlit as st
import pandas as pd
import sqlite3
import os

# Archivo de la base de datos
DB_FILE = "docentes_actualizado.db"

# Conectar a SQLite
def connect_db():
    conn = sqlite3.connect(DB_FILE)
    return conn

# Cargar datos desde la base de datos
def load_data():
    conn = connect_db()
    query = "SELECT * FROM docentes"
    df = pd.read_sql(query, conn)
    conn.close()
    df.columns = df.columns.str.strip().str.upper()
    column_mapping = {"NOMBRE (S)": "NOMBRE"}
    df.rename(columns=column_mapping, inplace=True)
    return df

# Obtener listado de docentes
def get_docentes(df):
    required_columns = ["APELLIDO PATERNO", "APELLIDO MATERNO", "NOMBRE"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error(f"Las siguientes columnas no están en la base de datos: {missing_columns}. Verifica la estructura.")
        return pd.DataFrame()
    return df[required_columns].drop_duplicates()

# Obtener documentos asignados a docentes
def get_documentos():
    documentos = ["Horario", "Reanudación", "Ratificación", "CURP", "SAT", "Talon de pago", "Otros"]
    return documentos

# Guardar estado de documentos en SQLite
def update_document_status(docente, documento, estado):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO estado_documentos (nombre, documento, estado)
        VALUES (?, ?, ?) ON CONFLICT(nombre, documento) DO UPDATE SET estado=excluded.estado
    """, (docente, documento, estado))
    conn.commit()
    conn.close()

# Interfaz Streamlit
st.title("Registro de Entrega de Documentación")
df = load_data()

tab1, tab2, tab3 = st.tabs(["Registro de Entrega", "Generar Listado", "Estadísticas"])

with tab1:
    st.header("Actualizar Estado de Documentación")
    docentes = get_docentes(df)
    if not docentes.empty:
        docentes_seleccionados = st.multiselect("Selecciona docentes", docentes["NOMBRE"].unique())
        documentos = get_documentos()
        if docentes_seleccionados:
            st.write("### Estado de Documentación")
            estados = ["Rojo (No Entregado)", "Amarillo (En Proceso)", "Verde (Entregado)"]
            for docente in docentes_seleccionados:
                st.subheader(docente)
                for doc in documentos:
                    estado = st.selectbox(f"Estado de {doc} para {docente}", estados, key=f"{docente}_{doc}")
                    if st.button(f"Actualizar {doc} de {docente}", key=f"btn_{docente}_{doc}"):
                        update_document_status(docente, doc, estado)
                        st.success(f"Estado actualizado para {docente} - {doc}: {estado}")
    else:
        st.warning("No se encontraron docentes en la base de datos.")

with tab2:
    st.header("Generar Listado de Documentos Pendientes")
    if not docentes.empty:
        docente_listado = st.multiselect("Selecciona docentes", docentes["NOMBRE"].unique())
        documento_listado = st.selectbox("Selecciona el documento", get_documentos())
        if st.button("Generar Listado"):
            listado_df = pd.DataFrame({"Docente": docente_listado, "Documento": documento_listado})
            listado_df.to_excel("listado_pendientes.xlsx", index=False)
            st.success("Listado generado. Descárgalo aquí:")
            st.download_button("Descargar Excel", data=open("listado_pendientes.xlsx", "rb").read(), file_name="listado_pendientes.xlsx")
    else:
        st.warning("No se encontraron docentes en la base de datos.")

with tab3:
    st.header("Estadísticas de Documentación")
    conn = connect_db()
    estado_df = pd.read_sql("SELECT estado, COUNT(*) as cantidad FROM estado_documentos GROUP BY estado", conn)
    conn.close()
    if not estado_df.empty:
        st.bar_chart(estado_df.set_index("estado"))
    else:
        st.warning("No hay registros de estado de documentos aún.")
