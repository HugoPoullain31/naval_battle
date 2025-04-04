document.addEventListener("DOMContentLoaded", () => {
    const playerGrid = document.getElementById("player-grid");
    const boats = document.querySelectorAll(".boat");
    const startGameButton = document.getElementById("start-game");

    const playerId = localStorage.getItem("player_id");
    const gameId = localStorage.getItem("game_id");
    let placedShips = [];

    for (let row = 0; row < 10; row++) {
        for (let col = 0; col < 10; col++) {
            const cell = document.createElement("div");
            cell.classList.add("grid-cell");
            cell.dataset.row = row;
            cell.dataset.col = col;
            playerGrid.appendChild(cell);
        }
    }

    boats.forEach(boat => {
        boat.draggable = true;
        boat.dataset.orientation = "horizontal";

        const size = parseInt(boat.dataset.size);
        boat.style.width = `${size * 50}px`;
        boat.style.height = "50px";

        boat.addEventListener("dragstart", (e) => {
            boat.classList.add("dragging");
            e.dataTransfer.setData("boatId", boat.id);
        });

        boat.addEventListener("dragend", () => boat.classList.remove("dragging"));

        boat.addEventListener("click", () => {
            const orientation = boat.dataset.orientation;
            const size = parseInt(boat.dataset.size);

            if (orientation === "horizontal") {
                boat.dataset.orientation = "vertical";
                boat.style.width = "50px";
                boat.style.height = `${size * 50}px`;
            } else {
                boat.dataset.orientation = "horizontal";
                boat.style.width = `${size * 50}px`;
                boat.style.height = "50px";
            }
        });
    });

    playerGrid.addEventListener("dragover", e => e.preventDefault());

    playerGrid.addEventListener("drop", (e) => {
        e.preventDefault();
        const boatId = e.dataTransfer.getData("boatId");
        const boat = document.getElementById(boatId);

        const row = parseInt(e.target.dataset.row);
        const col = parseInt(e.target.dataset.col);
        const size = parseInt(boat.dataset.size);
        const orientation = boat.dataset.orientation;

        if (isNaN(row) || isNaN(col)) return;

        if ((orientation === "horizontal" && col + size > 10) ||
            (orientation === "vertical" && row + size > 10)) return;

        for (let i = 0; i < size; i++) {
            const checkRow = orientation === "vertical" ? row + i : row;
            const checkCol = orientation === "horizontal" ? col + i : col;
            const cell = document.querySelector(`[data-row="${checkRow}"][data-col="${checkCol}"]`);
            if (!cell || cell.children.length > 0) return;
        }

        for (let i = 0; i < size; i++) {
            const checkRow = orientation === "vertical" ? row + i : row;
            const checkCol = orientation === "horizontal" ? col + i : col;
            const cell = document.querySelector(`[data-row="${checkRow}"][data-col="${checkCol}"]`);
            const shipPart = document.createElement("div");
            shipPart.classList.add("ship-part");
            shipPart.style.backgroundColor = "blue";
            shipPart.style.width = "50px";
            shipPart.style.height = "50px";
            cell.appendChild(shipPart);
        }

        placedShips.push({ row, col, size, orientation });
        boat.remove();

        if (placedShips.length === 5) {
            startGameButton.disabled = false;
        }
    });

    startGameButton.addEventListener("click", () => {
        if (!playerId || !gameId) return alert("Nom ou game_id manquant");

        fetch("/save_ships", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ player_id: playerId, game_id: gameId, ships: placedShips }),
        })
        .then(res => res.json())
        .then(data => {
            console.log(data.message);
            checkBothPlayersReady();
        });
    });

    function checkBothPlayersReady() {
        fetch("/confirm_ships", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ game_id: gameId })
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === "ready") {
                window.location.href = `/battle/${gameId}/${playerId}`;
            } else {
                alert("En attente du deuxième joueur...");
                setTimeout(checkBothPlayersReady, 1500);
            }
        });
    }
});
