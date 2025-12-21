function horseRow(h) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
        <td>${h.no}</td>
        <td>${h.name}</td>
        <td>${h.jockey}</td>
        <td>${(h.win_prob * 100).toFixed(1)}%</td>
        <td>${(h.place_prob * 100).toFixed(1)}%</td>
    `;
    return tr;
}
