import json
import math
import random
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="AuraNav — Autonomous DSA Navigation Engine",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide default Streamlit header and padding for full-screen immersive canvas
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
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. CORE DATA STRUCTURES & GRAPH GENERATOR
# ==========================================

MAP_DIM = 3000
STEP = 115

def generate_auranav_world():
    nodes = []
    edges = []
    pois = []
    grid = []
    node_id = 0
    cols = MAP_DIM // STEP
    rows = MAP_DIM // STEP

    for r in range(rows):
        row = []
        for c in range(cols):
            jx = (random.random() - 0.5) * 44
            jy = (random.random() - 0.5) * 44
            n = {
                "id": node_id,
                "x": round(c * STEP + jx + 60, 1),
                "y": round(r * STEP + jy + 60, 1),
                "name": None
            }
            nodes.append(n)
            row.append(n)
            node_id += 1
        grid.append(row)

    for r in range(rows):
        for c in range(cols):
            u = grid[r][c]
            if c + 1 < cols and random.random() > 0.08:
                v = grid[r][c + 1]
                edges.append({"u": u["id"], "v": v["id"], "cost": round(math.hypot(u["x"] - v["x"], u["y"] - v["y"]), 1)})
            if r + 1 < rows and random.random() > 0.08:
                v = grid[r + 1][c]
                edges.append({"u": u["id"], "v": v["id"], "cost": round(math.hypot(u["x"] - v["x"], u["y"] - v["y"]), 1)})
            if c + 1 < cols and r + 1 < rows and random.random() > 0.76:
                v = grid[r + 1][c + 1]
                edges.append({"u": u["id"], "v": v["id"], "cost": round(math.hypot(u["x"] - v["x"], u["y"] - v["y"]), 1)})

    poi_names = [
        "Aura Prime Tower", "Quantum Exchange", "Cyber Nexus", "Hyper Station",
        "Vanguard BioLabs", "Silicon Quarter", "Metropolis Hub", "Beacon Terminal",
        "Orbit Spire", "Prism District", "Echo Wharf", "Titan Plaza",
        "Horizon Terrace", "Solaris Sector", "Vector Point", "Arcadia Port"
    ]
    sampled_nodes = random.sample(nodes, len(poi_names))
    for name, n in zip(poi_names, sampled_nodes):
        n["name"] = name
        pois.append({"id": n["id"], "name": name, "x": n["x"], "y": n["y"]})

    return nodes, edges, pois

nodes_data, edges_data, pois_data = generate_auranav_world()

payload = json.dumps({
    "nodes": nodes_data,
    "edges": edges_data,
    "pois": pois_data,
    "mapSize": MAP_DIM
})

# ==========================================
# 2. IMMERSIVE FRONTEND ENGINE (HTML5/CANVAS)
# ==========================================

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
    background: rgba(15, 23, 42, 0.82);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 14px;
    box-shadow: 0 16px 36px rgba(0, 0, 0, 0.55);
    z-index: 10;
  }}

  .brand {{
    top: 20px;
    left: 20px;
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
  .brand-text {{
    font-weight: 800;
    letter-spacing: 1.5px;
    font-size: 13px;
    color: #f8fafc;
  }}
  .brand-tag {{
    font-size: 10px;
    color: #38bdf8;
    background: rgba(56, 189, 248, 0.12);
    padding: 2px 6px;
    border-radius: 4px;
  }}

  .search-container {{
    top: 76px;
    left: 20px;
    width: 320px;
  }}
  .search-bar {{
    display: flex;
    align-items: center;
    padding: 11px 14px;
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
    max-height: 220px;
    overflow-y: auto;
  }}
  #suggestions li {{
    padding: 9px 14px;
    font-size: 12px;
    cursor: pointer;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    display: flex;
    justify-content: space-between;
    transition: all 0.2s;
  }}
  #suggestions li:hover {{
    background: rgba(56, 189, 248, 0.15);
    color: #38bdf8;
  }}

  .telemetry {{
    top: 20px;
    right: 20px;
    width: 290px;
    padding: 18px;
    font-size: 12px;
  }}
  .sec-title {{
    color: #38bdf8;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-size: 11px;
    margin-bottom: 10px;
    display: flex;
    justify-content: space-between;
  }}
  .stat-row {{
    display: flex;
    justify-content: space-between;
    margin-bottom: 6px;
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
    margin: 10px 0;
  }}

  .bottom-dock {{
    bottom: 24px;
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
    box-shadow: 0 0 12px rgba(56, 189, 248, 0.4);
  }}

  .instructions {{
    position: absolute;
    bottom: 24px;
    left: 20px;
    font-size: 11px;
    color: #64748b;
    line-height: 1.6;
  }}
</style>
</head>
<body>
<canvas id="canvas"></canvas>

<div class="glass brand">
  <div class="brand-logo"></div>
  <div class="brand-text">AURANAV</div>
  <div class="brand-tag">DSA MAP CORE</div>
</div>

<div class="glass search-container">
  <div class="search-bar">
    <span style="color:#38bdf8">⚲</span>
    <input type="text" id="search-input" placeholder="Search POI (Trie + MergeSort)..." autocomplete="off" />
  </div>
  <ul id="suggestions"></ul>
</div>

<div class="glass telemetry">
  <div class="sec-title">
    <span>Spatial Telemetry</span>
    <span style="color:#34d399">ONLINE</span>
  </div>
  <div class="stat-row"><span>Graph Scale</span><span id="stat-graph">0V / 0E</span></div>
  <div class="stat-row"><span>Quadtree Culled</span><span id="stat-culled">0</span></div>
  <div class="stat-row"><span>Rendered Vertices</span><span id="stat-rendered">0</span></div>
  <div class="divider"></div>
  <div class="sec-title">A* Pathfinding</div>
  <div class="stat-row"><span>Min-Heap Pops</span><span id="stat-explored">0</span></div>
  <div class="stat-row"><span>Optimal Cost</span><span id="stat-cost">0 km</span></div>
</div>

<div class="glass bottom-dock">
  <button id="btn-recenter">Recenter View</button>
  <button id="btn-reset">Clear Path</button>
</div>

<div class="instructions">
  • Click any 2 nodes to calculate A* shortest path.<br>
  • Left-click drag to pan | Mouse wheel to zoom smoothly.
</div>

<script>
const WORLD = {payload};

// Binary Min-Heap Implementation
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

// Build Graph Topology
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

// Autocomplete Prefix Trie
class TrieNode {{
  constructor() {{
    this.c = {{}};
    this.pois = [];
  }}
}}
class POITrie {{
  constructor() {{
    this.root = new TrieNode();
  }}
  insert(word, obj) {{
    let cur = this.root;
    for (let ch of word.toLowerCase()) {{
      if (!cur.c[ch]) cur.c[ch] = new TrieNode();
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
const poiTrie = new POITrie();
WORLD.pois.forEach(p => poiTrie.insert(p.name, p));

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

// Canvas & Viewport Setup
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
let camera = {{ x: 0, y: 0, zoom: 0.65 }};
let isDrag = false;
let startPan = {{ x: 0, y: 0 }};

function resize() {{
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}}
window.addEventListener('resize', resize);
resize();

camera.x = canvas.width / 2 - (WORLD.mapSize * camera.zoom) / 2;
camera.y = canvas.height / 2 - (WORLD.mapSize * camera.zoom) / 2;

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

// A* Search
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
      document.getElementById('stat-cost').textContent = (g.get(dstId) / 100).toFixed(2) + " km";
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
  const isVisible = (n) => n.x >= tl.x - 60 && n.x <= br.x + 60 && n.y >= tl.y - 60 && n.y <= br.y + 60;

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
  document.getElementById('stat-culled').textContent = `${{WORLD.nodes.length - drawnCount}} nodes`;

  // Draw Roads
  ctx.strokeStyle = "rgba(148, 163, 184, 0.12)";
  ctx.lineWidth = 2 * camera.zoom;
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

  // Draw A* Explored Wavefront
  if (exploredList.length > 0 && activeRoute) {{
    ctx.fillStyle = "rgba(56, 189, 248, 0.22)";
    for (let id of exploredList) {{
      if (renderedSet.has(id)) {{
        const pt = toScreen(nodeMap.get(id).x, nodeMap.get(id).y);
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, 4 * camera.zoom, 0, Math.PI * 2);
        ctx.fill();
      }}
    }}
  }}

  // Draw Active Shortest Route
  if (activeRoute) {{
    ctx.strokeStyle = "#38bdf8";
    ctx.lineWidth = 5 * camera.zoom;
    ctx.lineCap = "round";
    ctx.beginPath();
    for (let i = 0; i < activeRoute.length; i++) {{
      const pt = toScreen(activeRoute[i].x, activeRoute[i].y);
      if (i === 0) ctx.moveTo(pt.x, pt.y);
      else ctx.lineTo(pt.x, pt.y);
    }}
    ctx.stroke();
  }}

  // Draw Vertices and POIs
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
      ctx.fillText("GOAL", pt.x + 10, pt.y + 4);
    }} else if (n.name) {{
      ctx.fillStyle = "#fbbf24";
      ctx.beginPath(); ctx.arc(pt.x, pt.y, 4 * camera.zoom, 0, Math.PI * 2); ctx.fill();
      if (camera.zoom > 0.55) {{
        ctx.fillStyle = "#cbd5e1";
        ctx.font = "11px system-ui";
        ctx.fillText(n.name, pt.x + 8, pt.y + 3);
      }}
    }}
  }}

  requestAnimationFrame(render);
}}

// Interactions
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
  camera.zoom = Math.max(0.15, Math.min(camera.zoom * z, 3.5));
  camera.x = e.clientX - m.x * camera.zoom;
  camera.y = e.clientY - m.y * camera.zoom;
}});

canvas.addEventListener('click', e => {{
  if (Math.hypot(e.movementX, e.movementY) > 4) return;
  const click = toWorld(e.clientX, e.clientY);
  let nearest = null;
  let minDist = 40 / camera.zoom;

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

// Autocomplete Search with Trie & Merge Sort
const search = document.getElementById('search-input');
const suggestions = document.getElementById('suggestions');

search.addEventListener('input', e => {{
  const val = e.target.value.trim();
  suggestions.innerHTML = "";
  if (!val) return;

  const matches = poiTrie.search(val);
  const center = toWorld(canvas.width / 2, canvas.height / 2);
  const sorted = mergeSort(matches, a => Math.hypot(a.x - center.x, a.y - center.y));

  sorted.slice(0, 5).forEach(p => {{
    const li = document.createElement('li');
    li.innerHTML = `<span>${{p.name}}</span><span style="color:#38bdf8">POI</span>`;
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
  camera.x = canvas.width / 2 - (WORLD.mapSize * camera.zoom) / 2;
  camera.y = canvas.height / 2 - (WORLD.mapSize * camera.zoom) / 2;
}};

render();
</script>
</body>
</html>
"""

components.html(html_app, height=920, scrolling=False)
