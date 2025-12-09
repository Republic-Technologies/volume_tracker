/**
 * Alert detection utilities
 * Detects large trades that are > 1.5 standard deviations above mean
 * for trades in past 5 days compared to baseline of past 14 days
 */

/**
 * Calculate mean and standard deviation of volumes
 * @param {Array} volumes - Array of volume numbers
 * @returns {Object} Object with mean and stdDev
 */
const calculateStats = (volumes) => {
  if (volumes.length === 0) return { mean: 0, stdDev: 0 };
  
  const mean = volumes.reduce((sum, vol) => sum + vol, 0) / volumes.length;
  const variance = volumes.reduce((sum, vol) => sum + Math.pow(vol - mean, 2), 0) / volumes.length;
  const stdDev = Math.sqrt(variance);
  
  return { mean, stdDev };
};

/**
 * Parse date string (YYYYMMDD) to Date object
 * @param {string} dateStr - Date string in YYYYMMDD format
 * @returns {Date} Date object
 */
const parseDate = (dateStr) => {
  const year = parseInt(dateStr.substring(0, 4));
  const month = parseInt(dateStr.substring(4, 6)) - 1; // Month is 0-indexed
  const day = parseInt(dateStr.substring(6, 8));
  return new Date(year, month, day);
};

/**
 * Get date string in YYYYMMDD format, N days ago
 * @param {number} daysAgo - Number of days ago
 * @returns {string} Date string in YYYYMMDD format
 */
const getDateDaysAgo = (daysAgo) => {
  const date = new Date();
  date.setDate(date.getDate() - daysAgo);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}${month}${day}`;
};

/**
 * Detect large trades in past 5 days that exceed 1.5 std devs
 * compared to baseline of past 14 days
 * @param {Array} trades - Array of trade objects with date and volume
 * @returns {Array} Array of alert objects with trade details
 */
export const detectLargeTrades = (trades) => {
  if (!trades || trades.length === 0) return [];
  
  // Normalize dates to midnight for proper comparison
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  const fiveDaysAgo = new Date(today);
  fiveDaysAgo.setDate(today.getDate() - 5);
  
  const fourteenDaysAgo = new Date(today);
  fourteenDaysAgo.setDate(today.getDate() - 14);
  
  // Filter trades from past 14 days for baseline (14-5 days ago)
  const baselineTrades = trades.filter(trade => {
    const tradeDate = parseDate(trade.date);
    tradeDate.setHours(0, 0, 0, 0);
    return tradeDate >= fourteenDaysAgo && tradeDate < fiveDaysAgo;
  });
  
  // Filter trades from past 5 days for alerts
  const recentTrades = trades.filter(trade => {
    const tradeDate = parseDate(trade.date);
    tradeDate.setHours(0, 0, 0, 0);
    return tradeDate >= fiveDaysAgo && tradeDate <= today;
  });
  
  if (baselineTrades.length === 0 || recentTrades.length === 0) {
    return [];
  }
  
  // Calculate baseline statistics
  const baselineVolumes = baselineTrades.map(t => t.volume);
  const { mean, stdDev } = calculateStats(baselineVolumes);
  
  // Threshold: mean + 1.5 * stdDev
  const threshold = mean + (1.5 * stdDev);
  
  // Find trades that exceed threshold
  const alerts = recentTrades
    .filter(trade => trade.volume > threshold)
    .map(trade => ({
      ...trade,
      threshold,
      mean,
      stdDev,
      deviation: trade.volume - mean,
      stdDevMultiplier: (trade.volume - mean) / stdDev
    }))
    .sort((a, b) => {
      // Sort by date descending, then by volume descending
      const dateCompare = b.date.localeCompare(a.date);
      if (dateCompare !== 0) return dateCompare;
      return b.volume - a.volume;
    });
  
  return alerts;
};

