let selectedElement = null;
const API_BASE_URL = 'http://localhost:8000';

document.addEventListener('DOMContentLoaded', () => {
    fetchGameStateAndRender(); // Renamed
    setupControls();
});

// Renamed function to reflect it fetches more than just map data
async function fetchGameStateAndRender() {
    const apiUrl = `${API_BASE_URL}/api/game_state`; // Updated endpoint
    try {
        const response = await fetch(apiUrl);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const gameState = await response.json();
        renderGameUI(gameState); // New function to handle full UI update
    } catch (error) {
        console.error('Error fetching game state:', error);
        const mapContainer = document.getElementById('map-container');
        if (mapContainer) {
            mapContainer.innerHTML = '<p>Error loading game data. Is the backend server running?</p>';
        }
        const playerHandContents = document.getElementById('player-hand-contents');
        if(playerHandContents) playerHandContents.textContent = 'Error loading hand.';
    }
}

function renderGameUI(gameState) {
    if (!gameState) {
        console.error("No game state to render.");
        return;
    }
    if (gameState.map_details) {
        renderMap(gameState.map_details);
    } else {
        console.error("Map details missing in game state:", gameState);
        const mapContainer = document.getElementById('map-container');
        if (mapContainer) mapContainer.innerHTML = '<p>Map data missing in game state.</p>';
    }

    // player_hand is now a list of seed names, player_hand_count is an integer
    // We need to derive the counts for display, or the backend could provide a count map.
    // For now, let's derive counts from the player_hand list.
    const handCounts = {};
    if (gameState.player_hand) {
        gameState.player_hand.forEach(seedName => {
            handCounts[seedName] = (handCounts[seedName] || 0) + 1;
        });
    }
    renderPlayerHand(handCounts, gameState.player_hand_count); // Pass derived counts and total count
}


function setupControls() {
    const elementButtons = document.querySelectorAll('.element-button');
    const selectedElementDisplay = document.getElementById('selected-element-display');

    elementButtons.forEach(button => {
        button.addEventListener('click', () => {
            selectedElement = button.dataset.element;
            if (selectedElementDisplay) {
                selectedElementDisplay.textContent = selectedElement;
            }
            console.log(`Selected element: ${selectedElement}`);
        });
    });

    const undoButton = document.getElementById('undo-button');
    if (undoButton) {
        undoButton.addEventListener('click', handleUndoClick);
    }

    const redoButton = document.getElementById('redo-button');
    if (redoButton) {
        redoButton.addEventListener('click', handleRedoClick);
    }

    const saveButton = document.getElementById('save-button');
    if (saveButton) {
        saveButton.addEventListener('click', handleSaveClick);
    }

    const loadButton = document.getElementById('load-button');
    if (loadButton) {
        loadButton.addEventListener('click', handleLoadClick);
    }
}

async function handleSaveClick() {
    console.log("Save Game button clicked");
    const apiUrl = `${API_BASE_URL}/api/save_map`;
    try {
        const response = await fetch(apiUrl, { method: 'POST' });
        const responseData = await response.json(); // Attempt to parse JSON regardless of ok status
        if (!response.ok) {
            throw new Error(responseData.detail || `HTTP error! status: ${response.status}`);
        }
        console.log("Game saved successfully:", responseData);
        alert(responseData.message || "Game saved successfully!");
    } catch (error) {
        console.error('Error saving game:', error);
        alert(`Save failed: ${error.message}`);
    }
}

async function handleLoadClick() {
    console.log("Load Game button clicked");
    const apiUrl = `${API_BASE_URL}/api/load_map`;
    try {
        const response = await fetch(apiUrl, { method: 'POST' });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: "Unknown error during load." }));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        const loadedGameState = await response.json();
        renderGameUI(loadedGameState);
        selectedElement = null;
        const selectedElementDisplay = document.getElementById('selected-element-display');
        if (selectedElementDisplay) selectedElementDisplay.textContent = "None";
        alert("Game loaded successfully!"); // Provide feedback
    } catch (error) {
        console.error('Error loading game:', error);
        alert(`Load failed: ${error.message}`);
    }
}

async function handleUndoClick() {
    console.log("Undo button clicked");
    const apiUrl = `${API_BASE_URL}/api/undo`;
    try {
        const response = await fetch(apiUrl, { method: 'POST' });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: "Unknown error during undo." }));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        const updatedGameState = await response.json();
        renderGameUI(updatedGameState);
        // Clear selected element after undo/redo as context might change
        selectedElement = null;
        const selectedElementDisplay = document.getElementById('selected-element-display');
        if (selectedElementDisplay) selectedElementDisplay.textContent = "None";
    } catch (error) {
        console.error('Error during undo:', error);
        alert(`Undo failed: ${error.message}`);
    }
}

async function handleRedoClick() {
    console.log("Redo button clicked");
    const apiUrl = `${API_BASE_URL}/api/redo`;
    try {
        const response = await fetch(apiUrl, { method: 'POST' });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: "Unknown error during redo." }));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        const updatedGameState = await response.json();
        renderGameUI(updatedGameState);
        // Clear selected element
        selectedElement = null;
        const selectedElementDisplay = document.getElementById('selected-element-display');
        if (selectedElementDisplay) selectedElementDisplay.textContent = "None";
    } catch (error) {
        console.error('Error during redo:', error);
        alert(`Redo failed: ${error.message}`);
    }
}

function renderPlayerHand(handCounts, totalCount) { // Expects a map of counts
    const playerHandContents = document.getElementById('player-hand-contents');
    if (!playerHandContents) {
        console.error("Player hand container 'player-hand-contents' not found!");
        return;
    }
    playerHandContents.innerHTML = ''; // Clear previous hand display

    if (totalCount === 0) {
        playerHandContents.textContent = 'No seeds in hand.';
    } else {
        // Get all known elements from buttons to display 0 for those not in hand
        const allKnownElements = Array.from(document.querySelectorAll('.element-button'))
                                     .map(btn => btn.dataset.element);

        allKnownElements.forEach(elementName => {
            const count = handCounts[elementName] || 0;
            const handSpan = document.createElement('span');
            handSpan.textContent = `${elementName}: ${count}`;
            playerHandContents.appendChild(handSpan);

            // Update button states
            const button = document.querySelector(`.element-button[data-element="${elementName}"]`);
            if (button) {
                button.disabled = (count === 0);
            }
        });
    }
}


function renderMap(mapData) { // mapData here is actually gameState.map_details
    const mapContainer = document.getElementById('map-container');
    if (!mapContainer) {
        console.error('Map container not found!');
        return;
    }

    mapContainer.innerHTML = ''; // Clear previous content

    // mapContainer.style.display = 'grid'; // This is now handled by style.css
    // Set gridTemplateColumns dynamically based on map width.
    // This is useful if map width can change. If fixed, could be in CSS.
    mapContainer.style.gridTemplateColumns = `repeat(${mapData.width}, auto)`;

    if (mapData && mapData.tiles && mapData.width && mapData.height) {
        mapData.tiles.forEach((row, y) => { // Add y-index for data attribute
            row.forEach((terrainType, x) => { // Add x-index for data attribute
                const tileDiv = document.createElement('div');
                tileDiv.classList.add('tile');

                const terrainClass = `tile-${terrainType.toLowerCase().replace(/\s+/g, '-')}`;
                tileDiv.classList.add(terrainClass);

                tileDiv.textContent = terrainType.charAt(0);

                // Store coordinates on the tile div
                tileDiv.dataset.x = x;
                tileDiv.dataset.y = y;

                tileDiv.addEventListener('click', handleTileClick);

                mapContainer.appendChild(tileDiv);
            });
        });
    } else {
        mapContainer.innerHTML = '<p>Map data is invalid or empty.</p>';
        console.error('Invalid map data:', mapData);
    }
}

async function handleTileClick(event) {
    if (!selectedElement) {
        console.log('No element selected. Click an element button first.');
        // Optionally provide user feedback, e.g., alert or message on page
        // alert('Please select an element first!');
        return;
    }

    const tileDiv = event.currentTarget; // Use currentTarget for the div the listener is attached to
    const x = parseInt(tileDiv.dataset.x, 10);
    const y = parseInt(tileDiv.dataset.y, 10);

    console.log(`Tile clicked at (${x}, ${y}) with element ${selectedElement}`);

    const apiUrl = `${API_BASE_URL}/api/apply_element`;
    const requestBody = {
        x: x,
        y: y,
        element_name: selectedElement
    };

    try {
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody),
        });

        if (!response.ok) {
            // Try to get error details from backend if possible
            let errorMsg = `HTTP error! status: ${response.status}`;
            try {
                const errorData = await response.json();
                errorMsg += ` - ${errorData.detail || JSON.stringify(errorData)}`;
            } catch (e) { /* ignore if error response is not json */ }
            throw new Error(errorMsg);
        }

        const updatedGameState = await response.json();
        renderGameUI(updatedGameState); // Re-render the entire UI with the new state

    } catch (error) {
        console.error('Error applying element:', error);
        // Optionally display this error to the user more prominently
        alert(`Error applying element: ${error.message}`);
    }
}
