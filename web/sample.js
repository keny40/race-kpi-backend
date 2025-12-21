document.addEventListener("DOMContentLoaded", () => {
  const raceIdInput = document.getElementById("raceId");
  const horseInput = document.getElementById("horseNumbers");
  const sampleNotice = document.getElementById("sampleNotice");
  const predictBtn = document.getElementById("predictBtn");

  const SAMPLE_HORSES = "1,3,5,7";

  const samples = {
    sample1: "2025121801,5,0",
    sample2: "121",
    sample3: ""
  };

  function setNotice(type, message) {
    if (!message) {
      sampleNotice.style.display = "none";
      sampleNotice.textContent = "";
      sampleNotice.className = "";
      return;
    }
    sampleNotice.style.display = "block";
    sampleNotice.textContent = message;
    sampleNotice.className = type; // ok | warn | error
  }

  function setPredictEnabled(enabled) {
    predictBtn.disabled = !enabled;
  }

  async function logExistsResult(payload) {
    try {
      await fetch("/api/metrics/exists-check", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
    } catch (_) {}
  }

  async function checkDataExists(raceId) {
    if (!raceId) {
      setNotice("", "");
      setPredictEnabled(false);
      return;
    }

    setNotice("warn", "데이터 존재 여부 확인 중...");
    setPredictEnabled(false);

    try {
      const res = await fetch(
        `/api/race/exists?race_id=${encodeURIComponent(raceId)}`
      );
      const data = await res.json();

      logExistsResult({
        race_id: raceId,
        exists: data.exists,
        count: data.count || 0
      });

      if (data.exists) {
        setNotice(
          "ok",
          `실제 데이터 ${data.count}건 존재 (${data.from} ~ ${data.to}) · 수정 후 예측 실행 가능`
        );
        setPredictEnabled(true);
      } else {
        setNotice(
          "error",
          "해당 경주 ID의 실제 데이터가 없습니다. 수정 후 다시 확인하세요."
        );
        setPredictEnabled(false);
      }
    } catch (e) {
      setNotice(
        "error",
        "데이터 확인 실패. 잠시 후 다시 시도해 주세요."
      );
      setPredictEnabled(false);
    }
  }

  function applySample(raceId) {
    raceIdInput.value = raceId;
    horseInput.value = SAMPLE_HORSES;
    checkDataExists(raceId.trim());
  }

  document.getElementById("sample1").onclick = () =>
    applySample(samples.sample1);
  document.getElementById("sample2").onclick = () =>
    applySample(samples.sample2);
  document.getElementById("sample3").onclick = () =>
    applySample(samples.sample3);

  raceIdInput.addEventListener("input", () => {
    checkDataExists(raceIdInput.value.trim());
  });

  setPredictEnabled(false);
});
