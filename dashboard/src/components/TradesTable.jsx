import React, { useState, useEffect, useMemo } from 'react';
import { loadTradesData, processTradesData, sortTradesByDate } from '../utils/dataLoader';
import '../styles/components.css';

const TradesTable = () => {
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pageSize, setPageSize] = useState(10);
  const [currentPage, setCurrentPage] = useState(1);
  
  // Filter states
  const [buyerFilter, setBuyerFilter] = useState('');
  const [sellerFilter, setSellerFilter] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [exchangeFilter, setExchangeFilter] = useState('');
  const [minVolume, setMinVolume] = useState('');
  const [maxVolume, setMaxVolume] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const tradesData = await loadTradesData();
        const processedTrades = processTradesData(tradesData);
        const sortedTrades = sortTradesByDate(processedTrades);
        setTrades(sortedTrades);
      } catch (error) {
        console.error('Error loading trades data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Get unique values for filter dropdowns
  const uniqueBuyers = useMemo(() => {
    const buyers = [...new Set(trades.map(t => t.buyer))].sort();
    return buyers;
  }, [trades]);

  const uniqueSellers = useMemo(() => {
    const sellers = [...new Set(trades.map(t => t.seller))].sort();
    return sellers;
  }, [trades]);

  const uniqueExchanges = useMemo(() => {
    const exchanges = [...new Set(trades.map(t => t.exchange))].sort();
    return exchanges;
  }, [trades]);

  // Filter and paginate trades
  const filteredTrades = useMemo(() => {
    let filtered = [...trades];

    // Apply filters
    if (buyerFilter) {
      filtered = filtered.filter(t => 
        t.buyer.toLowerCase().includes(buyerFilter.toLowerCase())
      );
    }

    if (sellerFilter) {
      filtered = filtered.filter(t => 
        t.seller.toLowerCase().includes(sellerFilter.toLowerCase())
      );
    }

    if (startDate) {
      filtered = filtered.filter(t => t.date >= startDate.replace(/-/g, ''));
    }

    if (endDate) {
      filtered = filtered.filter(t => t.date <= endDate.replace(/-/g, ''));
    }

    if (exchangeFilter) {
      filtered = filtered.filter(t => t.exchange === exchangeFilter);
    }

    if (minVolume) {
      const min = parseInt(minVolume);
      filtered = filtered.filter(t => t.volume >= min);
    }

    if (maxVolume) {
      const max = parseInt(maxVolume);
      filtered = filtered.filter(t => t.volume <= max);
    }

    return filtered;
  }, [trades, buyerFilter, sellerFilter, startDate, endDate, exchangeFilter, minVolume, maxVolume]);

  // Paginate filtered trades
  const paginatedTrades = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    return filteredTrades.slice(startIndex, endIndex);
  }, [filteredTrades, currentPage, pageSize]);

  const totalPages = Math.ceil(filteredTrades.length / pageSize);

  // Reset to first page when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [buyerFilter, sellerFilter, startDate, endDate, exchangeFilter, minVolume, maxVolume, pageSize]);

  const handlePageSizeChange = (e) => {
    setPageSize(parseInt(e.target.value));
  };

  const formatDate = (dateStr) => {
    const year = dateStr.substring(0, 4);
    const month = dateStr.substring(4, 6);
    const day = dateStr.substring(6, 8);
    return `${year}-${month}-${day}`;
  };

  if (loading) {
    return (
      <section className="trades-section">
        <h2>Trades</h2>
        <p>Loading trades...</p>
      </section>
    );
  }

  return (
    <section className="trades-section">
      <h2>Trades</h2>
      
      {/* Filters */}
      <div className="filters-container">
        <div className="filter-group">
          <label>Buyer:</label>
          <input
            type="text"
            value={buyerFilter}
            onChange={(e) => setBuyerFilter(e.target.value)}
            placeholder="Filter by buyer..."
            list="buyers-list"
          />
          <datalist id="buyers-list">
            {uniqueBuyers.map(buyer => (
              <option key={buyer} value={buyer} />
            ))}
          </datalist>
        </div>

        <div className="filter-group">
          <label>Seller:</label>
          <input
            type="text"
            value={sellerFilter}
            onChange={(e) => setSellerFilter(e.target.value)}
            placeholder="Filter by seller..."
            list="sellers-list"
          />
          <datalist id="sellers-list">
            {uniqueSellers.map(seller => (
              <option key={seller} value={seller} />
            ))}
          </datalist>
        </div>

        <div className="filter-group">
          <label>Start Date:</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </div>

        <div className="filter-group">
          <label>End Date:</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </div>

        <div className="filter-group">
          <label>Exchange:</label>
          <select
            value={exchangeFilter}
            onChange={(e) => setExchangeFilter(e.target.value)}
          >
            <option value="">All Exchanges</option>
            {uniqueExchanges.map(exchange => (
              <option key={exchange} value={exchange}>{exchange}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>Min Volume:</label>
          <input
            type="number"
            value={minVolume}
            onChange={(e) => setMinVolume(e.target.value)}
            placeholder="Min"
            min="0"
          />
        </div>

        <div className="filter-group">
          <label>Max Volume:</label>
          <input
            type="number"
            value={maxVolume}
            onChange={(e) => setMaxVolume(e.target.value)}
            placeholder="Max"
            min="0"
          />
        </div>

        <div className="filter-group">
          <label>Per Page:</label>
          <select value={pageSize} onChange={handlePageSizeChange}>
            <option value={10}>10</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
        </div>
      </div>

      {/* Results count */}
      <div className="results-info">
        Showing {paginatedTrades.length} of {filteredTrades.length} trades
      </div>

      {/* Table */}
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Time (ET)</th>
              <th>Exchange</th>
              <th>Price</th>
              <th>Change</th>
              <th>Volume</th>
              <th>Buyer</th>
              <th>Seller</th>
              <th>Markers</th>
            </tr>
          </thead>
          <tbody>
            {paginatedTrades.map((trade, index) => (
              <tr key={index}>
                <td>{formatDate(trade.date)}</td>
                <td>{trade.time_et}</td>
                <td>{trade.exchange}</td>
                <td>${trade.price.toFixed(3)}</td>
                <td className={trade.change !== null && trade.change !== undefined ? (trade.change >= 0 ? 'positive' : 'negative') : ''}>
                  {trade.change !== null && trade.change !== undefined 
                    ? `${trade.change >= 0 ? '+' : ''}${trade.change.toFixed(3)}`
                    : '-'
                  }
                </td>
                <td>{trade.volume.toLocaleString()}</td>
                <td>{trade.buyer}</td>
                <td>{trade.seller}</td>
                <td>{trade.markers || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="pagination">
          <button
            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
            disabled={currentPage === 1}
          >
            Previous
          </button>
          <span>
            Page {currentPage} of {totalPages}
          </span>
          <button
            onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
            disabled={currentPage === totalPages}
          >
            Next
          </button>
        </div>
      )}
    </section>
  );
};

export default TradesTable;

