import streamlit as st
import pandas as pd
import os
import requests

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

# Verificar y descargar el archivo
st.info("Verificando archivo...")
download_file()

# Cargar el archivo Excel
def load_data():
    return pd.read_excel(LOCAL_FILE_PATH, engine="openpyxl")

# Guardar el archivo Excel actualizado
def save_data(df):
    df.to_excel(LOCAL_FILE_PATH, index=False, engine="openpyxl")

# Obtener listado de docentes
def get_docentes(df):
    return df[["APELLIDO PATERNO", "APELLIDO MATERNO", "NOMBRE"]].drop_duplicates()

# Obtener documentos de un docente
def get_documentos(df, docente):
    return df[df["NOMBRE"] == docente]

# Actualizar estado del documento
def update_document_status(df, docente, documento, estado):
    df.loc[(df["NOMBRE"] == docente) & (df["DOCUMENTO"] == documento), "ESTADO"] = estado
    save_data(df)

# Interfaz Streamlit
st.title("Registro de Entrega de Documentación")

df = load_data()

tab1, tab2 = st.tabs(["Registro de Entrega", "Generar Listado"])

with tab1:
    st.header("Actualizar Estado de Documentación")
    docentes = get_docentes(df)
    docente_seleccionado = st.selectbox("Selecciona un docente", docentes["NOMBRE"].unique())
    documentos_df = get_documentos(df, docente_seleccionado)
    
    if not documentos_df.empty:
        for index, row in documentos_df.iterrows():
            nuevo_estado = st.selectbox(f"Estado para {row['DOCUMENTO']}", ["Verde", "Amarillo", "Rojo"], index=["Verde", "Amarillo", "Rojo"].index(row.get('ESTADO', 'Rojo')))
            if st.button(f"Actualizar {row['DOCUMENTO']}"):
                update_document_status(df, docente_seleccionado, row['DOCUMENTO'], nuevo_estado)
                st.success(f"Estado de {row['DOCUMENTO']} actualizado a {nuevo_estado}")
    else:
        st.warning("Este docente no tiene documentos registrados.")

with tab2:
    st.header("Generar Listado de Documentos Pendientes")
    docente_listado = st.selectbox("Selecciona un docente", docentes["NOMBRE"].unique())
    documento_listado = st.selectbox("Selecciona el documento", ["Horario", "Reanudación", "Ratificación", "CURP", "SAT", "Otros"])
    
    if st.button("Generar Listado"):
        df_listado = get_documentos(df, docente_listado)
        df_listado = df_listado[df_listado["DOCUMENTO"] == documento_listado]
        if not df_listado.empty:
            df_listado.to_excel("listado_pendientes.xlsx", index=False, engine="openpyxl")
            st.success("Listado generado con éxito. Descárgalo en el siguiente enlace:")
            st.download_button(label="Descargar Excel", data=open("listado_pendientes.xlsx", "rb").read(), file_name="listado_pendientes.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.warning("No hay documentos pendientes para este docente.")
