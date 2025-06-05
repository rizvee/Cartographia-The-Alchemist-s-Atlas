document.addEventListener('DOMContentLoaded', () => {
    const API_BASE_URL = 'http://localhost:8000/api'; // Adjust if your backend runs elsewhere

    // DOM Elements
    const mapContainer = document.getElementById('map-container');
    const elementButtonsContainer = document.getElementById('element-buttons');
    const selectedElementDisplay = document.getElementById('selected-element-display');
    const playerHandContents = document.getElementById('player-hand-contents');

    const fusionSlot1Display = document.getElementById('fusion-slot-1');
    const fusionSlot2Display = document.getElementById('fusion-slot-2');
    const fuseButton = document.getElementById('fuse-button');
    const clearFusionSlotsButton = document.getElementById('clear-fusion-slots-button');
    const fusionResultMessage = document.getElementById('fusion-result-message');
    const discoveredFusionsDisplay = document.getElementById('discovered-fusions-display');

    const objectiveDescription = document.getElementById('objective-description');
    const objectiveStatusMessage = document.getElementById('objective-status-message');
    const objectiveRequirementsList = document.getElementById('objective-requirements-list'); // New element

    const undoButton = document.getElementById('undo-button');
    const redoButton = document.getElementById('redo-button');
    const saveButton = document.getElementById('save-button');
    const loadButton = document.getElementById('load-button');
    const resetButton = document.getElementById('reset-button');

    const tileInfoPanel = document.getElementById('tile-info-panel');
    const infoTerrain = document.getElementById('info-terrain');
    const infoElevation = document.getElementById('info-elevation');
    const infoFeature = document.getElementById('info-feature');
    const infoSaturation = document.getElementById('info-saturation');

    const loreEntriesList = document.getElementById('lore-entries-list');
    const eventMessageDiv = document.getElementById('event-message'); // New event message div

    // Game State Variables
    let selectedElement = null;
    let fusionSlot1Element = null;
    let fusionSlot2Element = null;
    let currentGameState = null; // To cache the latest game state
    let displayedObjectiveId = null; // To track objective message display
    let objectiveStatusTimeout = null; // Timeout for clearing objective completion message

    // --- Utility Functions ---
    async function apiRequest(endpoint, method = 'GET', body = null) {
        const options = {
            method,
            headers: { 'Content-Type': 'application/json' },
        };
        if (body) {
            options.body = JSON.stringify(body);
        }
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: response.statusText }));
                throw new Error(`API Error (${response.status}): ${errorData.detail || 'Unknown error'}`);
            }
            return response.json();
        } catch (error) {
            console.error(`Error during API request to ${endpoint}:`, error);
            alert(`Error: ${error.message}`); // Simple error display
            throw error; // Re-throw to allow callers to handle
        }
    }

    // --- Rendering Functions ---
    function renderMap(mapDetails) {
        if (!mapDetails || !mapDetails.grid) {
            console.error("Invalid map details for rendering:", mapDetails);
            mapContainer.innerHTML = '<p>Error loading map.</p>';
            return;
        }
        mapContainer.innerHTML = ''; // Clear previous map
        mapContainer.style.gridTemplateColumns = `repeat(${mapDetails.width}, 1fr)`;

        mapDetails.grid.forEach((row, y) => {
            row.forEach((tileData, x) => {
                const tileDiv = document.createElement('div');
                tileDiv.classList.add('tile');
                tileDiv.dataset.x = x;
                tileDiv.dataset.y = y;
                tileDiv.dataset.terrain = tileData.terrain_type; // For styling

                // Basic representation: first letter of terrain type or a symbol
                let tileSymbol = tileData.terrain_type.charAt(0).toUpperCase();
                if (tileData.terrain_type === "Water") tileSymbol = "~";
                if (tileData.terrain_type === "Forest") tileSymbol = "T";
                if (tileData.terrain_type === "Mountain") tileSymbol = "M";
                if (tileData.terrain_type === "Desert") tileSymbol = "D";
                if (tileData.terrain_type === "Volcano") tileSymbol = "V";
                // Add more symbols as needed

                tileDiv.textContent = tileSymbol;

                if (tileData.feature) {
                    const featureSpan = document.createElement('span');
                    featureSpan.classList.add('tile-feature');

                    switch (tileData.feature) {
                        case "Ruins":
                            featureSpan.textContent = "R";
                            featureSpan.classList.add('feature-ruins'); // Optional: if specific styling needed beyond general .tile-feature
                            break;
                        case "Ancient Obelisk":
                            featureSpan.textContent = "O";
                            featureSpan.classList.add('feature-ancient-obelisk');
                            break;
                        case "Activated Obelisk":
                            featureSpan.textContent = "O*";
                            featureSpan.classList.add('feature-activated-obelisk');
                            break;
                        default:
                            featureSpan.textContent = "F"; // Generic feature
                    }
                    tileDiv.appendChild(featureSpan);
                }

                tileDiv.addEventListener('click', () => handleTileClick(x, y));
                tileDiv.addEventListener('mouseover', () => handleTileMouseOver(x,y));
                tileDiv.addEventListener('mouseout', handleTileMouseOut);
                mapContainer.appendChild(tileDiv);
            });
        });
    }

    function renderPlayerHand(handCounts, totalCount) { // handCounts is a dict like {'Earth': 2}
        elementButtonsContainer.innerHTML = ''; // Clear old buttons
        playerHandContents.innerHTML = ''; // Clear old text display

        if (totalCount === 0) {
            playerHandContents.textContent = 'Hand is empty.';
            return;
        }

        const uniqueElements = Object.keys(handCounts).sort();

        uniqueElements.forEach(elementName => {
            const count = handCounts[elementName];
            // Update text display
            const handEntry = document.createElement('p');
            handEntry.textContent = `${elementName}: ${count}`;
            playerHandContents.appendChild(handEntry);

            // Create buttons for applying elements
            const button = document.createElement('button');
            button.classList.add('element-button');
            button.textContent = `${elementName} (${count})`;
            button.dataset.element = elementName;
            button.disabled = count === 0;
            elementButtonsContainer.appendChild(button);
        });
    }

    function renderObjective(objective) {
        objectiveRequirementsList.innerHTML = ''; // Clear previous requirements

        if (!objective) {
            objectiveDescription.textContent = "No current objective.";
            objectiveStatusMessage.textContent = "";
            return;
        }

        // Handle "Objective Completed!" message
        if (objective.completed && objective.id !== displayedObjectiveId) {
            objectiveStatusMessage.textContent = "Objective Completed! New Objective:";
            displayedObjectiveId = objective.id;

            if (objectiveStatusTimeout) clearTimeout(objectiveStatusTimeout);
            objectiveStatusTimeout = setTimeout(() => {
                objectiveStatusMessage.textContent = "";
            }, 5000);
        } else if (!objective.completed && objective.id !== displayedObjectiveId) {
            objectiveStatusMessage.textContent = "";
            displayedObjectiveId = objective.id;
        }

        objectiveDescription.textContent = objective.description;

        // Display sub-requirements
        if (objective.requirements && Array.isArray(objective.requirements)) {
            objective.requirements.forEach(req => {
                const li = document.createElement('li');
                let reqText = "Unknown requirement";
                switch (req.type) {
                    case "terrain_count":
                        reqText = ` - Have at least ${req.min_count} tile(s) of '${req.terrain}' terrain.`;
                        break;
                    case "feature_adjacent_to_terrain":
                        // Note: The original subtask description for this type was:
                        // `Text = f" - Have {req.min_count} {req.feature} next to {req.terrain}."`
                        // The actual Objective model in models.py for this type is:
                        // {"type": "feature_adjacent_to_terrain", "feature": None, "terrain": "River", "target_terrain": "Forest", "min_count": 1}
                        // This seems to imply "a feature (or lack thereof if feature is None) on a tile of target_terrain, adjacent to a tile of terrain"
                        // Or, more likely, it was simplified in game_logic.py's PREDEFINED_OBJECTIVES.
                        // Let's check OBJ003: {"type": "feature_adjacent_to_terrain", "feature": None, "terrain": "River", "target_terrain": "Forest", "min_count": 1}
                        // This means "A Forest tile (target_terrain) adjacent to a River tile (terrain)". 'feature' here is not the primary aspect.
                        // The check_completion logic for this in models.py iterates through tiles, checks if tile.feature matches req.feature,
                        // then checks neighbors for req.terrain. This is a bit confusing.
                        // Let's assume the description from subtask is what user wants to see for now if feature is specified.
                        // If feature is not specified, it's about target_terrain next to terrain.
                        if (req.feature) {
                             reqText = ` - Have ${req.min_count} instance(s) of '${req.feature}' feature adjacent to '${req.terrain}' terrain.`;
                        } else if (req.target_terrain) {
                             reqText = ` - Have ${req.min_count} instance(s) of '${req.target_terrain}' terrain adjacent to '${req.terrain}' terrain.`;
                        } else {
                             reqText = ` - Complex adjacency requirement involving '${req.terrain}'.`;
                        }
                        break;
                    case "discover_fusions":
                        reqText = ` - Discover at least ${req.min_count} unique fusion(s).`;
                        break;
                    case "specific_tile_condition":
                        let condition_parts = [];
                        if (req.expected_terrain) condition_parts.push(`terrain is '${req.expected_terrain}'`);
                        if (req.has_feature) condition_parts.push(`has feature '${req.has_feature}'`);
                        else if (req.hasOwnProperty('has_feature') && req.has_feature === null) condition_parts.push('has no feature');
                        // Add more conditions like elevation, saturation if they get added to objectives
                        reqText = ` - Tile at (${req.x}, ${req.y}) must satisfy: ${condition_parts.join(' and ')}.`;
                        break;
                    // Add more cases here as new requirement types are defined in backend
                    default:
                        console.warn("Unknown objective requirement type:", req.type);
                }
                li.textContent = reqText;
                li.style.opacity = '0'; // Initial state for transition
                objectiveRequirementsList.appendChild(li);
                requestAnimationFrame(() => { // Ensure element is in DOM
                    setTimeout(() => { // Allow browser to paint initial opacity=0
                        li.style.opacity = '1';
                    }, 0); // Minimal delay
                });
            });
        }
    }

    function renderFusionPanel(discoveredFusions) {
        fusionSlot1Display.textContent = fusionSlot1Element || "Empty";
        fusionSlot1Display.dataset.element = fusionSlot1Element || "";
        fusionSlot2Display.textContent = fusionSlot2Element || "Empty";
        fusionSlot2Display.dataset.element = fusionSlot2Element || "";

        discoveredFusionsDisplay.innerHTML = '';
        if (discoveredFusions && discoveredFusions.length > 0) {
            discoveredFusions.forEach(fusionName => {
                const li = document.createElement('li');
                li.textContent = fusionName;
                // No fade-in for discovered fusions list for now, could be added if desired
                discoveredFusionsDisplay.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.textContent = "No fusions discovered yet.";
            discoveredFusionsDisplay.appendChild(li);
        }
    }

    function renderLoreCompendium(loreEntries) {
        loreEntriesList.innerHTML = '';
        if (loreEntries && loreEntries.length > 0) {
            loreEntries.forEach(entry => {
                const li = document.createElement('li');
                li.textContent = entry;
                li.style.opacity = '0'; // Initial state for transition
                loreEntriesList.appendChild(li);
                requestAnimationFrame(() => { // Ensure element is in DOM
                     setTimeout(() => { // Allow browser to paint initial opacity=0
                        li.style.opacity = '1';
                    }, 0); // Minimal delay
                });
            });
        } else {
            const li = document.createElement('li');
            li.textContent = "No lore entries discovered yet.";
            loreEntriesList.appendChild(li);
        }
    }


    function renderGameUI(gameState) {
        if (!gameState) return;

        const oldGameState = currentGameState; // Preserve old state for comparison
        currentGameState = gameState; // Cache the new state

        // Check for Obelisk activation before rendering map
        if (oldGameState && oldGameState.map_details && gameState.map_details) {
            gameState.map_details.grid.forEach((row, y) => {
                row.forEach((newTileData, x) => {
                    const oldTileData = oldGameState.map_details.grid[y]?.[x];
                    if (oldTileData &&
                        oldTileData.feature === "Ancient Obelisk" &&
                        newTileData.feature === "Activated Obelisk") {

                        displayTemporaryEventMessage("Ancient Obelisk Activated!");
                    }
                });
            });
        }

        renderMap(gameState.map_details);
        renderPlayerHand(gameState.player_hand_count || {}, (gameState.player_hand || []).length);
        renderObjective(gameState.current_objective);
        renderFusionPanel(gameState.discovered_fusions);
        renderLoreCompendium(gameState.discovered_lore);

        // Reset selections
        selectedElement = null;
        selectedElementDisplay.textContent = 'None';
        // fusionSlot1Element and fusionSlot2Element are NOT reset here,
        // because a failed fusion might return a new game state but the player
        // would want their slots preserved. They are cleared by "Clear Slots" or successful fusion.
    }

    // --- Event Handlers ---
    async function handleTileClick(x, y) {
        if (!selectedElement) {
            alert("Please select an element first.");
            return;
        }
        try {
            const updatedGameState = await apiRequest('/apply_element', 'POST', { x, y, element_name: selectedElement });
            renderGameUI(updatedGameState);
            // No need to reset selectedElement here as renderGameUI does it
        } catch (error) {
            // Error already alerted by apiRequest
        }
    }

    function handleTileMouseOver(x,y) {
        if (!currentGameState || !currentGameState.map_details) return;
        const tileData = currentGameState.map_details.grid[y][x];
        if (!tileData) return;

        infoTerrain.textContent = tileData.terrain_type;
        infoElevation.textContent = tileData.elevation;
        infoFeature.textContent = tileData.feature || "None";

        infoSaturation.innerHTML = ''; // Clear previous saturation
        for (const [element, value] of Object.entries(tileData.elemental_saturation)) {
            if (value > 0) { // Only show elements with some saturation
                const p = document.createElement('p');
                p.textContent = `${element}: ${value}`;
                infoSaturation.appendChild(p);
            }
        }
        tileInfoPanel.style.display = 'block';
    }

    function handleTileMouseOut() {
        tileInfoPanel.style.display = 'none';
    }

    function selectElementForApplication(elementName) {
        selectedElement = elementName;
        selectedElementDisplay.textContent = elementName;
        fusionResultMessage.textContent = ''; // Clear previous fusion messages
    }

    function selectElementForFusion(elementName) {
        if (!elementName) return; // Should not happen if called from valid button

        if (!fusionSlot1Element) {
            fusionSlot1Element = elementName;
        } else if (!fusionSlot2Element) {
            fusionSlot2Element = elementName;
        } else {
            fusionResultMessage.textContent = "Both fusion slots are full. Clear one first.";
            return;
        }
        renderFusionPanel(currentGameState ? currentGameState.discovered_fusions : []);
        fusionResultMessage.textContent = ''; // Clear previous fusion messages
    }

    function handleElementButtonClick(event) {
        const clickedButton = event.target.closest('.element-button');
        if (!clickedButton || clickedButton.disabled) return;

        const elementName = clickedButton.dataset.element;

        // Simple toggle: if an element is selected for application, clicking another selects it.
        // If it's for fusion, it tries to fill a slot.
        // This could be more sophisticated (e.g. different modes for "Apply" vs "Fuse")
        // For now, let's prioritize application, then fusion if application target is not clear.
        // A more robust approach: Have "Add to Fusion Slot 1/2" buttons or a context menu.

        // Current simplified logic:
        // If selectedElement is already this element, it's a toggle to deselect for application.
        if (selectedElement === elementName) {
            selectedElement = null;
            selectedElementDisplay.textContent = 'None';
        } else {
            // If it's a different element, or no element is selected for application, select this one.
            selectElementForApplication(elementName);
        }
        // Also, try to add to fusion slot if a slot is empty
        // This might be confusing. Consider separate "add to slot" interaction.
        // For now, clicking an element button will BOTH select it for application AND try to put it in a fusion slot.
        selectElementForFusion(elementName);
    }


    async function handleFuse() {
        if (!fusionSlot1Element || !fusionSlot2Element) {
            fusionResultMessage.textContent = "Please select two elements for fusion.";
            return;
        }
        try {
            const response = await apiRequest('/fuse_elements', 'POST', {
                element1_name: fusionSlot1Element,
                element2_name: fusionSlot2Element,
            });
            // response should be the full game state, plus last_fusion_result
            fusionResultMessage.classList.remove('success', 'error'); // Clear previous classes
            if (response.last_fusion_result) {
                fusionResultMessage.textContent = response.last_fusion_result.message;
                if (response.last_fusion_result.success) {
                    fusionResultMessage.classList.add('success');
                    fusionSlot1Element = null; // Clear slots on successful fusion
                    fusionSlot2Element = null;
                } else {
                    fusionResultMessage.classList.add('error');
                }
            } else {
                fusionResultMessage.textContent = "Fusion request processed, but no specific result message.";
            }
            renderGameUI(response); // This will re-render fusion panel (and clear slots if needed)
        } catch (error) {
            fusionResultMessage.classList.remove('success');
            fusionResultMessage.classList.add('error');
            fusionResultMessage.textContent = `Fusion failed: ${error.message}`;
        }
    }

    function handleClearFusionSlots() {
        fusionSlot1Element = null;
        fusionSlot2Element = null;
        fusionResultMessage.textContent = "Fusion slots cleared.";
        if (currentGameState) { // Re-render to show empty slots
            renderFusionPanel(currentGameState.discovered_fusions);
        } else { // Fallback if no game state yet
            fusionSlot1Display.textContent = "Empty";
            fusionSlot2Display.textContent = "Empty";
        }
    }

    // --- Action Button Handlers ---
    async function handleUndoClick() {
        try {
            // Assuming /api/undo endpoint exists and returns new game state
            const updatedGameState = await apiRequest('/undo', 'POST');
            renderGameUI(updatedGameState);
            fusionResultMessage.textContent = "Last action undone.";
        } catch (error) {
            fusionResultMessage.textContent = `Undo failed: ${error.message}`;
        }
    }

    async function handleRedoClick() {
        try {
            // Assuming /api/redo endpoint exists
            const updatedGameState = await apiRequest('/redo', 'POST');
            renderGameUI(updatedGameState);
            fusionResultMessage.textContent = "Last undone action redone.";
        } catch (error) {
            fusionResultMessage.textContent = `Redo failed: ${error.message}`;
        }
    }

    async function handleSaveClick() {
        try {
            const response = await apiRequest('/save_map', 'POST');
            alert(response.message || "Game saved!"); // Show confirmation
        } catch (error) {
            // Error already alerted
        }
    }

    async function handleLoadClick() {
        if (!confirm("Loading will overwrite current game. Are you sure?")) return;
        try {
            const loadedGameState = await apiRequest('/load_map', 'POST');
            renderGameUI(loadedGameState);
            fusionSlot1Element = null; // Clear fusion slots on load
            fusionSlot2Element = null;
            fusionResultMessage.textContent = "Game loaded.";
            objectiveStatusMessage.textContent = ""; // Clear any lingering objective messages
            displayedObjectiveId = loadedGameState.current_objective ? loadedGameState.current_objective.id : null;
        } catch (error) {
            // Error already alerted
        }
    }

    async function handleResetClick() {
        if (!confirm("Are you sure you want to reset the game? All progress will be lost.")) return;
        try {
            const freshGameState = await apiRequest('/reset_game', 'POST');
            renderGameUI(freshGameState);
            fusionSlot1Element = null; // Clear fusion slots on reset
            fusionSlot2Element = null;
            fusionResultMessage.textContent = "Game has been reset.";
            objectiveStatusMessage.textContent = ""; // Clear any lingering objective messages
            displayedObjectiveId = freshGameState.current_objective ? freshGameState.current_objective.id : null;

        } catch (error)
        {
            // Error already alerted
        }
    }

    // --- Initial Setup ---
    async function fetchGameStateAndRender() {
        try {
            const initialState = await apiRequest('/game_state');
            renderGameUI(initialState);
        } catch (error) {
            mapContainer.innerHTML = `<p>Error fetching initial game state: ${error.message}. Please ensure the backend server is running.</p>`;
        }
    }

    function setupEventListeners() {
        // Event delegation for dynamically created element buttons
        elementButtonsContainer.addEventListener('click', handleElementButtonClick);

        fuseButton.addEventListener('click', handleFuse);
        clearFusionSlotsButton.addEventListener('click', handleClearFusionSlots);

        // Undo/Redo buttons are initially disabled as backend support is pending
        undoButton.addEventListener('click', handleUndoClick);
        // undoButton.disabled = true; // Enable once backend is ready
        redoButton.addEventListener('click', handleRedoClick);
        // redoButton.disabled = true; // Enable once backend is ready

        saveButton.addEventListener('click', handleSaveClick);
        loadButton.addEventListener('click', handleLoadClick);
        resetButton.addEventListener('click', handleResetClick);
    }

    // --- Start ---
    fetchGameStateAndRender();
    setupEventListeners();

    function displayTemporaryEventMessage(message) {
        if (!eventMessageDiv) return;
        eventMessageDiv.textContent = message;
        eventMessageDiv.classList.add('visible');
        setTimeout(() => {
            eventMessageDiv.classList.remove('visible');
        }, 3000); // Message visible for 3 seconds
    }
});
