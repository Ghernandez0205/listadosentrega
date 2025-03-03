import streamlit as st
import pandas as pd
import sqlite3
import os

def connect_db():
    """ Conectar con la base de datos y obtener la lista de docentes. """
    conn = sqlite3.connect("database.db")
    query = "SELECT apellido_paterno, apellido_materno, nombres FROM docentes"
    df = pd.read_sql(query, conn)
    conn.close()
    df["Nombre Completo"] = df["apellido_paterno"] + " " + df["apellido_materno"] + " " + df["nombres"]
    return df[["Nombre Completo"]]

# Cargar datos iniciales
docentes_df = connect_db()

documentos = ["Horario", "Reanudación", "Hoja de Datos", "Ratificación", "SAT", "CURP", "INE", "Talón de Pago", "Otros"]

# Crear DataFrame para estados de documentos
def crear_df_estado():
    estado_df = docentes_df.copy()
    for doc in documentos[:4]:  # Solo los 4 principales en seguimiento
        estado_df[doc] = "Rojo"  # Estado inicial: No entregado
    return estado_df

df_estado = crear_df_estado()

st.title("📄 Registro de Entrega de Documentación")

tab1, tab2 = st.tabs(["📌 Seguimiento de Documentos", "📋 Generar Listado"])

# Tab 1: Seguimiento de Documentos
with tab1:
    st.header("Seguimiento de Entrega de Documentos")
    st.write("Haz clic en las celdas para cambiar el estado de entrega")
    
    estados_colores = {"Rojo": "🔴 No entregado", "Amarillo": "🟡 En proceso", "Verde": "🟢 Entregado"}
    for doc in documentos[:4]:
        df_estado[doc] = df_estado[doc].apply(lambda x: st.selectbox(f"{doc} para {df_estado['Nombre Completo']}", estados_colores.keys(), index=list(estados_colores.keys()).index(x)))
    
    if st.button("💾 Guardar Cambios"):
        df_estado.to_excel("estado_documentos.xlsx", index=False)
        st.success("Estados actualizados y guardados en Excel")
        st.download_button("📥 Descargar Excel", data=open("estado_documentos.xlsx", "rb").read(), file_name="estado_documentos.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Tab 2: Generador de Listados
with tab2:
    st.header("Generar Listado de Documentos a Entregar")
    seleccionados = st.multiselect("Selecciona docentes", docentes_df["Nombre Completo"].tolist())
    documento_seleccionado = st.selectbox("Selecciona el documento a entregar", documentos)
    
    if st.button("📋 Generar Listado"):
        df_listado = pd.DataFrame({"Nombre Completo": seleccionados, "Documento a Entregar": documento_seleccionado})
        df_listado.to_excel("listado_entrega.xlsx", index=False)
        st.success("Listado generado con éxito.")
        st.download_button("📥 Descargar Listado", data=open("listado_entrega.xlsx", "rb").read(), file_name="listado_entrega.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
