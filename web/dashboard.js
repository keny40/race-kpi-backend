// === 설정 ===
const RECENT_LIMIT = 500;
let AUTO_PASS = false;
let CONF_BIAS = 0.0; // 스트릭에 따른 confidence 보정값

async function loadTimeline() {
  const res = await fetch(`/api/metrics/timeline?limit=${RECENT_LIMIT}`);
  const data = await res.json();

  const alertMiss = Number(document.getElementById("alertMiss").value || 3);
  const alertHit  = Number(document.getElementById("alertHit").value  || 5);
  const recentN   = Number(document.getElementById("recentN").value   || 20);

  // 최근 N 결과(피드백 기준)
  const recent = [];
  const lastPredictByRace = new Map();

  data.items.forEach(item => {
    if (item.type === "predict") {
      lastPredictByRace.set(item.race_id ?? "__none__", item.payload);
    }
    if (item.type === "feedback") {
      const hit = item.payload.hit === true;
      recent.push(hit);
      if (recent.length > recentN) recent.shift();
    }
  });

  // 스트릭 계산
  let rHit = 0, rMiss = 0;
  for (let i = recent.length - 1; i >= 0; i--) {
    if (recent[i]) { rHit++; if (rMiss) break; }
    else { rMiss++; if (rHit) break; }
  }

  // === 알림 → 자동 PASS ===
  AUTO_PASS = rMiss >= alertMiss;

  // === 스트릭 → confidence 자동 조절 ===
  // 실패 스트릭 ↑ → 보수적(감산), 적중 스트릭 ↑ → 공격적(가산)
  if (rMiss >= alertMiss) CONF_BIAS = -0.15;
  else if (rHit >= alertHit) CONF_BIAS = +0.10;
  else CONF_BIAS = 0.0;

  // 상태를 서버에 전달 (예측 시 사용)
  await fetch("/api/runtime/state", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      auto_pass: AUTO_PASS,
      confidence_bias: CONF_BIAS,
      recent_hit_streak: rHit,
      recent_miss_streak: rMiss
    })
  });
}

document.addEventListener("DOMContentLoaded", () => {
  ["recentN","alertMiss","alertHit"].forEach(id =>
    document.getElementById(id).addEventListener("input", loadTimeline)
  );
  loadTimeline();
  setInterval(loadTimeline, 5000);
});
