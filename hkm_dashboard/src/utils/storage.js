/**
 * Get current user email from Frappe session
 * @returns {string|null} User email or null if not available
 */
export const getCurrentUser = () => {
  if (typeof window === 'undefined') {
    return null;
  }
  try {
    return window?.frappe?.session?.user || null;
  } catch (error) {
    console.warn('Failed to get current user:', error);
    return null;
  }
};

/**
 * Get user-specific storage key
 * @param {string} baseKey - Base storage key
 * @param {string|null} userEmail - User email (optional, will be fetched if not provided)
 * @returns {string} User-specific storage key
 */
export const getUserStorageKey = (baseKey, userEmail = null) => {
  const user = userEmail || getCurrentUser();
  if (user) {
    // Sanitize user email for use in localStorage key
    const sanitizedUser = user.replace(/[@.]/g, '_');
    return `${baseKey}_${sanitizedUser}`;
  }
  // Fallback to base key if user is not available
  return baseKey;
};

export const loadJSON = (key, fallback = null) => {
  if (typeof window === 'undefined') {
    return fallback;
  }
  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) {
      return fallback;
    }
    return JSON.parse(raw);
  } catch (error) {
    console.warn(`Failed to parse localStorage key "${key}"`, error);
    return fallback;
  }
};

/**
 * Load JSON from user-specific storage
 * @param {string} baseKey - Base storage key
 * @param {any} fallback - Fallback value if not found
 * @param {string|null} userEmail - User email (optional)
 * @returns {any} Parsed JSON or fallback
 */
export const loadUserJSON = (baseKey, fallback = null, userEmail = null) => {
  const userKey = getUserStorageKey(baseKey, userEmail);
  return loadJSON(userKey, fallback);
};

export const saveJSON = (key, value) => {
  if (typeof window === 'undefined') {
    return;
  }
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.warn(`Failed to save localStorage key "${key}"`, error);
  }
};

/**
 * Save JSON to user-specific storage
 * @param {string} baseKey - Base storage key
 * @param {any} value - Value to save
 * @param {string|null} userEmail - User email (optional)
 */
export const saveUserJSON = (baseKey, value, userEmail = null) => {
  const userKey = getUserStorageKey(baseKey, userEmail);
  saveJSON(userKey, value);
};

export const removeKey = (key) => {
  if (typeof window === 'undefined') {
    return;
  }
  try {
    window.localStorage.removeItem(key);
  } catch (error) {
    console.warn(`Failed to remove localStorage key "${key}"`, error);
  }
};

/**
 * Remove user-specific storage key
 * @param {string} baseKey - Base storage key
 * @param {string|null} userEmail - User email (optional)
 */
export const removeUserKey = (baseKey, userEmail = null) => {
  const userKey = getUserStorageKey(baseKey, userEmail);
  removeKey(userKey);
};

