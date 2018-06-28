# CES22_FlaskProject

Para rodar em localhost ativar as seguinte API's do Google:
  * Geocoding API
  * Distance Matrix API
  * Maps JavaScript API 
  * Directios API
  * Places API

e susbstituir sua chave na linha 19 de index.html


```html
<script defer src="https://maps.googleapis.com/maps/api/js?libraries=places&language=en&key=SUA_CHAVE_API" type="text/javascript"></script>
```
 e também no início de app.py
 ```python
gmaps = googlemaps.Client(key='SUA_CHAVE_API')
app = Flask(__name__, template_folder="templates")
app.config['GOOGLEMAPS_KEY'] = "SUA_CHAVE_API"
app.secret_key = "SUA_CHAVE_API"
GoogleMaps(app, key="SUA_CHAVE_API")
```
