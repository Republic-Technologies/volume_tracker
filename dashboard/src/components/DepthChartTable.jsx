import React, { useState, useEffect } from 'react';
import { loadDepthChartData } from '../utils/dataLoader';
import '../styles/components.css';

const DepthChartTable = () => {
  const [depthData, setDepthData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const data = await loadDepthChartData();
        setDepthData(data);
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
      <section className="depth-chart-section">
        <h2>Order Book Depth Chart</h2>
        <p>Loading data...</p>
      </section>
    );
  }

  return (
    <section className="depth-chart-section">
      <h2>Order Book Depth Chart</h2>
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Price</th>
              <th>Volume</th>
              <th>Buyer Broker</th>
              <th>Seller Broker</th>
              <th>Bid Price</th>
              <th>Ask Price</th>
              <th>Bid Size</th>
              <th>Ask Size</th>
            </tr>
          </thead>
          <tbody>
            {depthData.map((entry, index) => (
              <tr key={index}>
                <td>{entry.timestamp}</td>
                <td>${entry.price.toFixed(3)}</td>
                <td>{entry.volume.toLocaleString()}</td>
                <td>{entry.buyer_broker}</td>
                <td>{entry.seller_broker}</td>
                <td>${entry.bid_price.toFixed(3)}</td>
                <td>${entry.ask_price.toFixed(3)}</td>
                <td>{entry.bid_size.toLocaleString()}</td>
                <td>{entry.ask_size.toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
};

export default DepthChartTable;

