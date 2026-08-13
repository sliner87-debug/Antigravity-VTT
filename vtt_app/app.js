const mapContainer = document.getElementById('map-container');
const logPanel = document.getElementById('log-panel');
const connectBtn = document.getElementById('connect-btn');
const repoInput = document.getElementById('repo-input');

let pollInterval = null;
const GRID_SIZE = 50; 
let knownEntities = {};

function log(msg) {
    const div = document.createElement('div');
    div.textContent = `> ${new Date().toLocaleTimeString()} - ${msg}`;
    logPanel.appendChild(div);
    logPanel.scrollTop = logPanel.scrollHeight;
}

function updateToken(entity) {
    let token = document.getElementById(`token-${entity.id}`);
    
    // Create token if it doesn't exist
    if (!token) {
        token = document.createElement('div');
        token.id = `token-${entity.id}`;
        token.className = `token ${entity.role.toLowerCase().includes('player') || entity.role.toLowerCase().includes('npc companion') ? 'player' : 'npc'}`;
        token.textContent = entity.name.substring(0, 4);
        token.title = `${entity.name}\nHP: ${entity.current_hp}/${entity.max_hp}`;
        mapContainer.appendChild(token);
        log(`Spawned token for ${entity.name}`);
    } else {
        token.title = `${entity.name}\nHP: ${entity.current_hp}/${entity.max_hp}`;
    }
    
    if (entity.image) {
        token.style.backgroundImage = `url('assets/${entity.image}')`;
        token.textContent = ''; // Clear text if image exists
    }

    // Determine grid coordinates (defaulting to 0 if missing)
    const x = entity.x || 0;
    const y = entity.y || 0;

    // Apply translation
    token.style.transform = `translate(${x * GRID_SIZE}px, ${y * GRID_SIZE}px)`;
    
    // Log movement if changed
    if (knownEntities[entity.id] && (knownEntities[entity.id].x !== x || knownEntities[entity.id].y !== y)) {
        log(`${entity.name} moved to (${x}, ${y})`);
    }
    
    knownEntities[entity.id] = {x, y};
}

async function fetchState(repo) {
    // Generate the raw URL. Note: GitHub raw files are aggressively cached. 
    // Appending a cache-busting timestamp is necessary.
    const url = `https://raw.githubusercontent.com/${repo}/main/campaign_state.json?t=${new Date().getTime()}`;
    
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const state = await response.json();
        
        // Update all entities
        if (state.entities && Array.isArray(state.entities)) {
            state.entities.forEach(updateToken);
        }
    } catch (error) {
        console.error("Error fetching state:", error);
    }
}

connectBtn.addEventListener('click', () => {
    const repo = repoInput.value.trim();
    if (!repo || repo === "Username/RepoName") {
        alert("Please enter a valid GitHub Username/RepoName");
        return;
    }
    
    log(`Connecting to GitHub repository: ${repo}...`);
    
    if (pollInterval) {
        clearInterval(pollInterval);
    }
    
    // Initial fetch
    fetchState(repo);
    
    // Poll every 3 seconds
    pollInterval = setInterval(() => {
        fetchState(repo);
    }, 3000);
    
    connectBtn.textContent = "Connected (Polling)";
    connectBtn.style.backgroundColor = "#5a8f2b";
});
