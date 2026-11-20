/**
 * Geo Vision Plan-Net - District Dataset
 * Contains precomputed GIS metrics, GeoJSON violation polygons, multi-year trends,
 * and AI analytical summaries for offline/instant execution across mobile & system views.
 */

const DISTRICT_DATA = [
  {
    slug: "wayanad",
    displayName: "Wayanad District",
    state: "Kerala",
    coordinates: { lat: 11.6854, lon: 76.1320, zoom: 11 },
    summary: {
      totalVegLossHa: 412.5,
      totalVegGainHa: 128.2,
      protectedAreaEncroachmentHa: 184.6,
      bufferZoneViolationHa: 142.3,
      severeLossHa: 85.6,
      totalFlaggedViolationHa: 326.9,
      riskScore: 84,
      studyPeriod: "2023 - 2026 (Sentinel-2 & Landsat Analysis)"
    },
    executiveSummary: "Wayanad has experienced severe canopy fragmentation along the forest fringe borders near Meppadi and Vythiri. Protected elephant corridors show critical buffer zone encroachment totaling 184.6 hectares. Immediate enforcement against unpermitted resort clearing is recommended.",
    multiLangSummaries: {
      "en": "Wayanad has experienced 412.5 hectares of vegetation loss, with 184.6 hectares of protected area encroachment. Risk level is Critical.",
      "hi": "वायनाड में 412.5 हेक्टेयर वनस्पति हानि दर्ज की गई है, जिसमें 184.6 हेक्टेयर संरक्षित क्षेत्र का अतिक्रमण शामिल है। जोखिम स्तर गंभीर है।",
      "ta": "வயநாட்டில் 412.5 ஹெக்டேர் காடழிப்பு பதிவாகியுள்ளது, இதில் 184.6 ஹெக்டேர் பாதுகாக்கப்பட்ட மண்டல ஆக்கிரமிப்பாகும். அபாய நிலை அதிகம்.",
      "te": "వాయనాడ్‌లో 412.5 హెక్టార్ల వృక్షసంపద నష్టం నమోదైంది. ఇందులో 184.6 హెక్టార్లు రక్షిత ప్రాంత ఆక్రమణ. ప్రమాద తీవ్రత ఎక్కువగా ఉంది.",
      "ml": "വയനാട്ടിൽ 412.5 ഹെക്ടർ വനനഷ്ടം രേഖപ്പെടുത്തി. 184.6 ഹെക്ടർ സംരക്ഷിത മേഖല കൈയേറ്റമാണ്.",
      "es": "Wayanad ha experimentado 412,5 hectáreas de pérdida de vegetación, con 184,6 hectáreas de invasión de áreas protegidas. Nivel de riesgo Crítico.",
      "fr": "Wayanad a subi 412,5 hectares de perte de végétation, avec 184,6 hectares d'empiétement sur zone protégée. Risque Critique.",
      "de": "Wayanad verzeichnete 412,5 Hektar Vegetationsverlust, davon 184,6 Hektar im Schutzgebiet. Risikostufe Kritisch."
    },
    trend: [
      { period: "2022-2023", lossHa: 180.2, gainHa: 145.0, violationsHa: 110.5 },
      { period: "2023-2024", lossHa: 260.4, gainHa: 138.1, violationsHa: 195.2 },
      { period: "2024-2025", lossHa: 345.8, gainHa: 130.5, violationsHa: 270.4 },
      { period: "2025-2026", lossHa: 412.5, gainHa: 128.2, violationsHa: 326.9 }
    ],
    recommendations: [
      "Deploy drone surveillance teams along the Meppadi eco-sensitive corridor.",
      "Issue stop-work notices for illegal hill cutting in Vythiri sub-division.",
      "Initiate native reforestation along 128 hectares of degraded riparian buffers."
    ],
    geojson: {
      type: "FeatureCollection",
      features: [
        {
          type: "Feature",
          properties: { id: "WYN-V01", name: "Vythiri Hill Clearing", type: "Resort Encroachment", areaHa: 68.4, severity: "High" },
          geometry: {
            type: "Polygon",
            coordinates: [[[76.10, 11.65], [76.13, 11.65], [76.13, 11.67], [76.10, 11.67], [76.10, 11.65]]]
          }
        },
        {
          type: "Feature",
          properties: { id: "WYN-V02", name: "Meppadi Elephant Corridor Encroachment", type: "Buffer Violation", areaHa: 116.2, severity: "Critical" },
          geometry: {
            type: "Polygon",
            coordinates: [[[76.14, 11.68], [76.18, 11.68], [76.17, 11.72], [76.14, 11.71], [76.14, 11.68]]]
          }
        }
      ]
    }
  },
  {
    slug: "idukki",
    displayName: "Idukki High Ranges",
    state: "Kerala",
    coordinates: { lat: 9.8497, lon: 76.9810, zoom: 11 },
    summary: {
      totalVegLossHa: 524.8,
      totalVegGainHa: 95.4,
      protectedAreaEncroachmentHa: 268.2,
      bufferZoneViolationHa: 198.5,
      severeLossHa: 142.1,
      totalFlaggedViolationHa: 466.7,
      riskScore: 92,
      studyPeriod: "2023 - 2026 (Sentinel-2 High Resolution)"
    },
    executiveSummary: "Idukki shows accelerating slopeside forest clearance in Cardamom Hill Reserves (CHR). Unregulated agricultural expansion into reserve boundaries poses extreme landslide vulnerabilities.",
    multiLangSummaries: {
      "en": "Idukki has 524.8 hectares of forest loss and 268.2 hectares of sanctuary encroachment. Risk level is Extremely High.",
      "hi": "इडुक्की में 524.8 हेक्टेयर वन हानि और 268.2 हेक्टेयर अभयारण्य अतिक्रमण है। जोखिम स्तर अत्यंत उच्च है।",
      "ta": "இடுக்கியில் 524.8 ஹெக்டேர் வனம் இழப்பு ஏற்பட்டுள்ளது. 268.2 ஹெக்டேர் பாதுகாக்கப்பட்ட பகுதி ஆக்கிரமிப்பு.",
      "te": "ఇడుక్కిలో 524.8 హెక్టార్ల అటవీ నష్టం మరియు 268.2 హెక్టార్ల ఆక్రమణ జరిగింది. ప్రమాదం అత్యంత తీవ్రంగా ఉంది.",
      "ml": "ഇടുക്കിയിൽ 524.8 ഹെക്ടർ വനനഷ്ടവും 268.2 ഹെക്ടർ കൈയേറ്റവും സ്ഥിരീകരിച്ചു.",
      "es": "Idukki registra 524.8 hectáreas de pérdida forestal y 268.2 hectáreas de invasión.",
      "fr": "Idukki enregistre 524,8 hectares de perte forestière et 268,2 hectares d'empiétement.",
      "de": "Idukki verzeichnet 524,8 Hektar Waldverlust und 268,2 Hektar Schutzgebietsverletzung."
    },
    trend: [
      { period: "2022-2023", lossHa: 210.0, gainHa: 110.0, violationsHa: 160.0 },
      { period: "2023-2024", lossHa: 320.5, gainHa: 104.2, violationsHa: 250.8 },
      { period: "2024-2025", lossHa: 440.0, gainHa: 98.0, violationsHa: 380.0 },
      { period: "2025-2026", lossHa: 524.8, gainHa: 95.4, violationsHa: 466.7 }
    ],
    recommendations: [
      "Mandate slope-stability checks for all ongoing construction in Munnar.",
      "Freeze new commercial clearings in Cardamom Hill Reserve zones.",
      "Implement satellite geo-fencing for real-time alert notifications."
    ],
    geojson: {
      type: "FeatureCollection",
      features: [
        {
          type: "Feature",
          properties: { id: "IDK-V01", name: "CHR Cardamom Encroachment", type: "Reserve Encroachment", areaHa: 154.2, severity: "Critical" },
          geometry: {
            type: "Polygon",
            coordinates: [[[76.94, 9.82], [76.99, 9.82], [76.99, 9.86], [76.94, 9.86], [76.94, 9.82]]]
          }
        }
      ]
    }
  }
];

function getAllDistricts() {
  return DISTRICT_DATA;
}

function getDistrictBySlug(slug) {
  return DISTRICT_DATA.find(d => d.slug === slug) || DISTRICT_DATA[0];
}

function getDistrictsByState(state) {
  if (!state || state === "All") return DISTRICT_DATA;
  return DISTRICT_DATA.filter(d => d.state === state);
}
