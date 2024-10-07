from flask import Flask,render_template,request, jsonify
import xml.etree.ElementTree as ET
import requests
import datetime
import pickle
import xmltodict
from datetime import datetime
from pymap3d import ecef2geodetic
import threading

app = Flask(__name__, static_folder='static', template_folder='templates', static_url_path='/static')
ub=[0,0]
def obtener_ubicacion_iss():
    global ub
    try:
        respuesta = requests.get("https://api.wheretheiss.at/v1/satellites/25544")
        datos = respuesta.json()
        
        if respuesta.status_code == 200 :
            latitud = float(datos['latitude'])
            longitud = float(datos['longitude'])
            ub=[latitud, longitud]
            return [latitud, longitud]
        else:
            # En caso de que la API no devuelva los datos esperados
            return ub  # O cualquier valor predeterminado que prefieras
    except requests.RequestException:
        # En caso de error en la solicitud
        return ub  # O cualquier valor predeterminado que prefieras

ubicaciones=[]

@app.route('/actualizar_ubicacion')
def actualizar_ubicacion():
    global ub
    global ubicaciones
  
    try:
        ubicacion = obtener_ubicacion_iss()
        ub=ubicacion
      
        ubicaciones.append(ubicacion)
    
       
     
        if len(ubicaciones) > 3600:
                # Guardar la lista de ubicaciones en un archivo pickle
                with open('ubicaciones.pickle', 'wb') as archivo:
                    pickle.dump(ubicaciones, archivo)
                
                # Reiniciar la lista y el tiempo de inicio
                ubicaciones = []
              
               
        # Asegurarse de que siempre se devuelva un diccionario
        return ({
            'latitud': ubicacion[0],
            'longitud': ubicacion[1]
        })
    
    except Exception as e:
        # Registrar el error y devolver un diccionario con valores predeterminados
        print(f"Error en actualizar_ubicacion: {str(e)}")
        return jsonify({
            'latitud': ub[0],
            'longitud': ub[1],
            'error': 'Se produjo un error al actualizar la ubicación'
        })

@app.route('/mapa')
def mostrar_mapa():
    global lista
    latitud = None
    longitud = None
    ubicacion = obtener_ubicacion_iss()
    return  render_template('mapa.html', ubicacion=ubicacion,lista=lista)
   

@app.route('/')
def inicio():
    
    return render_template("index.html")


@app.route('/obtener_coordenadas_ciudad', methods=['GET'])
def obtener_coordenadas_ciudad():
    ciudad = request.args.get('buscador')
    lugares = []
    if not ciudad:
        return render_template('/componentes/datos-ciudad.html', ciudades="No se proporcionó ninguna ciudad", latitudes=0, longitudes=0)

    try:
        # Modificamos la URL para buscar lugares en general, no solo ciudades
        url = f"https://nominatim.openstreetmap.org/search?q={ciudad}&format=json"
        respuesta = requests.get(url, headers={'User-Agent': 'MiAplicacion/1.0'})
        datos = respuesta.json()

        if respuesta.status_code == 200 and datos:
           
           
            
            for lugar in datos:
                lugares.append([lugar['display_name'],lugar['lat'],lugar['lon']])
               
            return render_template('/componentes/datos-ciudad.html', ciudades=lugares)
        else:
            lugares.append([f"No se encontraron datos para: {ciudad}","",""])
            return render_template('/componentes/datos-ciudad.html', ciudades=lugares)

    except Exception as e:
        print(f"Error en la búsqueda de coordenadas: {str(e)}")
        lugares.append([f"Error en la búsqueda: {str(e)}","",""])
        return render_template('/componentes/datos-ciudad.html', ciudades=lugares)
pais=""
@app.route('/ciudades', methods=['GET'])
def ciudades():
    global pais
    pais = request.args.get('country')
    if not pais:
        return jsonify({"error": "No se proporcionó un país"}), 400

    url = "https://countriesnow.space/api/v0.1/countries"
    try:
        respuesta = requests.get(url, timeout=10)
        respuesta.raise_for_status()
        datos = respuesta.json()
        
        pais_encontrado = next((item for item in datos['data'] if item['country'].lower() == pais.lower()), None)
        
        if pais_encontrado:
            ciudades = pais_encontrado['cities']
            if isinstance(ciudades, list):
                try:
                    return render_template('/componentes/select-ciudades.html', ciudades=ciudades, pais=pais_encontrado['country'])
                except Exception as e:
                    print(f"Error al renderizar la plantilla: {str(e)}")
                    return jsonify({"error": f"Error al renderizar la plantilla: {str(e)}"}), 500
            else:
                return jsonify({"error": f"Formato de datos inesperado para las ciudades de {pais}"}), 500
        
        return jsonify({"error": f"No se encontró el país: {pais}"}), 404
    
    except requests.Timeout:
        print("La solicitud excedió el tiempo de espera")
        return jsonify({"error": "La solicitud al servidor tardó demasiado"}), 504
    except requests.RequestException as e:
        print(f"Error en la solicitud: {str(e)}")
        return jsonify({"error": f"Error en la solicitud: {str(e)}"}), 500
    except ValueError as e:
        print(f"Error al procesar JSON: {str(e)}")
        return jsonify({"error": "Error al procesar la respuesta del servidor"}), 500
    except Exception as e:
        print(f"Error inesperado: {str(e)}")
        return jsonify({"error": f"Error inesperado: {str(e)}"}), 500

@app.route('/pasos', methods=['GET'])
def pasos():
  global pais
  ciudad = request.args.get('lista-ciudades')
  return render_template('/componentes/pasos.html',pais=pais,ciudad=ciudad)

def descargar_archivo_en_segundo_plano():
    url_archivo = "https://nasa-public-data.s3.amazonaws.com/iss-coords/current/ISS_OEM/ISS.OEM_J2K_EPH.xml"
    nombre_archivo_local = "iis.xml"
    descargar_archivo(url_archivo, nombre_archivo_local)
    procesar_archivo_xml(nombre_archivo_local)

def procesar_archivo_xml(nombre_archivo):
    global lista, latitudes, longitudes
    try:
        with open(nombre_archivo, "r") as file:
            data = xmltodict.parse(file.read())

        state_vectors = data['ndm']['oem']['body']['segment']['data']['stateVector']

        lista = []
        latitudes = []
        longitudes = []

        for vector in state_vectors:
            epoch = vector['EPOCH']
            x = float(vector['X']['#text']) * 1000  # Convertir km a m
            y = float(vector['Y']['#text']) * 1000
            z = float(vector['Z']['#text']) * 1000
            
            fecha, hora = extraer_fecha_hora(epoch)
            lat, lon = cartesian_to_geodetic(x, y, z)
            lista.append([lat, lon])
            latitudes.append(lat)
            longitudes.append(lon)
        
        print(f"Archivo XML procesado: {len(lista)} coordenadas extraídas")
    except Exception as e:
        print(f"Error al procesar el archivo XML: {str(e)}")

def iniciar_descarga_en_segundo_plano():
    hilo_descarga = threading.Thread(target=descargar_archivo_en_segundo_plano)
    hilo_descarga.start()

@app.before_request
def antes_de_cada_solicitud():
    if not hasattr(app, 'descarga_iniciada'):
        iniciar_descarga_en_segundo_plano()
        app.descarga_iniciada = True

def descargar_archivo(url, nombre_archivo):
        try:
            # Realizar la solicitud GET a la URL
            respuesta = requests.get(url)
            
            # Verificar si la solicitud fue exitosa
            respuesta.raise_for_status()
            
            # Guardar el contenido en un archivo local
            with open(nombre_archivo, 'wb') as archivo:
                archivo.write(respuesta.content)
            
         
        except requests.exceptions.RequestException as e:
            print(f"Error al descargar el archivo: {e}")

    # Ejemplo de uso
url_archivo = "https://nasa-public-data.s3.amazonaws.com/iss-coords/current/ISS_OEM/ISS.OEM_J2K_EPH.xml"
nombre_archivo_local = "iis.xml"
descargar_archivo(url_archivo, nombre_archivo_local)


def extraer_fecha_hora(epoch_str):
    dt = datetime.strptime(epoch_str, '%Y-%jT%H:%M:%S.%fZ')
    return dt.strftime('%Y-%m-%d'), dt.strftime('%H:%M:%S')

def cartesian_to_geodetic(x, y, z):
    lat, lon, alt = ecef2geodetic(x, y, z)
    return lat, lon

# Leer y parsear el archivo XML
with open("iis.xml", "r") as file:
    data = xmltodict.parse(file.read())

state_vectors = data['ndm']['oem']['body']['segment']['data']['stateVector']

latitudes = []
longitudes = []
lista=[]
for vector in state_vectors:
    epoch = vector['EPOCH']
    x = float(vector['X']['#text']) * 1000  # Convertir km a m
    y = float(vector['Y']['#text']) * 1000
    z = float(vector['Z']['#text']) * 1000
    
    fecha, hora = extraer_fecha_hora(epoch)
    lat, lon = cartesian_to_geodetic(x, y, z)
    lista.append([lat,lon])
    latitudes.append(lat)
    longitudes.append(lon)
    
   

if __name__ == '__main__':
    app.run()


