import streamlit as st
import pandas as pd

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

    # Aplicar el filtro de coordenadas para el área de Perú
    df_filtered = df[(df['Latitud'] >= -18) & (df['Latitud'] <= -0.1) & 
                     (df['Longitud'] >= -81) & (df['Longitud'] <= -68)]

    # Eliminar cualquier valor nulo en las coordenadas y renombrar columnas para st.map
    map_data = df_filtered[['Latitud', 'Longitud']].dropna()
    map_data = map_data.rename(columns={'Latitud': 'latitude', 'Longitud': 'longitude'})
    
    return df_filtered, map_data

# Definir la ruta del archivo
file_path = 'data/TB_CENTRO_VACUNACION.csv'

# Llamar a la función cacheada para cargar y procesar los datos
df_filtered, map_data = load_and_process_data(file_path)

# Título de la aplicación
st.title('Centros de Vacunacion COVID-19')
st.subheader("Mapa de Centros de Vacunación")

# Mostrar la cantidad de puntos en el mapa
st.write(f"Cantidad de puntos que se muestran en el mapa: {len(map_data)}")

# Mostrar el mapa usando st.map
st.map(map_data)

# Mostrar la tabla de datos en Streamlit con los nombres de columnas actualizados
st.dataframe(df_filtered)
