/**
 * Data loading and processing utilities
 * Handles fetching and processing trades.json and depth_chart.json
 */

/**
 * Load trades data from JSON file
 * @returns {Promise<Array>} Array of trade objects
 */
export const loadTradesData = async () => {
  try {
    // Add cache-busting query parameter to ensure fresh data
    const cacheBuster = `?v=${Date.now()}`;
    const response = await fetch(`/trades.json${cacheBuster}`);
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error loading trades data:', error);
    return [];
  }
};

/**
 * Load depth chart data from JSON file
 * @returns {Promise<Array>} Array of depth chart objects
 */
export const loadDepthChartData = async () => {
  try {
    // Add cache-busting query parameter to ensure fresh data
    const cacheBuster = `?v=${Date.now()}`;
    const response = await fetch(`/depth_chart.json${cacheBuster}`);
    const data = await response.json();
    return data;
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

