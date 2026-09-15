import json
import math
import random
import requests
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="AuraNav — Real World DSA Vector Engine",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Streamlit UI styling
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp {
        background-color: #060913;
        color: #e2e8f0;
    }
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. MERCATOR PROJECTION & GEOCODING
# ==========================================

def lat_lon_to_mercator(lat: float, lon: float):
    """Converts geographic WGS84 (Lat, Lon) to 2D Cartesian Web Mercator coordinates."""
    r = 6378137.0
    x = r * math.radians(lon)
    lat_rad = math.radians(max(min(lat, 85.0511), -85.0511))
    y = r * math.log(math.tan((math.pi / 4.0) + (lat_rad / 2.0)))
    return x, y

def geocode_location(query: str):
    """Fetches real-world (lat, lon) coordinates for any location worldwide using Nominatim."""
    headers = {"User-Agent": "AuraNav-Vector-Engine/2.0 (student-project)"}
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": query, "format": "json", "limit": 1}
    try:
        res = requests.get(url, params=params, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if len(data) > 0:
                item = data[0]
                return float(item["lat"]), float(item["lon"]), item.get("display_name", query)
    except Exception as e:
        st.sidebar.error(f"Geocoding error: {e}")
    return None, None, None

def fetch_real_world_vectors(lat: float, lon: float, radius_km: float = 1.0):
    """Queries OpenStreetMap Overpass vector API for road vectors around coordinates."""
    radius_deg = (radius_km / 111.0) * 0.95
    south = lat - radius_deg
    north = lat + radius_deg
    west = lon - (radius_deg * 1.3)
    east = lon + (radius_deg * 1.3)

    overpass_query = f"""
    [out:json][timeout:20];
    (
      way["highway"~"primary|secondary|tertiary|residential|trunk|motorway|unclassified"]({south},{west},{north},{east});
    );
    out body;
    >;
    out skel qt;
    """
    
    headers = {"User-Agent": "AuraNav-Vector-Engine/2.0"}
    endpoints = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
    ]
    
    for ep in endpoints:
        try:
            res = requests.post(ep, data={"data": overpass_query}, headers=headers, timeout=15)
            if res.status_code == 200:
                data = res.json()
                if "elements" in data and len(data["elements"]) > 0:
                    return data
        except Exception:
            continue
    return None

# ==========================================
# 2. SIDEBAR CONTROLS (GLOBAL SEARCH)
# ==========================================

st.sidebar.markdown("### 🧭 AuraNav Global Search")

# Maintain current place in session state
if "active_place" not in st.session_state:
    st.session_state.active_place = "Park Street, Kolkata"

# Custom input takes absolute priority
typed_input = st.sidebar.text_input(
    "Search any city, neighborhood, or landmark:",
    value=st.session_state.active_place,
    help="Examples: Park Street Kolkata, Shibuya Tokyo, Connaught Place Delhi, Times Square NYC"
)

radius_select = st.sidebar.slider("Vector Radius (km):", min_value=0.5, max_value=2.5, value=1.0, step=0.25)
load_btn = st.sidebar.button("🚀 Fetch & Build Vector Graph", type="primary")

st.sidebar.markdown("---")
st.sidebar.markdown("**Quick Preset Shortcuts:**")
preset_cols = st.sidebar.columns(2)
if preset_cols[0].button("Kolkata"):
    st.session_state.active_place = "Park Street, Kolkata"
    st.rerun()
if preset_cols[1].button("Delhi"):
    st.session_state.active_place = "Connaught Place, New Delhi"
    st.rerun()
if preset_cols[0].button("Mumbai"):
    st.session_state.active_place = "Marine Drive, Mumbai"
    st.rerun()
if preset_cols[1].button("Tokyo"):
    st.session_state.active_place = "Shibuya, Tokyo"
    st.rerun()

if load_btn and typed_input:
    st.session_state.active_place = typed_input

# ==========================================
# 3. BUILD VECTOR GRAPH & PROJECT DATA
# ==========================================

with st.spinner(f"Fetching vectors for '{st.session_state.active_place}'..."):
    center_lat, center_lon, display_label = geocode_location(st.session_state.active_place)
    
    if center_lat is None:
        st.sidebar.error(f"Could not find coordinates for '{st.session_state.active_place}'. Try a more specific name like 'Park Street, Kolkata'.")
        center_lat, center_lon = 22.5511, 88.3526  # Default fallback: Park Street, Kolkata
        display_label = "Park Street, Kolkata, West Bengal, India"
    else:
        st.sidebar.success(f"📍 Loaded: {display_label[:40]}...")

    osm_data = fetch_real_world_vectors(center_lat, center_lon, radius_km=radius_select)

nodes = []
edges = []
pois = []
node_id_map = {}

if osm_data and "elements" in osm_data:
    raw_nodes = {}
    for el in osm_data["elements"]:
        if el["type"] == "node":
            raw_nodes[el["id"]] = (el["lat"], el["lon"])

    cx, cy = lat_lon_to_mercator(center_lat, center_lon)
    internal_id = 0
    scale = 0.85

    for el in osm_data["elements"]:
        if el["type"] == "way" and "nodes" in el:
            way_nodes = el["nodes"]
            street_name = el.get("tags", {}).get("name", None)

            prev_idx = None
            for nid in way_nodes:
                if nid in raw_nodes:
                    if nid not in node_id_map:
                        lat, lon = raw_nodes[nid]
                        mx, my = lat_lon_to_mercator(lat, lon)
                        px = round((mx - cx) * scale, 1)
                        py = round(-(my - cy) * scale, 1)

                        n_obj = {
                            "id": internal_id,
                            "x": px,
                            "y": py,
                            "name": street_name if (street_name and random.random() > 0.85) else None
                        }
                        nodes.append(n_obj)
                        node_id_map[nid] = internal_id
                        
                        if n_obj["name"] and len(pois) < 40:
                            pois.append({"id": internal_id, "name": n_obj["name"], "x": px, "y": py})
                        
                        curr_idx = internal_id
                        internal_id += 1
                    else:
                        curr_idx = node_id_map[nid]

                    if prev_idx is not None and prev_idx != curr_idx:
                        u = nodes[prev_idx]
                        v = nodes[curr_idx]
                        dist = round(math.hypot(u["x"] - v["x"], u["y"] - v["y"]), 1)
                        edges.append({"u": prev_idx, "v": curr_idx, "cost": dist})

                    prev_idx = curr_idx

# Fallback graph in case Overpass is throttled
if len(nodes) < 15:
    st.sidebar.warning("Vector API traffic heavy, generating fallback mesh for current coordinates.")
    nodes = []
    edges = []
    pois = []
    STEP = 90
    grid_size = 20
    idx = 0
    for r in range(grid_size):
        for c in range(grid_size):
            px = (c - grid_size // 2) * STEP + random.uniform(-15, 15)
            py = (r - grid_size // 2) * STEP + random.uniform(-15, 15)
            n_obj = {"id": idx, "x": px, "y": py, "name": None}
            nodes.append(n_obj)
            idx += 1

    for r in range(grid_size):
        for c in range(grid_size):
            curr = r * grid_size + c
            if c + 1 < grid_size:
                nxt = r * grid_size + (c + 1)
                edges.append({"u": curr, "v": nxt, "cost": STEP})
            if r + 1 < grid_size:
                nxt = (r + 1) * grid_size + c
                edges.append({"u": curr, "v": nxt, "cost": STEP})

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Vertices (Intersections):** `{len(nodes)}`")
st.sidebar.markdown(f"**Edges (Road Segments):** `{len(edges)}`")
st.sidebar.markdown(f"**Indexed Streets:** `{len(pois)}`")

# ==========================================
# 4. HIGH-PERFORMANCE INTERACTIVE CANVAS
# ==========================================

payload = json.dumps({
    "locationName": display_label if 'display_label' in locals() else st.session_state.active_place,
    "nodes": nodes,
    "edges": edges,
    "pois": pois
})

html_app = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #060913;
    color: #e2e8f0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    overflow: hidden;
    height: 100vh;
    width: 100vw;
  }}
  #canvas {{
    width: 100vw;
    height: 100vh;
    display: block;
    cursor: grab;
  }}
  #canvas:active {{ cursor: grabbing; }}

  .glass {{
    position: absolute;
    background: rgba(15, 23, 42, 0.85);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 12px;
    box-shadow: 0 16px 36px rgba(0, 0, 0, 0.55);
    z-index: 10;
  }}

  .brand {{
    top: 16px;
    left: 16px;
    padding: 10px 16px;
    display: flex;
    align-items: center;
    gap: 10px;
  }}
  .brand-logo {{
    width: 10px;
    height: 10px;
    background: #38bdf8;
    border-radius: 50%;
    box-shadow: 0 0 10px #38bdf8;
  }}
  .brand-title {{
    font-weight: 800;
    letter-spacing: 1.2px;
    font-size: 13px;
    color: #f8fafc;
  }}
  .brand-loc {{
    font-size: 11px;
    color: #38bdf8;
    max-width: 250px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}

  .search-container {{
    top: 72px;
    left: 16px;
    width: 320px;
  }}
  .search-bar {{
    display: flex;
    align-items: center;
    padding: 10px 14px;
    gap: 10px;
  }}
  #search-input {{
    background: transparent;
    border: none;
    outline: none;
    color: #fff;
    font-size: 13px;
    width: 100%;
  }}
  #suggestions {{
    list-style: none;
    max-height: 200px;
    overflow-y: auto;
  }}
  #suggestions li {{
    padding: 9px 14px;
    font-size: 12px;
    cursor: pointer;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    display: flex;
    justify-content: space-between;
  }}
  #suggestions li:hover {{
    background: rgba(56, 189, 248, 0.15);
    color: #38bdf8;
  }}

  .telemetry {{
    top: 16px;
    right: 16px;
    width: 280px;
    padding: 16px;
    font-size: 12px;
  }}
  .sec-title {{
    color: #38bdf8;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-size: 11px;
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
  }}
  .stat-row {{
    display: flex;
    justify-content: space-between;
    margin-bottom: 5px;
    color: #94a3b8;
  }}
  .stat-row span:last-child {{
    color: #f8fafc;
    font-family: monospace;
    font-weight: 600;
  }}
  .divider {{
    height: 1px;
    background: rgba(255, 255, 255, 0.08);
    margin: 8px 0;
  }}

  .bottom-dock {{
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    padding: 6px 12px;
    display: flex;
    gap: 8px;
  }}
  button {{
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.15);
    color: #f8fafc;
    padding: 7px 14px;
    border-radius: 8px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.2s;
  }}
  button:hover {{
    background: #38bdf8;
    color: #030712;
  }}

  .instructions {{
    position: absolute;
    bottom: 20px;
    left: 16px;
    font-size: 11px;
    color: #64748b;
    line-height: 1.5;
  }}
</style>
</head>
<body>
<canvas id="canvas"></canvas>

<div class="glass brand">
  <div class="brand-logo"></div>
  <div class="brand-title">AURANAV</div>
  <div class="brand-loc" id="loc-name">Real-World Map</div>
</div>

<div class="glass search-container">
  <div class="search-bar">
    <span style="color:#38bdf8">⚲</span>
    <input type="text" id="search-input" placeholder="Search Street/POI (Trie)..." autocomplete="off" />
  </div>
  <ul id="suggestions"></ul>
</div>

<div class="glass telemetry">
  <div class="sec-title">
    <span>Spatial Index</span>
    <span style="color:#34d399">ONLINE</span>
  </div>
  <div class="stat-row"><span>Graph Scale</span><span id="stat-graph">0V / 0E</span></div>
  <div class="stat-row"><span>Quadtree Culled</span><span id="stat-culled">0</span></div>
  <div class="stat-row"><span>Rendered Nodes</span><span id="stat-rendered">0</span></div>
  <div class="divider"></div>
  <div class="sec-title">A* Pathfinding</div>
  <div class="stat-row"><span>Heap Operations</span><span id="stat-explored">0</span></div>
  <div class="stat-row"><span>Optimal Cost</span><span id="stat-cost">0 km</span></div>
</div>

<div class="glass bottom-dock">
  <button id="btn-recenter">Recenter Map</button>
  <button id="btn-reset">Clear Path</button>
</div>

<div class="instructions">
  • Click any 2 intersections to calculate A* shortest driving route.<br>
  • Left-click drag to pan | Scroll to zoom in/out.
</div>

<script>
const WORLD = {payload};
document.getElementById('loc-name').textContent = WORLD.locationName;

// Min-Heap for A* Search
class MinHeap {{
  constructor(scoreFn) {{
    this.tree = [];
    this.score = scoreFn;
  }}
  push(val) {{
    this.tree.push(val);
    this.up(this.tree.length - 1);
  }}
  pop() {{
    const min = this.tree[0];
    const end = this.tree.pop();
    if (this.tree.length > 0) {{
      this.tree[0] = end;
      this.down(0);
    }}
    return min;
  }}
  isEmpty() {{ return this.tree.length === 0; }}
  up(i) {{
    const node = this.tree[i];
    const val = this.score(node);
    while (i > 0) {{
      const p = Math.floor((i - 1) / 2);
      if (val >= this.score(this.tree[p])) break;
      this.tree[i] = this.tree[p];
      i = p;
    }}
    this.tree[i] = node;
  }}
  down(i) {{
    const len = this.tree.length;
    const node = this.tree[i];
    const val = this.score(node);
    while (true) {{
      let left = 2 * i + 1, right = 2 * i + 2, swap = null;
      let leftVal, rightVal;
      if (left < len) {{
        leftVal = this.score(this.tree[left]);
        if (leftVal < val) swap = left;
      }}
      if (right < len) {{
        rightVal = this.score(this.tree[right]);
        if ((swap === null && rightVal < val) || (swap !== null && rightVal < leftVal)) swap = right;
      }}
      if (swap === null) break;
      this.tree[i] = this.tree[swap];
      i = swap;
    }}
    this.tree[i] = node;
  }}
}}

// Graph Setup
const nodeMap = new Map();
const adj = new Map();
WORLD.nodes.forEach(n => {{
  nodeMap.set(n.id, n);
  adj.set(n.id, []);
}});
WORLD.edges.forEach(e => {{
  adj.get(e.u).push({{ to: e.v, cost: e.cost }});
  adj.get(e.v).push({{ to: e.u, cost: e.cost }});
}});

// Trie for Autocomplete
class POITrie {{
  constructor() {{ this.root = {{ c: {{}}, pois: [] }}; }}
  insert(word, obj) {{
    let cur = this.root;
    for (let ch of word.toLowerCase()) {{
      if (!cur.c[ch]) cur.c[ch] = {{ c: {{}}, pois: [] }};
      cur = cur.c[ch];
      cur.pois.push(obj);
    }}
  }}
  search(prefix) {{
    let cur = this.root;
    for (let ch of prefix.toLowerCase()) {{
      if (!cur.c[ch]) return [];
      cur = cur.c[ch];
    }}
    return cur.pois;
  }}
}}
const trie = new POITrie();
WORLD.pois.forEach(p => trie.insert(p.name, p));

// Merge Sort
function mergeSort(arr, keyFn) {{
  if (arr.length <= 1) return arr;
  const mid = Math.floor(arr.length / 2);
  const left = mergeSort(arr.slice(0, mid), keyFn);
  const right = mergeSort(arr.slice(mid), keyFn);
  let res = [], i = 0, j = 0;
  while (i < left.length && j < right.length) {{
    if (keyFn(left[i]) <= keyFn(right[j])) res.push(left[i++]);
    else res.push(right[j++]);
  }}
  return res.concat(left.slice(i)).concat(right.slice(j));
}}

// Canvas & Camera Matrix
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
let camera = {{ x: 0, y: 0, zoom: 1.0 }};
let isDrag = false;
let startPan = {{ x: 0, y: 0 }};

function resize() {{
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}}
window.addEventListener('resize', resize);
resize();

// Center camera on coordinate center (0,0)
camera.x = canvas.width / 2;
camera.y = canvas.height / 2;

function toScreen(wx, wy) {{
  return {{ x: wx * camera.zoom + camera.x, y: wy * camera.zoom + camera.y }};
}}
function toWorld(sx, sy) {{
  return {{ x: (sx - camera.x) / camera.zoom, y: (sy - camera.y) / camera.zoom }};
}}

let startNode = null;
let goalNode = null;
let activeRoute = null;
let exploredList = [];

// A* Pathfinding Engine
function runAStar(srcId, dstId) {{
  const g = new Map();
  const f = new Map();
  const parent = new Map();
  exploredList = [];

  WORLD.nodes.forEach(n => {{
    g.set(n.id, Infinity);
    f.set(n.id, Infinity);
  }});

  g.set(srcId, 0);
  const target = nodeMap.get(dstId);
  const h = (nid) => {{
    const node = nodeMap.get(nid);
    return Math.hypot(node.x - target.x, node.y - target.y);
  }};
  f.set(srcId, h(srcId));

  const heap = new MinHeap(id => f.get(id));
  heap.push(srcId);

  while (!heap.isEmpty()) {{
    const curr = heap.pop();
    exploredList.push(curr);

    if (curr === dstId) {{
      const path = [];
      let temp = dstId;
      while (parent.has(temp)) {{
        path.unshift(nodeMap.get(temp));
        temp = parent.get(temp);
      }}
      path.unshift(nodeMap.get(srcId));
      document.getElementById('stat-explored').textContent = exploredList.length;
      document.getElementById('stat-cost').textContent = (g.get(dstId) / 1000).toFixed(2) + " km";
      return path;
    }}

    for (let edge of adj.get(curr)) {{
      const nxt = edge.to;
      const tentative = g.get(curr) + edge.cost;
      if (tentative < g.get(nxt)) {{
        parent.set(nxt, curr);
        g.set(nxt, tentative);
        f.set(nxt, tentative + h(nxt));
        heap.push(nxt);
      }}
    }}
  }}
  return null;
}}

// Continuous Render Loop
function render() {{
  ctx.fillStyle = "#060913";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  const tl = toWorld(0, 0);
  const br = toWorld(canvas.width, canvas.height);
  const isVisible = (n) => n.x >= tl.x - 40 && n.x <= br.x + 40 && n.y >= tl.y - 40 && n.y <= br.y + 40;

  let drawnCount = 0;
  const renderedSet = new Set();
  for (let n of WORLD.nodes) {{
    if (isVisible(n)) {{
      renderedSet.add(n.id);
      drawnCount++;
    }}
  }}

  document.getElementById('stat-graph').textContent = `${{WORLD.nodes.length}}V / ${{WORLD.edges.length}}E`;
  document.getElementById('stat-rendered').textContent = drawnCount;
  document.getElementById('stat-culled').textContent = `${{WORLD.nodes.length - drawnCount}} culled`;

  // Draw Real-world Road Vectors
  ctx.strokeStyle = "rgba(148, 163, 184, 0.22)";
  ctx.lineWidth = Math.max(1.5, 2.2 * camera.zoom);
  ctx.beginPath();
  for (let e of WORLD.edges) {{
    if (renderedSet.has(e.u) || renderedSet.has(e.v)) {{
      const u = nodeMap.get(e.u);
      const v = nodeMap.get(e.v);
      const p1 = toScreen(u.x, u.y);
      const p2 = toScreen(v.x, v.y);
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
    }}
  }}
  ctx.stroke();

  // Draw Explored Exploration Wave (A*)
  if (exploredList.length > 0 && activeRoute) {{
    ctx.fillStyle = "rgba(56, 189, 248, 0.25)";
    for (let id of exploredList) {{
      if (renderedSet.has(id)) {{
        const pt = toScreen(nodeMap.get(id).x, nodeMap.get(id).y);
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, 4 * camera.zoom, 0, Math.PI * 2);
        ctx.fill();
      }}
    }}
  }}

  // Draw Calculated Shortest Path
  if (activeRoute) {{
    ctx.strokeStyle = "#38bdf8";
    ctx.lineWidth = Math.max(3.5, 5 * camera.zoom);
    ctx.lineCap = "round";
    ctx.beginPath();
    for (let i = 0; i < activeRoute.length; i++) {{
      const pt = toScreen(activeRoute[i].x, activeRoute[i].y);
      if (i === 0) ctx.moveTo(pt.x, pt.y);
      else ctx.lineTo(pt.x, pt.y);
    }}
    ctx.stroke();
  }}

  // Draw Intersections and Landmark Labels
  for (let id of renderedSet) {{
    const n = nodeMap.get(id);
    const pt = toScreen(n.x, n.y);

    if (startNode && startNode.id === n.id) {{
      ctx.fillStyle = "#34d399";
      ctx.beginPath(); ctx.arc(pt.x, pt.y, 8, 0, Math.PI * 2); ctx.fill();
      ctx.font = "bold 11px system-ui";
      ctx.fillText("START", pt.x + 10, pt.y + 4);
    }} else if (goalNode && goalNode.id === n.id) {{
      ctx.fillStyle = "#f87171";
      ctx.beginPath(); ctx.arc(pt.x, pt.y, 8, 0, Math.PI * 2); ctx.fill();
      ctx.font = "bold 11px system-ui";
      ctx.fillText("DEST", pt.x + 10, pt.y + 4);
    }} else if (n.name) {{
      ctx.fillStyle = "#fbbf24";
      ctx.beginPath(); ctx.arc(pt.x, pt.y, 4 * camera.zoom, 0, Math.PI * 2); ctx.fill();
      if (camera.zoom > 0.6) {{
        ctx.fillStyle = "#cbd5e1";
        ctx.font = "11px system-ui";
        ctx.fillText(n.name, pt.x + 8, pt.y + 3);
      }}
    }}
  }}

  requestAnimationFrame(render);
}}

// Pan & Zoom Controls
canvas.addEventListener('mousedown', e => {{
  if (e.button === 0) {{
    isDrag = true;
    startPan = {{ x: e.clientX - camera.x, y: e.clientY - camera.y }};
  }}
}});
window.addEventListener('mousemove', e => {{
  if (isDrag) {{
    camera.x = e.clientX - startPan.x;
    camera.y = e.clientY - startPan.y;
  }}
}});
window.addEventListener('mouseup', () => isDrag = false);

canvas.addEventListener('wheel', e => {{
  e.preventDefault();
  const z = e.deltaY < 0 ? 1.15 : 1 / 1.15;
  const m = toWorld(e.clientX, e.clientY);
  camera.zoom = Math.max(0.2, Math.min(camera.zoom * z, 5.0));
  camera.x = e.clientX - m.x * camera.zoom;
  camera.y = e.clientY - m.y * camera.zoom;
}});

// Click to Route with A*
canvas.addEventListener('click', e => {{
  if (Math.hypot(e.movementX, e.movementY) > 4) return;
  const click = toWorld(e.clientX, e.clientY);
  let nearest = null;
  let minDist = 35 / camera.zoom;

  for (let n of WORLD.nodes) {{
    const d = Math.hypot(n.x - click.x, n.y - click.y);
    if (d < minDist) {{
      minDist = d;
      nearest = n;
    }}
  }}

  if (nearest) {{
    if (!startNode || (startNode && goalNode)) {{
      startNode = nearest;
      goalNode = null;
      activeRoute = null;
      exploredList = [];
    }} else {{
      goalNode = nearest;
      activeRoute = runAStar(startNode.id, goalNode.id);
    }}
  }}
}});

// Autocomplete with Trie + Merge Sort
const search = document.getElementById('search-input');
const suggestions = document.getElementById('suggestions');

search.addEventListener('input', e => {{
  const val = e.target.value.trim();
  suggestions.innerHTML = "";
  if (!val) return;

  const matches = trie.search(val);
  const center = toWorld(canvas.width / 2, canvas.height / 2);
  const sorted = mergeSort(matches, a => Math.hypot(a.x - center.x, a.y - center.y));

  sorted.slice(0, 6).forEach(p => {{
    const li = document.createElement('li');
    li.innerHTML = `<span>${{p.name}}</span><span style="color:#38bdf8">STREET</span>`;
    li.onclick = () => {{
      camera.x = canvas.width / 2 - p.x * camera.zoom;
      camera.y = canvas.height / 2 - p.y * camera.zoom;
      startNode = nodeMap.get(p.id);
      goalNode = null;
      activeRoute = null;
      suggestions.innerHTML = "";
      search.value = p.name;
    }};
    suggestions.appendChild(li);
  }});
}});

document.getElementById('btn-reset').onclick = () => {{
  startNode = null;
  goalNode = null;
  activeRoute = null;
  exploredList = [];
  document.getElementById('stat-explored').textContent = 0;
  document.getElementById('stat-cost').textContent = "0 km";
}};

document.getElementById('btn-recenter').onclick = () => {{
  camera.x = canvas.width / 2;
  camera.y = canvas.height / 2;
  camera.zoom = 1.0;
}};

render();
</script>
</body>
</html>
"""

components.html(html_app, height=880, scrolling=False)
