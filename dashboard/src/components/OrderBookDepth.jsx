import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { loadDepthChartData } from '../utils/dataLoader';
import '../styles/components.css';

const OrderBookDepth = () => {
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const depthData = await loadDepthChartData();
        
        // Aggregate bid and ask data by price level
        const bidMap = new Map();
        const askMap = new Map();
        
        depthData.forEach(entry => {
          // Aggregate bids
          const bidPrice = entry.bid_price;
          if (bidMap.has(bidPrice)) {
            bidMap.set(bidPrice, bidMap.get(bidPrice) + entry.bid_size);
          } else {
            bidMap.set(bidPrice, entry.bid_size);
          }
          
          // Aggregate asks
          const askPrice = entry.ask_price;
          if (askMap.has(askPrice)) {
            askMap.set(askPrice, askMap.get(askPrice) + entry.ask_size);
          } else {
            askMap.set(askPrice, entry.ask_size);
          }
        });
        
        // Convert to array and combine
        const allPrices = new Set([...bidMap.keys(), ...askMap.keys()]);
        const chartDataArray = Array.from(allPrices)
          .sort((a, b) => a - b)
          .map(price => ({
            price: price.toFixed(3),
            bidSize: bidMap.get(price) || 0,
            askSize: askMap.get(price) || 0
          }));
        
        setChartData(chartDataArray);
      } catch (error) {
        console.error('Error loading depth chart data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="chart-container">
        <h3>Order Book Depth Chart</h3>
        <p>Loading chart data...</p>
      </div>
    );
  }

  return (
    <div className="chart-container">
      <h3>Order Book Depth Chart</h3>
      <p className="chart-description">
        Visualizing buy walls (bids) and sell walls (asks) at different price levels
      </p>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 20, bottom: 80 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="price" 
            angle={-45}
            textAnchor="end"
            height={80}
            label={{ value: 'Price ($)', position: 'insideBottom', offset: -5 }}
          />
          <YAxis 
            label={{ value: 'Volume', angle: -90, position: 'insideLeft' }}
            tickFormatter={(value) => value.toLocaleString()}
          />
          <Tooltip 
            formatter={(value) => value.toLocaleString()}
            labelFormatter={(label) => `Price: $${label}`}
          />
          <Legend />
          <Bar dataKey="bidSize" fill="#22c55e" name="Buy Wall (Bids)" />
          <Bar dataKey="askSize" fill="#ef4444" name="Sell Wall (Asks)" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default OrderBookDepth;

