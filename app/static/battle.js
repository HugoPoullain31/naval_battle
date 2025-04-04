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
        fetch(`/get_ships/${gameId}/${playerId}`)
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

        fetch(`/fire`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ player_id: playerId, row, col, game_id: gameId })
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

                isYourTurn = false;
                checkVictory();
            } else {
                if (data.message === "Ce n'est pas votre tour") {
                    turnIndicator.textContent = "⚠️ Ce n'est pas votre tour !";
                    setTimeout(updateTurn, 1500);
                } else {
                    alert(data.message || "Erreur lors du tir");
                }
            }
        });
    }

    function pollHits() {
        fetch(`/received_shots/${gameId}/${playerId}`)
            .then(res => res.json())
            .then(data => {
                if (data.status === "success") {
                    data.shots.forEach(shot => {
                        const r = shot.row;
                        const c = shot.col;
                        const result = shot.result;

                        const cell = yourGrid.querySelector(`[data-row="${r}"][data-col="${c}"]`);
                        if (cell && !cell.classList.contains("hit") && !cell.classList.contains("miss") && !cell.classList.contains("ship-hit")) {
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

    async function checkVictory() {
        const resEnemyShots = await fetch(`/received_shots/${gameId}/${enemyId}`);
        const enemyData = await resEnemyShots.json();

        let enemyDefeated = false;
        let playerDefeated = false;

        if (enemyData.status === "success") {
            const resEnemyShips = await fetch(`/get_ships/${gameId}/${enemyId}`);
            const enemyShips = await resEnemyShips.json();

            if (enemyShips.status === "success") {
                const totalParts = enemyShips.ships.reduce((sum, ship) => sum + ship.size, 0);
                const hits = enemyData.shots.filter(s => s.result === "hit").length;
                if (hits >= totalParts) {
                    turnIndicator.innerHTML = "🎉 Vous avez gagné ! 🎉";
                    document.getElementById("victory-popup").classList.remove("hidden");
                    gameOver = true;
                    enemyDefeated = true;
                }
            }
        }

        const resOwnShots = await fetch(`/received_shots/${gameId}/${playerId}`);
        const ownData = await resOwnShots.json();

        if (ownData.status === "success") {
            const resOwnShips = await fetch(`/get_ships/${gameId}/${playerId}`);
            const ownShips = await resOwnShips.json();

            if (ownShips.status === "success") {
                const totalParts = ownShips.ships.reduce((sum, ship) => sum + ship.size, 0);
                const hits = ownData.shots.filter(s => s.result === "hit").length;
                if (hits >= totalParts) {
                    turnIndicator.innerHTML = "💀 Vous avez perdu... 💀";
                    document.getElementById("defeat-popup").classList.remove("hidden");
                    gameOver = true;
                    playerDefeated = true;
                }
            }
        }

        if (!enemyDefeated && !playerDefeated) {
            setTimeout(updateTurn, 500); 
        }

        fetch(`/received_shots/${gameId}/${playerId}`)
            .then(res => res.json())
            .then(data => {
                if (data.status === "success") {
                    fetch(`/get_ships/${gameId}/${playerId}`)
                        .then(res => res.json())
                        .then(ownData => {
                            if (ownData.status === "success") {
                                const totalParts = ownData.ships.reduce((sum, ship) => sum + ship.size, 0);
                                const hits = data.shots.filter(s => s.result === "hit").length;
                                if (hits >= totalParts) {
                                    turnIndicator.innerHTML = "💀 Vous avez perdu... 💀";
                                    document.getElementById("defeat-popup").classList.remove("hidden");
                                    gameOver = true;
                                }
                            }
                        });
                }
            });
    }

    function updateTurn() {
        if (gameOver) return;
    
        fetch(`/turn/${gameId}/${playerId}`)
            .then(res => res.json())
            .then(data => {
                isYourTurn = data.your_turn;
    
                turnIndicator.textContent = isYourTurn
                    ? "🎯 À vous de tirer !"
                    : "⏳ En attente de l'adversaire...";
    
                pollHits();
                checkVictory(); 
    
                if (!isYourTurn && !gameOver) {
                    setTimeout(updateTurn, 1500);
                }
            });
    }
    

    createGrid(yourGrid, false);
    createGrid(enemyGrid, true);
    loadShips();
    updateTurn();
});
