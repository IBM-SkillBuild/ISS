from flask import Flask, render_template, request, jsonify
import requests
import xmltodict
from datetime import datetime
from pymap3d import ecef2geodetic

app = Flask(__name__, static_folder='static', template_folder='templates', static_url_path='/static')
ub = [0, 0]

def obtener_ubicacion_iss():
    global ub
    try:
        respuesta = requests.get("https://api.wheretheiss.at/v1/satellites/25544")
        datos = respuesta.json()
        
        if respuesta.status_code == 200:
            latitud = float(datos['latitude'])
            longitud = float(datos['longitude'])
            ub = [latitud, longitud]
            return [latitud, longitud]
        else:
            return ub
    except requests.RequestException:
        return ub

@app.route('/actualizar_ubicacion')
def actualizar_ubicacion():
    try:
        ubicacion = obtener_ubicacion_iss()
        return {
            'latitud': ubicacion[0],
            'longitud': ubicacion[1]
        }
    except Exception as e:
        print(f"Error en actualizar_ubicacion: {str(e)}")
        return jsonify({
            'latitud': ub[0],
            'longitud': ub[1],
            'error': 'Se produjo un error al actualizar la ubicación'
        })

def obtener_y_procesar_datos_xml():
    url_archivo = "https://nasa-public-data.s3.amazonaws.com/iss-coords/current/ISS_OEM/ISS.OEM_J2K_EPH.xml"
    try:
        respuesta = requests.get(url_archivo)
        respuesta.raise_for_status()
        
        data = xmltodict.parse(respuesta.content)
        state_vectors = data['ndm']['oem']['body']['segment']['data']['stateVector']
        
        lista = []
        latitudes = []
        longitudes = []
        
        for vector in state_vectors:
            epoch = vector['EPOCH']
            x = float(vector['X']['#text']) * 1000
            y = float(vector['Y']['#text']) * 1000
            z = float(vector['Z']['#text']) * 1000
            
            fecha, hora = extraer_fecha_hora(epoch)
            lat, lon = cartesian_to_geodetic(x, y, z)
            lista.append([lat, lon])
            latitudes.append(lat)
            longitudes.append(lon)
        
        return lista, latitudes, longitudes
    except requests.RequestException as e:
        print(f"Error al obtener o procesar el archivo XML: {str(e)}")
        return [], [], []

@app.route('/mapa')
def mostrar_mapa():
    ubicacion = obtener_ubicacion_iss()
    lista, latitudes, longitudes = obtener_y_procesar_datos_xml()
    return render_template('mapa.html', ubicacion=ubicacion, lista=lista)

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
        url = f"https://nominatim.openstreetmap.org/search?q={ciudad}&format=json"
        respuesta = requests.get(url, headers={'User-Agent': 'MiAplicacion/1.0'})
        datos = respuesta.json()

        if respuesta.status_code == 200 and datos:
            for lugar in datos:
                lugares.append([lugar['display_name'], lugar['lat'], lugar['lon']])
            return render_template('/componentes/datos-ciudad.html', ciudades=lugares)
        else:
            lugares.append([f"No se encontraron datos para: {ciudad}", "", ""])
            return render_template('/componentes/datos-ciudad.html', ciudades=lugares)

    except Exception as e:
        print(f"Error en la búsqueda de coordenadas: {str(e)}")
        lugares.append([f"Error en la búsqueda: {str(e)}", "", ""])
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

def extraer_fecha_hora(epoch_str):
    dt = datetime.strptime(epoch_str, '%Y-%jT%H:%M:%S.%fZ')
    return dt.strftime('%Y-%m-%d'), dt.strftime('%H:%M:%S')

def cartesian_to_geodetic(x, y, z):
    lat, lon, alt = ecef2geodetic(x, y, z)
    return lat, lon

@app.route('/pasos', methods=['GET'])
def pasos():
  global pais
  ciudad = request.args.get('lista-ciudades')
  return render_template('/componentes/pasos.html',pais=pais,ciudad=ciudad)

if __name__ == '__main__':
    app.run()