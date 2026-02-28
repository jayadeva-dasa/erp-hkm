/**
 * HKM Theme Toggle - Dark/Light Mode Switcher
 * Automatically saves user preference to localStorage
 */

(function() {
    'use strict';
    
    // Check for saved theme preference or default to 'light'
    const getThemePreference = () => {
        return localStorage.getItem('hkm-theme') || 'light';
    };
    
    // Save theme preference
    const saveThemePreference = (theme) => {
        localStorage.setItem('hkm-theme', theme);
    };
    
    // Apply theme to document
    const applyTheme = (theme) => {
        document.documentElement.setAttribute('data-theme', theme);
        updateToggleButton(theme);
    };
    
    // Update toggle button icon
    const updateToggleButton = (theme) => {
        const button = document.querySelector('.theme-toggle-btn');
        if (!button) return;
        
        if (theme === 'dark') {
            button.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
            `;
            button.setAttribute('title', 'Switch to Light Mode');
        } else {
            button.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
            `;
            button.setAttribute('title', 'Switch to Dark Mode');
        }
    };
    
    // Toggle theme
    const toggleTheme = () => {
        const currentTheme = getThemePreference();
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        saveThemePreference(newTheme);
        applyTheme(newTheme);
        
        // Show a brief notification
        showThemeNotification(newTheme);
    };
    
    // Show theme change notification
    const showThemeNotification = (theme) => {
        const themeName = theme === 'dark' ? 'Dark Mode' : 'Light Mode';
        
        // Use Frappe's notification system if available
        if (window.frappe && frappe.show_alert) {
            frappe.show_alert({
                message: `${themeName} activated`,
                indicator: 'green'
            }, 2);
        }
    };
    
    // Create toggle button
    const createToggleButton = () => {
        // Check if button already exists
        if (document.querySelector('.theme-toggle-btn')) return;
        
        const button = document.createElement('button');
        button.className = 'theme-toggle-btn';
        button.setAttribute('aria-label', 'Toggle theme');
        
        button.addEventListener('click', toggleTheme);
        
        document.body.appendChild(button);
        
        // Update button icon based on current theme
        updateToggleButton(getThemePreference());
    };
    
    // Initialize theme on page load
    const initTheme = () => {
        const savedTheme = getThemePreference();
        applyTheme(savedTheme);
        
        // Create toggle button after a short delay to ensure DOM is ready
        setTimeout(createToggleButton, 500);
    };
    
    // Listen for system theme changes (optional)
    const watchSystemTheme = () => {
        if (window.matchMedia) {
            const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
            
            darkModeQuery.addEventListener('change', (e) => {
                // Only auto-switch if user hasn't set a preference
                if (!localStorage.getItem('hkm-theme')) {
                    const systemTheme = e.matches ? 'dark' : 'light';
                    applyTheme(systemTheme);
                }
            });
        }
    };
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTheme);
    } else {
        initTheme();
    }
    
    // Watch for system theme changes
    watchSystemTheme();
    
    // Expose toggle function globally for manual control
    window.hkmToggleTheme = toggleTheme;
    
    // Add keyboard shortcut (Ctrl/Cmd + Shift + D)
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'D') {
            e.preventDefault();
            toggleTheme();
        }
    });
    
})();
