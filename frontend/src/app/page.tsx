'use client';

import { useState, useEffect } from 'react';
import ThemeToggle from '../components/ThemeToggle';
import FileExplorer from '../components/FileExplorer';

export default function Home() {
  const [portfolios, setPortfolios] = useState<string[]>([]);
  const [opportunities, setOpportunities] = useState<string[]>([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState('');
  const [selectedOpportunity, setSelectedOpportunity] = useState('');

  // Fetch portfolios on first render
  useEffect(() => {
    fetch('/api/portfolios')
      .then((res) => res.json())
      .then(setPortfolios)
      .catch((err) => console.error('Failed to fetch portfolios:', err));
  }, []);

  // Fetch opportunities when portfolio changes
  useEffect(() => {
    if (!selectedPortfolio) return;
    fetch(`/api/portfolios/${selectedPortfolio}/opportunities`)
      .then((res) => res.json())
      .then(setOpportunities)
      .catch((err) => console.error('Failed to fetch opportunities:', err));
  }, [selectedPortfolio]);

  // Persist selection to localStorage
  useEffect(() => {
    const storedPortfolio = localStorage.getItem('portfolio');
    const storedOpportunity = localStorage.getItem('opportunity');
    if (storedPortfolio) setSelectedPortfolio(storedPortfolio);
    if (storedOpportunity) setSelectedOpportunity(storedOpportunity);
  }, []);

  useEffect(() => {
    if (selectedPortfolio) {
      localStorage.setItem('portfolio', selectedPortfolio);
    }
  }, [selectedPortfolio]);

  useEffect(() => {
    if (selectedOpportunity) {
      localStorage.setItem('opportunity', selectedOpportunity);
    }
  }, [selectedOpportunity]);

  return (
    <div className="flex min-h-screen">
      {/* Main content */}
      <div
        className="flex-1 space-y-6 px-6 py-4"
        style={{
          background: 'linear-gradient(to bottom right, #e8eafc, #f3f8e1)',
        }}
      >
        {/* Header: Title + Theme Toggle */}
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-[28px] font-bold tracking-tight text-[#1a18b9]">
            Sol Connect
          </h1>
          <ThemeToggle />
        </div>

        {/* Portfolio + Opportunity + Create */}
        <div className="flex flex-wrap sm:flex-nowrap gap-4 max-w-4xl items-center">
  {/* Reset Button */}
  
  <button
  onClick={() => {
    localStorage.removeItem('portfolio');
    localStorage.removeItem('opportunity');
    setSelectedPortfolio('');
    setSelectedOpportunity('');
  }}
  title="Clear Portfolio Selection"
  className="text-blue-700 border border-blue-600 px-3 py-1 rounded hover:bg-blue-50 text-xl"
>
  🧹
</button>

          {/* Portfolio Dropdown */}
          <select
            className="form-input flex-1 h-12 rounded-lg border border-gray-300 bg-white px-4 text-sm text-[#101518]"
            value={selectedPortfolio}
            onChange={(e) => {
              setSelectedPortfolio(e.target.value);
              setSelectedOpportunity('');
            }}
          >
            <option value="">Select Portfolio</option>
            {portfolios.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>

          {/* Opportunity Dropdown */}
          <select
            className="form-input flex-1 h-12 rounded-lg border border-gray-300 bg-white px-4 text-sm text-[#101518]"
            value={selectedOpportunity}
            onChange={(e) => setSelectedOpportunity(e.target.value)}
            disabled={!selectedPortfolio}
          >
            <option value="">Select Opportunity</option>
            {opportunities.map((o) => (
              <option key={o} value={o}>
                {o}
              </option>
            ))}
          </select>

          {/* + Create Opportunity */}
          <button
            onClick={async () => {
              const name = prompt('Enter name for new opportunity:');
              if (!name) return;
              if (!selectedPortfolio) {
                alert('Please select a portfolio first.');
                return;
              }

              const res = await fetch(
                `/api/portfolios/${selectedPortfolio}/opportunities/create`,
                {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ name }),
                }
              );

              if (res.ok) {
                const updated = await fetch(
                  `/api/portfolios/${selectedPortfolio}/opportunities`
                ).then((res) => res.json());
                setOpportunities(updated);
                setSelectedOpportunity(name);
              } else {
                alert('Failed to create opportunity');
              }
            }}
            title="Create Opportunity"
            className="rounded-full bg-[#1a18b9] text-white w-10 h-10 flex items-center justify-center text-lg font-bold hover:bg-[#1414a3]"
          >
            +
          </button>
        </div>

        {/* File Explorer */}
        {selectedOpportunity && (
          <FileExplorer
            basePrefix={`${selectedPortfolio}/opportunities/${selectedOpportunity}/`}
          />
        )}
      </div>

      {/* Right panel */}
      <div className="w-80 px-6 py-10 bg-white border-l flex flex-col justify-center text-center shadow-md relative">
        <div className="absolute top-1/3 left-0 right-0 px-4 transform -translate-y-1/2">
          <img
            src="/ritchie-logo.png"
            alt="Ritchie's Logo"
            className="w-24 h-24 mx-auto mb-4 rounded-full border border-gray-200 shadow-sm"
          />
          <h2 className="text-2xl font-bold text-[#1a18b9] mb-1">
            Ritchie’s Den
          </h2>
          <p className="text-sm italic text-gray-600 mb-3">
            Sol-searching? <span className="not-italic">We’ve got the answers.</span>
          </p>
          <p className="text-sm text-[#444] font-medium leading-relaxed tracking-wide">
            <span className="block text-base font-semibold text-[#1a18b9] mb-1">
              Welcome to your unfair advantage in proposal development!
            </span>
          </p>
        </div>
      </div>
    </div>
  );
}
