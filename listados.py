import streamlit as st
import sqlite3
import pandas as pd

# Conectar a la base de datos SQLite
def get_connection():
    return sqlite3.connect("plantilla.db", check_same_thread=False)

# Crear la tabla si no existe
def create_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS docentes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        apellido_paterno TEXT,
                        apellido_materno TEXT,
                        nombre TEXT,
                        rfc TEXT,
                        curp TEXT,
                        documento TEXT,
                        estado TEXT)''')
    conn.commit()
    conn.close()

# Obtener listado de docentes
def get_docentes():
    conn = get_connection()
    df = pd.read_sql("SELECT DISTINCT apellido_paterno, apellido_materno, nombre FROM docentes", conn)
    conn.close()
    return df

# Obtener documentos de un docente
def get_documentos(docente):
    conn = get_connection()
    df = pd.read_sql(f"SELECT documento, estado FROM docentes WHERE nombre='{docente}'", conn)
    conn.close()
    return df

# Actualizar estado del documento
def update_document_status(docente, documento, estado):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE docentes SET estado=? WHERE nombre=? AND documento=?", (estado, docente, documento))
    conn.commit()
    conn.close()

# Interfaz Streamlit
st.title("Registro de Entrega de Documentación")
create_table()

tab1, tab2 = st.tabs(["Registro de Entrega", "Generar Listado"])

with tab1:
    st.header("Actualizar Estado de Documentación")
    docentes = get_docentes()
    docente_seleccionado = st.selectbox("Selecciona un docente", docentes["nombre"].unique())
    documentos_df = get_documentos(docente_seleccionado)
    
    for index, row in documentos_df.iterrows():
        nuevo_estado = st.selectbox(f"Estado para {row['documento']}", ["Verde", "Amarillo", "Rojo"], index=["Verde", "Amarillo", "Rojo"].index(row['estado']))
        if st.button(f"Actualizar {row['documento']}"):
            update_document_status(docente_seleccionado, row['documento'], nuevo_estado)
            st.success(f"Estado de {row['documento']} actualizado a {nuevo_estado}")

with tab2:
    st.header("Generar Listado de Documentos Pendientes")
    docente_listado = st.selectbox("Selecciona un docente", docentes["nombre"].unique())
    documento_listado = st.selectbox("Selecciona el documento", ["Horario", "Reanudación", "Ratificación", "CURP", "SAT", "Otros"])
    
    if st.button("Generar Listado"):
        df_listado = get_documentos(docente_listado)
        df_listado = df_listado[df_listado["documento"] == documento_listado]
        df_listado.to_excel("listado_pendientes.xlsx", index=False)
        st.success("Listado generado con éxito. Descárgalo en el siguiente enlace:")
        st.download_button(label="Descargar Excel", data=open("listado_pendientes.xlsx", "rb").read(), file_name="listado_pendientes.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
