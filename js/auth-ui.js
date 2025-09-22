// js/auth-ui.js

/**
 * Updates the navigation bar UI based on the user's authentication status.
 * This function should be called once the DOM is fully loaded.
 */
function updateAuthUI() {
    const token = localStorage.getItem('authToken');
    
    // Get the containers for the two states
    const loggedOutLinks = document.getElementById('nav-auth-links');
    const loggedInLinks = document.getElementById('nav-user-links');
    
    if (!loggedOutLinks || !loggedInLinks) {
        console.error('Auth UI Error: Could not find nav link containers. Check element IDs.');
        return;
    }

    if (token) {
        // User is logged in
        loggedOutLinks.style.display = 'none';
        loggedInLinks.style.display = 'flex'; // Use 'flex', 'block', or '' depending on your CSS
    } else {
        // User is logged out
        loggedOutLinks.style.display = 'flex';
        loggedInLinks.style.display = 'none';
    }
}

/**
 * Handles the user logout process.
 */
function handleLogout() {
    // Remove the token
    localStorage.removeItem('authToken');
    // Redirect to the home page
    window.location.href = '/';
}


// --- This is the most important part ---
// We wait for the browser to finish loading the HTML before we try to change it.
document.addEventListener('DOMContentLoaded', () => {
    updateAuthUI();

    // Attach the logout function to the logout button
    const logoutButton = document.getElementById('logout-button');
    if (logoutButton) {
        logoutButton.addEventListener('click', handleLogout);
    }
});