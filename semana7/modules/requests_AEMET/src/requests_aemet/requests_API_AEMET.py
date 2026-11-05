import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("AEMET_API_KEY")

url_inventario = "https://opendata.aemet.es/opendata/api/valores/climatologicos/inventarioestaciones/todasestaciones"

response_inventario = requests.get(url_inventario, params={"api_key": API_KEY})
response_inventario.raise_for_status()
url_datos_inventario = response_inventario.json()["datos"]

response_datos = requests.get(url_datos_inventario, params={"api_key": API_KEY})
response_datos.raise_for_status()

indicativo = ""
for dato in response_datos.json():
    if(dato["nombre"] == "MADRID, CIUDAD UNIVERSITARIA"):
        indicativo = dato["indicativo"]
        break

if indicativo == "":
    raise ValueError("No se ha encontrado la estación")

fecha_inicio = "2019-10-01T00:00:00UTC"
fecha_fin = "2019-10-30T23:59:59UTC"

response_diarios = requests.get("https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/datos/fechaini"
                        f"/{fecha_inicio}/fechafin/{fecha_fin}/estacion/{indicativo}", params={"api_key": API_KEY})
response_diarios.raise_for_status()

url_datos_finales = response_diarios.json()["datos"]

response_final = requests.get(url_datos_finales, params={"api_key": API_KEY})
response_final.raise_for_status()

print(response_final.json())