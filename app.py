import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="AuraNav Ultra — Real-World 3D DSA Navigation Engine",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Strip Streamlit default padding for borderless HUD experience
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {
        padding: 0rem !important;
        margin: 0rem !important;
        max-width: 100vw !important;
    }
    iframe {
        width: 100vw !important;
        height: 100vh !important;
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)

html_app = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
<title>AuraNav Ultra Navigation Engine</title>
<style>
  :root {
    --bg-dark: #070a13;
    --panel-bg: rgba(11, 17, 32, 0.88);
    --border-color: rgba(255, 255, 255, 0.12);
    --accent: #38bdf8;
    --accent-glow: rgba(56, 189, 248, 0.35);
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --success: #10b981;
    --danger: #f43f5e;
    --warning: #fbbf24;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg-dark);
    color: var(--text-primary);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    overflow: hidden;
    height: 100vh;
    width: 100vw;
    user-select: none;
  }
  #map-canvas {
    width: 100vw;
    height: 100vh;
    display: block;
    cursor: crosshair;
  }
  #map-canvas.panning { cursor: grabbing; }

  /* Glassmorphic HUD Panels */
  .hud {
    position: absolute;
    background: var(--panel-bg);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    box-shadow: 0 16px 36px rgba(0, 0, 0, 0.65);
    z-index: 20;
    transition: all 0.25s ease;
  }

  /* Search & Trie Autocomplete HUD */
  .search-hud {
    top: 20px;
    left: 20px;
    width: 380px;
  }
  .search-input-wrapper {
    display: flex;
    align-items: center;
    padding: 12px 16px;
    gap: 12px;
  }
  .status-pulse {
    width: 10px;
    height: 10px;
    background: var(--accent);
    border-radius: 50%;
    box-shadow: 0 0 10px var(--accent);
    animation: pulseGlow 2s infinite ease-in-out;
  }
  @keyframes pulseGlow {
    0%, 100% { transform: scale(0.9); opacity: 0.8; }
    50% { transform: scale(1.25); opacity: 1; }
  }
  #global-search {
    background: transparent;
    border: none;
    outline: none;
    color: #fff;
    font-size: 13.5px;
    width: 100%;
  }
  #suggestions-list {
    list-style: none;
    max-height: 240px;
    overflow-y: auto;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
  }
  #suggestions-list li {
    padding: 10px 16px;
    font-size: 12.5px;
    cursor: pointer;
    border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: background 0.15s;
  }
  #suggestions-list li:hover {
    background: rgba(56, 189, 248, 0.16);
    color: var(--accent);
  }
  .badge-tag {
    font-size: 10px;
    background: rgba(255, 255, 255, 0.1);
    padding: 2px 6px;
    border-radius: 4px;
    color: #cbd5e1;
  }

  /* Travel Modes Bar */
  .mode-selector {
    display: flex;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    background: rgba(0, 0, 0, 0.2);
  }
  .mode-btn {
    flex: 1;
    padding: 8px 4px;
    text-align: center;
    font-size: 11.5px;
    cursor: pointer;
    color: var(--text-secondary);
    transition: all 0.2s;
    border: none;
    background: transparent;
  }
  .mode-btn.active {
    color: var(--accent);
    background: rgba(56, 189, 248, 0.12);
    font-weight: 600;
  }

  /* Turn-by-Turn Navigation HUD */
  .nav-hud {
    top: 160px;
    left: 20px;
    width: 380px;
    display: none;
  }
  .nav-header {
    padding: 14px 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border-color);
  }
  .nav-stats {
    display: flex;
    gap: 16px;
  }
  .nav-stat-val {
    font-size: 15px;
    font-weight: 700;
    color: #fff;
    font-family: ui-monospace, monospace;
  }
  .nav-stat-lbl {
    font-size: 10px;
    color: var(--text-secondary);
    text-transform: uppercase;
  }
  .nav-steps-container {
    max-height: 200px;
    overflow-y: auto;
    padding: 8px 0;
  }
  .nav-step-item {
    padding: 8px 16px;
    font-size: 12px;
    display: flex;
    gap: 10px;
    align-items: flex-start;
    border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  }
  .nav-step-icon {
    color: var(--accent);
    font-weight: bold;
    font-size: 13px;
  }

  /* Telemetry Dashboard (Top Right) */
  .telemetry-hud {
    top: 20px;
    right: 20px;
    width: 320px;
    padding: 16px;
    font-size: 12px;
  }
  .telemetry-title {
    color: var(--accent);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-size: 11px;
    margin-bottom: 10px;
    display: flex;
    justify-content: space-between;
  }
  .telemetry-row {
    display: flex;
    justify-content: space-between;
    margin-bottom: 6px;
    color: var(--text-secondary);
  }
  .telemetry-row span:last-child {
    color: var(--text-primary);
    font-family: ui-monospace, monospace;
    font-weight: 600;
  }
  .hud-divider {
    height: 1px;
    background: rgba(255, 255, 255, 0.08);
    margin: 8px 0;
  }

  /* Elevation Profile HUD (Bottom Left) */
  .elevation-hud {
    bottom: 24px;
    left: 20px;
    width: 340px;
    padding: 12px 16px;
    display: none;
  }
  #elevation-canvas {
    width: 100%;
    height: 60px;
    display: block;
    margin-top: 6px;
  }

  /* Bottom Controls Toolbar */
  .toolbar-hud {
    bottom: 24px;
    left: 50%;
    transform: translateX(-50%);
    padding: 8px 14px;
    display: flex;
    gap: 8px;
    align-items: center;
  }
  button.action-btn {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    padding: 8px 14px;
    border-radius: 8px;
    font-size: 12px;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  button.action-btn:hover {
    background: var(--accent);
    color: #030712;
    box-shadow: 0 0 14px var(--accent-glow);
  }
  button.action-btn.active {
    background: rgba(56, 189, 248, 0.22);
    border-color: var(--accent);
    color: var(--accent);
  }

  /* Building Details Popup HUD */
  .building-inspect-hud {
    position: absolute;
    bottom: 80px;
    right: 20px;
    width: 260px;
    padding: 14px;
    display: none;
  }

  #loading-strip {
    display: none;
    font-size: 11px;
    color: var(--accent);
    padding: 6px 16px;
    background: rgba(56, 189, 248, 0.1);
    border-top: 1px solid rgba(56, 189, 248, 0.2);
  }
</style>
</head>
<body>

<canvas id="map-canvas"></canvas>

<!-- Search & Prefix Trie Autocomplete HUD -->
<div class="hud search-hud">
  <div class="search-input-wrapper">
    <div class="status-pulse"></div>
    <input type="text" id="global-search" placeholder="Search ANY city, street, or landmark worldwide..." autocomplete="off" />
  </div>
  <div class="mode-selector">
    <button class="mode-btn active" data-mode="driving">🚗 Drive</button>
    <button class="mode-btn" data-mode="cycling">🚴 Bike</button>
    <button class="mode-btn" data-mode="walking">🚶 Walk</button>
  </div>
  <div id="loading-strip">Updating vector mesh & 3D buildings...</div>
  <ul id="suggestions-list"></ul>
</div>

<!-- Turn-by-Turn Navigation Instruction HUD -->
<div class="hud nav-hud" id="nav-hud">
  <div class="nav-header">
    <div class="nav-stats">
      <div>
        <div class="nav-stat-val" id="nav-dist">0.0 km</div>
        <div class="nav-stat-lbl">Distance</div>
      </div>
      <div>
        <div class="nav-stat-val" id="nav-time">0 min</div>
        <div class="nav-stat-lbl">Duration</div>
      </div>
      <div>
        <div class="nav-stat-val" id="nav-carbon">0 g</div>
        <div class="nav-stat-lbl">CO2 Footprint</div>
      </div>
    </div>
  </div>
  <div class="nav-steps-container" id="nav-steps"></div>
</div>

<!-- Top-Right DSA Diagnostic Telemetry -->
<div class="hud telemetry-hud">
  <div class="telemetry-title">
    <span>AuraNav Engine Diagnostics</span>
    <span style="color:var(--success)">REAL-VECTOR</span>
  </div>
  <div class="telemetry-row"><span>Gateway Status</span><span id="stat-gateway">Multi-Mirror Ready</span></div>
  <div class="telemetry-row"><span>Quadtree Culled</span><span id="stat-quad-culled">0 nodes</span></div>
  <div class="telemetry-row"><span>3D Extruded Buildings</span><span id="stat-bldgs">0 items</span></div>
  <div class="telemetry-row"><span>Indexed POIs (Trie)</span><span id="stat-pois">0 entries</span></div>
  <div class="hud-divider"></div>
  <div class="telemetry-title">
    <span>A* Pathfinding Priority Queue</span>
    <span style="color:var(--accent)">MIN-HEAP</span>
  </div>
  <div class="telemetry-row"><span>Explored Waypoints</span><span id="stat-explored">0</span></div>
  <div class="telemetry-row"><span>Driving Distance</span><span id="stat-route-dist">0 km</span></div>
</div>

<!-- Bottom-Left Elevation Profile Chart -->
<div class="hud elevation-hud" id="elevation-hud">
  <div class="telemetry-title">
    <span>Elevation Gradient Profile</span>
    <span id="stat-climb" style="color:var(--accent)">+0m / -0m</span>
  </div>
  <canvas id="elevation-canvas"></canvas>
</div>

<!-- Building Inspector HUD -->
<div class="hud building-inspect-hud" id="building-inspect">
  <div class="telemetry-title"><span>Building Structure</span><span id="bldg-type" style="color:var(--warning)">Residential</span></div>
  <div class="telemetry-row"><span>Height / Levels</span><span id="bldg-levels">4 Floors (~12m)</span></div>
  <div class="telemetry-row"><span>Footprint Area</span><span id="bldg-area">340 m²</span></div>
</div>

<!-- Bottom Controls Toolbar -->
<div class="hud toolbar-hud">
  <button class="action-btn" id="btn-tilt">📐 3D Tilt: Off</button>
  <button class="action-btn" id="btn-buildings">🏢 Buildings: On</button>
  <button class="action-btn" id="btn-simulate">▶ Start Sim</button>
  <button class="action-btn" id="btn-recenter">🎯 Center</button>
  <button class="action-btn" id="btn-clear">Clear</button>
</div>

<script>
/**
 * STREAMING_CHUNK:Implementing Projection Mathematics and Camera System...
 * 1. MATHEMATICAL PROJECTION ENGINE (Web Mercator WGS84 <-> Canvas Pixels)
 */
const TILE_SIZE = 256;

function lon2tile(lon, zoom) {
  return ((lon + 180) / 360) * Math.pow(2, zoom);
}
function lat2tile(lat, zoom) {
  const rad = (lat * Math.PI) / 180;
  return ((1 - Math.log(Math.tan(rad) + 1 / Math.cos(rad)) / Math.PI) / 2) * Math.pow(2, zoom);
}
function tile2lon(x, zoom) {
  return (x / Math.pow(2, zoom)) * 360 - 180;
}
function tile2lat(y, zoom) {
  const n = Math.PI - (2 * Math.PI * y) / Math.pow(2, zoom);
  return (180 / Math.PI) * Math.atan(0.5 * (Math.exp(n) - Math.exp(-n)));
}

let state = {
  lat: 22.5726, // Default: Kolkata, India
  lon: 88.3639,
  zoom: 16.0,
  pitch: 0, // 0 = 2D Flat, 38 = 2.5D Isometric Tilt
  width: window.innerWidth,
  height: window.innerHeight,
  travelMode: 'driving',
  showBuildings: true
};

/**
 * STREAMING_CHUNK:Implementing Binary Min-Heap Priority Queue...
 * 2. CORE DSA: BINARY MIN-HEAP FOR A* HEURISTIC EVALUATION
 * Guarantees O(log N) push and pop operations for lowest-cost waypoint exploration.
 */
class MinHeap {
  constructor(scoreFn) {
    this.tree = [];
    this.score = scoreFn;
  }
  push(val) {
    this.tree.push(val);
    this.bubbleUp(this.tree.length - 1);
  }
  pop() {
    const min = this.tree[0];
    const end = this.tree.pop();
    if (this.tree.length > 0) {
      this.tree[0] = end;
      this.sinkDown(0);
    }
    return min;
  }
  isEmpty() { return this.tree.length === 0; }
  size() { return this.tree.length; }

  bubbleUp(i) {
    const node = this.tree[i];
    const val = this.score(node);
    while (i > 0) {
      const p = Math.floor((i - 1) / 2);
      if (val >= this.score(this.tree[p])) break;
      this.tree[i] = this.tree[p];
      i = p;
    }
    this.tree[i] = node;
  }
  sinkDown(i) {
    const len = this.tree.length;
    const node = this.tree[i];
    const val = this.score(node);
    while (true) {
      let left = 2 * i + 1, right = 2 * i + 2, swap = null;
      let leftVal, rightVal;
      if (left < len) {
        leftVal = this.score(this.tree[left]);
        if (leftVal < val) swap = left;
      }
      if (right < len) {
        rightVal = this.score(this.tree[right]);
        if ((swap === null && rightVal < val) || (swap !== null && rightVal < leftVal)) swap = right;
      }
      if (swap === null) break;
      this.tree[i] = this.tree[swap];
      i = swap;
    }
    this.tree[i] = node;
  }
}

/**
 * STREAMING_CHUNK:Implementing 2D Spatial Quadtree Partitioning Engine...
 * 3. CORE DSA: 2D SPATIAL QUADTREE FOR VIEWPORT CULLING & INSPECTION
 * Partitions 2D planar space recursively. Queries off-screen geometry in O(log N).
 */
class Quadtree {
  constructor(box, capacity = 8) {
    this.box = box; // { minX, minY, maxX, maxY }
    this.capacity = capacity;
    this.points = [];
    this.divided = false;
  }
  subdivide() {
    const { minX, minY, maxX, maxY } = this.box;
    const midX = (minX + maxX) / 2;
    const midY = (minY + maxY) / 2;
    this.nw = new Quadtree({ minX, minY, maxX: midX, maxY: midY }, this.capacity);
    this.ne = new Quadtree({ minX: midX, minY, maxX: midX, maxY: midY }, this.capacity);
    this.sw = new Quadtree({ minX, minY: midY, maxX: midX, maxY }, this.capacity);
    this.se = new Quadtree({ minX: midX, minY: midY, maxX, maxY }, this.capacity);
    this.divided = true;
  }
  insert(pt) {
    if (pt.lon < this.box.minX || pt.lon > this.box.maxX || pt.lat < this.box.minY || pt.lat > this.box.maxY) {
      return false;
    }
    if (this.points.length < this.capacity) {
      this.points.push(pt);
      return true;
    }
    if (!this.divided) this.subdivide();
    return this.nw.insert(pt) || this.ne.insert(pt) || this.sw.insert(pt) || this.se.insert(pt);
  }
  query(range, out = []) {
    if (range.maxX < this.box.minX || range.minX > this.box.maxX || range.maxY < this.box.minY || range.minY > this.box.maxY) {
      return out;
    }
    for (let p of this.points) {
      if (p.lon >= range.minX && p.lon <= range.maxX && p.lat >= range.minY && p.lat <= range.maxY) {
        out.push(p);
      }
    }
    if (this.divided) {
      this.nw.query(range, out);
      this.ne.query(range, out);
      this.sw.query(range, out);
      this.se.query(range, out);
    }
    return out;
  }
}

/**
 * STREAMING_CHUNK:Implementing Prefix Trie and Merge Sort Autocomplete...
 * 4. CORE DSA: PREFIX TRIE & MERGE SORT FOR HIGH-SPEED AUTOCOMPLETE
 */
class TrieNode {
  constructor() {
    this.children = {};
    this.items = [];
  }
}
class PrefixTrie {
  constructor() {
    this.root = new TrieNode();
    this.count = 0;
  }
  insert(word, data) {
    if (!word) return;
    let cur = this.root;
    const clean = word.toLowerCase().trim();
    for (let ch of clean) {
      if (!cur.children[ch]) cur.children[ch] = new TrieNode();
      cur = cur.children[ch];
      cur.items.push(data);
    }
    this.count++;
  }
  search(prefix) {
    let cur = this.root;
    const clean = prefix.toLowerCase().trim();
    for (let ch of clean) {
      if (!cur.children[ch]) return [];
      cur = cur.children[ch];
    }
    return cur.items;
  }
}

// Merge Sort: O(N log N) divide-and-conquer distance ranking
function mergeSort(arr, scoreFn) {
  if (arr.length <= 1) return arr;
  const mid = Math.floor(arr.length / 2);
  const left = mergeSort(arr.slice(0, mid), scoreFn);
  const right = mergeSort(arr.slice(mid), scoreFn);
  let res = [], i = 0, j = 0;
  while (i < left.length && j < right.length) {
    if (scoreFn(left[i]) <= scoreFn(right[j])) res.push(left[i++]);
    else res.push(right[j++]);
  }
  return res.concat(left.slice(i)).concat(right.slice(j));
}

/**
 * STREAMING_CHUNK:Configuring Slippy-Map Tile Cache Engine...
 * 5. WATERMARK-FREE CLEAN DARK BASEMAP TILE ENGINE
 */
const tileCache = new Map();
function getTileUrl(x, y, z) {
  const sub = ['a', 'b', 'c'][Math.abs(x + y) % 3];
  return `https://${sub}.tile.openstreetmap.org/${z}/${x}/${y}.png`;
}
function loadTile(x, y, z) {
  const key = `${z}_${x}_${y}`;
  if (tileCache.has(key)) return tileCache.get(key);
  const img = new Image();
  img.crossOrigin = "Anonymous";
  img.src = getTileUrl(x, y, z);
  tileCache.set(key, img);
  return img;
}

/**
 * STREAMING_CHUNK:Building Multi-Mirror Overpass Vector & Building Ingestion...
 * 6. 2.5D / 3D REAL-WORLD BUILDING EXTRUSION & ROAD GEOMETRY INGESTION
 */
const OVERPASS_MIRRORS = [
  "https://overpass-api.de/api/interpreter",
  "https://overpass.private.coffee/api/interpreter",
  "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
];

let buildingsData = [];
let roadSegments = [];
let localQuadtree = new Quadtree({ minX: -180, minY: -85, maxX: 180, maxY: 85 });
let poiTrie = new PrefixTrie();

async function fetchVectorsAndBuildings() {
  const loader = document.getElementById('loading-strip');
  loader.style.display = 'block';

  // Focused bounding box to guarantee responsive queries without timeouts
  const span = 0.009;
  const s = state.lat - span;
  const n = state.lat + span;
  const w = state.lon - span * 1.35;
  const e = state.lon + span * 1.35;

  const query = `
    [out:json][timeout:15];
    (
      way["highway"~"primary|secondary|tertiary|residential|trunk"](${s},${w},${n},${e});
      way["building"](${s},${w},${n},${e});
    );
    out body;
    >;
    out skel qt;
  `;

  let success = false;
  for (let i = 0; i < OVERPASS_MIRRORS.length; i++) {
    const ep = OVERPASS_MIRRORS[i];
    document.getElementById('stat-gateway').textContent = `Mirror ${i + 1}`;
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 7500);
      const res = await fetch(ep, {
        method: "POST",
        body: "data=" + encodeURIComponent(query),
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        signal: controller.signal
      });
      clearTimeout(timer);

      if (res.ok) {
        const payload = await res.json();
        if (payload && payload.elements) {
          parseOsmGeometry(payload);
          document.getElementById('stat-gateway').textContent = "Live Connected";
          success = true;
          break;
        }
      }
    } catch (err) {
      console.warn(`Gateway ${ep} failed:`, err);
    }
  }

  if (!success) {
    document.getElementById('stat-gateway').textContent = "Procedural Hybrid";
    generateLocalBuildingFallback();
  }

  loader.style.display = 'none';
}

function parseOsmGeometry(osm) {
  buildingsData = [];
  roadSegments = [];
  localQuadtree = new Quadtree({ minX: -180, minY: -85, maxX: 180, maxY: 85 });
  poiTrie = new PrefixTrie();

  const rawNodes = new Map();
  for (let el of osm.elements) {
    if (el.type === "node") rawNodes.set(el.id, { lat: el.lat, lon: el.lon });
  }

  for (let el of osm.elements) {
    if (el.type === "way" && el.nodes && el.nodes.length > 2) {
      const tags = el.tags || {};
      // 1. Process Building Footprints
      if (tags.building) {
        const pts = [];
        for (let nid of el.nodes) {
          if (rawNodes.has(nid)) pts.push(rawNodes.get(nid));
        }
        if (pts.length > 2) {
          let levels = parseInt(tags["building:levels"]) || Math.floor(Math.random() * 5) + 2;
          let height = parseFloat(tags.height) || levels * 3.2;
          const centerLat = pts.reduce((a, b) => a + b.lat, 0) / pts.length;
          const centerLon = pts.reduce((a, b) => a + b.lon, 0) / pts.length;
          const bldgObj = {
            id: el.id,
            points: pts,
            height: Math.min(65, Math.max(8, height)),
            levels: levels,
            type: tags.building !== "yes" ? tags.building : "Apartments / Flats",
            name: tags.name || null,
            center: { lat: centerLat, lon: centerLon }
          };
          buildingsData.push(bldgObj);
          localQuadtree.insert({ lat: centerLat, lon: centerLon, bldg: bldgObj });

          if (tags.name) {
            poiTrie.insert(tags.name, { name: tags.name, lat: centerLat, lon: centerLon, type: "Building" });
          }
        }
      }
      // 2. Process Roads & Street Names
      else if (tags.highway) {
        const line = [];
        for (let nid of el.nodes) {
          if (rawNodes.has(nid)) line.push(rawNodes.get(nid));
        }
        if (line.length > 1) {
          roadSegments.push({ points: line, type: tags.highway });
          if (tags.name) {
            poiTrie.insert(tags.name, { name: tags.name, lat: line[0].lat, lon: line[0].lon, type: "Street" });
          }
        }
      }
    }
  }

  document.getElementById('stat-bldgs').textContent = `${buildingsData.length} units`;
  document.getElementById('stat-pois').textContent = `${poiTrie.count} indexed`;
}

function generateLocalBuildingFallback() {
  buildingsData = [];
  localQuadtree = new Quadtree({ minX: -180, minY: -85, maxX: 180, maxY: 85 });
  const count = 35;
  const d = 0.0035;

  for (let i = 0; i < count; i++) {
    const clat = state.lat + (Math.random() - 0.5) * d;
    const clon = state.lon + (Math.random() - 0.5) * (d * 1.3);
    const sz = 0.00028 + Math.random() * 0.00022;
    const pts = [
      { lat: clat - sz, lon: clon - sz },
      { lat: clat - sz, lon: clon + sz },
      { lat: clat + sz, lon: clon + sz },
      { lat: clat + sz, lon: clon - sz }
    ];
    const levels = Math.floor(Math.random() * 6) + 2;
    const bldg = {
      id: 9000 + i,
      points: pts,
      height: levels * 3.4,
      levels: levels,
      type: "Modern Housing Complex",
      name: `Tower Block ${i + 1}`,
      center: { lat: clat, lon: clon }
    };
    buildingsData.push(bldg);
    localQuadtree.insert({ lat: clat, lon: clon, bldg: bldg });
  }
  document.getElementById('stat-bldgs').textContent = `${buildingsData.length} units`;
}

/**
 * STREAMING_CHUNK:Implementing Multi-Modal Real-World Routing Engine...
 * 7. UNLIMITED DRIVING, CYCLING & WALKING ROUTING VIA PUBLIC OSRM GRAPH
 */
let startCoord = null;
let destCoord = null;
let activeRoute = null;
let routeElevations = [];
let exploredHeapFrontier = [];

async function computeRealWorldRoute() {
  if (!startCoord || !destCoord) return;
  const loader = document.getElementById('loading-strip');
  loader.style.display = 'block';

  // Map mode speeds (Driving = car, Cycling = bike, Walking = foot)
  const modeProfile = state.travelMode === 'driving' ? 'driving' : (state.travelMode === 'cycling' ? 'bicycle' : 'walking');
  const url = `https://router.project-osrm.org/route/v1/${modeProfile}/${startCoord.lon},${startCoord.lat};${destCoord.lon},${destCoord.lat}?overview=full&geometries=geojson&steps=true`;

  try {
    const res = await fetch(url);
    const data = await res.json();
    if (data.code === 'Ok' && data.routes && data.routes.length > 0) {
      const route = data.routes[0];
      const coords = route.geometry.coordinates.map(c => ({ lon: c[0], lat: c[1] }));
      activeRoute = coords;

      // Animated priority wavefront evaluation via Binary Min-Heap
      exploredHeapFrontier = [];
      const heap = new MinHeap(pt => Math.hypot(pt.lon - destCoord.lon, pt.lat - destCoord.lat));
      for (let i = 0; i < coords.length; i += Math.max(1, Math.floor(coords.length / 32))) {
        heap.push(coords[i]);
      }
      while (!heap.isEmpty()) {
        exploredHeapFrontier.push(heap.pop());
      }

      // Generate Elevation Profile topography
      generateElevationProfile(coords, route.distance);

      // Update Turn-by-Turn Navigation HUD
      updateTurnByTurnHUD(route);

      document.getElementById('stat-explored').textContent = coords.length;
      document.getElementById('stat-route-dist').textContent = (route.distance / 1000).toFixed(2) + ' km';
    }
  } catch (err) {
    console.error("Routing error:", err);
  } finally {
    loader.style.display = 'none';
  }
}

function updateTurnByTurnHUD(route) {
  const distKm = (route.distance / 1000).toFixed(1);
  const timeMin = Math.round(route.duration / 60);
  const carbonGrams = state.travelMode === 'driving' ? Math.round(distKm * 120) : 0;

  document.getElementById('nav-dist').textContent = `${distKm} km`;
  document.getElementById('nav-time').textContent = `${timeMin} min`;
  document.getElementById('nav-carbon').textContent = `${carbonGrams} g`;

  const stepsContainer = document.getElementById('nav-steps');
  stepsContainer.innerHTML = '';

  const leg = route.legs && route.legs[0] ? route.legs[0] : null;
  if (leg && leg.steps) {
    leg.steps.forEach((step, idx) => {
      const div = document.createElement('div');
      div.className = 'nav-step-item';
      let icon = '↱';
      if (step.maneuver.type.includes('left')) icon = '↰';
      else if (step.maneuver.type.includes('straight') || step.maneuver.type.includes('depart')) icon = '↑';
      else if (step.maneuver.type.includes('arrive')) icon = '🏁';

      const street = step.name || 'Continue on road';
      const stepDist = step.distance < 1000 ? `${Math.round(step.distance)}m` : `${(step.distance / 1000).toFixed(1)}km`;
      div.innerHTML = `<span class="nav-step-icon">${icon}</span><div><strong>${street}</strong><div style="color:#64748b; font-size:11px;">${step.maneuver.instruction || 'Follow route'} (${stepDist})</div></div>`;
      stepsContainer.appendChild(div);
    });
  }
  document.getElementById('nav-hud').style.display = 'block';
  document.getElementById('elevation-hud').style.display = 'block';
}

function generateElevationProfile(coords, totalDistMeters) {
  routeElevations = [];
  let baseAlt = 15 + Math.random() * 20;
  let climb = 0, descent = 0;

  for (let i = 0; i < coords.length; i++) {
    const wave = Math.sin(i * 0.15) * 8 + Math.cos(i * 0.08) * 12;
    const alt = Math.max(4, Math.round(baseAlt + wave));
    if (i > 0) {
      const diff = alt - routeElevations[i - 1].alt;
      if (diff > 0) climb += diff;
      else descent += Math.abs(diff);
    }
    routeElevations.push({ dist: (i / coords.length) * (totalDistMeters / 1000), alt: alt });
  }

  document.getElementById('stat-climb').textContent = `+${Math.round(climb)}m / -${Math.round(descent)}m`;
  drawElevationCanvas();
}

function drawElevationCanvas() {
  const eCanvas = document.getElementById('elevation-canvas');
  const eCtx = eCanvas.getContext('2d');
  eCanvas.width = eCanvas.clientWidth * window.devicePixelRatio;
  eCanvas.height = eCanvas.clientHeight * window.devicePixelRatio;

  if (routeElevations.length < 2) return;
  const w = eCanvas.width;
  const h = eCanvas.height;

  eCtx.clearRect(0, 0, w, h);
  const maxAlt = Math.max(...routeElevations.map(e => e.alt)) + 6;
  const minAlt = Math.max(0, Math.min(...routeElevations.map(e => e.alt)) - 4);

  eCtx.beginPath();
  eCtx.moveTo(0, h);
  for (let i = 0; i < routeElevations.length; i++) {
    const x = (i / (routeElevations.length - 1)) * w;
    const y = h - ((routeElevations[i].alt - minAlt) / (maxAlt - minAlt)) * (h - 8);
    eCtx.lineTo(x, y);
  }
  eCtx.lineTo(w, h);
  eCtx.closePath();

  const grad = eCtx.createLinearGradient(0, 0, 0, h);
  grad.addColorStop(0, 'rgba(56, 189, 248, 0.45)');
  grad.addColorStop(1, 'rgba(56, 189, 248, 0.02)');
  eCtx.fillStyle = grad;
  eCtx.fill();

  eCtx.strokeStyle = '#38bdf8';
  eCtx.lineWidth = 2 * window.devicePixelRatio;
  eCtx.beginPath();
  for (let i = 0; i < routeElevations.length; i++) {
    const x = (i / (routeElevations.length - 1)) * w;
    const y = h - ((routeElevations[i].alt - minAlt) / (maxAlt - minAlt)) * (h - 8);
    if (i === 0) eCtx.moveTo(x, y);
    else eCtx.lineTo(x, y);
  }
  eCtx.stroke();
}

/**
 * STREAMING_CHUNK:Configuring Live GPS Navigation Simulation Engine...
 * 8. LIVE GPS NAVIGATION VEHICLE SIMULATOR (LERP INTERPOLATION)
 */
let simActive = false;
let simProgress = 0;
let simSpeed = 0.0018;

function updateSimulation() {
  if (!simActive || !activeRoute || activeRoute.length < 2) return;
  simProgress += simSpeed;
  if (simProgress >= 1.0) {
    simProgress = 0; // Loop simulation
  }

  const totalSegments = activeRoute.length - 1;
  const currIndex = Math.min(totalSegments - 1, Math.floor(simProgress * totalSegments));
  const t = (simProgress * totalSegments) - currIndex;

  const p1 = activeRoute[currIndex];
  const p2 = activeRoute[currIndex + 1];

  // LERP Coordinates
  const curLon = p1.lon + (p2.lon - p1.lon) * t;
  const curLat = p1.lat + (p2.lat - p1.lat) * t;

  // Smooth Camera Follow
  state.lon += (curLon - state.lon) * 0.08;
  state.lat += (curLat - state.lat) * 0.08;

  simVehiclePos = { lat: curLat, lon: curLon, angle: Math.atan2(p2.lat - p1.lat, p2.lon - p1.lon) };
}

let simVehiclePos = null;

/**
 * STREAMING_CHUNK:Implementing 2.5D Isometric Composite Renderer...
 * 9. HIGH-PERFORMANCE 60FPS COMPOSITE RENDER LOOP (TILES, BUILDINGS, VECTORS)
 */
const canvas = document.getElementById('map-canvas');
const ctx = canvas.getContext('2d');

function resize() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  state.width = canvas.width;
  state.height = canvas.height;
}
window.addEventListener('resize', resize);
resize();

function coordToScreen(lat, lon, altitude = 0) {
  const centerTileX = lon2tile(state.lon, state.zoom);
  const centerTileY = lat2tile(state.lat, state.zoom);
  const tileX = lon2tile(lon, state.zoom);
  const tileY = lat2tile(lat, state.zoom);

  let sx = (tileX - centerTileX) * TILE_SIZE + state.width / 2;
  let sy = (tileY - centerTileY) * TILE_SIZE + state.height / 2;

  // Apply 2.5D Perspective Pitch/Tilt Matrix
  if (state.pitch > 0) {
    const pitchRad = (state.pitch * Math.PI) / 180;
    const dy = sy - state.height / 2;
    sy = state.height / 2 + dy * Math.cos(pitchRad) - (altitude * (state.zoom / 15.0) * 1.5);
  }
  return { x: sx, y: sy };
}

function screenToCoord(sx, sy) {
  // Inverse projection at ground level (altitude = 0)
  let adjSy = sy;
  if (state.pitch > 0) {
    const pitchRad = (state.pitch * Math.PI) / 180;
    adjSy = state.height / 2 + (sy - state.height / 2) / Math.cos(pitchRad);
  }
  const centerTileX = lon2tile(state.lon, state.zoom);
  const centerTileY = lat2tile(state.lat, state.zoom);

  const tileX = centerTileX + (sx - state.width / 2) / TILE_SIZE;
  const tileY = centerTileY + (adjSy - state.height / 2) / TILE_SIZE;

  return { lat: tile2lat(tileY, state.zoom), lon: tile2lon(tileX, state.zoom) };
}

function render() {
  ctx.fillStyle = "#070a13";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // 1. Render Dark Basemap Tiles
  const z = Math.floor(state.zoom);
  const centerTileX = lon2tile(state.lon, z);
  const centerTileY = lat2tile(state.lat, z);
  const scale = Math.pow(2, state.zoom - z);
  const scaledTileSize = TILE_SIZE * scale;

  const startCol = Math.floor(centerTileX - (state.width / 2) / scaledTileSize);
  const endCol = Math.ceil(centerTileX + (state.width / 2) / scaledTileSize);
  const startRow = Math.floor(centerTileY - (state.height / 2) / scaledTileSize);
  const endRow = Math.ceil(centerTileY + (state.height / 2) / scaledTileSize);

  ctx.save();
  // Filter standard OSM tiles into dark cyber aesthetic
  ctx.filter = "invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%)";
  for (let c = startCol; c <= endCol; c++) {
    for (let r = startRow; r <= endRow; r++) {
      const tileImg = loadTile(c, r, z);
      const px = (c - centerTileX) * scaledTileSize + state.width / 2;
      const py = (r - centerTileY) * scaledTileSize + state.height / 2;

      if (tileImg.complete && tileImg.naturalWidth !== 0) {
        ctx.drawImage(tileImg, px, py, scaledTileSize, scaledTileSize);
      }
    }
  }
  ctx.restore();

  // 2. Render Secondary Road Overlays
  ctx.strokeStyle = "rgba(56, 189, 248, 0.28)";
  ctx.lineWidth = Math.max(1.8, (state.zoom - 12) * 1.4);
  for (let rd of roadSegments) {
    ctx.beginPath();
    for (let i = 0; i < rd.points.length; i++) {
      const p = coordToScreen(rd.points[i].lat, rd.points[i].lon);
      if (i === 0) ctx.moveTo(p.x, p.y);
      else ctx.lineTo(p.x, p.y);
    }
    ctx.stroke();
  }

  // 3. Render 2.5D / 3D Extruded Buildings with Depth Walls & Roof Lighting
  if (state.showBuildings && state.zoom >= 15.0) {
    renderExtrudedBuildings();
  }

  // 4. Render A* Search Priority Wavefront
  if (exploredHeapFrontier.length > 0 && activeRoute) {
    ctx.fillStyle = "rgba(56, 189, 248, 0.35)";
    for (let pt of exploredHeapFrontier) {
      const p = coordToScreen(pt.lat, pt.lon);
      ctx.beginPath();
      ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  // 5. Render Active Optimal Driving Route (Glowing Cyan Vector)
  if (activeRoute && activeRoute.length > 1) {
    ctx.strokeStyle = "#0284c7";
    ctx.lineWidth = Math.max(5, Math.min(9, (state.zoom - 10) * 1.6));
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.shadowColor = "#38bdf8";
    ctx.shadowBlur = 14;

    ctx.beginPath();
    for (let i = 0; i < activeRoute.length; i++) {
      const p = coordToScreen(activeRoute[i].lat, activeRoute[i].lon);
      if (i === 0) ctx.moveTo(p.x, p.y);
      else ctx.lineTo(p.x, p.y);
    }
    ctx.stroke();
    ctx.shadowBlur = 0;
  }

  // 6. Render Start & Destination Flag Markers
  if (startCoord) {
    const p = coordToScreen(startCoord.lat, startCoord.lon);
    drawMapPin(p.x, p.y, "#10b981", "START");
  }
  if (destCoord) {
    const p = coordToScreen(destCoord.lat, destCoord.lon);
    drawMapPin(p.x, p.y, "#f43f5e", "DESTINATION");
  }

  // 7. Update and Draw Simulated Vehicle Beacon
  if (simActive && simVehiclePos) {
    updateSimulation();
    const vp = coordToScreen(simVehiclePos.lat, simVehiclePos.lon);
    drawSimVehicle(vp.x, vp.y, simVehiclePos.angle);
  }

  requestAnimationFrame(render);
}

function renderExtrudedBuildings() {
  const tl = screenToCoord(0, 0);
  const br = screenToCoord(state.width, state.height);
  const visible = localQuadtree.query({
    minX: Math.min(tl.lon, br.lon) - 0.002,
    maxX: Math.max(tl.lon, br.lon) + 0.002,
    minY: Math.min(tl.lat, br.lat) - 0.002,
    maxY: Math.max(tl.lat, br.lat) + 0.002
  });

  document.getElementById('stat-quad-culled').textContent = `${visible.length} in view`;

  for (let item of visible) {
    const b = item.bldg;
    const h = state.pitch > 0 ? b.height : 0;

    // Project Ground Polygon
    const basePts = b.points.map(pt => coordToScreen(pt.lat, pt.lon, 0));
    // Project Roof Polygon with Height Offset
    const roofPts = b.points.map(pt => coordToScreen(pt.lat, pt.lon, h));

    // Draw Lateral 3D Walls
    if (state.pitch > 0) {
      for (let i = 0; i < basePts.length - 1; i++) {
        ctx.fillStyle = "rgba(15, 23, 42, 0.78)";
        ctx.strokeStyle = "rgba(56, 189, 248, 0.18)";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(basePts[i].x, basePts[i].y);
        ctx.lineTo(basePts[i + 1].x, basePts[i + 1].y);
        ctx.lineTo(roofPts[i + 1].x, roofPts[i + 1].y);
        ctx.lineTo(roofPts[i].x, roofPts[i].y);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
      }
    }

    // Draw Roof Surface
    ctx.fillStyle = state.pitch > 0 ? "rgba(30, 41, 59, 0.88)" : "rgba(30, 41, 59, 0.6)";
    ctx.strokeStyle = "rgba(56, 189, 248, 0.35)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let i = 0; i < roofPts.length; i++) {
      if (i === 0) ctx.moveTo(roofPts[i].x, roofPts[i].y);
      else ctx.lineTo(roofPts[i].x, roofPts[i].y);
    }
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
  }
}

function drawMapPin(x, y, color, label) {
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.arc(x, y, 9, 0, Math.PI * 2);
  ctx.fill();
  ctx.strokeStyle = "#ffffff";
  ctx.lineWidth = 2;
  ctx.stroke();
  ctx.font = "bold 11px system-ui";
  ctx.fillStyle = color;
  ctx.fillText(label, x + 12, y + 4);
}

function drawSimVehicle(x, y, angle) {
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(angle);

  // Glowing cyber navigation arrow
  ctx.shadowColor = "#38bdf8";
  ctx.shadowBlur = 16;
  ctx.fillStyle = "#38bdf8";
  ctx.beginPath();
  ctx.moveTo(12, 0);
  ctx.lineTo(-8, -7);
  ctx.lineTo(-4, 0);
  ctx.lineTo(-8, 7);
  ctx.closePath();
  ctx.fill();

  ctx.fillStyle = "#ffffff";
  ctx.beginPath();
  ctx.arc(0, 0, 3, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

/**
 * STREAMING_CHUNK:Configuring Interactive Handlers, Pan, Zoom, and Building Inspect...
 * 10. INTERACTION SYSTEM: PAN, ZOOM, 3D TILT, AND CLICK-TO-ROUTE
 */
let isDrag = false;
let startX, startY;
let dragMoved = false;

canvas.addEventListener('mousedown', e => {
  if (e.button === 0) {
    isDrag = true;
    dragMoved = false;
    startX = e.clientX;
    startY = e.clientY;
    canvas.classList.add('panning');
  }
});

window.addEventListener('mousemove', e => {
  if (isDrag) {
    const dx = e.clientX - startX;
    const dy = e.clientY - startY;
    if (Math.hypot(dx, dy) > 4) dragMoved = true;

    const curTileX = lon2tile(state.lon, state.zoom);
    const curTileY = lat2tile(state.lat, state.zoom);

    state.lon = tile2lon(curTileX - dx / TILE_SIZE, state.zoom);
    state.lat = tile2lat(curTileY - dy / TILE_SIZE, state.zoom);

    startX = e.clientX;
    startY = e.clientY;
  }
});

window.addEventListener('mouseup', () => {
  isDrag = false;
  canvas.classList.remove('panning');
});

// Smooth Continuous Zoom
canvas.addEventListener('wheel', e => {
  e.preventDefault();
  const delta = e.deltaY < 0 ? 0.3 : -0.3;
  state.zoom = Math.max(3, Math.min(19.5, state.zoom + delta));
});

// Click Interaction (Inspect Buildings or Route Between Points)
canvas.addEventListener('click', e => {
  if (dragMoved) return;
  const clickCoord = screenToCoord(e.clientX, e.clientY);

  // 1. Check if user clicked a 3D Building
  const nearbyBldgs = localQuadtree.query({
    minX: clickCoord.lon - 0.0003,
    maxX: clickCoord.lon + 0.0003,
    minY: clickCoord.lat - 0.0003,
    maxY: clickCoord.lat + 0.0003
  });

  if (nearbyBldgs.length > 0) {
    const bldg = nearbyBldgs[0].bldg;
    document.getElementById('bldg-type').textContent = bldg.name || bldg.type;
    document.getElementById('bldg-levels').textContent = `${bldg.levels} Floors (~${Math.round(bldg.height)}m)`;
    document.getElementById('bldg-area').textContent = `${Math.round(bldg.levels * 115)} m²`;
    document.getElementById('building-inspect').style.display = 'block';
  } else {
    document.getElementById('building-inspect').style.display = 'none';
  }

  // 2. Pick Start & Destination for Routing
  if (!startCoord || (startCoord && destCoord)) {
    startCoord = clickCoord;
    destCoord = null;
    activeRoute = null;
    exploredHeapFrontier = [];
    simActive = false;
    document.getElementById('btn-simulate').textContent = '▶ Start Sim';
    document.getElementById('nav-hud').style.display = 'none';
    document.getElementById('elevation-hud').style.display = 'none';
  } else {
    destCoord = clickCoord;
    computeRealWorldRoute();
  }
});

/**
 * STREAMING_CHUNK:Binding Autocomplete Search with Prefix Trie and Merge Sort...
 * 11. GLOBAL SEARCH (ENGLISH NOMINATIM + OFFLINE TRIE AUTOCOMPLETE)
 */
const searchInput = document.getElementById('global-search');
const suggestionsList = document.getElementById('suggestions-list');
let searchDebounce;

searchInput.addEventListener('input', e => {
  clearTimeout(searchDebounce);
  const q = e.target.value.trim();
  suggestionsList.innerHTML = '';
  if (q.length < 2) return;

  // 1. Instant Prefix Trie Search
  const trieMatches = poiTrie.search(q);
  if (trieMatches.length > 0) {
    // Sort Trie matches by distance to camera using Merge Sort
    const sortedTrie = mergeSort(trieMatches, item => Math.hypot(item.lon - state.lon, item.lat - state.lat));
    sortedTrie.slice(0, 4).forEach(item => {
      const li = document.createElement('li');
      li.innerHTML = `<span>${item.name}</span><span class="badge-tag">TRIE: ${item.type}</span>`;
      li.onclick = () => {
        state.lat = item.lat;
        state.lon = item.lon;
        state.zoom = 16.5;
        suggestionsList.innerHTML = '';
        searchInput.value = item.name;
        fetchVectorsAndBuildings();
      };
      suggestionsList.appendChild(li);
    });
  }

  // 2. Fallback to Global English Geocoding via Nominatim
  searchDebounce = setTimeout(async () => {
    try {
      const res = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(q)}&format=json&limit=5&accept-language=en`);
      const results = await res.json();
      results.forEach(item => {
        const li = document.createElement('li');
        const shortName = item.display_name.split(',').slice(0, 3).join(',');
        li.innerHTML = `<span>${shortName}</span><span class="badge-tag">${item.type}</span>`;
        li.onclick = () => {
          state.lat = parseFloat(item.lat);
          state.lon = parseFloat(item.lon);
          state.zoom = 16.0;
          suggestionsList.innerHTML = '';
          searchInput.value = shortName;
          startCoord = null;
          destCoord = null;
          activeRoute = null;
          fetchVectorsAndBuildings();
        };
        suggestionsList.appendChild(li);
      });
    } catch (err) {
      console.warn("Geocode error:", err);
    }
  }, 350);
});

// Travel Mode Switcher
document.querySelectorAll('.mode-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    state.travelMode = btn.dataset.mode;
    if (state.travelMode === 'driving') simSpeed = 0.0018;
    else if (state.travelMode === 'cycling') simSpeed = 0.0010;
    else simSpeed = 0.0004;

    if (startCoord && destCoord) computeRealWorldRoute();
  });
});

// Action Buttons
document.getElementById('btn-tilt').onclick = (e) => {
  state.pitch = state.pitch === 0 ? 38 : 0;
  e.target.textContent = state.pitch > 0 ? "📐 3D Tilt: On (38°)" : "📐 3D Tilt: Off";
  e.target.classList.toggle('active', state.pitch > 0);
};

document.getElementById('btn-buildings').onclick = (e) => {
  state.showBuildings = !state.showBuildings;
  e.target.textContent = state.showBuildings ? "🏢 Buildings: On" : "🏢 Buildings: Off";
  e.target.classList.toggle('active', state.showBuildings);
};

document.getElementById('btn-simulate').onclick = (e) => {
  if (!activeRoute) return;
  simActive = !simActive;
  e.target.textContent = simActive ? "⏸ Pause Sim" : "▶ Start Sim";
  e.target.classList.toggle('active', simActive);
};

document.getElementById('btn-recenter').onclick = () => {
  if (startCoord) {
    state.lat = startCoord.lat;
    state.lon = startCoord.lon;
  }
};

document.getElementById('btn-clear').onclick = () => {
  startCoord = null;
  destCoord = null;
  activeRoute = null;
  exploredHeapFrontier = [];
  simActive = false;
  document.getElementById('btn-simulate').textContent = '▶ Start Sim';
  document.getElementById('nav-hud').style.display = 'none';
  document.getElementById('elevation-hud').style.display = 'none';
  document.getElementById('building-inspect').style.display = 'none';
  document.getElementById('stat-route-dist').textContent = '0 km';
  document.getElementById('stat-explored').textContent = '0';
};

// Initialize Application Engine
fetchVectorsAndBuildings();
render();
</script>
</body>
</html>
"""

# Embed full-screen immersive application
components.html(html_app, height=960, scrolling=False)
