const HIT_GREEN = 0.60;
const HIT_YELLOW = 0.40;

let MODE = "month";
let PERIOD = null;
let chart = null;

/* =====================
   기간 선택 (24개월 / 8분기)
===================== */
function setMode(mode){
  MODE = mode;
  document.getElementById("btnMonth").classList.toggle("btn-active", MODE==="month");
  document.getElementById("btnQuarter").classList.toggle("btn-active", MODE==="quarter");
  buildPeriods();
  loadKpi();
}

function buildPeriods(){
  const sel = document.getElementById("periodSelect");
  sel.innerHTML = "";

  const now = new Date();

  if (MODE === "month") {
    for (let i=0; i<24; i++){
      const d = new Date(now.getFullYear(), now.getMonth()-i, 1);
      const v = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}`;
      sel.add(new Option(v, v));
    }
  } else {
    let y = now.getFullYear();
    let q = Math.floor(now.getMonth()/3)+1;
    for (let i=0; i<8; i++){
      sel.add(new Option(`${y}-Q${q}`, `${y}-Q${q}`));
      q--;
      if (q===0){ q=4; y--; }
    }
  }

  PERIOD = sel.value;
  sel.onchange = ()=>{ PERIOD = sel.value; loadKpi(); };
}

/* =====================
   KPI 표
===================== */
function hitClass(hitRate){
  if (hitRate === null) return "kpi-pass";
  if (hitRate >= HIT_GREEN) return "kpi-green";
  if (hitRate >= HIT_YELLOW) return "kpi-yellow";
  return "kpi-red";
}

function deltaClass(delta){
  if (delta === null) return "kpi-pass";
  if (delta > 0) return "kpi-green";
  if (delta < 0) return "kpi-red";
  return "kpi-pass";
}

async function loadKpi(){
  const content = document.getElementById("content");
  const alertbar = document.getElementById("alertbar");
  const periodLabel = document.getElementById("periodLabel");

  content.innerHTML = "로딩 중…";
  alertbar.style.display = "none";

  const res = await fetch(`/api/kpi/summary?mode=${MODE}&period=${PERIOD}`);
  const data = await res.json();

  periodLabel.textContent = `기간: ${data.period} (${data.mode})`;

  let html = `
    <table>
      <thead>
        <tr>
          <th>MODEL</th>
          <th>HIT</th>
          <th>MISS</th>
          <th>PASS</th>
          <th>PASS %</th>
          <th>HIT RATE</th>
          <th>Δ HIT RATE</th>
        </tr>
      </thead>
      <tbody>
  `;

  data.rows.forEach(r=>{
    const hr = r.hit_rate===null ? "N/A" : (r.hit_rate*100).toFixed(1)+"%";
    const dlt = r.hit_rate_delta===null
      ? "-"
      : ((r.hit_rate_delta>0?"+":"")+(r.hit_rate_delta*100).toFixed(1)+"%");

    html += `
      <tr>
        <td>${r.model}</td>
        <td>${r.hit}</td>
        <td>${r.miss}</td>
        <td class="kpi-pass">${r.pass}</td>
        <td>${(r.pass_rate*100).toFixed(1)}%</td>
        <td class="${hitClass(r.hit_rate)}">${hr}</td>
        <td class="${deltaClass(r.hit_rate_delta)}">${dlt}</td>
      </tr>
    `;
  });

  html += "</tbody></table>";
  content.innerHTML = html;

  if (data.alerts && data.alerts.length > 0){
    alertbar.textContent =
      "경고: " + data.alerts.map(a=>`${a.model} (${a.message})`).join(" / ");
    alertbar.style.display = "block";
  }

  loadTrend();
}

/* =====================
   모델별 추이 그래프
===================== */
async function loadTrend(){
  const res = await fetch(`/api/kpi/trend?mode=${MODE}&period=${PERIOD}`);
  const data = await res.json();

  const ctx = document.getElementById("trendChart").getContext("2d");
  if (chart) chart.destroy();

  const datasets = Object.keys(data.series).map(model=>({
    label: model,
    data: data.series[model],
    borderWidth: 2,
    tension: 0.25
  }));

  chart = new Chart(ctx, {
    type: "line",
    data: {
      labels: data.labels,
      datasets: datasets
    },
    options: {
      plugins: { legend: { position: "bottom" } },
      scales: {
        y: {
          min: 0,
          max: 100,
          ticks: { callback: v => v + "%" }
        }
      }
    }
  });
}

/* =====================
   PDF / 알림
===================== */
function downloadPdf(){
  window.open(`/api/kpi/report/pdf?mode=${MODE}&period=${PERIOD}`, "_blank");
}

async function dispatchReport(){
  const res = await fetch(`/api/kpi/report/dispatch?mode=${MODE}&period=${PERIOD}`, {
    method: "POST"
  });
  const d = await res.json();
  alert(`발송 결과\nSlack: ${d.slack_sent}\nMail: ${d.mail_sent}`);
}

/* =====================
   초기화
===================== */
buildPeriods();
setMode("month");
