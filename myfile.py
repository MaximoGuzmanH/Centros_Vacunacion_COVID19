import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_card import card
import folium
from streamlit_folium import folium_static

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
file_path = './data/TB_CENTRO_VACUNACION.csv'

# Llamar a la función cacheada para cargar y procesar los datos
(df, df_filtered, total_puntos, nulos_latitud, nulos_longitud, 
 ceros_latitud, ceros_longitud, fuera_rango_latitud, fuera_rango_longitud, cantidad_puntos_validos) = load_and_process_data(file_path)

# Mapa general
st.title('Centros de Vacunacion COVID-19')
st.subheader("Mapa de Centros de Vacunación")
st.map(df_filtered[['Latitud', 'Longitud']].rename(columns={'Latitud': 'latitude', 'Longitud': 'longitude'}))
st.dataframe(df_filtered.drop(columns=['ID Centro de Vacunacion', 'Latitud', 'Longitud', 'id_eess']))

# Mostrar los datos con streamlit_card
st.subheader("Análisis de Datos")

# Configurar los cards en dos columnas
col1, col2 = st.columns(2)

with col1:
    card(title=f"{total_puntos}", text="Total de puntos en el DataFrame", key="total_puntos")
    card(title=f"{nulos_latitud}", text="Cantidad de puntos con valores nulos en Latitud", key="nulos_latitud")
    card(title=f"{ceros_latitud}", text="Cantidad de puntos con valores 0 en Latitud", key="ceros_latitud")
    card(title=f"{fuera_rango_latitud}", text="Cantidad de puntos fuera de rango en Latitud", key="fuera_rango_latitud")

with col2:
    card(title=f"{nulos_longitud}", text="Cantidad de puntos con valores nulos en Longitud", key="nulos_longitud")
    card(title=f"{ceros_longitud}", text="Cantidad de puntos con valores 0 en Longitud", key="ceros_longitud")
    card(title=f"{fuera_rango_longitud}", text="Cantidad de puntos fuera de rango en Longitud", key="fuera_rango_longitud")
    card(title=f"{cantidad_puntos_validos}", text="Cantidad de puntos válidos que se muestran en el mapa", key="puntos_validos")


# Gráficos de pastel
st.subheader("Distribución de Centros de Vacunación por Entidad Administradora (Top 4 + Otros)")
entidad_counts = df_filtered['Entidad Administradora'].value_counts()
top_4_entidades = entidad_counts.nlargest(4)
otros = entidad_counts[4:].sum()
entidad_labels = list(top_4_entidades.index) + ['OTROS']
entidad_sizes = list(top_4_entidades.values) + [otros]
fig1 = px.pie(values=entidad_sizes, names=entidad_labels, 
              category_orders={"Entidad Administradora": entidad_labels[:-1] + ["OTROS"]})
st.plotly_chart(fig1)

st.subheader("Distribución de Centros de Vacunación por Departamento (Top 5 + Otros)")
centros_vacunacion_porDept = df_filtered[['Departamento', 'ID Centro de Vacunacion']].copy()
centros_vacunacion_porDept['Cantidad'] = 1
centros_vacunacion_porDept = centros_vacunacion_porDept.groupby('Departamento', as_index=False).sum()
top5_Dept = centros_vacunacion_porDept.nlargest(5, 'Cantidad')
otros_dept_count = centros_vacunacion_porDept['Cantidad'][5:].sum()
dept_data = pd.concat([top5_Dept, pd.DataFrame({'Departamento': ['OTROS'], 'Cantidad': [otros_dept_count]})]) if otros_dept_count > 0 else top5_Dept
fig2 = px.pie(dept_data, values='Cantidad', names='Departamento', 
              category_orders={"Departamento": list(top5_Dept['Departamento']) + (["OTROS"] if otros_dept_count > 0 else [])})
st.plotly_chart(fig2)

st.subheader("Centros de Vacunación por Provincia (Top 5 + Otras)")
departamentos_opciones = sorted(df_filtered['Departamento'].unique())
departamento_seleccionado = st.selectbox('Seleccione un Departamento para ver detalles por Provincia', departamentos_opciones)
centros_por_provincia = df_filtered[df_filtered['Departamento'] == departamento_seleccionado]
provincia_counts = centros_por_provincia['Provincia'].value_counts().reset_index()
provincia_counts.columns = ['Provincia', 'Cantidad']
top5_Prov = provincia_counts.nlargest(5, 'Cantidad')
otros_prov_count = provincia_counts['Cantidad'][5:].sum()
prov_data = pd.concat([top5_Prov, pd.DataFrame({'Provincia': ['OTRAS'], 'Cantidad': [otros_prov_count]})]) if otros_prov_count > 0 else top5_Prov
fig3 = px.pie(prov_data, values='Cantidad', names='Provincia',
              title=f'Centros de Vacunación en {departamento_seleccionado} por Provincia (Top 5 + Otras)',
              category_orders={"Provincia": list(top5_Prov['Provincia']) + (["OTRAS"] if otros_prov_count > 0 else [])})
st.plotly_chart(fig3)

# Filtrado por Ubicación con Mapa y Tabla
st.subheader("Filtrar Centros de Vacunación por Ubicación")
departamentos = sorted(df_filtered['Departamento'].unique())
departamento_seleccionado_mapa = st.selectbox("Seleccione un Departamento", options=departamentos, key="dep_map")
provincias = sorted(df_filtered[df_filtered['Departamento'] == departamento_seleccionado_mapa]['Provincia'].unique())
provincia_seleccionada_mapa = st.selectbox("Seleccione una Provincia", options=provincias, key="prov_map")
distritos = sorted(df_filtered[(df_filtered['Departamento'] == departamento_seleccionado_mapa) & 
                               (df_filtered['Provincia'] == provincia_seleccionada_mapa)]['Distrito'].unique())
distrito_seleccionado_mapa = st.selectbox("Seleccione un Distrito", options=distritos, key="dist_map")

df_filtrado_ubicacion = df_filtered[(df_filtered['Departamento'] == departamento_seleccionado_mapa) & 
                                    (df_filtered['Provincia'] == provincia_seleccionada_mapa) & 
                                    (df_filtered['Distrito'] == distrito_seleccionado_mapa)]

st.map(df_filtrado_ubicacion[['Latitud', 'Longitud']].rename(columns={'Latitud': 'latitude', 'Longitud': 'longitude'}))

# Mostrar la tabla de datos filtrados con las mismas columnas que la primera tabla
st.subheader("Datos Filtrados por Ubicación")
st.dataframe(df_filtrado_ubicacion.drop(columns=['ID Centro de Vacunacion', 'Latitud', 'Longitud', 'id_eess']))

# Choropleth Map para la clasificación por entidad administrativa
st.subheader('Centros de Vacunación por Entidad Administradora')

# Cargar el archivo GeoJSON de los departamentos de Perú
json_peru_dept = './data/peru_departamental_simple.geojson'  # Asegúrate de que este archivo esté en el mismo directorio
map_center = [-12.0464, -77.0428]

# Seleccionar la entidad administrativa para el choropleth
entidades_opciones = list(entidad_labels) + ['Sin Identificar']
entidad_seleccionada_choropleth = st.selectbox('Elija la entidad que desee visualizar', entidades_opciones)

# Preparar datos para el choropleth
centros_vacunacion_porDept_Choropleth = df_filtered.copy()
centros_vacunacion_porDept_Choropleth['Entidad Administradora'] = centros_vacunacion_porDept_Choropleth['Entidad Administradora'].fillna('Sin Identificar')
centros_vacunacion_porDept_Choropleth.loc[~centros_vacunacion_porDept_Choropleth['Entidad Administradora'].isin(top_4_entidades.index.tolist() + ['Sin Identificar']), 'Entidad Administradora'] = 'OTROS'

# Filtrar los datos según la entidad seleccionada
df_choropleth_filtered = centros_vacunacion_porDept_Choropleth[centros_vacunacion_porDept_Choropleth['Entidad Administradora'] == entidad_seleccionada_choropleth]
df_choropleth_grouped = df_choropleth_filtered.groupby('Departamento').size().reset_index(name='Cantidad')

# Crear el mapa de folium
mapa_peru_chor = folium.Map(location=map_center, tiles='CartoDB positron', name='Light Map', zoom_start=5)

# Crear el choropleth
cplth_centros_por_dept = folium.Choropleth(
    geo_data=json_peru_dept,
    data=df_choropleth_grouped,
    columns=['Departamento', 'Cantidad'],
    key_on='feature.properties.NOMBDEP',
    fill_color='YlGnBu',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Cantidad de Centros de Vacunación por Entidad'
).add_to(mapa_peru_chor)

# Crear un diccionario para mapear departamento con cantidad
cantidad_por_departamento = dict(zip(df_choropleth_grouped['Departamento'], df_choropleth_grouped['Cantidad']))

# Añadir tooltip para cada departamento
for feature in cplth_centros_por_dept.geojson.data['features']:
    departamento = feature['properties']['NOMBDEP']
    cantidad = cantidad_por_departamento.get(departamento, 0)  # Obtener cantidad de centros
    feature['properties']['tooltip'] = f'Departamento: {departamento}<br>Cantidad de Centros: {cantidad}'

folium.GeoJsonTooltip(
    fields=['tooltip'],
    aliases=[''],
    sticky=True
).add_to(cplth_centros_por_dept.geojson)

# Mostrar el mapa en Streamlit
folium_static(mapa_peru_chor)
