// web/app.js
let roiChart = null;
let trendChart = null;

const $ = (id) => document.getElementById(id);

async function loadKPI(){
  const days = $("days").value;
  const r = await fetch(`/api/report/kpi?days=${days}`);
  const d = await r.json();
  const k = d.kpi;

  $("kpi-roi").innerText  = (k.roi*100).toFixed(1)+"%";
  $("kpi-hit").innerText  = (k.hit_rate*100).toFixed(1)+"%";
  $("kpi-pass").innerText = (k.pass_rate*100).toFixed(1)+"%";

  $("kpi-warning").innerHTML = (d.warnings && d.warnings.length)
    ? d.warnings.map(w => "⚠ " + w).join("<br>")
    : "";
}

async function loadStrategyROI(){
  const days = $("days").value;
  const r = await fetch(`/api/metrics/strategy_compare?days=${days}&only_enabled=true`);
  const d = await r.json();

  const labels = Object.keys(d);
  const values = labels.map(k => d[k].roi);

  if(roiChart) roiChart.destroy();
  roiChart = new Chart($("roiChart"),{
    type:"bar",
    data:{labels, datasets:[{label:"ROI", data:values}]},
    options:{plugins:{legend:{display:false}}}
  });
}

async function loadTrend(){
  const period = $("trendPeriod").value;
  const r = await fetch(`/api/metrics/strategy_trend?period=${period}&only_enabled=true`);
  const d = await r.json();

  const keys = Object.keys(d);
  if(!keys.length) return;

  const labels = d[keys[0]].map(x => x.period);

  const datasets = keys.map(k => ({
    label: k,
    data: d[k].map(x => x.roi),
    fill: false,
    tension: 0.2
  }));

  if(trendChart) trendChart.destroy();
  trendChart = new Chart($("trendChart"),{
    type:"line",
    data:{labels, datasets},
    options:{plugins:{legend:{display:true}}}
  });
}

async function loadStrategyList(){
  const r = await fetch(`/api/strategy/list`);
  const d = await r.json();
  const items = d.strategies || [];

  const wrap = $("strategyList");
  wrap.innerHTML = "";

  items.forEach(it => {
    const row = document.createElement("div");
    row.style.display = "flex";
    row.style.alignItems = "center";
    row.style.gap = "10px";
    row.style.margin = "6px 0";

    const chk = document.createElement("input");
    chk.type = "checkbox";
    chk.checked = !!it.is_enabled;
    chk.onchange = async () => {
      await fetch(`/api/strategy/toggle`, {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({strategy: it.strategy, is_enabled: chk.checked})
      });
      await loadStrategyROI();
      await loadTrend();
    };

    const name = document.createElement("span");
    name.innerText = it.strategy;

    row.appendChild(chk);
    row.appendChild(name);
    wrap.appendChild(row);
  });
}

async function loadAlertHistory(){
  const r = await fetch(`/api/alerts/history?limit=50`);
  const d = await r.json();
  const items = d.items || [];

  const box = $("alertHistory");
  if(!items.length){
    box.innerText = "이력 없음";
    return;
  }

  box.innerHTML = items.map(it => {
    const warns = (it.warnings || []).join(", ");
    return `<div style="margin:6px 0;">
      <div><b>#${it.id}</b> ${it.created_at} (days=${it.days})</div>
      <div>ROI=${it.roi} HIT=${it.hit_rate} PASS=${it.pass_rate}</div>
      <div>${warns ? "⚠ " + warns : "정상"}</div>
      <div>slack=${it.sent_slack} mail=${it.sent_mail}</div>
    </div>`;
  }).join("<hr style='border:0;border-top:1px solid #222;margin:10px 0'/>");
}

function openExecPdf(){
  const days = $("days").value;
  const period = $("trendPeriod").value;
  window.open(`/api/report/exec/pdf?days=${days}&period=${period}`, "_blank");
}

window.addEventListener("DOMContentLoaded", async () => {
  // 기존 버튼이 있다면 유지, 없으면 아래만으로도 동작
  if($("btnRefresh")) $("btnRefresh").onclick = async () => { await loadKPI(); await loadStrategyROI(); };

  if($("btnTrend")) $("btnTrend").onclick = loadTrend;
  if($("btnAlertHistory")) $("btnAlertHistory").onclick = loadAlertHistory;
  if($("btnExecPdf")) $("btnExecPdf").onclick = openExecPdf;

  await loadStrategyList();
  await loadKPI();
  await loadStrategyROI();
  await loadTrend();
  await loadAlertHistory();
});
