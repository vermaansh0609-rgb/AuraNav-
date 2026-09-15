import json
import math
import urllib.parse
import requests
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="AuraNav — Real-World DSA Navigation Engine",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Streamlit viewport container reset for borderless HUD
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        max-width: 100% !important;
    }
    iframe {
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)

PRESETS = {
    "Manhattan Core (NYC)": {"lat": 40.7549, "lon": -73.9840, "radius": 750},
    "Paris (Eiffel Tower & Seine)": {"lat": 48.8584, "lon": 2.2945, "radius": 750},
    "Tokyo (Shibuya Crossing)": {"lat": 35.6595, "lon": 139.7005, "radius": 700},
    "London (Westminster & Thames)": {"lat": 51.5007, "lon": -0.1246, "radius": 750},
    "Mumbai (Marine Drive & Nariman Pt)": {"lat": 18.9220, "lon": 72.8240, "radius": 750},
    "Rome (Colosseum & Historic Core)": {"lat": 41.8902, "lon": 12.4922, "radius": 700},
    "San Francisco (Financial & Embarcadero)": {"lat": 37.7937, "lon": -122.3965, "radius": 750}
}

@st.cache_data(show_spinner=False, ttl=3600)
def fetch_real_world_osm_vectors(lat: float, lon: float, radius: int = 750):
    """
    Queries OpenStreetMap Overpass vector endpoint to extract real street geometry,
    nodes (intersections), and highway segments without pre-rendered tiles.
    """
    overpass_url = "https://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json][timeout:25];
    (
      way["highway"~"motorway|trunk|primary|secondary|tertiary|residential|service|unclassified|living_street"](around:{radius},{lat},{lon});
    );
    out body;
    >;
    out skel qt;
    """
    
    headers = {
        "User-Agent": "AuraNav-Vector-Engine/1.0 (Educational DSA Cartography Project)"
    }
    
    try:
        response = requests.post(overpass_url, data={"data": overpass_query}, headers=headers, timeout=28)
        if response.status_code != 200:
            return None, f"Overpass server responded with status code: {response.status_code}"
        data = response.json()
        return data, None
    except Exception as e:
        return None, str(e)

def geocode_location(query_str: str):
    """
    Resolves arbitrary natural language location queries into latitude/longitude pairs.
    """
    if not query_str:
        return None
    encoded = urllib.parse.quote(query_str.strip())
    url = f"https://nominatim.openstreetmap.org/search?q={encoded}&format=json&limit=1"
    headers = {
        "User-Agent": "AuraNav-Geocoding-Engine/1.0"
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            parsed = res.json()
            if parsed and len(parsed) > 0:
                item = parsed[0]
                return {
                    "display_name": item.get("display_name", query_str),
                    "lat": float(item["lat"]),
                    "lon": float(item["lon"])
                }
    except Exception:
        pass
    return None

def build_vector_graph_from_osm(osm_data, origin_lat, origin_lon):
    """
    Projects latitude/longitude into local 2D Metric Cartesian coordinates
    using the Web Mercator projection and constructs graph vertices & edges.
    """
    elements = osm_data.get("elements", [])
    raw_nodes = {}
    raw_ways = []
    
    for el in elements:
        t = el.get("type")
        if t == "node":
            raw_nodes[el["id"]] = (el["lat"], el["lon"])
        elif t == "way":
            raw_ways.append(el)
            
    if not raw_nodes or not raw_ways:
        return None

    # Equirectangular / Local Mercator Projection centered at query origin
    lat_rad = math.radians(origin_lat)
    meters_per_deg_lat = 111132.92 - 559.82 * math.cos(2 * lat_rad) + 1.175 * math.cos(4 * lat_rad)
    meters_per_deg_lon = 111412.84 * math.cos(lat_rad) - 93.5 * math.cos(3 * lat_rad)

    nodes_list = []
    node_id_map = {}
    used_node_ids = set()

    for w in raw_ways:
        for nid in w.get("nodes", []):
            used_node_ids.add(nid)

    # Transform coordinates
    for nid in used_node_ids:
        if nid in raw_nodes:
            n_lat, n_lon = raw_nodes[nid]
            # World coordinates with origin (0, 0) centered at the queried spot
            wx = (n_lon - origin_lon) * meters_per_deg_lon
            wy = -(n_lat - origin_lat) * meters_per_deg_lat
            
            node_record = {
                "id": nid,
                "x": round(wx, 2),
                "y": round(wy, 2),
                "lat": n_lat,
                "lon": n_lon,
                "name": None
            }
            nodes_list.append(node_record)
            node_id_map[nid] = node_record

    edges_list = []
    pois_list = []
    registered_names = set()

    # Build road topology and collect named segments for Trie
    for w in raw_ways:
        way_nodes = w.get("nodes", [])
        tags = w.get("tags", {})
        street_name = tags.get("name")
        highway_type = tags.get("highway", "residential")

        # Associate landmark name to first available node in the way
        if street_name and street_name not in registered_names and len(way_nodes) > 0:
            first_nid = way_nodes[0]
            if first_nid in node_id_map:
                node_id_map[first_nid]["name"] = street_name
                pois_list.append({
                    "id": first_nid,
                    "name": street_name,
                    "x": node_id_map[first_nid]["x"],
                    "y": node_id_map[first_nid]["y"]
                })
                registered_names.add(street_name)

        # Connect chain of nodes as road segments
        for i in range(len(way_nodes) - 1):
            u_id = way_nodes[i]
            v_id = way_nodes[i + 1]
            if u_id in node_id_map and v_id in node_id_map:
                u = node_id_map[u_id]
                v = node_id_map[v_id]
                dist = math.hypot(u["x"] - v["x"], u["y"] - v["y"])
                edges_list.append({
                    "u": u_id,
                    "v": v_id,
                    "cost": round(dist, 2),
                    "type": highway_type,
                    "name": street_name
                })

    return {
        "nodes": nodes_list,
        "edges": edges_list,
        "pois": pois_list[:60]
    }

if "current_location" not in st.session_state:
    st.session_state.current_location = "Manhattan Core (NYC)"
if "geo_coords" not in st.session_state:
    st.session_state.geo_coords = PRESETS["Manhattan Core (NYC)"]
if "custom_error" not in st.session_state:
    st.session_state.custom_error = None

# Floating control bar rendered natively in Streamlit for switching real cities
with st.sidebar:
    st.markdown("### 🧭 AuraNav Controller")
    st.caption("Custom Vector Engine & DSA Network")

    selected_preset = st.selectbox(
        "World City Presets",
        list(PRESETS.keys()),
        index=list(PRESETS.keys()).index(st.session_state.current_location) if st.session_state.current_location in PRESETS else 0
    )

    custom_search = st.text_input(
        "Or Search Any Global Location",
        placeholder="e.g. Ginza Tokyo, Venice Italy, Taj Mahal...",
        help="Queries Nominatim OpenStreetMap geocoder to download real street graphs anywhere on the planet."
    )

    btn_load = st.button("Fetch & Build Vector Graph", use_container_width=True)

    if btn_load:
        if custom_search.strip():
            with st.spinner(f"Geocoding '{custom_search}'..."):
                geo_res = geocode_location(custom_search)
                if geo_res:
                    st.session_state.current_location = geo_res["display_name"].split(",")[0]
                    st.session_state.geo_coords = {
                        "lat": geo_res["lat"],
                        "lon": geo_res["lon"],
                        "radius": 800
                    }
                    st.session_state.custom_error = None
                    st.rerun()
                else:
                    st.session_state.custom_error = f"Could not find coordinates for: {custom_search}"
        else:
            st.session_state.current_location = selected_preset
            st.session_state.geo_coords = PRESETS[selected_preset]
            st.session_state.custom_error = None
            st.rerun()

    if st.session_state.custom_error:
        st.error(st.session_state.custom_error)

    st.markdown("---")
    st.markdown("""
    **DSA Pipeline in Active Play:**
    * 📐 **Mercator Projection**: Converts $S^2$ spherical Lat/Lon to $\mathbb{R}^2$.
    * 🌲 **Quadtree**: Recursively clips thousands of vectors off-screen.
    * 🔤 **Prefix Trie**: $O(L)$ character-by-character landmark lookup.
    * 📊 **Merge Sort**: Distance-ordered autocomplete ranking.
    * ⚡ **A\* Heuristic Search**: Guided pathing on real-world road networks.
    """)

# Fetch live real-world vector data
coords = st.session_state.geo_coords
raw_osm_payload, fetch_err = fetch_real_world_osm_vectors(coords["lat"], coords["lon"], coords.get("radius", 750))

if fetch_err or not raw_osm_payload:
    st.warning("Public Overpass gateway is rate-limited or busy. Loading Manhattan fallback coordinates...")
    raw_osm_payload, _ = fetch_real_world_osm_vectors(40.7549, -73.9840, 700)

graph_data = build_vector_graph_from_osm(raw_osm_payload, coords["lat"], coords["lon"])

if not graph_data or len(graph_data["nodes"]) == 0:
    st.error("No traversable roads found in this bounding area. Try expanding or picking another city.")
    st.stop()

# Prepare JSON bundle to inject into client canvas engine
client_payload = json.dumps({
    "locationName": st.session_state.current_location,
    "lat": coords["lat"],
    "lon": coords["lon"],
    "nodes": graph_data["nodes"],
    "edges": graph_data["edges"],
    "pois": graph_data["pois"]
})

html_canvas_component = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  :root {{
    --bg: #070a13;
    --panel-bg: rgba(13, 18, 32, 0.85);
    --border: rgba(255, 255, 255, 0.12);
    --accent: #38bdf8;
    --accent-glow: rgba(56, 189, 248, 0.4);
    --text: #f1f5f9;
    --text-muted: #94a3b8;
    --success: #10b981;
    --danger: #f43f5e;
    --warning: #f59e0b;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    overflow: hidden;
    height: 100vh;
    width: 100vw;
    user-select: none;
  }}
  #canvas {{
    width: 100vw;
    height: 100vh;
    display: block;
    cursor: grab;
  }}
  #canvas:active {{ cursor: grabbing; }}

  /* Glassmorphic UI Paneling */
  .hud {{
    position: absolute;
    background: var(--panel-bg);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid var(--border);
    border-radius: 14px;
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.55);
    z-index: 20;
  }}

  /* Top Bar Branding & Live Location */
  .brand-bar {{
    top: 20px;
    left: 20px;
    padding: 10px 18px;
    display: flex;
    align-items: center;
    gap: 12px;
  }}
  .brand-pulse {{
    width: 10px;
    height: 10px;
    background: var(--accent);
    border-radius: 50%;
    box-shadow: 0 0 12px var(--accent);
    animation: pulse 2s infinite ease-in-out;
  }}
  @keyframes pulse {{
    0%, 100% {{ transform: scale(0.9); opacity: 0.8; }}
    50% {{ transform: scale(1.3); opacity: 1; }}
  }}
  .brand-title {{
    font-size: 13px;
    font-weight: 800;
    letter-spacing: 1.5px;
    color: #ffffff;
  }}
  .location-badge {{
    font-size: 11px;
    padding: 3px 8px;
    border-radius: 6px;
    background: rgba(56, 189, 248, 0.15);
    color: var(--accent);
    border: 1px solid rgba(56, 189, 248, 0.25);
    max-width: 240px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}

  /* Search & Street Autocomplete Bar */
  .search-hud {{
    top: 76px;
    left: 20px;
    width: 320px;
  }}
  .input-wrapper {{
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
    align-items: center;
    transition: all 0.15s;
  }}
  #suggestions li:hover {{
    background: rgba(56, 189, 248, 0.18);
    color: var(--accent);
  }}

  /* DSA Telemetry Dashboard */
  .telemetry-hud {{
    top: 20px;
    right: 20px;
    width: 310px;
    padding: 18px;
    font-size: 12px;
  }}
  .telemetry-header {{
    color: var(--accent);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-size: 11px;
    margin-bottom: 10px;
    display: flex;
    justify-content: space-between;
  }}
  .metric-item {{
    display: flex;
    justify-content: space-between;
    margin-bottom: 6px;
    color: var(--text-muted);
  }}
  .metric-item span:last-child {{
    color: var(--text);
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-weight: 600;
  }}
  .divider {{
    height: 1px;
    background: var(--border);
    margin: 10px 0;
  }}

  /* Bottom Controls Toolbar */
  .toolbar-hud {{
    bottom: 24px;
    left: 50%;
    transform: translateX(-50%);
    padding: 6px 10px;
    display: flex;
    gap: 8px;
  }}
  button {{
    background: rgba(255, 255, 255, 0.07);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 7px 14px;
    border-radius: 8px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.2s;
    font-weight: 500;
  }}
  button:hover {{
    background: var(--accent);
    color: #040711;
    box-shadow: 0 0 14px var(--accent-glow);
  }}
  button.active {{
    background: rgba(56, 189, 248, 0.25);
    border-color: var(--accent);
    color: var(--accent);
  }}

  .user-tip {{
    position: absolute;
    bottom: 24px;
    left: 20px;
    font-size: 11px;
    color: #64748b;
    line-height: 1.6;
    pointer-events: none;
  }}
</style>
</head>
<body>

<canvas id="canvas"></canvas>

<!-- Top Branding -->
<div class="hud brand-bar">
  <div class="brand-pulse"></div>
  <div class="brand-title">AURANAV</div>
  <div class="location-badge" id="loc-badge">Manhattan, NY</div>
</div>

<!-- Autocomplete Search -->
<div class="hud search-hud">
  <div class="input-wrapper">
    <span style="color:var(--accent); font-size:14px;">⚲</span>
    <input type="text" id="search-input" placeholder="Search street in active city (Trie)..." autocomplete="off">
  </div>
  <ul id="suggestions"></ul>
</div>

<!-- Telemetry Diagnostics Panel -->
<div class="hud telemetry-hud">
  <div class="telemetry-header">
    <span>Spatial Telemetry</span>
    <span style="color:var(--success)">REAL-VECTOR</span>
  </div>
  <div class="metric-item"><span>Graph Scale</span><span id="stat-graph">0V / 0E</span></div>
  <div class="metric-item"><span>Quadtree Culled Vertices</span><span id="stat-culled">0</span></div>
  <div class="metric-item"><span>Rendered Screen Segments</span><span id="stat-rendered">0</span></div>
  <div class="divider"></div>
  <div class="telemetry-header">
    <span>A* Pathfinding Engine</span>
    <span style="color:var(--accent)">HEURISTIC</span>
  </div>
  <div class="metric-item"><span>Heap Extractions (Min)</span><span id="stat-explored">0</span></div>
  <div class="metric-item"><span>Open Set Peak Size</span><span id="stat-heap-peak">0</span></div>
  <div class="metric-item"><span>Real Driving Cost</span><span id="stat-cost">0.00 km</span></div>
</div>

<!-- Interaction Controls -->
<div class="hud toolbar-hud">
  <button id="btn-recenter">Recenter View</button>
  <button id="btn-quadtree">Show Quadtree</button>
  <button id="btn-clear">Reset Route</button>
</div>

<div class="user-tip">
  • Click any two real intersections to calculate shortest driving route.<br>
  • Left click + drag to pan smoothly | Wheel to scale continuous zoom.
</div>

<script>
const PAYLOAD = {client_payload};
document.getElementById('loc-badge').textContent = PAYLOAD.locationName;

/**
 * =========================================================
 * 1. BINARY MIN-HEAP (PRIORITY QUEUE) FOR A* SEARCH
 * Complexity: O(log N) push and extract-min.
 * =========================================================
 */
class PriorityQueue {{
  constructor(scoreFn) {{
    this.tree = [];
    this.score = scoreFn;
  }}
  push(val) {{
    this.tree.push(val);
    this.bubbleUp(this.tree.length - 1);
  }}
  pop() {{
    const top = this.tree[0];
    const bottom = this.tree.pop();
    if (this.tree.length > 0) {{
      this.tree[0] = bottom;
      this.sinkDown(0);
    }}
    return top;
  }}
  isEmpty() {{ return this.tree.length === 0; }}
  size() {{ return this.tree.length; }}

  bubbleUp(i) {{
    const item = this.tree[i];
    const itemVal = this.score(item);
    while (i > 0) {{
      const p = Math.floor((i - 1) / 2);
      if (itemVal >= this.score(this.tree[p])) break;
      this.tree[i] = this.tree[p];
      i = p;
    }}
    this.tree[i] = item;
  }}

  sinkDown(i) {{
    const len = this.tree.length;
    const item = this.tree[i];
    const itemVal = this.score(item);
    while (true) {{
      let left = 2 * i + 1, right = 2 * i + 2, swap = null;
      let leftVal, rightVal;
      if (left < len) {{
        leftVal = this.score(this.tree[left]);
        if (leftVal < itemVal) swap = left;
      }}
      if (right < len) {{
        rightVal = this.score(this.tree[right]);
        if ((swap === null && rightVal < itemVal) || (swap !== null && rightVal < leftVal)) swap = right;
      }}
      if (swap === null) break;
      this.tree[i] = this.tree[swap];
      i = swap;
    }}
    this.tree[i] = item;
  }}
}}

/**
 * =========================================================
 * 2. 2D SPATIAL QUADTREE FOR VIEWPORT CULLING & NEAREST-NEIGHBOR
 * =========================================================
 */
class Quadtree {{
  constructor(box, capacity = 12) {{
    this.box = box; // {{ x, y, w, h }}
    this.capacity = capacity;
    this.points = [];
    this.divided = false;
  }}

  subdivide() {{
    const {{ x, y, w, h }} = this.box;
    const hw = w / 2, hh = h / 2;
    this.nw = new Quadtree({{ x, y, w: hw, h: hh }}, this.capacity);
    this.ne = new Quadtree({{ x: x + hw, y, w: hw, h: hh }}, this.capacity);
    this.sw = new Quadtree({{ x, y: y + hh, w: hw, h: hh }}, this.capacity);
    this.se = new Quadtree({{ x: x + hw, y: y + hh, w: hw, h: hh }}, this.capacity);
    this.divided = true;
  }}

  insert(node) {{
    if (!this.contains(this.box, node)) return false;
    if (this.points.length < this.capacity) {{
      this.points.push(node);
      return true;
    }}
    if (!this.divided) this.subdivide();
    return this.nw.insert(node) || this.ne.insert(node) || this.sw.insert(node) || this.se.insert(node);
  }}

  query(range, found = []) {{
    if (!this.intersects(this.box, range)) return found;
    for (let p of this.points) {{
      if (this.contains(range, p)) found.push(p);
    }}
    if (this.divided) {{
      this.nw.query(range, found);
      this.ne.query(range, found);
      this.sw.query(range, found);
      this.se.query(range, found);
    }}
    return found;
  }}

  contains(r, p) {{
    return p.x >= r.x && p.x <= r.x + r.w && p.y >= r.y && p.y <= r.y + r.h;
  }}

  intersects(r1, r2) {{
    return !(r2.x > r1.x + r1.w || r2.x + r2.w < r1.x || r2.y > r1.y + r1.h || r2.y + r2.h < r1.y);
  }}
}}

/**
 * =========================================================
 * 3. PREFIX TRIE FOR REAL-WORLD STREET AUTOCOMPLETE
 * =========================================================
 */
class TrieNode {{
  constructor() {{
    this.children = {{}};
    this.matches = [];
  }}
}}

class AutocompleteTrie {{
  constructor() {{
    this.root = new TrieNode();
  }}

  insert(name, nodeObj) {{
    let cur = this.root;
    const clean = name.toLowerCase();
    for (let ch of clean) {{
      if (!cur.children[ch]) cur.children[ch] = new TrieNode();
      cur = cur.children[ch];
      cur.matches.push(nodeObj);
    }}
  }}

  search(prefix) {{
    let cur = this.root;
    const clean = prefix.toLowerCase();
    for (let ch of clean) {{
      if (!cur.children[ch]) return [];
      cur = cur.children[ch];
    }}
    return cur.matches;
  }}
}}

// Merge Sort for sorting Trie results by distance to current view
function mergeSort(arr, comp) {{
  if (arr.length <= 1) return arr;
  const mid = Math.floor(arr.length / 2);
  const left = mergeSort(arr.slice(0, mid), comp);
  const right = mergeSort(arr.slice(mid), comp);
  let out = [], i = 0, j = 0;
  while (i < left.length && j < right.length) {{
    if (comp(left[i], right[j]) <= 0) out.push(left[i++]);
    else out.push(right[j++]);
  }}
  return out.concat(left.slice(i)).concat(right.slice(j));
}}

/**
 * =========================================================
 * 4. BUILDING LOCAL GRAPH TOPOLOGY & QUADTREE
 * =========================================================
 */
// Calculate spatial bounding box for Quadtree
let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
const nodeMap = new Map();
const adjList = new Map();

PAYLOAD.nodes.forEach(n => {{
  minX = Math.min(minX, n.x);
  maxX = Math.max(maxX, n.x);
  minY = Math.min(minY, n.y);
  maxY = Math.max(maxY, n.y);
  nodeMap.set(n.id, n);
  adjList.set(n.id, []);
}});

const boundPad = 100;
const quadBox = {{
  x: minX - boundPad,
  y: minY - boundPad,
  w: (maxX - minX) + boundPad * 2,
  h: (maxY - minY) + boundPad * 2
}};
const quadtree = new Quadtree(quadBox);

PAYLOAD.nodes.forEach(n => quadtree.insert(n));

PAYLOAD.edges.forEach(e => {{
  if (adjList.has(e.u) && adjList.has(e.v)) {{
    adjList.get(e.u).push({{ to: e.v, cost: e.cost, type: e.type }});
    adjList.get(e.v).push({{ to: e.u, cost: e.cost, type: e.type }});
  }}
}});

const trie = new AutocompleteTrie();
PAYLOAD.pois.forEach(p => trie.insert(p.name, p));

document.getElementById('stat-graph').textContent = `${{PAYLOAD.nodes.length}}V / ${{PAYLOAD.edges.length}}E`;

/**
 * =========================================================
 * 5. HARDWARE-ACCELERATED CANVAS & CAMERA MATRIX
 * =========================================================
 */
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');

let camera = {{ x: 0, y: 0, zoom: 1.0 }};
let isDragging = false;
let startPan = {{ x: 0, y: 0 }};
let showQuadtreeBoxes = false;

function resizeCanvas() {{
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}}
window.addEventListener('resize', resizeCanvas);
resizeCanvas();

// Center camera on coordinate origin
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
let exploredSet = [];
let maxHeapTrack = 0;

function runAStar(srcId, dstId) {{
  const gScore = new Map();
  const fScore = new Map();
  const cameFrom = new Map();
  exploredSet = [];
  maxHeapTrack = 0;

  PAYLOAD.nodes.forEach(n => {{
    gScore.set(n.id, Infinity);
    fScore.set(n.id, Infinity);
  }});

  gScore.set(srcId, 0);
  const dest = nodeMap.get(dstId);
  const heuristic = (id) => {{
    const n = nodeMap.get(id);
    return Math.hypot(n.x - dest.x, n.y - dest.y);
  }};
  fScore.set(srcId, heuristic(srcId));

  const heap = new PriorityQueue(id => fScore.get(id));
  heap.push(srcId);

  while (!heap.isEmpty()) {{
    maxHeapTrack = Math.max(maxHeapTrack, heap.size());
    const currId = heap.pop();
    exploredSet.push(currId);

    if (currId === dstId) {{
      const path = [];
      let step = dstId;
      while (cameFrom.has(step)) {{
        path.unshift(nodeMap.get(step));
        step = cameFrom.get(step);
      }}
      path.unshift(nodeMap.get(srcId));

      document.getElementById('stat-explored').textContent = exploredSet.length;
      document.getElementById('stat-heap-peak').textContent = maxHeapTrack;
      document.getElementById('stat-cost').textContent = (gScore.get(dstId) / 1000).toFixed(2) + " km";
      return path;
    }}

    for (let edge of adjList.get(currId)) {{
      const neighbor = edge.to;
      const tentativeG = gScore.get(currId) + edge.cost;

      if (tentativeG < gScore.get(neighbor)) {{
        cameFrom.set(neighbor, currId);
        gScore.set(neighbor, tentativeG);
        fScore.set(neighbor, tentativeG + heuristic(neighbor));
        heap.push(neighbor);
      }}
    }}
  }}
  return null;
}}

/**
 * =========================================================
 * 6. HIGH-PERFORMANCE RENDER LOOP WITH VIEWPORT CULLING
 * =========================================================
 */
function render() {{
  ctx.fillStyle = "#070a13";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Compute bounding box of the camera viewport in world coordinates
  const tl = toWorld(0, 0);
  const br = toWorld(canvas.width, canvas.height);
  const viewportBox = {{
    x: tl.x,
    y: tl.y,
    w: br.x - tl.x,
    h: br.y - tl.y
  }};

  // Quadtree query: Discard thousands of off-screen nodes in O(log N)
  const visibleNodes = quadtree.query(viewportBox);
  const visibleIds = new Set(visibleNodes.map(n => n.id));

  document.getElementById('stat-rendered').textContent = visibleNodes.length;
  document.getElementById('stat-culled').textContent = `${{PAYLOAD.nodes.length - visibleNodes.length}} nodes`;

  // Draw Quadtree partition boundaries if toggled
  if (showQuadtreeBoxes) {{
    drawQuadBorders(quadtree);
  }}

  // Draw Road Hierarchy
  ctx.lineCap = "round";
  for (let e of PAYLOAD.edges) {{
    if (visibleIds.has(e.u) || visibleIds.has(e.v)) {{
      const u = nodeMap.get(e.u);
      const v = nodeMap.get(e.v);
      const p1 = toScreen(u.x, u.y);
      const p2 = toScreen(v.x, v.y);

      ctx.beginPath();
      if (e.type === "primary" || e.type === "trunk" || e.type === "motorway") {{
        ctx.strokeStyle = "rgba(56, 189, 248, 0.35)";
        ctx.lineWidth = 3.5 * camera.zoom;
      }} else if (e.type === "secondary" || e.type === "tertiary") {{
        ctx.strokeStyle = "rgba(148, 163, 184, 0.25)";
        ctx.lineWidth = 2.2 * camera.zoom;
      }} else {{
        ctx.strokeStyle = "rgba(71, 85, 105, 0.2)";
        ctx.lineWidth = 1.2 * camera.zoom;
      }}
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.stroke();
    }}
  }}

  // Draw A* Explored Wavefront
  if (exploredSet.length > 0 && activeRoute) {{
    ctx.fillStyle = "rgba(56, 189, 248, 0.25)";
    for (let nid of exploredSet) {{
      if (visibleIds.has(nid)) {{
        const n = nodeMap.get(nid);
        const p = toScreen(n.x, n.y);
        ctx.beginPath();
        ctx.arc(p.x, p.y, 3.5 * camera.zoom, 0, Math.PI * 2);
        ctx.fill();
      }}
    }}
  }}

  // Draw Active Optimal Route with Neon Cyan Glow
  if (activeRoute && activeRoute.length > 1) {{
    ctx.shadowColor = "#38bdf8";
    ctx.shadowBlur = 14;
    ctx.strokeStyle = "#38bdf8";
    ctx.lineWidth = 5.5 * camera.zoom;
    ctx.beginPath();
    for (let i = 0; i < activeRoute.length; i++) {{
      const p = toScreen(activeRoute[i].x, activeRoute[i].y);
      if (i === 0) ctx.moveTo(p.x, p.y);
      else ctx.lineTo(p.x, p.y);
    }}
    ctx.stroke();
    ctx.shadowBlur = 0;
  }}

  // Draw Vertices, POIs, and Route Endpoints
  for (let n of visibleNodes) {{
    const p = toScreen(n.x, n.y);

    if (startNode && startNode.id === n.id) {{
      drawMarker(p.x, p.y, "#10b981", "ORIGIN");
    }} else if (goalNode && goalNode.id === n.id) {{
      drawMarker(p.x, p.y, "#f43f5e", "DESTINATION");
    }} else if (n.name && camera.zoom > 0.75) {{
      ctx.fillStyle = "#f59e0b";
      ctx.beginPath();
      ctx.arc(p.x, p.y, 3 * camera.zoom, 0, Math.PI * 2);
      ctx.fill();

      ctx.font = "10px -apple-system, sans-serif";
      ctx.fillStyle = "#cbd5e1";
      ctx.fillText(n.name, p.x + 6, p.y + 3);
    }}
  }}

  requestAnimationFrame(render);
}}

function drawMarker(x, y, color, label) {{
  ctx.shadowColor = color;
  ctx.shadowBlur = 12;
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.arc(x, y, 7.5, 0, Math.PI * 2);
  ctx.fill();
  ctx.font = "bold 11px -apple-system, sans-serif";
  ctx.fillText(label, x + 10, y + 4);
  ctx.shadowBlur = 0;
}}

function drawQuadBorders(q) {{
  const p = toScreen(q.box.x, q.box.y);
  ctx.strokeStyle = "rgba(56, 189, 248, 0.08)";
  ctx.lineWidth = 1;
  ctx.strokeRect(p.x, p.y, q.box.w * camera.zoom, q.box.h * camera.zoom);
  if (q.divided) {{
    drawQuadBorders(q.nw);
    drawQuadBorders(q.ne);
    drawQuadBorders(q.sw);
    drawQuadBorders(q.se);
  }}
}}

canvas.addEventListener('mousedown', e => {{
  if (e.button === 0) {{
    isDragging = true;
    startPan = {{ x: e.clientX - camera.x, y: e.clientY - camera.y }};
  }}
}});

window.addEventListener('mousemove', e => {{
  if (isDragging) {{
    camera.x = e.clientX - startPan.x;
    camera.y = e.clientY - startPan.y;
  }}
}});

window.addEventListener('mouseup', () => isDragging = false);

canvas.addEventListener('wheel', e => {{
  e.preventDefault();
  const zoomFactor = e.deltaY < 0 ? 1.15 : 1 / 1.15;
  const mouseWorld = toWorld(e.clientX, e.clientY);

  camera.zoom = Math.max(0.2, Math.min(camera.zoom * zoomFactor, 6.0));
  camera.x = e.clientX - mouseWorld.x * camera.zoom;
  camera.y = e.clientY - mouseWorld.y * camera.zoom;
}});

// Click to pick route vertices using Quadtree candidate selection
canvas.addEventListener('click', e => {{
  if (Math.hypot(e.movementX, e.movementY) > 4) return;
  const click = toWorld(e.clientX, e.clientY);

  const radius = 60 / camera.zoom;
  const candidates = quadtree.query({{
    x: click.x - radius,
    y: click.y - radius,
    w: radius * 2,
    h: radius * 2
  }});

  let nearest = null;
  let minDist = Infinity;
  for (let n of candidates) {{
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
      exploredSet = [];
      document.getElementById('stat-explored').textContent = 0;
      document.getElementById('stat-cost').textContent = "0.00 km";
    }} else {{
      goalNode = nearest;
      activeRoute = runAStar(startNode.id, goalNode.id);
    }}
  }}
}});

// Street search autocomplete handler (Trie + Merge Sort)
const searchInput = document.getElementById('search-input');
const suggestions = document.getElementById('suggestions');

searchInput.addEventListener('input', e => {{
  const val = e.target.value.trim();
  suggestions.innerHTML = "";
  if (!val) return;

  const matches = trie.search(val);
  const center = toWorld(canvas.width / 2, canvas.height / 2);

  // Distinct POIs
  const uniqueMatches = Array.from(new Set(matches));

  // Merge Sort by distance to viewport center
  const sorted = mergeSort(uniqueMatches, (a, b) => {{
    const distA = Math.hypot(a.x - center.x, a.y - center.y);
    const distB = Math.hypot(b.x - center.x, b.y - center.y);
    return distA - distB;
  }});

  sorted.slice(0, 6).forEach(poi => {{
    const li = document.createElement('li');
    li.innerHTML = `<span>${{poi.name}}</span><span style="color:var(--accent); font-size:10px;">STREET</span>`;
    li.onclick = () => {{
      // Smooth center camera on selected road node
      camera.x = canvas.width / 2 - poi.x * camera.zoom;
      camera.y = canvas.height / 2 - poi.y * camera.zoom;
      startNode = nodeMap.get(poi.id);
      goalNode = null;
      activeRoute = null;
      suggestions.innerHTML = "";
      searchInput.value = poi.name;
    }};
    suggestions.appendChild(li);
  }});
}});

// HUD Action Buttons
document.getElementById('btn-recenter').onclick = () => {{
  camera.x = canvas.width / 2;
  camera.y = canvas.height / 2;
  camera.zoom = 1.0;
}};

document.getElementById('btn-quadtree').onclick = (e) => {{
  showQuadtreeBoxes = !showQuadtreeBoxes;
  e.target.classList.toggle('active', showQuadtreeBoxes);
}};

document.getElementById('btn-clear').onclick = () => {{
  startNode = null;
  goalNode = null;
  activeRoute = null;
  exploredSet = [];
  document.getElementById('stat-explored').textContent = 0;
  document.getElementById('stat-cost').textContent = "0.00 km";
}};

// Boot render engine
render();
</script>
</body>
</html>
"""

# Embed interactive canvas into Streamlit
components.html(html_canvas_component, height=920, scrolling=False)
