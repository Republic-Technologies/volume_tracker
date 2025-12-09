import React from 'react';
import OrderBookDepth from './OrderBookDepth';
import VolumeOverTime from './VolumeOverTime';
import BuyerSellerBreakdown from './BuyerSellerBreakdown';
import '../styles/components.css';

const AnalysisSection = () => {
  return (
    <section className="analysis-section">
      <h2>Analysis</h2>
      <OrderBookDepth />
      <VolumeOverTime />
      <BuyerSellerBreakdown />
    </section>
  );
};

export default AnalysisSection;

