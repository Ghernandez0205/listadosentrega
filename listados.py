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
    df = pd.read_excel(LOCAL_FILE_PATH, engine="openpyxl")
    df.columns = df.columns.str.strip().str.upper()  # Normalizar nombres de columnas
    st.write("Columnas detectadas en el archivo:", df.columns.tolist())  # Mostrar columnas en Streamlit
    return df

# Guardar el archivo Excel actualizado
def save_data(df):
    df.to_excel(LOCAL_FILE_PATH, index=False, engine="openpyxl")

# Obtener listado de docentes
def get_docentes(df):
    required_columns = ["APELLIDO PATERNO", "APELLIDO MATERNO", "NOMBRE"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error(f"Las siguientes columnas no están en el archivo: {missing_columns}. Verifica la estructura del archivo.")
        st.write("Columnas disponibles en el archivo:", df.columns.tolist())
        return pd.DataFrame()
    return df[required_columns].drop_duplicates()

# Obtener documentos de un docente
def get_documentos(df, docente):
    if "DOCUMENTO" in df.columns:
        return df[df["NOMBRE"] == docente]
    else:
        st.warning("El archivo no contiene la columna 'DOCUMENTO'. Verifica la estructura del archivo.")
        return pd.DataFrame(columns=["DOCUMENTO", "ESTADO"])

# Actualizar estado del documento
def update_document_status(df, docente, documento, estado):
    if "DOCUMENTO" in df.columns and "ESTADO" in df.columns:
        df.loc[(df["NOMBRE"] == docente) & (df["DOCUMENTO"] == documento), "ESTADO"] = estado
        save_data(df)

# Interfaz Streamlit
st.title("Registro de Entrega de Documentación")

df = load_data()

tab1, tab2 = st.tabs(["Registro de Entrega", "Generar Listado"])

with tab1:
    st.header("Actualizar Estado de Documentación")
    docentes = get_docentes(df)
    if not docentes.empty:
        docente_seleccionado = st.selectbox("Selecciona un docente", docentes["NOMBRE"].unique(), key="docente1")
        documentos_df = get_documentos(df, docente_seleccionado)
        
        if not documentos_df.empty:
            for index, row in documentos_df.iterrows():
                nuevo_estado = st.selectbox(f"Estado para {row['DOCUMENTO']}", ["Verde", "Amarillo", "Rojo"], index=["Verde", "Amarillo", "Rojo"].index(row.get('ESTADO', 'Rojo')), key=f"estado_{index}")
                if st.button(f"Actualizar {row['DOCUMENTO']}", key=f"boton_{index}"):
                    update_document_status(df, docente_seleccionado, row['DOCUMENTO'], nuevo_estado)
                    st.success(f"Estado de {row['DOCUMENTO']} actualizado a {nuevo_estado}")
        else:
            st.warning("Este docente no tiene documentos registrados o no hay una columna 'DOCUMENTO' en el archivo.")
    else:
        st.warning("No se encontraron docentes. Verifica la estructura del archivo.")

with tab2:
    st.header("Generar Listado de Documentos Pendientes")
    if not docentes.empty:
        docente_listado = st.selectbox("Selecciona un docente", docentes["NOMBRE"].unique(), key="docente2")
        documento_listado = st.selectbox("Selecciona el documento", ["Horario", "Reanudación", "Ratificación", "CURP", "SAT", "Otros"], key="documento")
        
        if st.button("Generar Listado", key="generar_listado"):
            df_listado = get_documentos(df, docente_listado)
            if "DOCUMENTO" in df_listado.columns:
                df_listado = df_listado[df_listado["DOCUMENTO"] == documento_listado]
                if not df_listado.empty:
                    df_listado.to_excel("listado_pendientes.xlsx", index=False, engine="openpyxl")
                    st.success("Listado generado con éxito. Descárgalo en el siguiente enlace:")
                    st.download_button(label="Descargar Excel", data=open("listado_pendientes.xlsx", "rb").read(), file_name="listado_pendientes.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                else:
                    st.warning("No hay documentos pendientes para este docente.")
            else:
                st.warning("El archivo no contiene la columna 'DOCUMENTO'. Verifica la estructura del archivo.")

