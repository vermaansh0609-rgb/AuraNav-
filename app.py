import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="AuraNav — Autonomous DSA Navigation Engine",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Strip default padding to allow edge-to-edge interactive canvas
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
    cursor: grab;
    /* Hardware-accelerated dark inversion: converts standard OSM tiles into a sleek modern dark map */
    filter: invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%);
  }
  #map-canvas:active { cursor: grabbing; }

  /* Glassmorphism HUD Panels */
  .hud {
    position: absolute;
    background: rgba(11, 17, 32, 0.88);
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
    width: 290px;
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
    color: #64748b;
    line-height: 1.6;
    pointer-events: none;
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
    <input type="text" id="global-search" placeholder="Search ANY city, street, or landmark on Earth..." autocomplete="off" />
  </div>
  <div id="loader">Fetching real-world vector topology...</div>
  <ul id="suggestions"></ul>
</div>

<!-- DSA Diagnostics Telemetry -->
<div class="hud telemetry-hud">
  <div class="title">
    <span>Algorithmic Telemetry</span>
    <span style="color:#34d399">ACTIVE</span>
  </div>
  <div class="stat-row"><span>Graph Scale</span><span id="stat-graph">0V / 0E</span></div>
  <div class="stat-row"><span>Quadtree Culled</span><span id="stat-culled">0 nodes</span></div>
  <div class="stat-row"><span>Tile Cache</span><span id="stat-tiles">0 tiles</span></div>
  <div class="divider"></div>
  <div class="title">A* Heuristic Pathing</div>
  <div class="stat-row"><span>Min-Heap Pops</span><span id="stat-explored">0</span></div>
  <div class="stat-row"><span>Optimal Cost</span><span id="stat-cost">0 km</span></div>
</div>

<div class="hud bottom-dock">
  <button id="btn-sync">⚡ Re-fetch Area Vectors</button>
  <button id="btn-clear">Clear Path</button>
</div>

<div class="instructions">
  • <strong>Left Click Drag</strong>: Pan across entire globe<br>
  • <strong>Scroll Wheel</strong>: Continuous scale zoom (Street & Building level)<br>
  • <strong>Click 2 Intersections</strong>: Run A* Shortest Driving Route
</div>

<script>
/**
 * 1. SLIPPY-MAP PROJECTION MATH (WGS84 <-> Mercator Pixels)
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
  lat: 22.5511,
  lon: 88.3526,
  zoom: 15.5,
  width: window.innerWidth,
  height: window.innerHeight
};

/**
 * 2. CORE DSA: BINARY MIN-HEAP FOR A* SEARCH O(log N)
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
 * 3. CORE DSA: SPATIAL QUADTREE
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
 * 4. CORE DSA: PREFIX TRIE & MERGE SORT
 */
class TrieNode {
  constructor() {
    this.c = {};
    this.pois = [];
  }
}
class POITrie {
  constructor() { this.root = new TrieNode(); }
  insert(str, obj) {
    let cur = this.root;
    for (let ch of str.toLowerCase()) {
      if (!cur.c[ch]) cur.c[ch] = new TrieNode();
      cur = cur.c[ch];
      cur.pois.push(obj);
    }
  }
  search(prefix) {
    let cur = this.root;
    for (let ch of prefix.toLowerCase()) {
      if (!cur.c[ch]) return [];
      cur = cur.c[ch];
    }
    return cur.pois;
  }
}
function mergeSort(arr, keyFn) {
  if (arr.length <= 1) return arr;
  const mid = Math.floor(arr.length / 2);
  const left = mergeSort(arr.slice(0, mid), keyFn);
  const right = mergeSort(arr.slice(mid), keyFn);
  let res = [], i = 0, j = 0;
  while (i < left.length && j < right.length) {
    if (keyFn(left[i]) <= keyFn(right[j])) res.push(left[i++]);
    else res.push(right[j++]);
  }
  return res.concat(left.slice(i)).concat(right.slice(j));
}

/**
 * 5. WATERMARK-FREE REAL WORLD TILE ENGINE (NO API KEY REQUIRED)
 */
const tileCache = new Map();
let graphNodes = [];
let graphEdges = [];
let nodeMap = new Map();
let adj = new Map();
let quadtree = new Quadtree({ minX: -180, minY: -85, maxX: 180, maxY: 85 });
let poiTrie = new POITrie();

// Standard OpenStreetMap public tile servers (100% Free worldwide, no watermarks, no API keys)
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
 * 6. REAL-WORLD VECTOR NETWORK INGESTION (OVERPASS)
 */
async function fetchVectorsForCurrentView() {
  const loader = document.getElementById('loader');
  loader.style.display = 'block';

  const span = 0.025 * (16 / state.zoom);
  const s = state.lat - span;
  const n = state.lat + span;
  const w = state.lon - span * 1.3;
  const e = state.lon + span * 1.3;

  const query = `
    [out:json][timeout:12];
    (
      way["highway"~"primary|secondary|tertiary|residential|trunk|motorway|unclassified|living_street"](${s},${w},${n},${e});
    );
    out body;
    >;
    out skel qt;
  `;

  try {
    const res = await fetch("https://overpass-api.de/api/interpreter", {
      method: "POST",
      body: "data=" + encodeURIComponent(query),
      headers: { "Content-Type": "application/x-www-form-urlencoded" }
    });

    if (!res.ok) throw new Error("Overpass unavailable");
    const data = await res.json();
    processOverpassData(data);
  } catch (err) {
    console.warn("Real-world vector fetch fallback to local coordinate grid:", err);
    buildLocalGridFallback();
  } finally {
    loader.style.display = 'none';
  }
}

function processOverpassData(osm) {
  graphNodes = [];
  graphEdges = [];
  nodeMap.clear();
  adj.clear();
  quadtree = new Quadtree({ minX: -180, minY: -85, maxX: 180, maxY: 85 });
  poiTrie = new POITrie();

  const rawNodes = new Map();
  for (let el of osm.elements) {
    if (el.type === "node") rawNodes.set(el.id, { lat: el.lat, lon: el.lon });
  }

  let idCounter = 0;
  const osmToInternal = new Map();

  for (let el of osm.elements) {
    if (el.type === "way" && el.nodes) {
      const streetName = el.tags && el.tags.name ? el.tags.name : null;
      let prevInternal = null;

      for (let nid of el.nodes) {
        if (!rawNodes.has(nid)) continue;
        let currInternal;

        if (!osmToInternal.has(nid)) {
          const { lat, lon } = rawNodes.get(nid);
          currInternal = idCounter++;
          const nodeObj = { id: currInternal, lat, lon, name: streetName };
          graphNodes.push(nodeObj);
          nodeMap.set(currInternal, nodeObj);
          adj.set(currInternal, []);
          quadtree.insert(nodeObj);
          osmToInternal.set(nid, currInternal);

          if (streetName && Math.random() > 0.8) {
            poiTrie.insert(streetName, nodeObj);
          }
        } else {
          currInternal = osmToInternal.get(nid);
        }

        if (prevInternal !== null && prevInternal !== currInternal) {
          const u = nodeMap.get(prevInternal);
          const v = nodeMap.get(currInternal);
          const dist = Math.hypot(u.lon - v.lon, u.lat - v.lat);
          graphEdges.push({ u: prevInternal, v: currInternal, cost: dist });
          adj.get(prevInternal).push({ to: currInternal, cost: dist });
          adj.get(currInternal).push({ to: prevInternal, cost: dist });
        }
        prevInternal = currInternal;
      }
    }
  }

  document.getElementById('stat-graph').textContent = `${graphNodes.length}V / ${graphEdges.length}E`;
}

function buildLocalGridFallback() {
  graphNodes = [];
  graphEdges = [];
  nodeMap.clear();
  adj.clear();
  quadtree = new Quadtree({ minX: -180, minY: -85, maxX: 180, maxY: 85 });

  const size = 18;
  const delta = 0.0015;
  let idx = 0;

  for (let r = 0; r < size; r++) {
    for (let c = 0; c < size; c++) {
      const lat = state.lat + (r - size / 2) * delta + (Math.random() - 0.5) * 0.0003;
      const lon = state.lon + (c - size / 2) * delta * 1.3 + (Math.random() - 0.5) * 0.0003;
      const nodeObj = { id: idx, lat, lon, name: null };
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

  document.getElementById('stat-graph').textContent = `${graphNodes.length}V / ${graphEdges.length}E (Active Mesh)`;
}

/**
 * 7. CORE DSA: A* PATHFINDING WITH MIN-HEAP
 */
let startNode = null;
let goalNode = null;
let activeRoute = null;
let exploredSet = new Set();

function runAStar(srcId, dstId) {
  const g = new Map();
  const f = new Map();
  const parent = new Map();
  exploredSet = new Set();

  graphNodes.forEach(n => {
    g.set(n.id, Infinity);
    f.set(n.id, Infinity);
  });

  g.set(srcId, 0);
  const target = nodeMap.get(dstId);
  const h = (nid) => {
    const node = nodeMap.get(nid);
    return Math.hypot(node.lon - target.lon, node.lat - target.lat);
  };
  f.set(srcId, h(srcId));

  const heap = new MinHeap(id => f.get(id));
  heap.push(srcId);

  while (!heap.isEmpty()) {
    const curr = heap.pop();
    exploredSet.add(curr);

    if (curr === dstId) {
      const path = [];
      let temp = dstId;
      while (parent.has(temp)) {
        path.unshift(nodeMap.get(temp));
        temp = parent.get(temp);
      }
      path.unshift(nodeMap.get(srcId));

      document.getElementById('stat-explored').textContent = exploredSet.size;
      const km = (g.get(dstId) * 111).toFixed(2);
      document.getElementById('stat-cost').textContent = `${km} km`;
      return path;
    }

    for (let edge of adj.get(curr) || []) {
      const nxt = edge.to;
      const tentative = g.get(curr) + edge.cost;
      if (tentative < g.get(nxt)) {
        parent.set(nxt, curr);
        g.set(nxt, tentative);
        f.set(nxt, tentative + h(nxt));
        heap.push(nxt);
      }
    }
  }
  return null;
}

/**
 * 8. RENDERING ENGINE (CANVAS 60FPS COMPOSITOR)
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

  const screenX = (tileX - centerTileX) * TILE_SIZE + state.width / 2;
  const screenY = (tileY - centerTileY) * TILE_SIZE + state.height / 2;
  return { x: screenX, y: screenY };
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

  // 1. Draw Clean Slippy Base Map Tiles (Without any watermarks)
  const z = Math.floor(state.zoom);
  const centerTileX = lon2tile(state.lon, z);
  const centerTileY = lat2tile(state.lat, z);

  const scale = Math.pow(2, state.zoom - z);
  const scaledTileSize = TILE_SIZE * scale;

  const startCol = Math.floor(centerTileX - (state.width / 2) / scaledTileSize);
  const endCol = Math.ceil(centerTileX + (state.width / 2) / scaledTileSize);
  const startRow = Math.floor(centerTileY - (state.height / 2) / scaledTileSize);
  const endRow = Math.ceil(centerTileY + (state.height / 2) / scaledTileSize);

  let tilesRendered = 0;
  for (let c = startCol; c <= endCol; c++) {
    for (let r = startRow; r <= endRow; r++) {
      const tileImg = loadTile(c, r, z);
      const px = (c - centerTileX) * scaledTileSize + state.width / 2;
      const py = (r - centerTileY) * scaledTileSize + state.height / 2;

      if (tileImg.complete && tileImg.naturalWidth !== 0) {
        ctx.drawImage(tileImg, px, py, scaledTileSize, scaledTileSize);
        tilesRendered++;
      }
    }
  }
  document.getElementById('stat-tiles').textContent = `${tilesRendered} tiles`;

  // 2. Query Quadtree for Nodes inside current screen bounds
  const tl = screenToCoord(0, 0);
  const br = screenToCoord(state.width, state.height);
  const viewRange = {
    minX: Math.min(tl.lon, br.lon),
    maxX: Math.max(tl.lon, br.lon),
    minY: Math.min(tl.lat, br.lat),
    maxY: Math.max(tl.lat, br.lat)
  };

  const visibleNodes = quadtree.query(viewRange);
  const visibleSet = new Set(visibleNodes.map(n => n.id));
  document.getElementById('stat-culled').textContent = `${graphNodes.length - visibleNodes.length} nodes`;

  // 3. Draw Road Vectors
  ctx.strokeStyle = "rgba(14, 165, 233, 0.45)";
  ctx.lineWidth = Math.max(2.0, (state.zoom - 12) * 1.5);
  ctx.beginPath();
  for (let e of graphEdges) {
    if (visibleSet.has(e.u) || visibleSet.has(e.v)) {
      const p1 = coordToScreen(nodeMap.get(e.u).lat, nodeMap.get(e.u).lon);
      const p2 = coordToScreen(nodeMap.get(e.v).lat, nodeMap.get(e.v).lon);
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
    }
  }
  ctx.stroke();

  // 4. Draw A* Search Explored Wavefront
  if (exploredSet.size > 0 && activeRoute) {
    ctx.fillStyle = "rgba(56, 189, 248, 0.35)";
    for (let nid of exploredSet) {
      if (visibleSet.has(nid)) {
        const n = nodeMap.get(nid);
        const pt = coordToScreen(n.lat, n.lon);
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, 4.5, 0, Math.PI * 2);
        ctx.fill();
      }
    }
  }

  // 5. Draw Optimal Driving Route
  if (activeRoute) {
    ctx.strokeStyle = "#0284c7";
    ctx.lineWidth = 6;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.shadowColor = "#0284c7";
    ctx.shadowBlur = 14;
    ctx.beginPath();
    for (let i = 0; i < activeRoute.length; i++) {
      const pt = coordToScreen(activeRoute[i].lat, activeRoute[i].lon);
      if (i === 0) ctx.moveTo(pt.x, pt.y);
      else ctx.lineTo(pt.x, pt.y);
    }
    ctx.stroke();
    ctx.shadowBlur = 0;
  }

  // 6. Draw Intersections & Labels
  for (let n of visibleNodes) {
    const pt = coordToScreen(n.lat, n.lon);

    if (startNode && startNode.id === n.id) {
      ctx.fillStyle = "#10b981";
      ctx.beginPath(); ctx.arc(pt.x, pt.y, 8, 0, Math.PI * 2); ctx.fill();
      ctx.font = "bold 11px system-ui";
      ctx.fillText("START", pt.x + 12, pt.y + 4);
    } else if (goalNode && goalNode.id === n.id) {
      ctx.fillStyle = "#ef4444";
      ctx.beginPath(); ctx.arc(pt.x, pt.y, 8, 0, Math.PI * 2); ctx.fill();
      ctx.font = "bold 11px system-ui";
      ctx.fillText("DEST", pt.x + 12, pt.y + 4);
    } else if (n.name && state.zoom > 15) {
      ctx.fillStyle = "#f59e0b";
      ctx.beginPath(); ctx.arc(pt.x, pt.y, 3.5, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = "#1e293b";
      ctx.font = "11px system-ui";
      ctx.fillText(n.name, pt.x + 6, pt.y + 3);
    }
  }

  requestAnimationFrame(render);
}

/**
 * 9. INTERACTION CONTROLLER: PAN, ZOOM, AND ROUTING
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
  }
});

window.addEventListener('mousemove', e => {
  if (isDrag) {
    const dx = e.clientX - startX;
    const dy = e.clientY - startY;
    if (Math.hypot(dx, dy) > 4) dragMoved = true;

    const curTileX = lon2tile(state.lon, state.zoom);
    const curTileY = lat2tile(state.lat, state.zoom);

    const newTileX = curTileX - dx / TILE_SIZE;
    const newTileY = curTileY - dy / TILE_SIZE;

    state.lon = tile2lon(newTileX, state.zoom);
    state.lat = tile2lat(newTileY, state.zoom);

    startX = e.clientX;
    startY = e.clientY;
  }
});

window.addEventListener('mouseup', () => isDrag = false);

canvas.addEventListener('wheel', e => {
  e.preventDefault();
  const zoomFactor = e.deltaY < 0 ? 0.25 : -0.25;
  state.zoom = Math.max(3, Math.min(19, state.zoom + zoomFactor));
});

canvas.addEventListener('click', e => {
  if (dragMoved) return;

  const clickCoord = screenToCoord(e.clientX, e.clientY);
  let nearest = null;
  let minDist = Infinity;

  for (let n of graphNodes) {
    const d = Math.hypot(n.lon - clickCoord.lon, n.lat - clickCoord.lat);
    if (d < minDist) {
      minDist = d;
      nearest = n;
    }
  }

  if (nearest) {
    if (!startNode || (startNode && goalNode)) {
      startNode = nearest;
      goalNode = null;
      activeRoute = null;
      exploredSet.clear();
    } else {
      goalNode = nearest;
      activeRoute = runAStar(startNode.id, goalNode.id);
    }
  }
});

/**
 * 10. GLOBAL SEARCH
 */
const searchInput = document.getElementById('global-search');
const suggestions = document.getElementById('suggestions');
let searchDebounce;

searchInput.addEventListener('input', e => {
  clearTimeout(searchDebounce);
  const q = e.target.value.trim();
  suggestions.innerHTML = "";
  if (q.length < 2) return;

  searchDebounce = setTimeout(async () => {
    try {
      const res = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(q)}&format=json&limit=5`);
      const results = await res.json();

      suggestions.innerHTML = "";
      results.forEach(item => {
        const li = document.createElement('li');
        li.innerHTML = `<span>${item.display_name.split(',').slice(0, 3).join(',')}</span><span class="tag">${item.type}</span>`;
        li.onclick = () => {
          state.lat = parseFloat(item.lat);
          state.lon = parseFloat(item.lon);
          state.zoom = 15.8;
          suggestions.innerHTML = "";
          searchInput.value = item.display_name.split(',')[0];
          startNode = null;
          goalNode = null;
          activeRoute = null;
          fetchVectorsForCurrentView();
        };
        suggestions.appendChild(li);
      });
    } catch (err) {
      console.warn("Geocoding lookup error", err);
    }
  }, 350);
});

// Controls
document.getElementById('btn-sync').onclick = () => fetchVectorsForCurrentView();
document.getElementById('btn-clear').onclick = () => {
  startNode = null;
  goalNode = null;
  activeRoute = null;
  exploredSet.clear();
  document.getElementById('stat-explored').textContent = 0;
  document.getElementById('stat-cost').textContent = "0 km";
};

// Start application
fetchVectorsForCurrentView();
render();
</script>
</body>
</html>
"""

components.html(html_engine, height=950, scrolling=False)
