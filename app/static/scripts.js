document.addEventListener("DOMContentLoaded", function() {
    console.log("Naval Battle is ready!");

    const gridSize = 5;
    const board = document.getElementById("gameBoard");

    function createBoard() {
        board.innerHTML = "";
        for (let i = 0; i < gridSize; i++) {
            for (let j = 0; j < gridSize; j++) {
                let cell = document.createElement("div");
                cell.classList.add("cell");
                cell.dataset.x = i;
                cell.dataset.y = j;
                cell.addEventListener("click", shoot);
                board.appendChild(cell);
            }
        }
    }

    function shoot(event) {
        let x = event.target.dataset.x;
        let y = event.target.dataset.y;

        fetch("/api/shoot", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ x: parseInt(x), y: parseInt(y) })
        })
        .then(response => response.json())
        .then(data => {
            console.log(data);
            event.target.classList.add(data.result === "hit" ? "hit" : "miss");
        });
    }

    function resetGame() {
        fetch("/api/start")
        .then(() => {
            createBoard();
            console.log("Nouvelle partie lancée !");
        });
    }

    document.getElementById("restartBtn").addEventListener("click", resetGame);
    createBoard();
});
