document.addEventListener("DOMContentLoaded", () => {
    const playerGrid = document.getElementById("player-grid");
    const boatsContainer = document.querySelector(".boats-container");
    const boats = document.querySelectorAll(".boat");
    const startGameButton = document.getElementById("start-game");

    let playerId = localStorage.getItem("player_id") || "player1"; // Alternance entre les joueurs
    let placedShips = [];

    // Générer la grille de jeu
    for (let row = 0; row < 10; row++) {
        for (let col = 0; col < 10; col++) {
            const cell = document.createElement("div");
            cell.classList.add("grid-cell");
            cell.dataset.row = row;
            cell.dataset.col = col;
            playerGrid.appendChild(cell);
        }
    }

    // Drag & Drop des bateaux
    boats.forEach(boat => {
        boat.draggable = true;
        boat.dataset.orientation = "horizontal";

        boat.addEventListener("dragstart", (e) => {
            boat.classList.add("dragging");
            e.dataTransfer.setData("boatId", boat.id);
        });

        boat.addEventListener("dragend", () => {
            boat.classList.remove("dragging");
        });

        // Rotation des bateaux au clic
        boat.addEventListener("click", () => {
            if (boat.dataset.orientation === "horizontal") {
                boat.dataset.orientation = "vertical";
                boat.style.width = "50px";
                boat.style.height = `${boat.dataset.size * 50}px`;
            } else {
                boat.dataset.orientation = "horizontal";
                boat.style.width = `${boat.dataset.size * 50}px`;
                boat.style.height = "50px";
            }
        });

        // Assurez-vous que les bateaux affichés sur le côté sont bien horizontaux
        boat.style.width = `${boat.dataset.size * 50}px`;
        boat.style.height = "50px";
    });

    // Gestion du drop des bateaux
    playerGrid.addEventListener("dragover", (e) => {
        e.preventDefault();
    });

    playerGrid.addEventListener("drop", (e) => {
        e.preventDefault();
        let boatId = e.dataTransfer.getData("boatId");
        let boat = document.getElementById(boatId);

        let row = parseInt(e.target.dataset.row);
        let col = parseInt(e.target.dataset.col);
        let size = parseInt(boat.dataset.size);
        let orientation = boat.dataset.orientation;

        if (!row || !col) return;

        // Vérifier si le bateau peut être placé sans sortir de la grille
        if ((orientation === "horizontal" && col + size > 10) ||
            (orientation === "vertical" && row + size > 10)) {
            return;
        }

        // Vérifier qu'aucun autre bateau ne bloque la position
        for (let i = 0; i < size; i++) {
            let checkRow = orientation === "vertical" ? row + i : row;
            let checkCol = orientation === "horizontal" ? col + i : col;
            let cell = document.querySelector(`[data-row="${checkRow}"][data-col="${checkCol}"]`);
            if (!cell || cell.children.length > 0) {
                return;
            }
        }

        // Placer le bateau sur plusieurs cases
        let shipParts = [];
        for (let i = 0; i < size; i++) {
            let checkRow = orientation === "vertical" ? row + i : row;
            let checkCol = orientation === "horizontal" ? col + i : col;
            let cell = document.querySelector(`[data-row="${checkRow}"][data-col="${checkCol}"]`);
            let shipPart = document.createElement("div");
            shipPart.classList.add("ship-part");
            shipPart.style.backgroundColor = "blue";
            shipPart.style.width = "50px";
            shipPart.style.height = "50px";
            cell.appendChild(shipPart);
            shipParts.push({ row: checkRow, col: checkCol });
        }

        // Ajouter le bateau à la liste des bateaux placés
        placedShips.push({ row, col, size, orientation, parts: shipParts });

        // Supprimer le bateau de la liste disponible
        boat.remove();

        // Vérifier si tous les bateaux sont placés
        if (placedShips.length === 5) {
            startGameButton.disabled = false;
        }
    });

    // Fonction pour sauvegarder les bateaux via l'API Flask
    function saveShips() {
        fetch("/save_ships", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ player_id: playerId, ships: placedShips }),
        })
        .then(response => response.json())
        .then(data => {
            console.log(data.message);
            if (data.status === "success") {
                checkBothPlayersReady();
            }
        })
        .catch(error => console.error("Erreur lors de l'enregistrement:", error));
    }

    function checkBothPlayersReady() {
        fetch("/confirm_ships", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === "ready") {
                alert("Les deux joueurs sont prêts ! Début de la bataille !");
                window.location.href = "/battle"; 
            } else {
                alert(data.message);
            }
        })
        .catch(error => console.error("Erreur de vérification:", error));
    }

    startGameButton.addEventListener("click", () => {
        saveShips();
    });
});
