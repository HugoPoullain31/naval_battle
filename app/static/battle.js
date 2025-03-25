document.addEventListener("DOMContentLoaded", () => {
    const yourGrid = document.getElementById("your-grid");
    const enemyGrid = document.getElementById("enemy-grid");
    const turnIndicator = document.getElementById("turn-indicator");

    let isYourTurn = false;
    let gameOver = false;

    const enemyId = playerId === "player1" ? "player2" : "player1";

    function createGrid(grid, isEnemy) {
        for (let row = 0; row < 10; row++) {
            for (let col = 0; col < 10; col++) {
                const cell = document.createElement("div");
                cell.dataset.row = row;
                cell.dataset.col = col;

                if (isEnemy) {
                    cell.addEventListener("click", () => fire(row, col, cell));
                }

                grid.appendChild(cell);
            }
        }
    }

    function loadShips() {
        fetch(`/get_ships/${playerId}`)
            .then(res => res.json())
            .then(data => {
                if (data.status === "success") {
                    data.ships.forEach(ship => {
                        const size = ship.size;
                        const orientation = ship.orientation;

                        for (let i = 0; i < size; i++) {
                            const r = ship.row + (orientation === "vertical" ? i : 0);
                            const c = ship.col + (orientation === "horizontal" ? i : 0);
                            const cell = yourGrid.querySelector(`[data-row="${r}"][data-col="${c}"]`);
                            if (cell) cell.classList.add("ship-cell");
                        }
                    });
                }
            });
    }

    function fire(row, col, cell) {
        if (!isYourTurn || gameOver || cell.classList.contains("hit") || cell.classList.contains("miss")) return;

        fetch("/fire", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ player_id: playerId, row, col })
        })
            .then(res => res.json())
            .then(data => {
                if (data.status === "success") {
                    if (data.result === "hit") {
                        cell.classList.add("hit");
                        cell.innerHTML = "💥";
                    } else {
                        cell.classList.add("miss");
                        cell.innerHTML = "❌";
                    }

                    checkVictory();
                } else {
                    if (data.message === "Ce n'est pas votre tour") {
                        const previousText = turnIndicator.textContent;
                        turnIndicator.textContent = "⚠️ Ce n'est pas votre tour !";
                        setTimeout(() => {
                            turnIndicator.textContent = previousText;
                        }, 2000);
                    } else {
                        alert(data.message || "Erreur lors du tir");
                    }
                }
            });
    }

    function pollHits() {
        fetch(`/received_shots/${playerId}`)
            .then(res => res.json())
            .then(data => {
                if (data.status === "success") {
                    data.shots.forEach(shot => {
                        const r = shot.row;
                        const c = shot.col;
                        const result = shot.result;

                        const cell = yourGrid.querySelector(`[data-row="${r}"][data-col="${c}"]`);
                        if (cell && !cell.classList.contains("hit") && !cell.classList.contains("miss")) {
                            if (result === "hit") {
                                cell.classList.add("ship-hit");
                                cell.innerHTML = "🔥";
                            } else {
                                cell.classList.add("miss");
                                cell.innerHTML = "❌";
                            }
                        }
                    });
                }
            });
    }

    function checkVictory() {
        fetch(`/received_shots/${enemyId}`)
            .then(res => res.json())
            .then(data => {
                if (data.status === "success") {
                    fetch(`/get_ships/${enemyId}`)
                        .then(res => res.json())
                        .then(enemyData => {
                            if (enemyData.status === "success") {
                                const totalParts = enemyData.ships.reduce((sum, ship) => sum + ship.size, 0);
                                const hits = data.shots.filter(s => s.result === "hit").length;
                                if (hits >= totalParts) {
                                    turnIndicator.innerHTML = "🎉 Vous avez gagné ! 🎉";
                                    gameOver = true;
                                } else {
                                    endTurn();
                                }
                            }
                        });
                }
            });

        fetch(`/received_shots/${playerId}`)
            .then(res => res.json())
            .then(data => {
                if (data.status === "success") {
                    fetch(`/get_ships/${playerId}`)
                        .then(res => res.json())
                        .then(ownData => {
                            if (ownData.status === "success") {
                                const totalParts = ownData.ships.reduce((sum, ship) => sum + ship.size, 0);
                                const hits = data.shots.filter(s => s.result === "hit").length;
                                if (hits >= totalParts) {
                                    turnIndicator.innerHTML = "💀 Vous avez perdu... 💀";
                                    gameOver = true;
                                }
                            }
                        });
                }
            });
    }

    function endTurn() {
        fetch("/next_turn", { method: "POST" }).then(() => {
            isYourTurn = false;
            updateTurn();
        });
    }

    function updateTurn() {
        fetch(`/turn/${playerId}`)
            .then(res => res.json())
            .then(data => {
                isYourTurn = data.your_turn;
                turnIndicator.textContent = isYourTurn
                    ? "🎯 À vous de tirer !"
                    : "⏳ En attente de l'adversaire...";
                if (!isYourTurn && !gameOver) {
                    setTimeout(updateTurn, 1500);
                } else if (isYourTurn && !gameOver) {
                    pollHits();
                }
            });
    }

    createGrid(yourGrid, false);
    createGrid(enemyGrid, true);
    loadShips();
    updateTurn();
});
