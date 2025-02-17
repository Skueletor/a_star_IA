<template>
  <div id="map" class="map">
    <!-- Controles flotantes dentro del mapa -->
    <div class="controls" @click.stop>
      <p class="instructions">
        Selecciona el punto de <strong>Inicio</strong> (primer clic) y el de <strong>Fin</strong> (segundo clic).
      </p>
      <div class="buttons">
        <button @click.stop="resetPoints">Resetear</button>
        <button v-if="start && end" @click.stop="getRoute">Ejecutar</button>
      </div>
    </div>
  </div>
</template>

<script>
import L from 'leaflet'
import { urls } from '@/services/apis.js'
import axios from '@/services/axios.js'
import 'leaflet/dist/leaflet.css'

export default {
  name: 'RouteMap',
  data() {
    return {
      map: null,
      start: null,        // Objeto { lat, lng }
      end: null,          // Objeto { lat, lng }
      startMarker: null,
      endMarker: null,
      visitedLayer: null, // Capa para los bordes explorados
      optimalLayer: null, // Capa para el camino óptimo
      animationTimeout: null // Para limpiar cualquier timeout en resetPoints
    }
  },
  mounted() {
    // Crear el mapa ocupando toda la pantalla, ocultando controles de zoom
    this.map = L.map('map', { zoomAnimation: false, zoomControl: false }).setView([-17.7833, -63.2000], 13)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: 'Hecho por <a href="http://wa.me/59171018245" target="_blank">Juan Luis</a> y <a href="http://wa.me/59170977927" target="_blank">Richard Semizo</a>',
    }).addTo(this.map)
    // Escuchar clics en el mapa para definir puntos
    this.map.on('click', this.onMapClick)
  },
  beforeUnmount() {
    // Cancelar cualquier timeout pendiente
    if (this.animationTimeout) {
      clearTimeout(this.animationTimeout)
      this.animationTimeout = null
    }
  },
  methods: {
    onMapClick(e) {
      // Si ya existen ambos puntos, no se asigna nada
      if (this.start && this.end) return

      if (!this.start) {
        // Primer clic => punto de inicio
        this.start = e.latlng
        this.startMarker = L.circleMarker(e.latlng, {
          radius: 10,
          fillColor: '#37FF8B',
          color: '#37FF8B',
          weight: 1,
          opacity: 1,
          fillOpacity: 1,
          className: 'neon-marker'
        })
          .addTo(this.map)
          .bindPopup('Inicio')
          .openPopup()
      } else if (!this.end) {
        // Segundo clic => punto de fin
        this.end = e.latlng
        this.endMarker = L.circleMarker(e.latlng, {
          radius: 10,
          fillColor: '#37FF8B',
          color: '#37FF8B',
          weight: 1,
          opacity: 1,
          fillOpacity: 1,
          className: 'neon-marker'
        })
          .addTo(this.map)
          .bindPopup('Fin')
          .openPopup()
      }
    },
    resetPoints() {
      // Cancelar cualquier timeout en curso
      if (this.animationTimeout) {
        clearTimeout(this.animationTimeout)
        this.animationTimeout = null
      }
      // Limpiar puntos, marcadores y capas
      this.start = null
      this.end = null
      if (this.startMarker) {
        this.map.removeLayer(this.startMarker)
        this.startMarker = null
      }
      if (this.endMarker) {
        this.map.removeLayer(this.endMarker)
        this.endMarker = null
      }
      if (this.visitedLayer) {
        this.map.removeLayer(this.visitedLayer)
        this.visitedLayer = null
      }
      if (this.optimalLayer) {
        this.map.removeLayer(this.optimalLayer)
        this.optimalLayer = null
      }
    },
    getRoute() {
      if (!this.start || !this.end) return
      const url = `${urls.route}?start_lat=${this.start.lat}&start_lon=${this.start.lng}&end_lat=${this.end.lat}&end_lon=${this.end.lng}`
      axios.get(url)
        .then(response => {
          const { optimal, visited } = response.data
          const optimalLatLngs = optimal.map(pt => [pt.y, pt.x])
          const visitedEdgesLatLng = visited.map(edge => [
            [edge.from.y, edge.from.x],
            [edge.to.y, edge.to.x]
          ])
          this.animateVisitedEdges(visitedEdgesLatLng, optimalLatLngs)
        })
        .catch(error => {
          console.error("Error al obtener la ruta:", error)
        })
    },
    animateVisitedEdges(visitedEdges, optimalLatLngs) {
      if (!this.map) return

      if (this.visitedLayer) {
        this.map.removeLayer(this.visitedLayer)
      }
      this.visitedLayer = L.layerGroup().addTo(this.map)
      
      let index = 0
      const delayVisited = 5  // Delay para los bordes visitados (5 ms)
      const delayOptimal = 10 // Delay antes de dibujar la ruta óptima (10 ms)

      const drawNextEdge = () => {
        if (!this.map || !this.visitedLayer) return

        if (index < visitedEdges.length) {
          L.polyline(visitedEdges[index], {
            color: '#37FF8B',
            weight: 2,
            opacity: 0.2
          }).addTo(this.visitedLayer)
          index++
          this.animationTimeout = setTimeout(drawNextEdge, delayVisited)
        } else {
          this.animationTimeout = setTimeout(() => {
            if (!this.map) return
            if (this.optimalLayer) {
              this.map.removeLayer(this.optimalLayer)
            }
            this.optimalLayer = L.polyline(optimalLatLngs, {
              color: '#37FF8B',
              weight: 4,
              opacity: 1,
              className: 'neon-line'
            }).addTo(this.map)
            const bounds = this.optimalLayer.getBounds()
            this.map.invalidateSize()
            this.map.flyToBounds(bounds, {
              animate: true,
              duration: 3,
              easeLinearity: 0.1
            })
          }, delayOptimal)
        }
      }
      drawNextEdge()
    }
  }
}
</script>

<style scoped>
/* Mapa a pantalla completa */
.map {
  position: relative;
  width: 100vw;
  height: 100vh;
  background-color: #000;
}

/* Ocultar controles de zoom que trae Leaflet */
.leaflet-control-zoom {
  display: none;
}

/* Controles flotantes en la parte inferior izquierda (desktop) */
.controls {
  position: absolute;
  z-index: 1000;
  bottom: 20px;
  left: 20px;
  background: #000;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.3);
  pointer-events: auto;
}

/* Instrucciones y botones */
.instructions {
  font-family: 'Roboto', sans-serif;
  font-size: 14px;
  margin-bottom: 10px;
  color: #37FF8B;
}

.buttons {
  display: flex;
  gap: 8px;
}

.buttons button,
.controls button {
  font-family: 'Roboto', sans-serif;
  font-size: 14px;
  background-color: #0d0d0d;
  border: 1px solid #37FF8B;
  color: #37FF8B;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s ease, color 0.3s ease;
}

.buttons button:hover,
.controls button:hover {
  background-color: #37FF8B;
  color: #0d0d0d;
}

/* --- Efecto "neón" --- */
.neon-line {
  filter: drop-shadow(0 0 6px #37FF8B);
}
.neon-marker {
  filter: drop-shadow(0 0 4px #37FF8B);
}

/* Estilos responsivos */
@media (max-width: 600px) {
  .controls {
    top: 10px;
    bottom: auto;
    left: 10px;
    padding: 10px;
  }
  .instructions {
    font-size: 12px;
  }
  .buttons button,
  .controls button {
    font-size: 12px;
    padding: 6px 10px;
  }
}
</style>
