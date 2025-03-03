import streamlit as st
import pandas as pd
import os
import requests
import sqlite3

# Verificar que las librerías necesarias estén instaladas
try:
    import openpyxl
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "-r", "requirements.txt"])
    import openpyxl

# URL del archivo en GitHub
GITHUB_FILE_URL = "https://raw.githubusercontent.com/TuUsuario/listadosentrega/main/plantilla1.xlsx"
LOCAL_FILE_PATH = "plantilla1.xlsx"
DB_FILE = "docentes_actualizado.db"

# Descargar el archivo si no existe localmente
def download_file():
    if not os.path.exists(LOCAL_FILE_PATH):
        st.info("Descargando el archivo desde GitHub...")
        response = requests.get(GITHUB_FILE_URL)
        if response.status_code == 200:
            with open(LOCAL_FILE_PATH, "wb") as file:
                file.write(response.content)
            st.success("Archivo descargado exitosamente.")
        else:
            st.error("No se pudo descargar el archivo. Verifica la URL.")

download_file()

# Cargar el archivo Excel
def load_data():
    df = pd.read_excel(LOCAL_FILE_PATH, engine="openpyxl")
    df.columns = df.columns.str.strip().str.upper()
    column_mapping = {"NOMBRE (S)": "NOMBRE"}
    df.rename(columns=column_mapping, inplace=True)
    return df

# Guardar el archivo Excel actualizado
def save_data(df):
    df.to_excel(LOCAL_FILE_PATH, index=False, engine="openpyxl")

# Conectar a SQLite
def connect_db():
    conn = sqlite3.connect(DB_FILE)
    return conn

# Obtener listado de docentes
def get_docentes(df):
    required_columns = ["APELLIDO PATERNO", "APELLIDO MATERNO", "NOMBRE"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error(f"Las siguientes columnas no están en el archivo: {missing_columns}. Verifica la estructura del archivo.")
        return pd.DataFrame()
    return df[required_columns].drop_duplicates()

# Obtener documentos de docentes seleccionados
def get_documentos(df, docentes):
    if "DOCUMENTO" in df.columns:
        return df[df["NOMBRE"].isin(docentes)]
    else:
        st.warning("El archivo no contiene la columna 'DOCUMENTO'. Verifica la estructura del archivo.")
        return pd.DataFrame(columns=["DOCUMENTO", "ESTADO"])

# Actualizar estado del documento
def update_document_status(df, docentes, documento, estado):
    if "DOCUMENTO" in df.columns and "ESTADO" in df.columns:
        df.loc[(df["NOMBRE"].isin(docentes)) & (df["DOCUMENTO"] == documento), "ESTADO"] = estado
        save_data(df)

# Interfaz Streamlit
st.title("Registro de Entrega de Documentación")
df = load_data()

tab1, tab2, tab3 = st.tabs(["Registro de Entrega", "Generar Listado", "Estadísticas"])

with tab1:
    st.header("Actualizar Estado de Documentación")
    docentes = get_docentes(df)
    if not docentes.empty:
        docentes_seleccionados = st.multiselect("Selecciona docentes", docentes["NOMBRE"].unique(), key="docentes")
        documentos_df = get_documentos(df, docentes_seleccionados)
        
        if not documentos_df.empty:
            documento_seleccionado = st.selectbox("Selecciona un documento", documentos_df["DOCUMENTO"].unique())
            nuevo_estado = st.selectbox("Selecciona el nuevo estado", ["Verde", "Amarillo", "Rojo"], key="estado")
            if st.button("Actualizar Estado"):
                update_document_status(df, docentes_seleccionados, documento_seleccionado, nuevo_estado)
                st.success(f"Estado de {documento_seleccionado} actualizado a {nuevo_estado} para los docentes seleccionados.")
        else:
            st.warning("No hay documentos registrados para los docentes seleccionados.")
    else:
        st.warning("No se encontraron docentes en el archivo.")

with tab2:
    st.header("Generar Listado de Documentos Pendientes")
    if not docentes.empty:
        docente_listado = st.multiselect("Selecciona docentes", docentes["NOMBRE"].unique(), key="docentes_listado")
        documento_listado = st.selectbox("Selecciona el documento", ["Horario", "Reanudación", "Ratificación", "CURP", "SAT", "Otros"], key="documento")
        
        if st.button("Generar Listado"):
            df_listado = get_documentos(df, docente_listado)
            if "DOCUMENTO" in df_listado.columns:
                df_listado = df_listado[df_listado["DOCUMENTO"] == documento_listado]
                if not df_listado.empty:
                    df_listado.to_excel("listado_pendientes.xlsx", index=False, engine="openpyxl")
                    st.success("Listado generado con éxito. Descárgalo en el siguiente enlace:")
                    st.download_button(label="Descargar Excel", data=open("listado_pendientes.xlsx", "rb").read(), file_name="listado_pendientes.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                else:
                    st.warning("No hay documentos pendientes para los docentes seleccionados.")
            else:
                st.warning("El archivo no contiene la columna 'DOCUMENTO'. Verifica la estructura del archivo.")

with tab3:
    st.header("Estadísticas de Documentación")
    if "ESTADO" in df.columns:
        st.bar_chart(df["ESTADO"].value_counts())
    else:
        st.warning("No se encontró la columna 'ESTADO'. Verifica la estructura del archivo.")
