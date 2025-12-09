import React, { useState, useEffect } from 'react';
import { loadTradesData, processTradesData } from '../utils/dataLoader';
import { detectLargeTrades } from '../utils/alerts';
import '../styles/components.css';

const AlertsSection = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAlerts = async () => {
      setLoading(true);
      try {
        const tradesData = await loadTradesData();
        const processedTrades = processTradesData(tradesData);
        const detectedAlerts = detectLargeTrades(processedTrades);
        setAlerts(detectedAlerts);
      } catch (error) {
        console.error('Error fetching alerts:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAlerts();
  }, []);

  if (loading) {
    return (
      <section className="alerts-section">
        <h2>Alerts</h2>
        <p>Loading alerts...</p>
      </section>
    );
  }

  if (alerts.length === 0) {
    return (
      <section className="alerts-section">
        <h2>Alerts</h2>
        <p className="no-alerts">No large trades detected in the past 5 days.</p>
      </section>
    );
  }

  return (
    <section className="alerts-section">
      <h2>Alerts - Large Trades Detected</h2>
      <div className="alerts-grid">
        {alerts.map((alert, index) => {
          const dateStr = alert.date;
          const year = dateStr.substring(0, 4);
          const month = dateStr.substring(4, 6);
          const day = dateStr.substring(6, 8);
          const formattedDate = `${year}-${month}-${day}`;
          
          return (
            <div key={index} className="alert-card">
              <div className="alert-header">
                <span className="alert-date">{formattedDate}</span>
                <span className="alert-time">{alert.time_et}</span>
              </div>
              <div className="alert-body">
                <div className="alert-volume">
                  <strong>Volume:</strong> {alert.volume.toLocaleString()}
                </div>
                <div className="alert-details">
                  <div><strong>Buyer:</strong> {alert.buyer}</div>
                  <div><strong>Seller:</strong> {alert.seller}</div>
                  <div><strong>Exchange:</strong> {alert.exchange}</div>
                  <div><strong>Price:</strong> ${alert.price.toFixed(3)}</div>
                </div>
                <div className="alert-stats">
                  <div>Threshold: {alert.threshold.toFixed(0)}</div>
                  <div>Mean: {alert.mean.toFixed(0)}</div>
                  <div>Std Dev: {alert.stdDev.toFixed(0)}</div>
                  <div className="deviation">
                    {alert.stdDevMultiplier.toFixed(2)}x above mean
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};

export default AlertsSection;

