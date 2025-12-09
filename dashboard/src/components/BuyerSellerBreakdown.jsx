import React, { useState, useEffect, useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { loadTradesData, processTradesData } from '../utils/dataLoader';
import '../styles/components.css';

const BuyerSellerBreakdown = () => {
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [topN, setTopN] = useState(15);

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

  // Calculate volume by buyer and seller
  const buyerData = useMemo(() => {
    const buyerVolume = {};
    
    trades.forEach(trade => {
      if (!buyerVolume[trade.buyer]) {
        buyerVolume[trade.buyer] = 0;
      }
      buyerVolume[trade.buyer] += trade.volume;
    });
    
    return Object.entries(buyerVolume)
      .map(([name, volume]) => ({ name, volume }))
      .sort((a, b) => b.volume - a.volume)
      .slice(0, topN);
  }, [trades, topN]);

  const sellerData = useMemo(() => {
    const sellerVolume = {};
    
    trades.forEach(trade => {
      if (!sellerVolume[trade.seller]) {
        sellerVolume[trade.seller] = 0;
      }
      sellerVolume[trade.seller] += trade.volume;
    });
    
    return Object.entries(sellerVolume)
      .map(([name, volume]) => ({ name, volume }))
      .sort((a, b) => b.volume - a.volume)
      .slice(0, topN);
  }, [trades, topN]);

  if (loading) {
    return (
      <div className="chart-container">
        <h3>Volume Breakdown by Buyers and Sellers</h3>
        <p>Loading chart data...</p>
      </div>
    );
  }

  return (
    <div className="chart-container">
      <h3>Volume Breakdown by Buyers and Sellers</h3>
      
      <div className="chart-controls">
        <div className="control-group">
          <label>Show Top:</label>
          <select value={topN} onChange={(e) => setTopN(parseInt(e.target.value))}>
            <option value={10}>10</option>
            <option value={15}>15</option>
            <option value={20}>20</option>
            <option value={25}>25</option>
          </select>
        </div>
      </div>
      
      <div className="breakdown-charts">
        <div className="breakdown-chart">
          <h4>Top Buyers by Volume</h4>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart
              data={buyerData}
              layout="vertical"
              margin={{ top: 20, right: 30, left: 150, bottom: 40 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                type="number"
                tickFormatter={(value) => value.toLocaleString()}
                label={{ value: 'Volume', position: 'insideBottom', offset: -5 }}
              />
              <YAxis 
                type="category" 
                dataKey="name"
                width={140}
                tick={{ fontSize: 12 }}
              />
              <Tooltip 
                formatter={(value) => value.toLocaleString()}
              />
              <Legend />
              <Bar dataKey="volume" fill="#3b82f6" name="Buyer Volume" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        
        <div className="breakdown-chart">
          <h4>Top Sellers by Volume</h4>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart
              data={sellerData}
              layout="vertical"
              margin={{ top: 20, right: 30, left: 150, bottom: 40 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                type="number"
                tickFormatter={(value) => value.toLocaleString()}
                label={{ value: 'Volume', position: 'insideBottom', offset: -5 }}
              />
              <YAxis 
                type="category" 
                dataKey="name"
                width={140}
                tick={{ fontSize: 12 }}
              />
              <Tooltip 
                formatter={(value) => value.toLocaleString()}
              />
              <Legend />
              <Bar dataKey="volume" fill="#ef4444" name="Seller Volume" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default BuyerSellerBreakdown;

