let selectedElement = null;
const API_BASE_URL = 'http://localhost:8000'; // Assuming backend runs here

document.addEventListener('DOMContentLoaded', () => {
    fetchMapDataAndRender();
    setupControls();
});

async function fetchMapDataAndRender() {
    const apiUrl = `${API_BASE_URL}/api/map_details`;
    try {
        const response = await fetch(apiUrl);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const mapData = await response.json();
        renderMap(mapData);
    } catch (error) {
        console.error('Error fetching map data:', error);
        const mapContainer = document.getElementById('map-container');
        if (mapContainer) {
            mapContainer.innerHTML = '<p>Error loading map data. Is the backend server running?</p>';
        }
    }
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
}

function renderMap(mapData) {
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

        const updatedMapData = await response.json();
        renderMap(updatedMapData); // Re-render the map with the new state

    } catch (error) {
        console.error('Error applying element:', error);
        // Optionally display this error to the user more prominently
        alert(`Error applying element: ${error.message}`);
    }
}
