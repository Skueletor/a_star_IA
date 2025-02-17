<template>
  <div>
    <div style="text-align: center; margin-top: 10px;">
      <p>
        Haz clic en el mapa para seleccionar el punto de <strong>Inicio</strong> (primer clic)
        y el punto de <strong>Fin</strong> (segundo clic).
      </p>
      <button @click="resetPoints">Resetear Puntos</button>
      <button v-if="start && end" @click="getRoute">Obtener Ruta</button>
    </div>
    <div id="map" style="height: 600px; width: 800px;"></div>
  </div>
</template>

<script>
import L from 'leaflet';
import axios from 'axios';

export default {
  name: 'RouteMap',
  data() {
    return {
      map: null,
      start: null,       // Objeto { lat, lng }
      end: null,         // Objeto { lat, lng }
      startMarker: null,
      endMarker: null,
      routeLayer: null
    }
  },
  mounted() {
    this.map = L.map('map', { zoomAnimation: false }).setView([-17.7833, -63.2000], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: 'Map data © OpenStreetMap contributors'
    }).addTo(this.map);
    
    // Capturamos clics en el mapa para seleccionar los puntos
    this.map.on('click', this.onMapClick);
  },
  methods: {
    onMapClick(e) {
      // Primer clic: punto de inicio
      if (!this.start) {
        this.start = e.latlng;
        this.startMarker = L.marker(e.latlng).addTo(this.map)
          .bindPopup('Inicio').openPopup();
      } 
      // Segundo clic: punto de fin
      else if (!this.end) {
        this.end = e.latlng;
        this.endMarker = L.marker(e.latlng).addTo(this.map)
          .bindPopup('Fin').openPopup();
      } 
      else {
        alert("Ya has seleccionado ambos puntos. Presiona 'Resetear Puntos' para elegir nuevos.");
      }
    },
    resetPoints() {
      this.start = null;
      this.end = null;
      if (this.startMarker) {
        this.map.removeLayer(this.startMarker);
        this.startMarker = null;
      }
      if (this.endMarker) {
        this.map.removeLayer(this.endMarker);
        this.endMarker = null;
      }
      if (this.routeLayer) {
        this.map.removeLayer(this.routeLayer);
        this.routeLayer = null;
      }
    },
    getRoute() {
      if (!this.start || !this.end) {
        alert("Por favor, selecciona ambos puntos antes de obtener la ruta.");
        return;
      }
      //hay que pasar los parámetros en el endpoint de la API
      const url = `http://127.0.0.1:5000/route?algorithm=a_star&start_lat=${this.start.lat}&start_lon=${this.start.lng}&end_lat=${this.end.lat}&end_lon=${this.end.lng}`;
      axios.get(url)
        .then(response => {
          const route = response.data.route;
          // Convertir cada punto: {x, y} donde x = lon y y = lat, a formato [lat, lon]
          const latlngs = route.map(point => [point.y, point.x]);
          
          // Eliminar la ruta anterior si existe
          if (this.routeLayer) {
            this.map.removeLayer(this.routeLayer);
          }
          this.routeLayer = L.polyline(latlngs, {
            color: '#39ff14',  // Verde neón
            weight: 5,
            opacity: 0.8
          }).addTo(this.map);
          
          this.map.invalidateSize();
          setTimeout(() => {
            try {
              this.map.fitBounds(this.routeLayer.getBounds(), { animate: false });
            } catch (err) {
              console.error("Error ajustando el zoom:", err);
            }
          }, 100);
        })
        .catch(error => {
          console.error("Error al obtener la ruta:", error);
        });
    }
  }
}
</script>

<style scoped>
#map {
  border: 2px solid #39ff14;
  margin: auto;
  display: block;
}
button {
  margin: 5px;
  padding: 8px 16px;
  font-size: 1em;
}
</style>
