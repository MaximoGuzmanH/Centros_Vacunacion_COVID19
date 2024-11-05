import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

@st.cache_resource
def load_and_process_data(file_path):
    # Cargar el archivo CSV
    df = pd.read_csv(file_path, encoding='latin1')

    # Verificar que las columnas 'latitud' y 'longitud' existan antes de renombrarlas
    if 'latitud' in df.columns and 'longitud' in df.columns:
        df = df.rename(columns={'latitud': 'latitude', 'longitud': 'longitude'})

    # Renombrar columnas para mostrarlas en la tabla con los nombres especificados
    df = df.rename(columns={
        'id_centro_vacunacion': 'ID Centro de Vacunacion', 
        'id_ubigeo': 'ID Ubigeo',
        'nombre': 'Nombre',
        'latitude': 'Latitud',
        'longitude': 'Longitud',
        'entidad_administra': 'Entidad Administradora',
        'departamento': 'Departamento',
        'provincia': 'Provincia',
        'distrito': 'Distrito'
    })

    # Obtener el total de puntos inicial
    total_puntos = len(df)

    # Contar los valores nulos y ceros en las columnas Latitud y Longitud
    nulos_latitud = df['Latitud'].isnull().sum()
    nulos_longitud = df['Longitud'].isnull().sum()
    ceros_latitud = (df['Latitud'] == 0).sum()
    ceros_longitud = (df['Longitud'] == 0).sum()

    # Contar los puntos fuera del rango de Perú (pero que no son nulos ni cero)
    fuera_rango_latitud = ((df['Latitud'] < -18) | (df['Latitud'] > -0.1)).sum()
    fuera_rango_longitud = ((df['Longitud'] < -81) | (df['Longitud'] > -68)).sum()
    
    # Filtrar puntos válidos (en el área de Perú, sin valores 0 ni nulos)
    df_filtered = df[(df['Latitud'] >= -18) & (df['Latitud'] <= -0.1) & 
                     (df['Longitud'] >= -81) & (df['Longitud'] <= -68) &
                     (df['Latitud'] != 0) & (df['Longitud'] != 0) &
                     df['Latitud'].notnull() & df['Longitud'].notnull()]

    # Obtener la cantidad final de puntos válidos
    cantidad_puntos_validos = len(df_filtered)

    return (df, df_filtered, total_puntos, nulos_latitud, nulos_longitud, 
            ceros_latitud, ceros_longitud, fuera_rango_latitud, fuera_rango_longitud, cantidad_puntos_validos)

# Definir la ruta del archivo
file_path = 'data/TB_CENTRO_VACUNACION.csv'

# Llamar a la función cacheada para cargar y procesar los datos
(df, df_filtered, total_puntos, nulos_latitud, nulos_longitud, 
 ceros_latitud, ceros_longitud, fuera_rango_latitud, fuera_rango_longitud, cantidad_puntos_validos) = load_and_process_data(file_path)

# Título de la aplicación
st.title('Centros de Vacunacion COVID-19')
st.subheader("Mapa de Centros de Vacunación")

# Mostrar el análisis de datos
st.write(f"Total de puntos en el DataFrame: {total_puntos}")
st.write(f"Cantidad de puntos con valores nulos en Latitud: {nulos_latitud}")
st.write(f"Cantidad de puntos con valores nulos en Longitud: {nulos_longitud}")
st.write(f"Cantidad de puntos con valores 0 en Latitud: {ceros_latitud}")
st.write(f"Cantidad de puntos con valores 0 en Longitud: {ceros_longitud}")
st.write(f"Cantidad de puntos fuera de rango en Latitud: {fuera_rango_latitud}")
st.write(f"Cantidad de puntos fuera de rango en Longitud: {fuera_rango_longitud}")
st.write(f"Cantidad de puntos válidos que se muestran en el mapa: {cantidad_puntos_validos}")

# Mostrar el mapa usando st.map
st.map(df_filtered[['Latitud', 'Longitud']].rename(columns={'Latitud': 'latitude', 'Longitud': 'longitude'}))

# Mostrar la tabla de datos en Streamlit excluyendo ciertas columnas
st.dataframe(df_filtered.drop(columns=['ID Centro de Vacunacion', 'Latitud', 'Longitud', 'id_eess']))

# Gráfico de pastel para la distribución de centros por entidad administradora (Top 4 + Otros)
st.subheader("Distribución de Centros de Vacunación por Entidad Administradora (Top 4 + Otros)")

# Calcular la cantidad de centros por entidad administradora
entidad_counts = df_filtered['Entidad Administradora'].value_counts()
top_4_entidades = entidad_counts.nlargest(4)
otros = entidad_counts[4:].sum()
entidad_labels = list(top_4_entidades.index) + ['Otros']
entidad_sizes = list(top_4_entidades.values) + [otros]

# Crear el gráfico de pastel
fig, ax = plt.subplots()
ax.pie(entidad_sizes, labels=entidad_labels, autopct='%1.1f%%', startangle=90,
       pctdistance=0.85, labeldistance=1.1, colors=plt.cm.Paired.colors)
ax.axis('equal')  # Asegura que el gráfico sea circular
plt.tight_layout()
st.pyplot(fig)

# Gráfico de pastel para la distribución de centros por departamento (Top 5 + Otros)
st.subheader("Distribución de Centros de Vacunación por Departamento (Top 5 + Otros)")

centros_vacunacion_porDept = df_filtered[['Departamento', 'ID Centro de Vacunacion']].copy()
centros_vacunacion_porDept['cant_centros'] = 1
centros_vacunacion_porDept = centros_vacunacion_porDept.groupby('Departamento', as_index=False).sum()
centros_vacunacion_porDept = centros_vacunacion_porDept.sort_values('cant_centros', ascending=False).reset_index(drop=True)

top5_Dept_porCantCentros = centros_vacunacion_porDept[:5]
otros_Dept_porCantCentros = pd.DataFrame(
    [['OTROS', centros_vacunacion_porDept['cant_centros'][5:].sum()]],
    columns=['Departamento', 'cant_centros']
)
centros_vacunacion_porDept_top5_y_otros = pd.concat([top5_Dept_porCantCentros, otros_Dept_porCantCentros])

piec_centros_porDept = px.pie(
    centros_vacunacion_porDept_top5_y_otros,
    values='cant_centros', names='Departamento',
    title='Centros por Departamento',
    category_orders={"Departamento": ["OTROS"] + list(top5_Dept_porCantCentros['Departamento'][::-1])}
)
st.plotly_chart(piec_centros_porDept)

# Selección de Departamento y gráfico de centros por provincia
st.subheader("Distribución de Centros de Vacunación por Provincia en Departamento Seleccionado")

departamentos_opciones = df_filtered['Departamento'].unique()
departamento_seleccionado = st.selectbox('Elija el departamento del cual desee mayor detalle', departamentos_opciones)

centros_por_provincia = df_filtered[df_filtered['Departamento'] == departamento_seleccionado][['Provincia', 'ID Centro de Vacunacion']].copy()
centros_por_provincia['cant_centros'] = 1
centros_por_provincia = centros_por_provincia.groupby('Provincia', as_index=False).sum()
centros_por_provincia = centros_por_provincia.sort_values('cant_centros', ascending=False).reset_index(drop=True)

top5_Prov_porCantCentros = centros_por_provincia[:5]
otras_Prov_porCantCentros = pd.DataFrame(
    [['OTRAS', centros_por_provincia['cant_centros'][5:].sum()]],
    columns=['Provincia', 'cant_centros']
)
centros_vacunacion_porProv_top5_y_otras = pd.concat([top5_Prov_porCantCentros, otras_Prov_porCantCentros])

piec_centros_porProv = px.pie(
    centros_vacunacion_porProv_top5_y_otras,
    values='cant_centros', names='Provincia',
    title='Centros por Provincia',
    category_orders={"Provincia": ["OTRAS"] + list(top5_Prov_porCantCentros['Provincia'][::-1])}
)
st.plotly_chart(piec_centros_porProv)
