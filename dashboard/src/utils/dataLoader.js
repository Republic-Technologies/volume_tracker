/**
 * Data loading and processing utilities
 * Handles fetching and processing trades.json and depth_chart.json
 */

/**
 * Get data version for cache-busting
 * Falls back to timestamp if version file doesn't exist
 * @returns {Promise<string>} Version string for cache-busting
 */
const getDataVersion = async () => {
  try {
    const publicUrl = process.env.PUBLIC_URL || '';
    const response = await fetch(`${publicUrl}/data-version.json?v=${Date.now()}`);
    if (response.ok) {
      const versionData = await response.json();
      return versionData.version || Date.now().toString();
    }
  } catch (error) {
    console.warn('Could not load data-version.json, using timestamp fallback');
  }
  // Fallback to timestamp if version file doesn't exist
  return Date.now().toString();
};

/**
 * Load trades data from JSON file
 * @returns {Promise<Array>} Array of trade objects
 */
export const loadTradesData = async () => {
  try {
    // Use PUBLIC_URL to handle both development and production paths
    // In development, PUBLIC_URL is empty string, in production it's the homepage path
    const publicUrl = process.env.PUBLIC_URL || '';
    // Get version for cache-busting (updates when scraper runs)
    const version = await getDataVersion();
    const cacheBuster = `?v=${version}`;
    const response = await fetch(`${publicUrl}/trades.json${cacheBuster}`);
    
    if (!response.ok) {
      throw new Error(`Failed to load trades.json: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error loading trades data:', error);
    return [];
  }
};

/**
 * Filter depth chart data to only include entries from the most recent date
 * @param {Array} depthData - Array of depth chart objects with timestamp field
 * @returns {Array} Filtered array containing only the most recent date's entries
 */
export const filterDepthChartByMostRecentDate = (depthData) => {
  if (!depthData || depthData.length === 0) {
    return [];
  }
  
  // Extract all unique dates and find the most recent one
  const dates = [...new Set(depthData.map(entry => entry.timestamp))];
  // Sort dates in descending order (most recent first)
  dates.sort((a, b) => b.localeCompare(a));
  const mostRecentDate = dates[0];
  
  // Filter to only include entries from the most recent date
  return depthData.filter(entry => entry.timestamp === mostRecentDate);
};

/**
 * Load depth chart data from JSON file
 * Only returns data from the most recent date
 * @returns {Promise<Array>} Array of depth chart objects from the most recent date
 */
export const loadDepthChartData = async () => {
  try {
    // Use PUBLIC_URL to handle both development and production paths
    // In development, PUBLIC_URL is empty string, in production it's the homepage path
    const publicUrl = process.env.PUBLIC_URL || '';
    // Get version for cache-busting (updates when scraper runs)
    const version = await getDataVersion();
    const cacheBuster = `?v=${version}`;
    const response = await fetch(`${publicUrl}/depth_chart.json${cacheBuster}`);
    
    if (!response.ok) {
      throw new Error(`Failed to load depth_chart.json: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    // Filter to only show the most recent date
    return filterDepthChartByMostRecentDate(data);
  } catch (error) {
    console.error('Error loading depth chart data:', error);
    return [];
  }
};

/**
 * Process trades data: combine date and time_et into a sortable datetime
 * @param {Array} trades - Array of trade objects
 * @returns {Array} Processed trades with datetime field
 */
export const processTradesData = (trades) => {
  return trades.map(trade => {
    // Convert date from YYYYMMDD to YYYY-MM-DD format
    const dateStr = trade.date;
    const year = dateStr.substring(0, 4);
    const month = dateStr.substring(4, 6);
    const day = dateStr.substring(6, 8);
    const dateFormatted = `${year}-${month}-${day}`;
    
    // Combine date and time_et for sorting
    const datetime = new Date(`${dateFormatted}T${trade.time_et}`);
    
    return {
      ...trade,
      datetime,
      dateFormatted
    };
  });
};

/**
 * Sort trades by date descending, then by time_et descending
 * @param {Array} trades - Array of processed trade objects
 * @returns {Array} Sorted trades
 */
export const sortTradesByDate = (trades) => {
  return [...trades].sort((a, b) => {
    // First sort by date (descending)
    const dateA = a.date;
    const dateB = b.date;
    if (dateA !== dateB) {
      return dateB.localeCompare(dateA);
    }
    // Then sort by time_et (descending) within same date
    return b.time_et.localeCompare(a.time_et);
  });
};

