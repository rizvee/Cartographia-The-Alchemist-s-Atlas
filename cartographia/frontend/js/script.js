let selectedElement = null;
const API_BASE_URL = 'http://localhost:8000';
let displayedObjectiveId = null;
let objectiveStatusTimeout = null;
let cachedGameState = null; // To store the latest full game state

// Fusion Slot States
let fusionSlot1Element = null;
let fusionSlot2Element = null;

document.addEventListener('DOMContentLoaded', () => {
    fetchGameStateAndRender();
    setupControls();
});

async function fetchGameStateAndRender() {
    const apiUrl = `${API_BASE_URL}/api/game_state`;
    try {
        const response = await fetch(apiUrl);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        cachedGameState = await response.json();
        renderGameUI(cachedGameState);
    } catch (error) {
        console.error('Error fetching game state:', error);
        const mapContainer = document.getElementById('map-container');
        if (mapContainer) {
            mapContainer.innerHTML = '<p>Error loading game data. Is the backend server running?</p>';
        }
        const playerHandContents = document.getElementById('player-hand-contents');
        if(playerHandContents) playerHandContents.textContent = 'Error loading hand.';
        const objectiveDescriptionElement = document.getElementById('objective-description');
        if(objectiveDescriptionElement) objectiveDescriptionElement.textContent = 'Error loading objective.';
        const loreListElement = document.getElementById('lore-entries-list');
        if(loreListElement) loreListElement.innerHTML = '<li>Error loading discoveries.</li>';
    }
}

function renderGameUI(gameStateToRender) {
    if (!gameStateToRender) {
        console.error("No game state to render.");
        return;
    }
    cachedGameState = gameStateToRender;

    if (cachedGameState.map_details) {
        renderMap(cachedGameState.map_details);
    } else {
        console.error("Map details missing in game state:", cachedGameState);
        const mapContainer = document.getElementById('map-container');
        if (mapContainer) mapContainer.innerHTML = '<p>Map data missing in game state.</p>';
    }

    const handCounts = {};
    if (cachedGameState.player_hand) {
        cachedGameState.player_hand.forEach(seedName => {
            handCounts[seedName] = (handCounts[seedName] || 0) + 1;
        });
    }
    renderPlayerHand(handCounts, cachedGameState.player_hand_count);

    const objectiveDescriptionElement = document.getElementById('objective-description');
    const objectiveStatusMessageElement = document.getElementById('objective-status-message');
    if (objectiveDescriptionElement) {
        if (cachedGameState.current_objective && cachedGameState.current_objective.description) {
            if (displayedObjectiveId !== null && cachedGameState.current_objective.id !== displayedObjectiveId) {
                if (objectiveStatusMessageElement) {
                    objectiveStatusMessageElement.textContent = "Objective Completed! New Objective:";
                    objectiveStatusMessageElement.style.opacity = '1';
                    if (objectiveStatusTimeout) clearTimeout(objectiveStatusTimeout);
                    objectiveStatusTimeout = setTimeout(() => {
                        objectiveStatusMessageElement.style.opacity = '0';
                        setTimeout(() => {
                           if (objectiveStatusMessageElement.style.opacity === '0') {
                               objectiveStatusMessageElement.textContent = "";
                           }
                        }, 500);
                    }, 3000);
                }
            } else if (displayedObjectiveId === null && objectiveStatusMessageElement) {
                if (objectiveStatusMessageElement) objectiveStatusMessageElement.textContent = "";
            }
            objectiveDescriptionElement.textContent = cachedGameState.current_objective.description;
            displayedObjectiveId = cachedGameState.current_objective.id;
        } else {
            objectiveDescriptionElement.textContent = "Explore and transform the world!";
            if (objectiveStatusMessageElement) objectiveStatusMessageElement.textContent = "";
            displayedObjectiveId = null;
        }
    } else {
        console.error("Objective description element not found!");
    }

    const discoveredFusionsDisplay = document.getElementById('discovered-fusions-display');
    if (discoveredFusionsDisplay) {
        if (cachedGameState.discovered_fusions && cachedGameState.discovered_fusions.length > 0) {
            discoveredFusionsDisplay.textContent = cachedGameState.discovered_fusions.join(', ');
        } else {
            discoveredFusionsDisplay.textContent = "None yet.";
        }
    } else {
        console.error("Discovered fusions display element not found!");
    }

    // Render Lore Compendium
    if (cachedGameState.discovered_lore) {
        renderLoreCompendium(cachedGameState.discovered_lore);
    } else {
        renderLoreCompendium([]); // Call with empty list if not present
        console.log("No 'discovered_lore' field in game state, rendering empty lore.");
    }
}

function renderLoreCompendium(loreEntries) {
    const loreListElement = document.getElementById('lore-entries-list');
    if (!loreListElement) {
        console.error("Lore entries list element 'lore-entries-list' not found!");
        return;
    }
    loreListElement.innerHTML = '';

    if (loreEntries && loreEntries.length > 0) {
        loreEntries.forEach(entryText => {
            const listItem = document.createElement('li');
            listItem.textContent = entryText;
            loreListElement.appendChild(listItem);
        });
    } else {
        const listItem = document.createElement('li');
        listItem.textContent = "No discoveries yet.";
        loreListElement.appendChild(listItem);
    }
}

function setupControls() {
    const selectedElementDisplay = document.getElementById('selected-element-display');
    const elementButtonsContainer = document.getElementById('element-buttons');

    if (elementButtonsContainer) {
        elementButtonsContainer.addEventListener('click', (event) => {
            if (event.target.classList.contains('element-button')) {
                const clickedElement = event.target.dataset.element;
                if (!event.target.disabled) {
                    selectedElement = clickedElement;
                    if (selectedElementDisplay) selectedElementDisplay.textContent = selectedElement;
                    console.log(`Selected element: ${selectedElement}`);
                } else {
                    console.log(`Cannot select disabled element: ${clickedElement}`);
                }
            }
        });
    }

    const undoButton = document.getElementById('undo-button');
    if (undoButton) undoButton.addEventListener('click', handleUndoClick);

    const redoButton = document.getElementById('redo-button');
    if (redoButton) redoButton.addEventListener('click', handleRedoClick);

    const saveButton = document.getElementById('save-button');
    if (saveButton) saveButton.addEventListener('click', handleSaveClick);

    const loadButton = document.getElementById('load-button');
    if (loadButton) loadButton.addEventListener('click', handleLoadClick);

    const fusionSlot1Display = document.getElementById('fusion-slot-1');
    const fusionSlot2Display = document.getElementById('fusion-slot-2');

    if (fusionSlot1Display) {
        fusionSlot1Display.addEventListener('click', () => {
            if (selectedElement) {
                fusionSlot1Element = selectedElement;
                fusionSlot1Display.textContent = selectedElement;
                fusionSlot1Display.classList.add('filled');
            } else { alert("Select an element first to place it in a fusion slot."); }
        });
    }

    if (fusionSlot2Display) {
        fusionSlot2Display.addEventListener('click', () => {
            if (selectedElement) {
                fusionSlot2Element = selectedElement;
                fusionSlot2Display.textContent = selectedElement;
                fusionSlot2Display.classList.add('filled');
            } else { alert("Select an element first to place it in a fusion slot."); }
        });
    }

    const clearFusionSlotsButton = document.getElementById('clear-fusion-slots-button');
    if (clearFusionSlotsButton) {
        clearFusionSlotsButton.addEventListener('click', () => {
            fusionSlot1Element = null;
            fusionSlot2Element = null;
            if(fusionSlot1Display) {
                fusionSlot1Display.textContent = "Slot 1";
                fusionSlot1Display.classList.remove('filled');
            }
            if(fusionSlot2Display) {
                fusionSlot2Display.textContent = "Slot 2";
                fusionSlot2Display.classList.remove('filled');
            }
            const fusionResultMessage = document.getElementById('fusion-result-message');
            if (fusionResultMessage) fusionResultMessage.textContent = "";
        });
    }

    const fuseButton = document.getElementById('fuse-button');
    if (fuseButton) fuseButton.addEventListener('click', handleFuseClick);
}

function renderPlayerHand(handCounts, totalCount) {
    const playerHandContents = document.getElementById('player-hand-contents');
    if (!playerHandContents) return;
    playerHandContents.innerHTML = '';

    const elementButtonsContainer = document.getElementById('element-buttons');
    if (!elementButtonsContainer) return;
    elementButtonsContainer.innerHTML = '';

    if (totalCount === 0) {
        playerHandContents.textContent = 'No seeds in hand.';
    } else {
        playerHandContents.textContent = '';
        const uniqueSeedNames = Object.keys(handCounts).sort();

        uniqueSeedNames.forEach(seedName => {
            const count = handCounts[seedName] || 0;
            const handSpan = document.createElement('span');
            handSpan.textContent = `${seedName}: ${count}`;
            playerHandContents.appendChild(handSpan);

            const button = document.createElement('button');
            button.classList.add('element-button');
            button.dataset.element = seedName;
            button.textContent = `${seedName} (${count})`;
            button.disabled = (count === 0);
            elementButtonsContainer.appendChild(button);
        });
    }
}

function renderMap(mapDetails) {
    const mapContainer = document.getElementById('map-container');
    if (!mapContainer) return;
    mapContainer.innerHTML = '';
    mapContainer.style.gridTemplateColumns = `repeat(${mapDetails.width}, auto)`;

    if (mapDetails && mapDetails.tiles && mapDetails.width && mapDetails.height) {
        mapDetails.tiles.forEach((row, y) => {
            row.forEach((tileData, x) => {
                const tileDiv = document.createElement('div');
                tileDiv.classList.add('tile');
                const terrainType = tileData.terrain_type || 'unknown';
                const terrainClass = `tile-${terrainType.toLowerCase().replace(/\s+/g, '-')}`;
                tileDiv.classList.add(terrainClass);

                const terrainCharSpan = document.createElement('span');
                terrainCharSpan.classList.add('terrain-char');
                terrainCharSpan.textContent = terrainType.charAt(0);
                tileDiv.appendChild(terrainCharSpan);

                if (tileData.feature) {
                    const featureSpan = document.createElement('span');
                    featureSpan.classList.add('tile-feature');
                    featureSpan.classList.add(`feature-${tileData.feature.toLowerCase().replace(/\s+/g, '-')}`);
                    featureSpan.textContent = tileData.feature.charAt(0).toUpperCase();
                    tileDiv.appendChild(featureSpan);
                }

                tileDiv.dataset.x = x;
                tileDiv.dataset.y = y;
                tileDiv.addEventListener('click', handleTileClick);
                tileDiv.addEventListener('mouseover', handleTileMouseOver);
                tileDiv.addEventListener('mouseout', handleTileMouseOut);
                mapContainer.appendChild(tileDiv);
            });
        });
    } else {
        mapContainer.innerHTML = '<p>Map data is invalid or empty.</p>';
    }
}

async function handleTileClick(event) {
    if (!selectedElement) {
        alert('Please select an element first!');
        return;
    }
    const tileDiv = event.currentTarget;
    const x = parseInt(tileDiv.dataset.x, 10);
    const y = parseInt(tileDiv.dataset.y, 10);
    console.log(`Tile clicked at (${x}, ${y}) with element ${selectedElement}`);

    const apiUrl = `${API_BASE_URL}/api/apply_element`;
    const requestBody = { x: x, y: y, element_name: selectedElement };

    try {
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody),
        });
        const responseData = await response.json();
        if (!response.ok) throw new Error(responseData.detail || `HTTP error! status: ${response.status}`);
        cachedGameState = responseData;
        renderGameUI(cachedGameState);
    } catch (error) {
        console.error('Error applying element:', error);
        alert(`Error applying element: ${error.message}`);
    }
}

async function handleUndoClick() {
    console.log("Undo button clicked");
    const apiUrl = `${API_BASE_URL}/api/undo`;
    try {
        const response = await fetch(apiUrl, { method: 'POST' });
        const responseData = await response.json();
        if (!response.ok) throw new Error(responseData.detail || "Unknown error during undo.");
        cachedGameState = responseData;
        renderGameUI(cachedGameState);
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
        const responseData = await response.json();
        if (!response.ok) throw new Error(responseData.detail || "Unknown error during redo.");
        cachedGameState = responseData;
        renderGameUI(cachedGameState);
        selectedElement = null;
        const selectedElementDisplay = document.getElementById('selected-element-display');
        if (selectedElementDisplay) selectedElementDisplay.textContent = "None";
    } catch (error) {
        console.error('Error during redo:', error);
        alert(`Redo failed: ${error.message}`);
    }
}

async function handleSaveClick() {
    console.log("Save Game button clicked");
    const apiUrl = `${API_BASE_URL}/api/save_map`;
    try {
        const response = await fetch(apiUrl, { method: 'POST' });
        const responseData = await response.json();
        if (!response.ok) throw new Error(responseData.detail || `HTTP error! status: ${response.status}`);
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
        const responseData = await response.json();
        if (!response.ok) throw new Error(responseData.detail || "Unknown error during load.");
        cachedGameState = responseData;
        renderGameUI(cachedGameState);
        selectedElement = null;
        const selectedElementDisplay = document.getElementById('selected-element-display');
        if (selectedElementDisplay) selectedElementDisplay.textContent = "None";
        alert("Game loaded successfully!");
    } catch (error) {
        console.error('Error loading game:', error);
        alert(`Load failed: ${error.message}`);
    }
}

async function handleFuseClick() {
    const fusionResultMessage = document.getElementById('fusion-result-message');
    if (!fusionSlot1Element || !fusionSlot2Element) {
        if(fusionResultMessage) fusionResultMessage.textContent = "Please select two elements for fusion.";
        return;
    }
    if(fusionResultMessage) fusionResultMessage.textContent = `Fusing ${fusionSlot1Element} + ${fusionSlot2Element}...`;
    const requestBody = { element1: fusionSlot1Element, element2: fusionSlot2Element };
    try {
        const response = await fetch(`${API_BASE_URL}/api/fuse_elements`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });
        const resultData = await response.json();
        if (!response.ok) throw new Error(resultData.detail || `HTTP error! status: ${response.status}`);
        if(fusionResultMessage) fusionResultMessage.textContent = resultData.message;

        // Re-fetch full game state to update hand, discovered fusions, and potentially lore
        cachedGameState = await fetch(`${API_BASE_URL}/api/game_state`).then(res => res.json());
        renderGameUI(cachedGameState);

        fusionSlot1Element = null; fusionSlot2Element = null;
        const fSlot1 = document.getElementById('fusion-slot-1');
        const fSlot2 = document.getElementById('fusion-slot-2');
        if(fSlot1) { fSlot1.textContent = "Slot 1"; fSlot1.classList.remove('filled'); }
        if(fSlot2) { fSlot2.textContent = "Slot 2"; fSlot2.classList.remove('filled'); }
    } catch (error) {
        console.error("Error fusing elements:", error);
        if(fusionResultMessage) fusionResultMessage.textContent = `Fusion error: ${error.message}`;
    }
}

function handleTileMouseOver(event) {
    if (!cachedGameState || !cachedGameState.map_details || !cachedGameState.map_details.grid) return;
    const tileDiv = event.currentTarget;
    const x = parseInt(tileDiv.dataset.x, 10);
    const y = parseInt(tileDiv.dataset.y, 10);
    const tileData = cachedGameState.map_details.grid[y]?.[x];

    const infoPanel = document.getElementById('tile-info-panel');
    if (infoPanel && tileData) {
        let content = `<h4>Tile Details</h4>`;
        content += `<p><strong>Coords:</strong> (${x}, ${y})</p>`;
        content += `<p><strong>Terrain:</strong> ${tileData.terrain_type || 'N/A'}</p>`;
        content += `<p><strong>Elevation:</strong> ${tileData.elevation !== undefined ? tileData.elevation : 'N/A'}</p>`;
        if (tileData.feature) {
            content += `<p><strong>Feature:</strong> ${tileData.feature}</p>`;
        } else {
            content += `<p><strong>Feature:</strong> None</p>`;
        }

        content += "<p><strong>Saturation:</strong>";
        if (tileData.elemental_saturation && Object.keys(tileData.elemental_saturation).length > 0) {
            const saturationEntries = Object.entries(tileData.elemental_saturation)
                                        .filter(([, value]) => value > 0)
                                        .sort(([keyA], [keyB]) => keyA.localeCompare(keyB));
            if (saturationEntries.length > 0) {
                content += "<ul>";
                saturationEntries.forEach(([key, value]) => {
                    content += `<li>${key}: ${value.toFixed(0)}</li>`;
                });
                content += "</ul>";
            } else {
                content += " None";
            }
        } else {
            content += " N/A";
        }
        content += "</p>";

        infoPanel.innerHTML = content;
        infoPanel.classList.add('visible');
    } else if (infoPanel) {
        infoPanel.innerHTML = '<p>Error: Could not retrieve tile data.</p>';
        infoPanel.classList.add('visible');
    }
}

function handleTileMouseOut(event) {
    const infoPanel = document.getElementById('tile-info-panel');
    if (infoPanel) {
        infoPanel.classList.remove('visible');
        setTimeout(() => {
            if (!infoPanel.classList.contains('visible')) {
                infoPanel.innerHTML = 'Hover over a tile to see details.';
            }
        }, 300);
    }
}
