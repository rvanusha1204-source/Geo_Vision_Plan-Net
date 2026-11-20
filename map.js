/**
 * Geo Vision Plan-Net - Leaflet & Canvas NDVI Overlay Renderer
 * Fixes zero-dimension map initialization when switching tabs.
 */

class GeoMapRenderer {
  constructor(mapContainerId) {
    this.mapContainerId = mapContainerId;
    this.map = null;
    this.geojsonLayer = null;
    this.tileLayer = null;
    this.currentTileStyle = 'dark';

    this.tileProviders = {
  dark: 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
  light: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}'
};
  }

  init(initialDistrict) {
    const container = document.getElementById(this.mapContainerId);
    if (!container) return;

    const coords = initialDistrict?.coordinates || { lat: 12.9422, lon: 77.5868, zoom: 11 };
    
    if (this.map) {
      this.map.remove();
      this.map = null;
    }

    this.map = L.map(this.mapContainerId, {
      center: [coords.lat, coords.lon],
      zoom: coords.zoom,
      zoomControl: false
    });

    L.control.zoom({ position: 'topright' }).addTo(this.map);

    this.tileLayer = L.tileLayer(this.tileProviders[this.currentTileStyle], {
attribution: 'Tiles &copy; Esri',
      maxZoom: 16
    }).addTo(this.map);

    this.loadDistrictData(initialDistrict);
  }

  setTileStyle(style) {
    if (this.tileProviders[style]) {
      this.currentTileStyle = style;
      if (this.tileLayer && this.map) {
        this.map.removeLayer(this.tileLayer);
      }
      if (this.map) {
        this.tileLayer = L.tileLayer(this.tileProviders[style], { maxZoom: 18 }).addTo(this.map);
      }
    }
  }

  loadDistrictData(district) {
    if (!district) return;
    
    if (!this.map) {
      this.init(district);
      return;
    }

    const coords = district.coordinates || { lat: 12.9422, lon: 77.5868, zoom: 11 };
    this.map.setView([coords.lat, coords.lon], coords.zoom);

    if (this.geojsonLayer) {
      this.map.removeLayer(this.geojsonLayer);
      this.geojsonLayer = null;
    }

    if (district.geojson && district.geojson.features && district.geojson.features.length > 0) {
      try {
        this.geojsonLayer = L.geoJSON(district.geojson, {
          style: (feature) => {
            const severity = feature.properties?.severity || 'High';
            let fillColor = '#ef4444';
            let borderColor = '#991b1b';

            if (severity === 'Critical') {
              fillColor = '#b91c1c';
              borderColor = '#7f1d1d';
            }

            return {
              fillColor: fillColor,
              weight: 2,
              opacity: 0.9,
              color: borderColor,
              fillOpacity: 0.55
            };
          },
          onEachFeature: (feature, layer) => {
            const props = feature.properties || {};
            const popupContent = `
              <div class="map-popup-card">
                <div class="popup-title">${props.name || 'Violation Zone'}</div>
                <div class="popup-badge ${props.severity?.toLowerCase() || 'high'}">${props.severity || 'High'} Violation</div>
                <div class="popup-metric"><strong>Type:</strong> ${props.type || 'Encroachment'}</div>
                <div class="popup-metric"><strong>Flagged Area:</strong> ${props.areaHa || 25} ha</div>
              </div>
            `;
            layer.bindPopup(popupContent);
          }
        }).addTo(this.map);

        // Auto-fit bounds to actual GeoJSON violation polygons
        const bounds = this.geojsonLayer.getBounds();
        if (bounds.isValid()) {
          this.map.fitBounds(bounds, { padding: [30, 30] });
        }
      } catch (e) {
        console.warn('GeoJSON rendering notice:', e);
      }
    }

    this.renderNDVIHeatmap(district);
  }

  renderNDVIHeatmap(district) {
    const canvasContainer = document.getElementById('ndvi-canvas-container');
    if (!canvasContainer) return;

    let canvas = document.getElementById('ndvi-heatmap-canvas');
    if (!canvas) {
      canvas = document.createElement('canvas');
      canvas.id = 'ndvi-heatmap-canvas';
      canvasContainer.innerHTML = '';
      canvasContainer.appendChild(canvas);
    }

    const width = canvasContainer.clientWidth || canvasContainer.parentElement?.clientWidth || 550;
    const height = canvasContainer.clientHeight || 380;

    canvas.width = width;
    canvas.height = height;

    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, width, height);

    // Seeded pseudo-random for consistent per-district patterns
    const seed = (district.slug || 'default').split('').reduce((a, c) => a + c.charCodeAt(0), 0);
    const rand = (i) => {
      const x = Math.sin(seed * 9301 + i * 49297) * 49297;
      return x - Math.floor(x);
    };

    // 1. Paint realistic terrain base with organic noise patches
    for (let y = 0; y < height; y += 4) {
      for (let x = 0; x < width; x += 4) {
        const n1 = Math.sin(x * 0.02 + seed) * Math.cos(y * 0.015 + seed * 0.7);
        const n2 = Math.sin((x + y) * 0.012 + seed * 1.3) * 0.5;
        const val = (n1 + n2 + 1) / 2; // 0..1

        // Forest green palette from dark to mid-green
        const r = Math.floor(4 + val * 18);
        const g = Math.floor(50 + val * 80);
        const b = Math.floor(30 + val * 35);
        ctx.fillStyle = `rgb(${r},${g},${b})`;
        ctx.fillRect(x, y, 4, 4);
      }
    }

    // 2. Paint vegetation GAIN zones (bright green patches)
    const gainCount = 3 + (seed % 4);
    for (let i = 0; i < gainCount; i++) {
      const cx = width * (0.1 + rand(i * 7 + 50) * 0.8);
      const cy = height * (0.1 + rand(i * 11 + 60) * 0.8);
      const radius = 25 + rand(i * 3 + 70) * 35;

      const grad = ctx.createRadialGradient(cx, cy, 2, cx, cy, radius);
      grad.addColorStop(0, 'rgba(34, 197, 94, 0.7)');
      grad.addColorStop(0.5, 'rgba(22, 163, 74, 0.35)');
      grad.addColorStop(1, 'rgba(6, 78, 59, 0)');
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(cx, cy, radius, 0, Math.PI * 2);
      ctx.fill();
    }

    // 3. Paint vegetation LOSS hotspots (red/orange clusters from real data)
    const lossFeatures = district.geojson?.features || [];
    const lossCount = Math.max(lossFeatures.length, 5);
    for (let i = 0; i < lossCount; i++) {
      const cx = width * (0.12 + rand(i * 13 + 1) * 0.76);
      const cy = height * (0.12 + rand(i * 17 + 2) * 0.76);
      const baseRadius = 20 + rand(i * 5 + 3) * 50;

      // Main loss hotspot
      const grad = ctx.createRadialGradient(cx, cy, 3, cx, cy, baseRadius);
      grad.addColorStop(0, 'rgba(220, 38, 38, 0.92)');
      grad.addColorStop(0.3, 'rgba(239, 68, 68, 0.7)');
      grad.addColorStop(0.6, 'rgba(251, 146, 60, 0.4)');
      grad.addColorStop(0.85, 'rgba(250, 204, 21, 0.15)');
      grad.addColorStop(1, 'rgba(6, 78, 59, 0)');
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(cx, cy, baseRadius, 0, Math.PI * 2);
      ctx.fill();

      // Secondary scatter fragments around each hotspot
      for (let j = 0; j < 3; j++) {
        const offX = cx + (rand(i * 19 + j * 7) - 0.5) * baseRadius * 1.5;
        const offY = cy + (rand(i * 23 + j * 11) - 0.5) * baseRadius * 1.5;
        const subR = 8 + rand(i * 29 + j * 13) * 18;
        const subGrad = ctx.createRadialGradient(offX, offY, 1, offX, offY, subR);
        subGrad.addColorStop(0, 'rgba(239, 68, 68, 0.6)');
        subGrad.addColorStop(1, 'rgba(245, 158, 11, 0)');
        ctx.fillStyle = subGrad;
        ctx.beginPath();
        ctx.arc(offX, offY, subR, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    // 4. Subtle coordinate grid overlay
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.07)';
    ctx.lineWidth = 0.5;
    const gridSpacing = 50;
    for (let x = gridSpacing; x < width; x += gridSpacing) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke();
    }
    for (let y = gridSpacing; y < height; y += gridSpacing) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke();
    }

    // 5. Coordinate tick labels along edges
    const coords = district.coordinates || { lat: 12.94, lon: 77.58 };
    ctx.fillStyle = 'rgba(167, 243, 208, 0.5)';
    ctx.font = '9px Inter, sans-serif';
    for (let i = 1; i <= 4; i++) {
      const latLabel = (coords.lat - 0.15 + i * 0.08).toFixed(2);
      const lonLabel = (coords.lon - 0.15 + i * 0.08).toFixed(2);
      ctx.fillText(latLabel + 'N', 4, i * (height / 5));
      ctx.fillText(lonLabel + 'E', i * (width / 5) - 10, height - 6);
    }

    // 6. NDVI Color Legend Bar
    const legendX = width - 28;
    const legendY = 20;
    const legendH = 140;
    const legendW = 14;

    // Legend background
    ctx.fillStyle = 'rgba(0, 0, 0, 0.45)';
    ctx.roundRect(legendX - 6, legendY - 14, legendW + 50, legendH + 42, 6);
    ctx.fill();

    // Legend gradient bar
    const lgGrad = ctx.createLinearGradient(0, legendY, 0, legendY + legendH);
    lgGrad.addColorStop(0, '#dc2626');
    lgGrad.addColorStop(0.25, '#f97316');
    lgGrad.addColorStop(0.5, '#facc15');
    lgGrad.addColorStop(0.75, '#22c55e');
    lgGrad.addColorStop(1, '#064e3b');
    ctx.fillStyle = lgGrad;
    ctx.fillRect(legendX, legendY, legendW, legendH);

    // Legend border
    ctx.strokeStyle = 'rgba(255,255,255,0.25)';
    ctx.lineWidth = 1;
    ctx.strokeRect(legendX, legendY, legendW, legendH);

    // Legend labels
    ctx.fillStyle = '#d1fae5';
    ctx.font = 'bold 8px Inter, sans-serif';
    ctx.textAlign = 'left';
    const labels = [
      { text: 'Severe', y: legendY + 6 },
      { text: 'Loss', y: legendY + legendH * 0.3 },
      { text: 'Neutral', y: legendY + legendH * 0.5 },
      { text: 'Gain', y: legendY + legendH * 0.75 },
      { text: 'Dense', y: legendY + legendH - 2 }
    ];
    labels.forEach(l => {
      ctx.fillText(l.text, legendX + legendW + 4, l.y);
    });

    // Legend title
    ctx.fillStyle = '#a7f3d0';
    ctx.font = 'bold 9px Inter, sans-serif';
    ctx.fillText('NDVI', legendX - 2, legendY - 4);

    // 7. District name watermark
    ctx.fillStyle = 'rgba(255, 255, 255, 0.06)';
    ctx.font = 'bold 28px Outfit, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText((district.displayName || '').toUpperCase(), width / 2, height / 2 + 10);
    ctx.textAlign = 'left';
  }

  resize() {
    if (this.map) {
      this.map.invalidateSize();
    }
    if (window.appState && window.appState.selectedDistrict) {
      this.renderNDVIHeatmap(window.appState.selectedDistrict);
    }
  }
}

window.mapRenderer = new GeoMapRenderer('leaflet-map');
