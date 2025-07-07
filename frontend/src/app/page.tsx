'use client';

import { useState, useEffect } from 'react';
import ThemeToggle from '../components/ThemeToggle';

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

  return (
    <div
      className="space-y-6 min-h-screen px-6 py-8"
      style={{
        background: 'linear-gradient(to bottom right, #e8eafc, #f3f8e1)',
      }}
    >
      {/* Theme Toggle */}
      <div className="flex justify-end">
        <ThemeToggle />
      </div>

      {/* Page Title */}
      <h1 className="text-[32px] font-bold tracking-tight text-[#1a18b9]">Sol Connect</h1>

      {/* Dropdowns + Create Opportunity Button */}
      <div className="flex flex-wrap gap-4 max-w-xl items-center">
        {/* Portfolio Dropdown */}
        <select
          className="form-input w-full h-12 rounded-lg border border-gray-300 bg-white px-4 text-sm text-[#101518]"
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

        {/* Opportunity Dropdown + Create Button */}
        <div className="flex gap-2 w-full">
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

          <button
           onClick={async () => {
  const name = prompt("Enter name for new opportunity:");
  if (!name) return;

  if (!selectedPortfolio) {
    alert("Please select a portfolio first.");
    return;
  }

  // (rest of the code to create folder)


              const res = await fetch(
                `/api/portfolios/${selectedPortfolio}/opportunities/create`,
                {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
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
                alert("Failed to create opportunity");
              }
            }}
            className="rounded-lg bg-[#1a18b9] text-white px-4 py-2 text-sm font-medium hover:bg-[#1414a3]"
          >
            + Create
          </button>
        </div>
      </div>

      {/* You can render document data below based on selections */}
    </div>
  );
}
