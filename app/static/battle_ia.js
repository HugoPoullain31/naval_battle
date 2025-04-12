const playerGrid = document.getElementById("player-grid");
const enemyGrid = document.getElementById("enemy-grid");
const turnIndicator = document.getElementById("turn-indicator");

let canPlay = true;

function createGrid(gridElement, isClickable = false) {
    for (let row = 0; row < 10; row++) {
        for (let col = 0; col < 10; col++) {
            const cell = document.createElement("div");
            cell.classList.add("cell");
            cell.dataset.row = row;
            cell.dataset.col = col;
            if (isClickable) {
                cell.addEventListener("click", handlePlayerShot);
            }
            gridElement.appendChild(cell);
        }
    }
}

async function loadPlayerShips() {
    const res = await fetch(`/get_ships/${gameId}/player`);
    const data = await res.json();
    if (data.status === "success") {
        data.ships.forEach(ship => {
            for (let i = 0; i < ship.size; i++) {
                const r = ship.orientation === "vertical" ? ship.row + i : ship.row;
                const c = ship.orientation === "horizontal" ? ship.col + i : ship.col;
                const cell = playerGrid.querySelector(`.cell[data-row="${r}"][data-col="${c}"]`);
                if (cell) cell.classList.add("ship");
            }
        });
    }
}

async function loadReceivedShots() {
    const res = await fetch(`/received_shots/${gameId}/player`);
    const data = await res.json();
    if (data.status === "success") {
        data.shots.forEach(shot => {
            const cell = playerGrid.querySelector(`.cell[data-row="${shot.row}"][data-col="${shot.col}"]`);
            if (cell) {
                if (shot.result === "hit") {
                    cell.classList.add("hit");
                    cell.classList.add("ship-hit");  // effet spécial si tu veux
                } else {
                    cell.classList.add("miss");
                }
            }
        });
    }
}

async function loadEnemyShots() {
    const res = await fetch(`/received_shots/${gameId}/ai`);
    const data = await res.json();
    if (data.status === "success") {
        data.shots.forEach(shot => {
            const cell = enemyGrid.querySelector(`.cell[data-row="${shot.row}"][data-col="${shot.col}"]`);
            if (cell && !cell.classList.contains("hit") && !cell.classList.contains("miss")) {
                cell.classList.add(shot.result === "hit" ? "hit" : "miss");
            }
        });
    }
}

async function handlePlayerShot(e) {
    if (!canPlay) return;
    const cell = e.target;
    if (cell.classList.contains("hit") || cell.classList.contains("miss")) return;

    const row = parseInt(cell.dataset.row);
    const col = parseInt(cell.dataset.col);

    canPlay = false;

    const res = await fetch("/fire", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            game_id: gameId,
            player_id: "player",
            row: row,
            col: col
        })
    });

    const data = await res.json();
    if (data.status === "success") {
        cell.classList.add(data.result === "hit" ? "hit" : "miss");
        turnIndicator.textContent = "⏳ L'IA joue...";
        await delay(1000);
        await iaPlay();
    } else {
        turnIndicator.textContent = data.message;
        canPlay = true;
    }
}

async function iaPlay() {
    const res = await fetch("/fire", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            game_id: gameId,
            player_id: "ai",
            row: -1,
            col: -1
        })
    });

    await loadReceivedShots();  // tirs de l'IA sur ta grille
    turnIndicator.textContent = "🎯 À vous de tirer !";
    canPlay = true;
}

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Initialisation
createGrid(playerGrid);
createGrid(enemyGrid, true);
loadPlayerShips();
loadReceivedShots();
loadEnemyShots();
