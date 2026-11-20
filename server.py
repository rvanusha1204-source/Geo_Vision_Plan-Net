"""
Geo Vision Plan-Net - ML Backend & UI/UX Integration Server
------------------------------------------------------------
Directly connects your trained ML model cache (CNN Classifier, U-Net Segmentation,
GeoTIFF rasters, and GIS CSV files) to the modern Mobile & Desktop UI/UX PWA.

Run from CMD in your desktop directory:
    cd C:\\Users\\inspi\\OneDrive\\Desktop\\green-cover-dashboar
    python server.py
"""

import os
import io
import json
import pandas as pd
from http.server import SimpleHTTPRequestHandler, HTTPServer
from gtts import gTTS

PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")

class GeoVisionServerHandler(SimpleHTTPRequestHandler):
    """Serves the modern UI/UX frontend and connects real ML backend model outputs."""

    def format_title(self, slug):
        return slug.replace('_', ' ').title()

    def discover_regions(self):
        """Scans cache/ directory for all precomputed ML model regions."""
        regions = []
        if not os.path.isdir(CACHE_DIR):
            return regions

        for folder in sorted(os.listdir(CACHE_DIR)):
            path = os.path.join(CACHE_DIR, folder)
            if not os.path.isdir(path):
                continue

            summary_csv = os.path.join(path, "violation_summary.csv")
            if not os.path.exists(summary_csv):
                continue

            meta_file = os.path.join(path, "metadata.json")
            display_name = self.format_title(folder)
            state = "India"
            lat, lon = 11.6854, 76.1320

            if os.path.exists(meta_file):
                try:
                    with open(meta_file, encoding='utf-8') as f:
                        meta = json.load(f)
                        display_name = meta.get("display_name", display_name)
                        state = meta.get("state", state)
                        lat = float(meta.get("lat", lat))
                        lon = float(meta.get("lon", lon))
                except Exception:
                    pass

            regions.append({
                "slug": folder,
                "displayName": display_name,
                "state": state,
                "coordinates": {"lat": lat, "lon": lon, "zoom": 10}
            })
        return regions

    def load_region_detail(self, slug):
        """Loads violation CSV, trend CSV, and GeoJSON for a specific district."""
        folder = os.path.join(CACHE_DIR, slug)
        if not os.path.exists(folder):
            return None

        display_name = self.format_title(slug)
        state = "India"
        lat, lon = 11.6854, 76.1320
        last_updated = None

        # 1. Load Metadata
        meta_file = os.path.join(folder, "metadata.json")
        if os.path.exists(meta_file):
            try:
                with open(meta_file, encoding='utf-8') as f:
                    meta = json.load(f)
                    display_name = meta.get("display_name", display_name)
                    state = meta.get("state", state)
                    lat = float(meta.get("lat", lat))
                    lon = float(meta.get("lon", lon))
                    last_updated = meta.get("last_updated")
            except Exception:
                pass

        data = {
            "slug": slug,
            "displayName": display_name,
            "state": state,
            "coordinates": {"lat": lat, "lon": lon, "zoom": 11},
            "lastUpdated": last_updated
        }

        # 2. Load Summary CSV
        summary_csv = os.path.join(folder, "violation_summary.csv")
        if os.path.exists(summary_csv):
            try:
                df = pd.read_csv(summary_csv)
                if len(df) > 0:
                    row = df.iloc[0].to_dict()
                    loss_ha = float(row.get('total_veg_loss_ha', 0))
                    gain_ha = float(row.get('total_veg_gain_ha', 0))
                    encroach_ha = float(row.get('protected_area_encroachment_ha', 0))
                    buffer_ha = float(row.get('buffer_zone_violation_ha', 0))
                    severe_ha = float(row.get('severe_loss_ha', 0))
                    flagged_ha = float(row.get('total_flagged_violation_ha', 0))
                    period = str(row.get('study_period', '2017 - 2025'))

                    # Risk Score Calculation based on real flagged violations
                    risk_score = int(min(100, max(20, (flagged_ha / (loss_ha + 1)) * 100 + 40)))

                    data["summary"] = {
                        "totalVegLossHa": round(loss_ha, 1),
                        "totalVegGainHa": round(gain_ha, 1),
                        "protectedAreaEncroachmentHa": round(encroach_ha, 1),
                        "bufferZoneViolationHa": round(buffer_ha, 1),
                        "severeLossHa": round(severe_ha, 1),
                        "totalFlaggedViolationHa": round(flagged_ha, 1),
                        "riskScore": risk_score,
                        "studyPeriod": period
                    }

                    # Dynamic Analytical Executive Summary
                    net_change = gain_ha - loss_ha
                    trend_word = "a net loss" if net_change < 0 else "a net gain"
                    data["executiveSummary"] = (
                        f"Over the study period ({period}), {display_name} experienced "
                        f"{loss_ha:,.1f} hectares of vegetation loss and {gain_ha:,.1f} hectares "
                        f"of vegetation gain, resulting in {trend_word} of {abs(net_change):,.1f} hectares. "
                        f"A total of {flagged_ha:,.1f} hectares were flagged across protected area encroachments "
                        f"({encroach_ha:,.1f} ha) and buffer zone violations ({buffer_ha:,.1f} ha)."
                    )
            except Exception as e:
                print(f"Error reading summary CSV for {slug}: {e}")

        # 3. Load Multi-Year Trend CSV
        trend_csv = os.path.join(folder, "violation_trend.csv")
        trend_list = []
        if os.path.exists(trend_csv):
            try:
                tdf = pd.read_csv(trend_csv)
                for _, trow in tdf.iterrows():
                    trend_list.append({
                        "period": str(trow.get('period_label', f"{trow.get('year_start')}-{trow.get('year_end')}")),
                        "lossHa": round(float(trow.get('total_veg_loss_ha', 0)), 1),
                        "gainHa": round(float(trow.get('total_veg_gain_ha', 0)), 1),
                        "violationsHa": round(float(trow.get('total_flagged_violation_ha', 0)), 1)
                    })
            except Exception as e:
                print(f"Error reading trend CSV for {slug}: {e}")
        data["trend"] = trend_list

        # 4. Load GeoJSON Violation Zones (Cap to 500 features for map performance)
        geojson_path = os.path.join(folder, "violation_zones.geojson")
        if os.path.exists(geojson_path):
            try:
                with open(geojson_path, encoding='utf-8') as f:
                    raw_geojson = json.load(f)
                    features = raw_geojson.get('features', [])
                    
                    # Cap features to top 300 to avoid browser memory overload
                    if len(features) > 300:
                        features = features[:300]
                    
                    data["geojson"] = {
                        "type": "FeatureCollection",
                        "features": features
                    }
            except Exception as e:
                print(f"Error loading GeoJSON for {slug}: {e}")

        return data

    def do_GET(self):
        # API: List all regions discovered in backend cache/
        if self.path == "/api/districts" or self.path == "/api/districts/":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            regions = self.discover_regions()
            self.wfile.write(json.dumps(regions).encode("utf-8"))
            return

        # API: Overall cache freshness (written by build_cache.py every refresh run)
        elif self.path == "/api/last_refresh" or self.path == "/api/last_refresh/":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            refresh_file = os.path.join(CACHE_DIR, "last_refresh.json")
            if os.path.exists(refresh_file):
                with open(refresh_file, encoding='utf-8') as f:
                    self.wfile.write(f.read().encode("utf-8"))
            else:
                self.wfile.write(json.dumps({"status": "never_run"}).encode("utf-8"))
            return

        # API: Get detailed real ML model metrics for specific region
        elif self.path.startswith("/api/district/"):
            slug = self.path.split("/api/district/")[1].strip("/")
            detail = self.load_region_detail(slug)
            self.send_response(200 if detail else 404)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            if detail:
                self.wfile.write(json.dumps(detail).encode("utf-8"))
            else:
                self.wfile.write(json.dumps({"error": f"Region '{slug}' not found"}).encode("utf-8"))
            return

        # Serve UI static files
        return super().do_GET()

    def do_POST(self):
        # API: Text-to-speech for languages the browser has no native voice for
        # (Tamil, Telugu, Malayalam, Kannada). Called by voice-assistant.js.
        if self.path == "/api/tts":
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length) if content_length else b''
                payload = json.loads(body.decode('utf-8')) if body else {}

                text = (payload.get('text') or '').strip()
                lang = (payload.get('lang') or 'en').strip().lower()

                if not text:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "No text provided"}).encode("utf-8"))
                    return

                supported_langs = {'ta': 'ta', 'te': 'te', 'ml': 'ml', 'kn': 'kn', 'hi': 'hi', 'en': 'en'}
                gtts_lang = supported_langs.get(lang, 'en')

                tts = gTTS(text=text, lang=gtts_lang)
                audio_buffer = io.BytesIO()
                tts.write_to_fp(audio_buffer)
                audio_bytes = audio_buffer.getvalue()

                self.send_response(200)
                self.send_header("Content-Type", "audio/mpeg")
                self.send_header("Content-Length", str(len(audio_bytes)))
                self.end_headers()
                self.wfile.write(audio_bytes)
            except Exception as e:
                print(f"TTS generation failed: {e}")
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "TTS generation failed"}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

def main():
    os.chdir(BASE_DIR)
    server = HTTPServer(('', PORT), GeoVisionServerHandler)
    print("============================================================")
    print("  Geo Vision Plan-Net Real ML Model Integration Server")
    print(f"  Serving Real Model Districts on: http://localhost:{PORT}")
    print("============================================================")
    server.serve_forever()

if __name__ == "__main__":
    main()
