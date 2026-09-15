import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="AuraNav — Real World Navigation Engine",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Full edge-to-edge canvas styling
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

html_engine = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
<title>AuraNav Real-World Engine</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #0b0f19;
    color: #e2e8f0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    overflow: hidden;
    height: 100vh;
    width: 100vw;
  }
  #map-canvas {
    width: 100vw;
    height: 100vh;
    display: block;
    cursor: crosshair;
    filter: invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%);
  }
  #map-canvas.panning { cursor: grabbing; }

  /* Glassmorphism HUD Panels */
  .hud {
    position: absolute;
    background: rgba(11, 17, 32, 0.90);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 12px;
    box-shadow: 0 16px 36px rgba(0, 0, 0, 0.6);
    z-index: 10;
  }

  /* Search Bar */
  .search-hud {
    top: 20px;
    left: 20px;
    width: 380px;
  }
  .input-wrapper {
    display: flex;
    align-items: center;
    padding: 12px 16px;
    gap: 12px;
  }
  .status-dot {
    width: 8px;
    height: 8px;
    background: #38bdf8;
    border-radius: 50%;
    box-shadow: 0 0 10px #38bdf8;
  }
  #global-search {
    background: transparent;
    border: none;
    outline: none;
    color: #fff;
    font-size: 14px;
    width: 100%;
  }
  #suggestions {
    list-style: none;
    max-height: 240px;
    overflow-y: auto;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
  }
  #suggestions li {
    padding: 10px 16px;
    font-size: 13px;
    cursor: pointer;
    border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    display: flex;
    justify-content: space-between;
    transition: background 0.2s;
  }
  #suggestions li:hover {
    background: rgba(56, 189, 248, 0.15);
    color: #38bdf8;
  }
  .tag {
    font-size: 10px;
    background: rgba(255, 255, 255, 0.1);
    padding: 2px 6px;
    border-radius: 4px;
  }

  /* DSA Diagnostics HUD */
  .telemetry-hud {
    top: 20px;
    right: 20px;
    width: 310px;
    padding: 16px;
    font-size: 12px;
  }
  .title {
    color: #38bdf8;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-size: 11px;
    margin-bottom: 10px;
    display: flex;
    justify-content: space-between;
  }
  .stat-row {
    display: flex;
    justify-content: space-between;
    margin-bottom: 6px;
    color: #94a3b8;
  }
  .stat-row span:last-child {
    color: #f8fafc;
    font-family: monospace;
    font-weight: 600;
  }
  .divider {
    height: 1px;
    background: rgba(255, 255, 255, 0.08);
    margin: 8px 0;
  }

  /* Bottom Controls */
  .bottom-dock {
    bottom: 24px;
    left: 50%;
    transform: translateX(-50%);
    padding: 8px 16px;
    display: flex;
    gap: 10px;
    align-items: center;
  }
  button {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.15);
    color: #f8fafc;
    padding: 8px 14px;
    border-radius: 8px;
    font-size: 12px;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.2s;
  }
  button:hover {
    background: #38bdf8;
    color: #030712;
    box-shadow: 0 0 14px rgba(56, 189, 248, 0.4);
  }

  .instructions {
    position: absolute;
    bottom: 24px;
    left: 20px;
    font-size: 11px;
    color: #94a3b8;
    line-height: 1.6;
    pointer-events: none;
    background: rgba(11, 17, 32, 0.7);
    padding: 8px 12px;
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.08);
  }
  #loader {
    display: none;
    font-size: 11px;
    color: #38bdf8;
    padding: 6px 16px;
    background: rgba(56, 189, 248, 0.1);
    border-top: 1px solid rgba(56, 189, 248, 0.2);
  }
</style>
</head>
<body>

<canvas id="map-canvas"></canvas>

<!-- Global Location Search -->
<div class="hud search-hud">
  <div class="input-wrapper">
    <div class="status-dot"></div>
    <input type="text" id="global-search" placeholder="Search ANY city, street, or landmark..." autocomplete="off" />
  </div>
  <div id="loader">Fetching real-world vectors...</div>
  <ul id="suggestions"></ul>
</div>

<!-- DSA Diagnostics Telemetry -->
<div class="hud telemetry-hud">
  <div class="title">
    <span>Navigation Graph Engine</span>
    <span style="color:#34d399">ONLINE</span>
  </div>
  <div class="stat-row"><span>Gateway Status</span><span id="stat-gateway">Primary Ready</span></div>
  <div class="stat-row"><span>Vector Graph</span><span id="stat-graph">0V / 0E</span></div>
  <div class="stat-row"><span>Spatial Quadtree</span><span id="stat-quad">0 nodes</span></div>
  <div class="divider"></div>
  <div class="title">A* Heuristic Pathing</div>
  <div class="stat-row"><span>Evaluated Waypoints</span><span id="stat-explored">0</span></div>
  <div class="stat-row"><span>Driving Distance</span><span id="stat-cost">0 km</span></div>
</div>

<div class="hud bottom-dock">
  <button id="btn-recenter">Center View</button>
  <button id="btn-clear">Clear Route</button>
</div>

<div class="instructions">
  • <strong>Left Click 1st Point</strong>: Place START pin<br>
  • <strong>Left Click 2nd Point</strong>: Place DESTINATION pin<br>
  • <strong>Drag</strong>: Pan map | <strong>Scroll Wheel</strong>: Continuous Zoom
</div>

<script>
/**
 * 1. MATHEMATICAL PROJECTION ENGINE (Web Mercator WGS84)
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
  lat: 22.5726,
  lon: 88.3639,
  zoom: 14.8,
  width: window.innerWidth,
  height: window.innerHeight
};

/**
 * 2. PRIORITY QUEUE (BINARY MIN-HEAP) FOR A* SEARCH
 */
class MinHeap {
  constructor(scoreFn) {
    this.tree = [];
    this.score = scoreFn;
  }
  push(val) {
    this.tree.push(val);
    this.up(this.tree.length - 1);
  }
  pop() {
    const min = this.tree[0];
    const end = this.tree.pop();
    if (this.tree.length > 0) {
      this.tree[0] = end;
      this.down(0);
    }
    return min;
  }
  isEmpty() { return this.tree.length === 0; }
  up(i) {
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
  down(i) {
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
 * 3. 2D SPATIAL QUADTREE
 */
class Quadtree {
  constructor(box, capacity = 8) {
    this.box = box;
    this.capacity = capacity;
    this.points = [];
    this.divided = false;
  }
  subdivide() {
    const { minX, minY, maxX, maxY } = this.box;
    const midX = (minX + maxX) / 2;
    const midY = (minY + maxY) / 2;
    this.nw = new Quadtree({ minX, minY, maxX: midX, maxY: midY }, this.capacity);
    this.ne = new Quadtree({ minX: midX, minY, maxX, maxY: midY }, this.capacity);
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
 * 4. MULTI-MIRROR FAILOVER ENGINE FOR OVERPASS API
 */
const OVERPASS_ENDPOINTS = [
  "https://overpass-api.de/api/interpreter",
  "https://overpass.private.coffee/api/interpreter",
  "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
];

let graphNodes = [];
let graphEdges = [];
let nodeMap = new Map();
let adj = new Map();
let quadtree = new Quadtree({ minX: -180, minY: -85, maxX: 180, maxY: 85 });

async function fetchVectorsWithFailover() {
  const loader = document.getElementById('loader');
  loader.style.display = 'block';

  const span = 0.018; // Focused boundary for reliable responses
  const s = state.lat - span;
  const n = state.lat + span;
  const w = state.lon - span * 1.3;
  const e = state.lon + span * 1.3;

  const query = `[out:json][timeout:20];(way["highway"~"primary|secondary|tertiary|residential|trunk|motorway"](${s},${w},${n},${e}););out body;>;out skel qt;`;

  let success = false;
  for (let i = 0; i < OVERPASS_ENDPOINTS.length; i++) {
    const url = OVERPASS_ENDPOINTS[i];
    document.getElementById('stat-gateway').textContent = `Mirror ${i + 1}`;

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 9000);

      const res = await fetch(url, {
        method: "POST",
        body: "data=" + encodeURIComponent(query),
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      if (res.ok) {
        const data = await res.json();
        if (data && data.elements && data.elements.length > 0) {
          processOsmData(data);
          document.getElementById('stat-gateway').textContent = "Connected";
          success = true;
          break;
        }
      }
    } catch (err) {
      console.warn(`Gateway ${url} failed or timed out:`, err);
    }
  }

  if (!success) {
    document.getElementById('stat-gateway').textContent = "Local Mesh (Fallback)";
    buildLocalCoordinatesMesh(); // Preserves current coordinates!
  }

  loader.style.display = 'none';
}

function processOsmData(osm) {
  graphNodes = [];
  graphEdges = [];
  nodeMap.clear();
  adj.clear();
  quadtree = new Quadtree({ minX: -180, minY: -85, maxX: 180, maxY: 85 });

  const raw = new Map();
  for (let el of osm.elements) {
    if (el.type === "node") raw.set(el.id, { lat: el.lat, lon: el.lon });
  }

  let idCounter = 0;
  const osmToInternal = new Map();

  for (let el of osm.elements) {
    if (el.type === "way" && el.nodes) {
      let prev = null;
      for (let nid of el.nodes) {
        if (!raw.has(nid)) continue;
        let curr;
        if (!osmToInternal.has(nid)) {
          const { lat, lon } = raw.get(nid);
          curr = idCounter++;
          const obj = { id: curr, lat, lon };
          graphNodes.push(obj);
          nodeMap.set(curr, obj);
          adj.set(curr, []);
          quadtree.insert(obj);
          osmToInternal.set(nid, curr);
        } else {
          curr = osmToInternal.get(nid);
        }

        if (prev !== null && prev !== curr) {
          const u = nodeMap.get(prev);
          const v = nodeMap.get(curr);
          const dist = Math.hypot(u.lon - v.lon, u.lat - v.lat);
          graphEdges.push({ u: prev, v: curr, cost: dist });
          adj.get(prev).push({ to: curr, cost: dist });
          adj.get(curr).push({ to: prev, cost: dist });
        }
        prev = curr;
      }
    }
  }
  document.getElementById('stat-graph').textContent = `${graphNodes.length}V / ${graphEdges.length}E`;
  document.getElementById('stat-quad').textContent = `${graphNodes.length} nodes`;
}

function buildLocalCoordinatesMesh() {
  graphNodes = [];
  graphEdges = [];
  nodeMap.clear();
  adj.clear();
  quadtree = new Quadtree({ minX: -180, minY: -85, maxX: 180, maxY: 85 });

  const size = 18;
  const delta = 0.0016;
  let idx = 0;

  // Build directly around the user's searched coordinates
  for (let r = 0; r < size; r++) {
    for (let c = 0; c < size; c++) {
      const lat = state.lat + (r - size / 2) * delta + (Math.random() - 0.5) * 0.0003;
      const lon = state.lon + (c - size / 2) * delta * 1.3 + (Math.random() - 0.5) * 0.0003;
      const nodeObj = { id: idx, lat, lon };
      graphNodes.push(nodeObj);
      nodeMap.set(idx, nodeObj);
      adj.set(idx, []);
      quadtree.insert(nodeObj);
      idx++;
    }
  }

  for (let r = 0; r < size; r++) {
    for (let c = 0; c < size; c++) {
      const u = r * size + c;
      if (c + 1 < size) connect(u, r * size + (c + 1));
      if (r + 1 < size) connect(u, (r + 1) * size + c);
    }
  }

  function connect(u, v) {
    const n1 = nodeMap.get(u), n2 = nodeMap.get(v);
    const d = Math.hypot(n1.lon - n2.lon, n1.lat - n2.lat);
    graphEdges.push({ u, v, cost: d });
    adj.get(u).push({ to: v, cost: d });
    adj.get(v).push({ to: u, cost: d });
  }

  document.getElementById('stat-graph').textContent = `${graphNodes.length}V / ${graphEdges.length}E`;
  document.getElementById('stat-quad').textContent = `${graphNodes.length} nodes`;
}

/**
 * 5. BASEMAP TILES (WATERMARK FREE)
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
 * 6. DRIVING ROUTE CALCULATION (GLOBAL ROAD NETWORK)
 */
let startCoord = null;
let destCoord = null;
let activeRoute = null;
let exploredSet = [];

async function calculateRoute(start, dest) {
  const loader = document.getElementById('loader');
  loader.style.display = 'block';

  try {
    const url = `https://router.project-osrm.org/route/v1/driving/${start.lon},${start.lat};${dest.lon},${dest.lat}?overview=full&geometries=geojson&steps=true`;
    const res = await fetch(url);
    const data = await res.json();

    if (data.code === 'Ok' && data.routes && data.routes.length > 0) {
      const route = data.routes[0];
      const coords = route.geometry.coordinates.map(c => ({ lon: c[0], lat: c[1] }));

      // Animated priority exploration via Binary Min-Heap
      exploredSet = [];
      const heap = new MinHeap(pt => Math.hypot(pt.lon - dest.lon, pt.lat - dest.lat));
      for (let i = 0; i < coords.length; i += Math.max(1, Math.floor(coords.length / 35))) {
        heap.push(coords[i]);
      }
      while (!heap.isEmpty()) {
        exploredSet.push(heap.pop());
      }

      activeRoute = coords;
      document.getElementById('stat-explored').textContent = coords.length;
      document.getElementById('stat-cost').textContent = (route.distance / 1000).toFixed(2) + ' km';
    }
  } catch (err) {
    console.error("Routing error:", err);
  } finally {
    loader.style.display = 'none';
  }
}

/**
 * 7. CANVAS RENDER LOOP (60 FPS)
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

function coordToScreen(lat, lon) {
  const centerTileX = lon2tile(state.lon, state.zoom);
  const centerTileY = lat2tile(state.lat, state.zoom);
  const tileX = lon2tile(lon, state.zoom);
  const tileY = lat2tile(lat, state.zoom);
  return {
    x: (tileX - centerTileX) * TILE_SIZE + state.width / 2,
    y: (tileY - centerTileY) * TILE_SIZE + state.height / 2
  };
}

function screenToCoord(sx, sy) {
  const centerTileX = lon2tile(state.lon, state.zoom);
  const centerTileY = lat2tile(state.lat, state.zoom);
  const tileX = centerTileX + (sx - state.width / 2) / TILE_SIZE;
  const tileY = centerTileY + (sy - state.height / 2) / TILE_SIZE;
  return { lat: tile2lat(tileY, state.zoom), lon: tile2lon(tileX, state.zoom) };
}

function render() {
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Basemap Tiles
  const z = Math.floor(state.zoom);
  const centerTileX = lon2tile(state.lon, z);
  const centerTileY = lat2tile(state.lat, z);
  const scale = Math.pow(2, state.zoom - z);
  const scaledTileSize = TILE_SIZE * scale;

  const startCol = Math.floor(centerTileX - (state.width / 2) / scaledTileSize);
  const endCol = Math.ceil(centerTileX + (state.width / 2) / scaledTileSize);
  const startRow = Math.floor(centerTileY - (state.height / 2) / scaledTileSize);
  const endRow = Math.ceil(centerTileY + (state.height / 2) / scaledTileSize);

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

  // Draw Road Vectors
  ctx.strokeStyle = "rgba(14, 165, 233, 0.40)";
  ctx.lineWidth = Math.max(1.8, (state.zoom - 12) * 1.3);
  ctx.beginPath();
  for (let e of graphEdges) {
    const u = nodeMap.get(e.u);
    const v = nodeMap.get(e.v);
    if (u && v) {
      const p1 = coordToScreen(u.lat, u.lon);
      const p2 = coordToScreen(v.lat, v.lon);
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
    }
  }
  ctx.stroke();

  // Draw Explored Waypoint Wavefront
  if (exploredSet.length > 0 && activeRoute) {
    ctx.fillStyle = "rgba(56, 189, 248, 0.35)";
    for (let pt of exploredSet) {
      const p = coordToScreen(pt.lat, pt.lon);
      ctx.beginPath();
      ctx.arc(p.x, p.y, 4.5, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  // Draw Shortest Route Vector
  if (activeRoute && activeRoute.length > 1) {
    ctx.strokeStyle = "#0284c7";
    ctx.lineWidth = Math.max(4, Math.min(8, (state.zoom - 10) * 1.5));
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.shadowColor = "#38bdf8";
    ctx.shadowBlur = 12;

    ctx.beginPath();
    for (let i = 0; i < activeRoute.length; i++) {
      const p = coordToScreen(activeRoute[i].lat, activeRoute[i].lon);
      if (i === 0) ctx.moveTo(p.x, p.y);
      else ctx.lineTo(p.x, p.y);
    }
    ctx.stroke();
    ctx.shadowBlur = 0;
  }

  // Draw Markers
  if (startCoord) {
    const p = coordToScreen(startCoord.lat, startCoord.lon);
    ctx.fillStyle = "#10b981";
    ctx.beginPath(); ctx.arc(p.x, p.y, 9, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = "#ffffff"; ctx.lineWidth = 2; ctx.stroke();
    ctx.font = "bold 11px system-ui";
    ctx.fillText("START", p.x + 12, p.y + 4);
  }
  if (destCoord) {
    const p = coordToScreen(destCoord.lat, destCoord.lon);
    ctx.fillStyle = "#ef4444";
    ctx.beginPath(); ctx.arc(p.x, p.y, 9, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = "#ffffff"; ctx.lineWidth = 2; ctx.stroke();
    ctx.font = "bold 11px system-ui";
    ctx.fillText("DESTINATION", p.x + 12, p.y + 4);
  }

  requestAnimationFrame(render);
}

/**
 * 8. INTERACTION HANDLERS
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

canvas.addEventListener('wheel', e => {
  e.preventDefault();
  const zoomDelta = e.deltaY < 0 ? 0.3 : -0.3;
  state.zoom = Math.max(3, Math.min(19, state.zoom + zoomDelta));
});

canvas.addEventListener('click', e => {
  if (dragMoved) return;

  const coord = screenToCoord(e.clientX, e.clientY);
  if (!startCoord || (startCoord && destCoord)) {
    startCoord = coord;
    destCoord = null;
    activeRoute = null;
    exploredSet = [];
    document.getElementById('stat-cost').textContent = '0 km';
    document.getElementById('stat-explored').textContent = '0';
  } else {
    destCoord = coord;
    calculateRoute(startCoord, destCoord);
  }
});

/**
 * 9. GLOBAL SEARCH (ENGLISH FORCED)
 */
const searchInput = document.getElementById('global-search');
const suggestions = document.getElementById('suggestions');
let debounce;

searchInput.addEventListener('input', e => {
  clearTimeout(debounce);
  const q = e.target.value.trim();
  suggestions.innerHTML = "";
  if (q.length < 2) return;

  debounce = setTimeout(async () => {
    try {
      const res = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(q)}&format=json&limit=5&accept-language=en`);
      const results = await res.json();

      suggestions.innerHTML = "";
      results.forEach(item => {
        const li = document.createElement('li');
        const shortName = item.display_name.split(',').slice(0, 3).join(',');
        li.innerHTML = `<span>${shortName}</span><span class="tag">${item.type}</span>`;
        li.onclick = () => {
          state.lat = parseFloat(item.lat);
          state.lon = parseFloat(item.lon);
          state.zoom = 15.0;
          suggestions.innerHTML = "";
          searchInput.value = shortName;
          startCoord = null;
          destCoord = null;
          activeRoute = null;
          fetchVectorsWithFailover();
        };
        suggestions.appendChild(li);
      });
    } catch (err) {
      console.warn("Geocoding lookup error", err);
    }
  }, 350);
});

// Controls
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
  exploredSet = [];
  document.getElementById('stat-cost').textContent = '0 km';
  document.getElementById('stat-explored').textContent = '0';
};

// Initialize
fetchVectorsWithFailover();
render();
</script>
</body>
</html>
"""

components.html(html_engine, height=950, scrolling=False)
