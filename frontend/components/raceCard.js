function raceCard(race) {
    const div = document.createElement("div");
    div.className = "race-card";

    div.innerHTML = `
        <div class="race-title">${race.title}</div>
        <div class="race-info">
            장소: ${race.track} / 거리: ${race.distance}m<br>
            날짜: ${race.date}
        </div>
    `;

    div.onclick = () => {
        window.location.href = `race.html?id=${race.id}`;
    };

    return div;
}
