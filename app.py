"""
app.py — Retail Shelf Monitoring System
Flask REST API + Web Dashboard
"""

from flask import Flask, jsonify, request
from database import (
    init_db, get_all_inventory, get_active_alerts,
    resolve_alert, update_quantity, log_detection
)
from detector import simulate_detection, raise_alerts
import threading, time

app = Flask(__name__)


# ─── BACKGROUND MONITOR THREAD ─────────────────────────────────────────────────

def background_scan():
    while True:
        inventory = get_all_inventory()
        zones = ["A1","A2","B1","B2","C1","C2"]
        all_detections = []
        for zone in zones:
            detections = simulate_detection(zone, inventory)
            for det in detections:
                log_detection(det["zone"], det["sku"],
                              det["detected_qty"], det["confidence"], det["status"])
                update_quantity(det["sku"], det["zone"], det["detected_qty"])
            all_detections.extend(detections)
        raise_alerts(all_detections)
        time.sleep(5)


# ─── MAIN DASHBOARD ROUTE ──────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>RSMS Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,sans-serif;background:#0f1117;color:#e2e8f0;min-height:100vh}
.topbar{background:#161b27;border-bottom:1px solid #1e293b;padding:16px 28px;
        display:flex;align-items:center;justify-content:space-between}
.topbar h1{font-size:18px;font-weight:600}
.topbar h1 span{color:#38bdf8}
.live{display:inline-flex;align-items:center;gap:6px;font-size:12px;
      background:#052e16;color:#22c55e;border:1px solid #166534;
      padding:4px 12px;border-radius:20px}
.dot{width:7px;height:7px;border-radius:50%;background:#22c55e;animation:blink 1.4s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.2}}
.main{padding:24px 28px;max-width:1200px;margin:0 auto}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:22px}
.stat{background:#161b27;border:1px solid #1e293b;border-radius:12px;padding:16px 20px}
.stat .lbl{font-size:11px;color:#475569;text-transform:uppercase;letter-spacing:.5px}
.stat .val{font-size:30px;font-weight:700;margin-top:6px}
.ok{color:#22c55e}.low{color:#f59e0b}.out{color:#ef4444}.wh{color:#e2e8f0}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px}
.panel{background:#161b27;border:1px solid #1e293b;border-radius:12px;padding:20px}
.panel h2{font-size:11px;font-weight:600;color:#475569;text-transform:uppercase;
          letter-spacing:.5px;margin-bottom:14px}
.zone-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.zone{background:#0f1117;border:1px solid #1e293b;border-radius:8px;padding:10px 12px}
.zlbl{font-size:11px;font-weight:700;color:#334155;margin-bottom:6px}
.prow{display:flex;align-items:center;justify-content:space-between;
      padding:5px 0;border-bottom:1px solid #1a2234}
.prow:last-child{border:none}
.pname{font-size:12px;color:#94a3b8}
.pill{font-size:11px;font-weight:600;padding:2px 9px;border-radius:10px}
.p-ok {background:#052e16;color:#22c55e;border:1px solid #166534}
.p-low{background:#422006;color:#f59e0b;border:1px solid #92400e}
.p-out{background:#450a0a;color:#ef4444;border:1px solid #991b1b}
.alist{display:flex;flex-direction:column;gap:8px;max-height:260px;overflow-y:auto}
.aitem{display:flex;align-items:center;justify-content:space-between;
       gap:10px;padding:10px 12px;border-radius:8px;border:1px solid}
.aitem.LOW{background:#422006;border-color:#92400e}
.aitem.OUT{background:#450a0a;border-color:#991b1b}
.amsg{font-size:12px;flex:1}
.amsg.LOW{color:#fbbf24}.amsg.OUT{color:#f87171}
.rbtn{font-size:11px;padding:4px 10px;border-radius:6px;cursor:pointer;
      background:#1e293b;border:1px solid #334155;color:#94a3b8;white-space:nowrap}
.rbtn:hover{background:#334155;color:#e2e8f0}
.no-alert{font-size:13px;color:#334155;text-align:center;padding:20px 0}
.chart-box{position:relative;height:200px;margin-top:4px}
.snote{font-size:11px;color:#334155;text-align:right;margin-top:8px}
.crow{display:flex;align-items:center;gap:8px;margin-bottom:7px}
.cname{font-size:11px;color:#475569;width:88px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ctrack{flex:1;height:6px;background:#1e293b;border-radius:4px;overflow:hidden}
.cfill{height:100%;border-radius:4px;transition:width .5s}
.cpct{font-size:11px;color:#475569;width:32px;text-align:right}
.rform{display:flex;gap:8px;margin-top:14px;flex-wrap:wrap;align-items:center}
.rform select,.rform input{background:#0f1117;border:1px solid #334155;color:#e2e8f0;
  padding:6px 10px;border-radius:6px;font-size:12px}
.rform button{padding:6px 16px;border-radius:6px;background:#0ea5e9;
  color:#fff;border:none;font-size:12px;font-weight:600;cursor:pointer}
.rform button:hover{background:#0284c7}
.toast{position:fixed;bottom:24px;right:24px;background:#22c55e;color:#fff;
       padding:10px 18px;border-radius:8px;font-size:13px;font-weight:600;
       display:none;z-index:999;box-shadow:0 4px 20px rgba(0,0,0,.4)}
</style>
</head>
<body>

<div class="topbar">
  <h1>Retail <span>Shelf</span> Monitor</h1>
  <div style="display:flex;align-items:center;gap:12px">
    <span style="font-size:12px;color:#334155" id="ts"></span>
    <div class="live"><div class="dot"></div>Live Scanning</div>
  </div>
</div>

<div class="main">
  <div class="stats">
    <div class="stat"><div class="lbl">Total Products</div><div class="val wh" id="s-total">—</div></div>
    <div class="stat"><div class="lbl">In Stock</div><div class="val ok"  id="s-ok">—</div></div>
    <div class="stat"><div class="lbl">Low Stock</div><div class="val low" id="s-low">—</div></div>
    <div class="stat"><div class="lbl">Out of Stock</div><div class="val out" id="s-out">—</div></div>
  </div>

  <div class="g2">
    <div class="panel">
      <h2>Shelf Zones</h2>
      <div class="zone-grid" id="zone-grid"></div>
      <div class="snote" id="snote"></div>
    </div>
    <div class="panel">
      <h2>Active Alerts</h2>
      <div class="alist" id="alist"><div class="no-alert">Loading...</div></div>
    </div>
  </div>

  <div class="g2">
    <div class="panel">
      <h2>Inventory Levels</h2>
      <div class="chart-box">
        <canvas id="invChart" role="img" aria-label="Bar chart of inventory quantities">Inventory data</canvas>
      </div>
    </div>
    <div class="panel">
      <h2>Detection Confidence</h2>
      <div id="conf-bars"></div>
      <hr style="border-color:#1e293b;margin:16px 0"/>
      <h2>Manual Restock</h2>
      <div class="rform">
        <select id="rs-sku" style="flex:1"></select>
        <input type="number" id="rs-qty" placeholder="Qty" min="1" max="99" style="width:80px"/>
        <button onclick="doRestock()">Restock</button>
      </div>
    </div>
  </div>
</div>

<div class="toast" id="toast">Restocked successfully!</div>

<script>
const ZONES=["A1","A2","B1","B2","C1","C2"];
let chart=null, skuSelectReady=false;

async function api(url,opts){const r=await fetch(url,opts);return r.json();}

function st(qty,min){return qty===0?"out":qty<min?"low":"ok";}

function renderStats(inv){
  const ok=inv.filter(i=>st(i.quantity,i.min_stock)==="ok").length;
  const low=inv.filter(i=>st(i.quantity,i.min_stock)==="low").length;
  const out=inv.filter(i=>st(i.quantity,i.min_stock)==="out").length;
  document.getElementById("s-total").textContent=inv.length;
  document.getElementById("s-ok").textContent=ok;
  document.getElementById("s-low").textContent=low;
  document.getElementById("s-out").textContent=out;
  document.getElementById("ts").textContent="Updated "+new Date().toLocaleTimeString();
}

function renderZones(inv){
  const g={};ZONES.forEach(z=>g[z]=[]);
  inv.forEach(i=>{if(g[i.shelf_zone])g[i.shelf_zone].push(i);});
  document.getElementById("zone-grid").innerHTML=ZONES.map(z=>
    `<div class="zone"><div class="zlbl">Zone ${z}</div>`+
    (g[z].length?g[z].map(i=>{
      const s=st(i.quantity,i.min_stock);
      return `<div class="prow"><span class="pname">${i.name.substring(0,16)}</span>
      <span class="pill p-${s}">${s==="out"?"OUT":i.quantity+" pcs"}</span></div>`;
    }).join(""):'<div class="prow"><span class="pname" style="color:#334155">Empty</span></div>')+
    `</div>`
  ).join("");
  document.getElementById("snote").textContent="Last scan: "+new Date().toLocaleTimeString();
}

function renderAlerts(alerts){
  const el=document.getElementById("alist");
  if(!alerts.length){el.innerHTML='<div class="no-alert">All shelves OK ✓</div>';return;}
  el.innerHTML=alerts.slice(0,8).map(a=>
    `<div class="aitem ${a.alert_type}">
      <span class="amsg ${a.alert_type}">${a.message}</span>
      <button class="rbtn" onclick="resolveAlert(${a.id})">Resolve</button>
    </div>`
  ).join("");
}

function renderChart(inv){
  const labels=inv.map(i=>i.name.substring(0,7));
  const data=inv.map(i=>i.quantity);
  const colors=inv.map(i=>st(i.quantity,i.min_stock)==="ok"?"#22c55e":st(i.quantity,i.min_stock)==="low"?"#f59e0b":"#ef4444");
  if(!chart){
    chart=new Chart(document.getElementById("invChart"),{
      type:"bar",
      data:{labels,datasets:[{label:"Qty",data,backgroundColor:colors,borderRadius:4}]},
      options:{responsive:true,maintainAspectRatio:false,
        plugins:{legend:{display:false}},
        scales:{
          x:{ticks:{color:"#475569",font:{size:10}},grid:{display:false}},
          y:{ticks:{color:"#475569",font:{size:10}},grid:{color:"rgba(255,255,255,0.05)"}}
        }}
    });
  }else{
    chart.data.datasets[0].data=data;
    chart.data.datasets[0].backgroundColor=colors;
    chart.update("none");
  }
}

function renderConf(inv){
  document.getElementById("conf-bars").innerHTML=inv.map(item=>{
    const pct=Math.round(72+Math.random()*26);
    const col=pct>=85?"#22c55e":pct>=72?"#f59e0b":"#ef4444";
    return `<div class="crow">
      <span class="cname">${item.name.substring(0,12)}</span>
      <div class="ctrack"><div class="cfill" style="width:${pct}%;background:${col}"></div></div>
      <span class="cpct">${pct}%</span></div>`;
  }).join("");
}

function renderSelect(inv){
  if(skuSelectReady)return;
  const sel=document.getElementById("rs-sku");
  inv.forEach(item=>{
    const o=document.createElement("option");
    o.value=JSON.stringify({sku:item.sku,zone:item.shelf_zone});
    o.textContent=item.name+" ("+item.shelf_zone+")";
    sel.appendChild(o);
  });
  skuSelectReady=true;
}

async function resolveAlert(id){
  await api("/api/alerts/"+id+"/resolve",{method:"POST"});
  refresh();
}

async function doRestock(){
  const sel=document.getElementById("rs-sku");
  const qty=parseInt(document.getElementById("rs-qty").value);
  if(!sel.value||!qty||qty<1){alert("Select a product and enter a valid quantity.");return;}
  const {sku,zone}=JSON.parse(sel.value);
  await api("/api/restock",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({sku,shelf_zone:zone,quantity:qty})});
  const t=document.getElementById("toast");
  t.style.display="block";setTimeout(()=>t.style.display="none",2500);
  skuSelectReady=false;
  document.getElementById("rs-sku").innerHTML="";
  refresh();
}

async function refresh(){
  const [inv,alerts]=await Promise.all([api("/api/inventory"),api("/api/alerts")]);
  renderStats(inv);renderZones(inv);renderAlerts(alerts);renderChart(inv);renderConf(inv);renderSelect(inv);
}

refresh();
setInterval(refresh,5000);
</script>
</body>
</html>"""


# ─── API ROUTES ─────────────────────────────────────────────────────────────────

@app.route("/api/inventory")
def api_inventory():
    return jsonify(get_all_inventory())

@app.route("/api/alerts")
def api_alerts():
    return jsonify(get_active_alerts())

@app.route("/api/alerts/<int:alert_id>/resolve", methods=["POST"])
def api_resolve(alert_id):
    resolve_alert(alert_id)
    return jsonify({"status": "resolved"})

@app.route("/api/stats")
def api_stats():
    inv    = get_all_inventory()
    ok     = sum(1 for i in inv if i["quantity"] >= i["min_stock"])
    low    = sum(1 for i in inv if 0 < i["quantity"] < i["min_stock"])
    out    = sum(1 for i in inv if i["quantity"] == 0)
    alerts = len(get_active_alerts())
    return jsonify({"total":len(inv),"ok":ok,"low":low,"out":out,"active_alerts":alerts})

@app.route("/api/restock", methods=["POST"])
def api_restock():
    data = request.json
    update_quantity(data["sku"], data["shelf_zone"], data["quantity"])
    return jsonify({"status": "restocked"})


if __name__ == "__main__":
    init_db()
    t = threading.Thread(target=background_scan, daemon=True)
    t.start()
    print("[RSMS] Dashboard ready → http://localhost:5000")
    app.run(debug=False, port=5000)