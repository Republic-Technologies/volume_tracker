import React, { useState, useEffect, useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { loadTradesData, processTradesData } from '../utils/dataLoader';
import '../styles/components.css';

const VolumeOverTime = () => {
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedExchanges, setSelectedExchanges] = useState([]);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const tradesData = await loadTradesData();
        const processedTrades = processTradesData(tradesData);
        setTrades(processedTrades);
      } catch (error) {
        console.error('Error loading trades data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Get unique exchanges
  const uniqueExchanges = useMemo(() => {
    return [...new Set(trades.map(t => t.exchange))].sort();
  }, [trades]);

  // Process data for chart
  const chartData = useMemo(() => {
    // Filter by date range if specified
    let filteredTrades = trades;
    
    if (startDate) {
      const startDateStr = startDate.replace(/-/g, '');
      filteredTrades = filteredTrades.filter(t => t.date >= startDateStr);
    }
    
    if (endDate) {
      const endDateStr = endDate.replace(/-/g, '');
      filteredTrades = filteredTrades.filter(t => t.date <= endDateStr);
    }
    
    // Filter by selected exchanges if any
    if (selectedExchanges.length > 0) {
      filteredTrades = filteredTrades.filter(t => selectedExchanges.includes(t.exchange));
    }
    
    // Group by date and sum volumes
    const volumeByDate = {};
    
    filteredTrades.forEach(trade => {
      const dateStr = trade.date;
      const year = dateStr.substring(0, 4);
      const month = dateStr.substring(4, 6);
      const day = dateStr.substring(6, 8);
      const formattedDate = `${year}-${month}-${day}`;
      
      if (!volumeByDate[formattedDate]) {
        volumeByDate[formattedDate] = 0;
      }
      volumeByDate[formattedDate] += trade.volume;
    });
    
    // Convert to array and sort by date
    return Object.entries(volumeByDate)
      .map(([date, volume]) => ({ date, volume }))
      .sort((a, b) => a.date.localeCompare(b.date));
  }, [trades, startDate, endDate, selectedExchanges]);

  const handleExchangeToggle = (exchange) => {
    setSelectedExchanges(prev => {
      if (prev.includes(exchange)) {
        return prev.filter(e => e !== exchange);
      } else {
        return [...prev, exchange];
      }
    });
  };

  if (loading) {
    return (
      <div className="chart-container">
        <h3>Aggregate Volume Over Time</h3>
        <p>Loading chart data...</p>
      </div>
    );
  }

  return (
    <div className="chart-container">
      <h3>Aggregate Volume Over Time</h3>
      
      {/* Controls */}
      <div className="chart-controls">
        <div className="control-group">
          <label>Start Date:</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </div>
        
        <div className="control-group">
          <label>End Date:</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </div>
        
        <div className="control-group">
          <label>Exchanges:</label>
          <div className="exchange-checkboxes">
            {uniqueExchanges.map(exchange => (
              <label key={exchange} className="checkbox-label">
                <input
                  type="checkbox"
                  checked={selectedExchanges.includes(exchange)}
                  onChange={() => handleExchangeToggle(exchange)}
                />
                {exchange}
              </label>
            ))}
          </div>
        </div>
      </div>
      
      <ResponsiveContainer width="100%" height={400}>
        <LineChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 20, bottom: 80 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="date" 
            angle={-45}
            textAnchor="end"
            height={80}
            label={{ value: 'Date', position: 'insideBottom', offset: -5 }}
          />
          <YAxis 
            label={{ value: 'Volume', angle: -90, position: 'insideLeft' }}
            tickFormatter={(value) => value.toLocaleString()}
          />
          <Tooltip 
            formatter={(value) => value.toLocaleString()}
            labelFormatter={(label) => `Date: ${label}`}
          />
          <Legend />
          <Line 
            type="monotone" 
            dataKey="volume" 
            stroke="#3b82f6" 
            strokeWidth={2}
            dot={{ r: 4 }}
            name="Total Volume"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default VolumeOverTime;

