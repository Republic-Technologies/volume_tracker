import React from 'react';
import Header from './components/Header';
import AlertsSection from './components/AlertsSection';
import DepthChartTable from './components/DepthChartTable';
import TradesTable from './components/TradesTable';
import AnalysisSection from './components/AnalysisSection';
import './styles/App.css';

function App() {
  return (
    <div className="App">
      <Header />
      <main className="main-content">
        <AlertsSection />
        <DepthChartTable />
        <TradesTable />
        <AnalysisSection />
      </main>
    </div>
  );
}

export default App;

