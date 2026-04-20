// ==================== CONFIG ====================

const API_URL = "http://localhost:8000/api";
let currentUserId = null;
let currentUsername = null;

// ==================== SCREEN MANAGEMENT ====================

function showScreen(screenName) {
    document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
    const screen = document.getElementById(`screen-${screenName}`);
    if (screen) {
        screen.classList.add("active");
        window.scrollTo(0, 0);
    }
}

// ==================== HOME & AUTH ====================

function showLoginForm() {
    document.getElementById("login-form").style.display = "block";
    document.getElementById("username-input").focus();
}

function hideLoginForm() {
    document.getElementById("login-form").style.display = "none";
    document.getElementById("username-input").value = "";
}

async function handleLogin() {
    const username = document.getElementById("username-input").value.trim();
    if (!username) {
        alert("Please enter a username");
        return;
    }

    try {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username })
        });

        const data = await response.json();

        if (data.status === "success") {
            currentUserId = data.user_id;
            currentUsername = username;
            hideLoginForm();
            await showProfile();
        } else {
            alert("Login failed: " + (data.detail || "Unknown error"));
        }
    } catch (error) {
        alert("Login error: " + error.message);
    }
}

async function startGuest() {
    try {
        const response = await fetch(`${API_URL}/auth/guest`, {
            method: "POST"
        });

        const data = await response.json();

        if (data.status === "success") {
            currentUserId = data.user_id;
            currentUsername = data.player.username;
            await showProfile();
        } else {
            alert("Guest login failed: " + (data.detail || "Unknown error"));
        }
    } catch (error) {
        alert("Guest login error: " + error.message);
    }
}

function logout() {
    currentUserId = null;
    currentUsername = null;
    showScreen("home");
}

// ==================== PROFILE ====================

async function showProfile() {
    if (!currentUserId) {
        showScreen("home");
        return;
    }

    try {
        const response = await fetch(`${API_URL}/player/${currentUserId}`);
        const data = await response.json();

        if (data.status === "success") {
            const player = data.player;
            
            document.getElementById("username-display").textContent = player.username;
            document.getElementById("level-display").textContent = player.level;
            document.getElementById("xp-display").textContent = player.xp;
            document.getElementById("coins-display").textContent = player.coins;
            document.getElementById("tickets-display").textContent = player.dirty_tickets;
            document.getElementById("dives-display").textContent = player.total_dives;

            showScreen("profile");
        } else {
            alert("Failed to load profile");
        }
    } catch (error) {
        alert("Profile error: " + error.message);
    }
}

// ==================== DIVE ====================

async function showDive() {
    showScreen("dive");
    
    try {
        document.getElementById("dive-result").innerHTML = '<div class="loading"></div> Finding treasure...';

        const response = await fetch(`${API_URL}/dive/start`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: currentUserId })
        });

        const result = await response.json();

        if (result.status === "success") {
            let html = `
                <div class="dive-item">${result.item_emoji || "🗑️"}</div>
                <div class="dive-name">${result.item_name}</div>
                <div class="dive-rarity">${result.item_rarity}</div>
                
                <div class="dive-rewards">
                    <div class="reward-item">
                        <div class="reward-amount">+${result.gained_coins}</div>
                        <div class="reward-label">Coins</div>
                    </div>
                    <div class="reward-item">
                        <div class="reward-amount">+${result.gained_xp}</div>
                        <div class="reward-label">XP</div>
                    </div>
                </div>
            `;

            if (result.leveled_up) {
                html += `
                    <div class="level-up">
                        🎉 Level ${result.new_level} Reached!
                    </div>
                `;
            }

            document.getElementById("dive-result").innerHTML = html;
        } else {
            document.getElementById("dive-result").innerHTML = `
                <p class="error-message">Dive failed: ${result.detail || "Unknown error"}</p>
            `;
        }
    } catch (error) {
        document.getElementById("dive-result").innerHTML = `
            <p class="error-message">Dive error: ${error.message}</p>
        `;
    }
}

// ==================== INVENTORY ====================

async function showInventory() {
    showScreen("inventory");
    
    try {
        const response = await fetch(`${API_URL}/player/${currentUserId}/inventory`);
        const data = await response.json();

        if (data.status === "success") {
            const items = data.items;

            if (items.length === 0) {
                document.getElementById("inventory-items").innerHTML = '<p>Your inventory is empty!</p>';
            } else {
                let html = '';
                items.forEach(item => {
                    html += `
                        <div class="inventory-item">
                            <div class="emoji">${item.emoji}</div>
                            <div class="name">${item.name}</div>
                            <div class="quantity">×${item.quantity}</div>
                            <div class="rarity">${item.rarity}</div>
                        </div>
                    `;
                });
                document.getElementById("inventory-items").innerHTML = html;
            }
        } else {
            document.getElementById("inventory-items").innerHTML = `
                <p class="error-message">Failed to load inventory</p>
            `;
        }
    } catch (error) {
        document.getElementById("inventory-items").innerHTML = `
            <p class="error-message">Inventory error: ${error.message}</p>
        `;
    }
}

// ==================== EQUIPMENT ====================

async function showEquipment() {
    showScreen("equipment");
    
    try {
        const response = await fetch(`${API_URL}/player/${currentUserId}/equipment`);
        const data = await response.json();

        if (data.status === "success") {
            const equipment = data.equipment;
            let html = '';

            for (const [slot, item] of Object.entries(equipment)) {
                html += `
                    <div class="equipment-slot">
                        <div class="slot-name">${slot}</div>
                        <div class="slot-item">
                            ${item ? `
                                <span class="emoji">${item.emoji}</span>
                                <div>${item.name}</div>
                            ` : `
                                <div class="slot-empty">Empty</div>
                            `}
                        </div>
                    </div>
                `;
            }

            document.getElementById("equipment-slots").innerHTML = html;
        } else {
            document.getElementById("equipment-slots").innerHTML = `
                <p class="error-message">Failed to load equipment</p>
            `;
        }
    } catch (error) {
        document.getElementById("equipment-slots").innerHTML = `
            <p class="error-message">Equipment error: ${error.message}</p>
        `;
    }
}

// ==================== MUSEUM ====================

async function showMuseum() {
    showScreen("museum");
    
    try {
        // Fetch museum overview
        const museumResponse = await fetch(`${API_URL}/museum/${currentUserId}`);
        const museumData = await museumResponse.json();

        if (museumData.status === "success") {
            document.getElementById("museum-level-display").textContent = museumData.museum_level;
            document.getElementById("museum-xp-display").textContent = museumData.museum_xp;
            document.getElementById("museum-discovered-display").textContent = museumData.discovered_count;
        }

        // Fetch collections
        const collectionsResponse = await fetch(`${API_URL}/museum/${currentUserId}/collections`);
        const collectionsData = await collectionsResponse.json();

        if (collectionsData.status === "success") {
            const collections = collectionsData.collections;

            if (collections.length === 0) {
                document.getElementById("museum-collections").innerHTML = '<p>No collections available</p>';
            } else {
                let html = '';
                collections.forEach(collection => {
                    const statusBadge = collection.is_completed ? '✅ Completed' : '📋 In Progress';
                    html += `
                        <div class="collection-card">
                            <div class="collection-header">
                                <div class="collection-name">${collection.collection_name}</div>
                                <div class="collection-status">${statusBadge}</div>
                            </div>
                            <div class="collection-bar">
                                <div class="collection-progress" style="width: ${collection.progress_percent}%">
                                    <span>${collection.progress_percent}%</span>
                                </div>
                            </div>
                            <div class="collection-percent">
                                ${collection.discovered_count} / ${collection.total_count} items
                            </div>
                        </div>
                    `;
                });
                document.getElementById("museum-collections").innerHTML = html;
            }
        } else {
            document.getElementById("museum-collections").innerHTML = `
                <p class="error-message">Failed to load collections</p>
            `;
        }
    } catch (error) {
        document.getElementById("museum-collections").innerHTML = `
            <p class="error-message">Museum error: ${error.message}</p>
        `;
    }
}

// ==================== PAGE LOAD ====================

document.addEventListener("DOMContentLoaded", function() {
    console.log("Trashbound Web Client loaded");
    console.log("API URL:", API_URL);
});

// Allow Enter key in login form
document.addEventListener("DOMContentLoaded", function() {
    const usernameInput = document.getElementById("username-input");
    if (usernameInput) {
        usernameInput.addEventListener("keypress", function(e) {
            if (e.key === "Enter") {
                handleLogin();
            }
        });
    }
});
