from flask import Flask, render_template_string, jsonify
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Retrieve the Google Maps API key from environment variables
google_maps_api_key = os.getenv('GOOGLE_MAPS_KEY')

app = Flask(__name__)

@app.route('/')
def index():
    html_content = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>Draw Polygon</title>
        <script>
          function loadGoogleMapsApi(apiKey) {
            const script = document.createElement('script');
            script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=drawing&callback=initMap`;
            script.async = true;
            script.defer = true;
            document.head.appendChild(script);
          }

          function fetchApiKey() {
            fetch('/get-api-key')
              .then(response => response.json())
              .then(data => {
                loadGoogleMapsApi(data.apiKey);
              })
              .catch(error => console.error('Error fetching API key:', error));
          }

          let map;
          let drawingManager;
          let currentPolygon;

          function initMap() {
            if (navigator.geolocation) {
              navigator.geolocation.getCurrentPosition(
                (position) => {
                  const userLocation = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude,
                  };

                  map = new google.maps.Map(document.getElementById('map'), {
                    center: userLocation,
                    zoom: 12,
                    mapTypeId: 'hybrid',
                  });

                  drawingManager = new google.maps.drawing.DrawingManager({
                    drawingMode: google.maps.drawing.OverlayType.POLYGON,
                    drawingControl: true,
                    drawingControlOptions: {
                      position: google.maps.ControlPosition.TOP_CENTER,
                      drawingModes: ['polygon'],
                    },
                    polygonOptions: {
                      editable: true,
                    },
                  });
                  drawingManager.setMap(map);

                  google.maps.event.addListener(drawingManager, 'overlaycomplete', function (event) {
                    if (event.type == google.maps.drawing.OverlayType.POLYGON) {
                      if (currentPolygon) {
                        currentPolygon.setMap(null);
                      }
                      currentPolygon = event.overlay;
                      const coordinates = event.overlay.getPath().getArray();
                      const geoJson = {
                        type: "Feature",
                        geometry: {
                          type: "Polygon",
                          coordinates: [[]]
                        },
                        properties: {}
                      };
                      coordinates.forEach((coord) => {
                        geoJson.geometry.coordinates[0].push([coord.lng(), coord.lat()]);
                      });
                      // Close the polygon by adding the first coordinate at the end
                      const firstCoord = coordinates[0];
                      geoJson.geometry.coordinates[0].push([firstCoord.lng(), firstCoord.lat()]);
                      const geoJsonString = JSON.stringify(geoJson, null, 2);
                      console.log(geoJsonString);
                      document.getElementById('polygonCoords').value = geoJsonString;

                      const blob = new Blob([geoJsonString], { type: 'application/json' });
                      const url = URL.createObjectURL(blob);
                      const downloadLink = document.getElementById('downloadLink');
                      downloadLink.href = url;
                      downloadLink.download = 'polygon.geojson';
                      downloadLink.style.display = 'block';
                    }
                  });
                },
                () => {
                  handleLocationError(true, map.getCenter());
                }
              );
            } else {
              // Browser doesn't support Geolocation
              handleLocationError(false, map.getCenter());
            }
          }

          function handleLocationError(browserHasGeolocation, pos) {
            console.log(
              browserHasGeolocation
                ? 'Error: The Geolocation service failed.'
                : "Error: Your browser doesn't support geolocation."
            );
            map.setCenter(pos);
          }

          function clearPolygon() {
            if (currentPolygon) {
              currentPolygon.setMap(null);
              currentPolygon = null;
            }
            document.getElementById('polygonCoords').value = '';
            document.getElementById('downloadLink').style.display = 'none';
          }
        </script>
      </head>
      <body onload="fetchApiKey()">
        <div id="map" style="height: 500px; width: 100%;"></div>
        <button onclick="clearPolygon()">Clear Polygon</button>
        <button onclick="document.getElementById('geoJsonContainer').style.display = 'block'">Show GeoJSON</button>
        <pre id="polygonCoords" style="width: 100%; height: 200px; overflow: auto; border: 1px solid black; display: none;"></pre>
        <a id="downloadLink" style="display: none;">Download GeoJSON</a>
        <div id="geoJsonContainer" style="display: none;">
          <button onclick="document.getElementById('geoJsonContainer').style.display = 'none'">Hide GeoJSON</button>
          <pre id="polygonCoordsDisplay" style="width: 100%; height: 200px; overflow: auto; border: 1px solid black;"></pre>
        </div>
      </body>
    </html>
    """
    return render_template_string(html_content)

@app.route('/get-api-key')
def get_api_key():
    return jsonify(apiKey=google_maps_api_key)

if __name__ == '__main__':
    app.run(debug=True)
