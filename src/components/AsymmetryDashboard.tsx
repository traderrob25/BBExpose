"use client";
// @ts-nocheck
import React, { useState, useEffect } from 'react';
import { Search, TrendingUp, TrendingDown, AlertCircle, CheckCircle, Filter, Plus, Trash2, RefreshCw, Download, Eye } from 'lucide-react';

const AsymmetryDashboard = () => {
  const [stocks, setStocks] = useState<any[]>([]);
  const [watchlist, setWatchlist] = useState<any[]>([]);
  const [viewMode, setViewMode] = useState<'all' | 'escenarioA' | 'escenarioB'>('all');
  const [quantFilters, setQuantFilters] = useState({
    pbUnder1: false,
    upsideOver50: false,
    strongBuy: false
  });
  const [filters, setFilters] = useState({
    minAsymmetries: 2,
    selectedAsymmetries: [] as number[],
    marketCapRange: 'all'
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStock, setSelectedStock] = useState<any>(null);
  const [lastUpdate, setLastUpdate] = useState(new Date().toLocaleDateString());
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Las 7 asimetrías estructurales
  const asymmetries = [
    {
      id: 1,
      name: 'Información',
      icon: '🔍',
      description: 'Small/Micro caps con poca cobertura analítica',
      criteria: 'Market cap $300M-$2B, <5 analistas'
    },
    {
      id: 2,
      name: 'Tiempo',
      icon: '⏰',
      description: 'Horizonte largo vs presión trimestral',
      criteria: 'Management con visión 5+ años, baja rotación'
    },
    {
      id: 3,
      name: 'Acceso',
      icon: '💰',
      description: 'Adquisiciones private a public arbitrage',
      criteria: '5+ adquisiciones/año, múltiplos <8x EBITDA'
    },
    {
      id: 4,
      name: 'Liquidez',
      icon: '💧',
      description: 'Demasiado pequeño para institucionales',
      criteria: 'Market cap $400-600M, <20% propiedad institucional'
    },
    {
      id: 5,
      name: 'Estructura',
      icon: '👔',
      description: 'Insider buying significativo',
      criteria: '3+ insiders comprando, CEO/CFO involucrados'
    },
    {
      id: 6,
      name: 'Incentivos',
      icon: '🎯',
      description: 'Management alineado con shareholders',
      criteria: '>10% insider ownership, compensación en acciones'
    },
    {
      id: 7,
      name: 'Decentralización',
      icon: '🌐',
      description: 'Operaciones descentralizadas resilientes',
      criteria: 'Estructura divisional, autonomía operativa'
    }
  ];

  // Datos de ejemplo con las nuevas métricas cuantitativas
  const sampleStocks = [
    {
      ticker: 'POWL',
      name: 'Powell Industries',
      price: 185.42,
      marketCap: 2.15,
      change: 2.3,
      asymmetriesPresent: [1, 3, 4, 6],
      analystCoverage: 3,
      insiderOwnership: 15.2,
      recentInsiderBuys: 2,
      roic: 22.1,
      acquisitionsYearly: 0,
      institutionalOwnership: 28.5,
      notes: 'Electrical equipment, strong ROIC, insider buying',
      pbRatio: 2.5,
      targetPrice: 220.0,
      analystScore: 1.8,
      sector: 'Industrials'
    },
    {
      ticker: 'SSD',
      name: 'Simpson Manufacturing',
      price: 198.75,
      marketCap: 8.6,
      change: -0.8,
      asymmetriesPresent: [1, 2, 6, 7],
      analystCoverage: 4,
      insiderOwnership: 12.8,
      recentInsiderBuys: 1,
      roic: 28.4,
      acquisitionsYearly: 2,
      institutionalOwnership: 72.3,
      notes: 'Construction products, decentralized operations',
      pbRatio: 3.1,
      targetPrice: 245.0,
      analystScore: 2.1,
      sector: 'Basic Materials'
    },
    {
      ticker: 'ROLL',
      name: "RBC Bearings",
      price: 285.30,
      marketCap: 6.8,
      change: 1.5,
      asymmetriesPresent: [1, 2, 3, 6],
      analystCoverage: 4,
      insiderOwnership: 8.5,
      recentInsiderBuys: 3,
      roic: 18.7,
      acquisitionsYearly: 3,
      institutionalOwnership: 88.2,
      notes: 'Industrial bearings, active acquirer',
      pbRatio: 4.2,
      targetPrice: 320.0,
      analystScore: 2.4,
      sector: 'Industrials'
    },
    {
      ticker: 'EXPD',
      name: 'Expeditors International',
      price: 125.80,
      marketCap: 19.2,
      change: 0.4,
      asymmetriesPresent: [2, 6, 7],
      analystCoverage: 12,
      insiderOwnership: 18.3,
      recentInsiderBuys: 0,
      roic: 35.2,
      acquisitionsYearly: 1,
      institutionalOwnership: 68.5,
      notes: 'Logistics, exceptional ROIC, decentralized model',
      pbRatio: 5.1,
      targetPrice: 140.0,
      analystScore: 2.8,
      sector: 'Industrials'
    },
    {
      ticker: 'BZH',
      name: 'Beazer Homes USA',
      price: 29.50,
      marketCap: 0.9,
      change: 4.2,
      asymmetriesPresent: [1, 5, 6],
      analystCoverage: 4,
      insiderOwnership: 12.1,
      recentInsiderBuys: 3,
      roic: 14.5,
      acquisitionsYearly: 0,
      institutionalOwnership: 85.0,
      notes: '★ EJEMPLO CREADO PARA TI: Deep value builder, P/B bajo 1.0, enorme potencial alcista.',
      pbRatio: 0.85,
      targetPrice: 48.00,
      analystScore: 1.9,
      sector: 'Consumer Cyclical'
    },
    {
      ticker: 'CWH',
      name: 'Camping World Holdings',
      price: 22.15,
      marketCap: 1.8,
      change: -1.5,
      asymmetriesPresent: [2, 4, 5, 7],
      analystCoverage: 6,
      insiderOwnership: 45.2,
      recentInsiderBuys: 5,
      roic: 11.2,
      acquisitionsYearly: 2,
      institutionalOwnership: 41.5,
      notes: '★ EJEMPLO CREADO PARA TI: Muy por debajo de valor, fuerte compra de insiders.',
      pbRatio: 0.95,
      targetPrice: 35.00,
      analystScore: 2.2,
      sector: 'Consumer Cyclical'
    }
  ];

  const fetchAsymmetryData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/asymmetry');
      if (!res.ok) throw new Error('Error al conectar con el motor cuantitativo (YF).');
      const json = await res.json();
      if (json.status === 'success' && json.data) {
        setStocks(json.data);
        setLastUpdate(new Date().toLocaleTimeString());
      } else {
        throw new Error('Formato de datos inválido desde la API.');
      }
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Error desconocido.');
      // Fallback a algunas de muestra si falla la red (solo para que no se vea vacío)
      setStocks([{
        ticker: 'BZH', name: 'Beazer Homes USA', price: 29.50, sector: 'Consumer Cyclical',
        marketCap: 0.9, pbRatio: 0.85, targetPrice: 48.00, analystScore: 1.9,
        change: 0, roic: 14.5, insiderOwnership: 12.1, analystCoverage: 4,
        recentInsiderBuys: 3, acquisitionsYearly: 0, asymmetriesPresent: [1, 5, 6],
        notes: 'Fallback Dummie: Error en API.'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAsymmetryData();
  }, []);

  const filteredStocks = stocks.filter((stock: any) => {
    // Filtros originales
    const meetsMinAsymmetries = stock.asymmetriesPresent.length >= filters.minAsymmetries;
    const matchesSearch = stock.ticker.toLowerCase().includes(searchTerm.toLowerCase()) ||
      stock.name.toLowerCase().includes(searchTerm.toLowerCase());
    const meetsSelectedAsymmetries = filters.selectedAsymmetries.length === 0 ||
      filters.selectedAsymmetries.every((id: number) => stock.asymmetriesPresent.includes(id));

    let meetsMarketCap = true;
    if (filters.marketCapRange === 'small') meetsMarketCap = stock.marketCap >= 0.3 && stock.marketCap <= 2;
    if (filters.marketCapRange === 'mid') meetsMarketCap = stock.marketCap > 2 && stock.marketCap <= 10;

    // Nuevos Filtros Cuantitativos
    const meetsPB = !quantFilters.pbUnder1 || stock.pbRatio < 1.0;
    const upside = (stock.targetPrice - stock.price) / stock.price;
    const meetsUpside = !quantFilters.upsideOver50 || upside >= 0.3; // Ajustado a 30%
    const meetsStrongBuy = !quantFilters.strongBuy || stock.analystScore <= 2.0; // Ajustado a Strong Buy real

    // Segmentación por Escenario
    let meetsScenario = true;
    if (viewMode === 'escenarioA') meetsScenario = stock.price > 50;
    if (viewMode === 'escenarioB') meetsScenario = stock.price >= 5 && stock.price <= 20;

    return meetsMinAsymmetries && matchesSearch && meetsSelectedAsymmetries && meetsMarketCap && meetsPB && meetsUpside && meetsStrongBuy && meetsScenario;
  });

  const addToWatchlist = (stock: any) => {
    if (!watchlist.find((s: any) => s.ticker === stock.ticker)) {
      setWatchlist([...watchlist, { ...stock, addedDate: new Date().toLocaleDateString() }]);
    }
  };

  const removeFromWatchlist = (ticker: string) => {
    setWatchlist(watchlist.filter((s: any) => s.ticker !== ticker));
  };

  const getAsymmetryColor = (count: number) => {
    if (count >= 4) return 'text-green-600 bg-green-50 border-green-200';
    if (count === 3) return 'text-blue-600 bg-blue-50 border-blue-200';
    return 'text-orange-600 bg-orange-50 border-orange-200';
  };

  const exportToCSV = () => {
    const headers = ['Ticker', 'Name', 'Price', 'Market Cap (B)', 'Change %', 'Asymmetries', 'ROIC %', 'Insider Own %'];
    const rows = filteredStocks.map((s: any) => [
      s.ticker, s.name, s.price, s.marketCap, s.change, s.asymmetriesPresent.length, s.roic, s.insiderOwnership
    ]);

    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `asymmetry-stocks-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-50 p-6 text-slate-900">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6 border border-slate-200">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h1 className="text-4xl font-bold text-slate-800 mb-2">
                🎯 Dashboard de Asimetrías Estructurales
              </h1>
              <p className="text-slate-600 text-lg">
                Seguimiento semanal de acciones USA con ventajas estructurales
              </p>
            </div>
            <div className="text-right">
              <div className="text-sm text-slate-500 mb-2">Última actualización</div>
              <div className="text-lg font-semibold text-slate-700">{lastUpdate}</div>
              <button
                onClick={fetchAsymmetryData}
                disabled={isLoading}
                className="mt-2 text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1 disabled:opacity-50"
              >
                <RefreshCw size={14} className={isLoading ? "animate-spin" : ""} /> {isLoading ? 'Cargando...' : 'Actualizar'}
              </button>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-4 gap-4 mt-6">
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
              <div className="text-sm text-blue-700 mb-1">Total Screened</div>
              <div className="text-3xl font-bold text-blue-900">{filteredStocks.length}</div>
            </div>
            <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg border border-green-200">
              <div className="text-sm text-green-700 mb-1">En Watchlist</div>
              <div className="text-3xl font-bold text-green-900">{watchlist.length}</div>
            </div>
            <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg border border-purple-200">
              <div className="text-sm text-purple-700 mb-1">Perfect Storm (4+)</div>
              <div className="text-3xl font-bold text-purple-900">
                {filteredStocks.filter(s => s.asymmetriesPresent.length >= 4).length}
              </div>
            </div>
            <div className="bg-gradient-to-br from-orange-50 to-orange-100 p-4 rounded-lg border border-orange-200">
              <div className="text-sm text-orange-700 mb-1">Promedio Asimetrías</div>
              <div className="text-3xl font-bold text-orange-900">
                {(filteredStocks.reduce((acc, s) => acc + s.asymmetriesPresent.length, 0) / filteredStocks.length || 0).toFixed(1)}
              </div>
            </div>
          </div>
        </div>

        {/* Las 7 Asimetrías - Reference Card */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6 border border-slate-200">
          <h2 className="text-2xl font-bold text-slate-800 mb-4 flex items-center gap-2">
            <AlertCircle className="text-blue-600" /> Las 7 Asimetrías Estructurales
          </h2>
          <div className="grid grid-cols-7 gap-3">
            {asymmetries.map(asym => (
              <div
                key={asym.id}
                onClick={() => {
                  const selected = filters.selectedAsymmetries.includes(asym.id)
                    ? filters.selectedAsymmetries.filter(id => id !== asym.id)
                    : [...filters.selectedAsymmetries, asym.id];
                  setFilters({ ...filters, selectedAsymmetries: selected });
                }}
                className={`cursor-pointer p-3 rounded-lg border-2 transition-all ${filters.selectedAsymmetries.includes(asym.id)
                  ? 'bg-blue-100 border-blue-500 shadow-md'
                  : 'bg-slate-50 border-slate-200 hover:border-blue-300'
                  }`}
              >
                <div className="text-3xl text-center mb-2">{asym.icon}</div>
                <div className="text-sm font-semibold text-slate-800 text-center mb-1">{asym.name}</div>
                <div className="text-xs text-slate-600 text-center leading-tight">{asym.criteria}</div>
              </div>
            ))}
          </div>
          <div className="mt-4 text-sm text-slate-600 bg-blue-50 p-3 rounded-lg border border-blue-200">
            💡 <strong>Tip:</strong> Haz clic en las asimetrías para filtrar. Las acciones con 3+ asimetrías son "Perfect Storm" candidates.
          </div>
        </div>

        {/* Filters & Search */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6 border border-slate-200">
          <div className="grid grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">
                🔍 Buscar Ticker/Nombre
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-3 text-slate-400" size={18} />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Ticker o nombre..."
                  className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-slate-900 bg-white placeholder-slate-400"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">
                📊 Asimetrías Mínimas
              </label>
              <select
                value={filters.minAsymmetries}
                onChange={(e) => setFilters({ ...filters, minAsymmetries: parseInt(e.target.value) })}
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-slate-900 bg-white"
              >
                <option value={2}>2 o más</option>
                <option value={3}>3 o más</option>
                <option value={4}>4 o más (Perfect Storm)</option>
                <option value={5}>5 o más</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">
                💰 Market Cap
              </label>
              <select
                value={filters.marketCapRange}
                onChange={(e) => setFilters({ ...filters, marketCapRange: e.target.value })}
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-slate-900 bg-white"
              >
                <option value="all">Todas</option>
                <option value="small">Small ($300M-$2B)</option>
                <option value="mid">Mid ($2B-$10B)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">
                ⚡ Acciones
              </label>
              <button
                onClick={exportToCSV}
                className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
              >
                <Download size={18} /> Exportar CSV
              </button>
            </div>
          </div>
        </div>

        {/* Filtros Cuantitativos (Deep Value & Upside) - NUEVO */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6 border border-slate-200">
          <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
            📊 Filtros Analista Cuantitativo (Deep Value & Upside)
          </h3>
          <div className="flex flex-wrap gap-4">
            <label className={`flex items-center gap-2 cursor-pointer px-4 py-2 rounded-lg border transition-all ${quantFilters.pbUnder1 ? 'bg-blue-100 border-blue-500' : 'bg-slate-50 border-slate-200 hover:bg-slate-100'}`}>
              <input type="checkbox" checked={quantFilters.pbUnder1} onChange={e => setQuantFilters({ ...quantFilters, pbUnder1: e.target.checked })} className="hidden" />
              <div className={`w-4 h-4 rounded border flex items-center justify-center ${quantFilters.pbUnder1 ? 'bg-blue-600 border-blue-600' : 'border-slate-400'}`}>
                {quantFilters.pbUnder1 && <CheckCircle size={12} className="text-white" />}
              </div>
              <span className="text-sm font-semibold text-slate-700">P/B &lt; 1.0 (Value)</span>
            </label>

            <label className={`flex items-center gap-2 cursor-pointer px-4 py-2 rounded-lg border transition-all ${quantFilters.upsideOver50 ? 'bg-blue-100 border-blue-500' : 'bg-slate-50 border-slate-200 hover:bg-slate-100'}`}>
              <input type="checkbox" checked={quantFilters.upsideOver50} onChange={e => setQuantFilters({ ...quantFilters, upsideOver50: e.target.checked })} className="hidden" />
              <div className={`w-4 h-4 rounded border flex items-center justify-center ${quantFilters.upsideOver50 ? 'bg-blue-600 border-blue-600' : 'border-slate-400'}`}>
                {quantFilters.upsideOver50 && <CheckCircle size={12} className="text-white" />}
              </div>
              <span className="text-sm font-semibold text-slate-700">Upside &gt; 30% (Filtro Anti-Value-Trap)</span>
            </label>

            <label className={`flex items-center gap-2 cursor-pointer px-4 py-2 rounded-lg border transition-all ${quantFilters.strongBuy ? 'bg-blue-100 border-blue-500' : 'bg-slate-50 border-slate-200 hover:bg-slate-100'}`}>
              <input type="checkbox" checked={quantFilters.strongBuy} onChange={e => setQuantFilters({ ...quantFilters, strongBuy: e.target.checked })} className="hidden" />
              <div className={`w-4 h-4 rounded border flex items-center justify-center ${quantFilters.strongBuy ? 'bg-blue-600 border-blue-600' : 'border-slate-400'}`}>
                {quantFilters.strongBuy && <CheckCircle size={12} className="text-white" />}
              </div>
              <span className="text-sm font-semibold text-slate-700">Strong Buy (Score &le; 2.0)</span>
            </label>
          </div>
        </div>

        {/* Main Content - 2 Columns */}
        <div className="grid grid-cols-3 gap-6">
          {/* Stocks List - 2/3 */}
          <div className="col-span-2">
            <div className="bg-white rounded-xl shadow-lg border border-slate-200">
              <div className="p-4 border-b border-slate-200 bg-slate-50 flex flex-col md:flex-row justify-between items-center gap-4">
                <h2 className="text-xl font-bold text-slate-800 whitespace-nowrap">
                  📈 Acciones Filtradas ({filteredStocks.length})
                </h2>

                {/* Tabs de Segmentación de Escenarios - NUEVO */}
                <div className="flex bg-slate-200/60 p-1 rounded-lg">
                  <button
                    onClick={() => setViewMode('all')}
                    className={`px-3 py-1.5 text-sm font-semibold rounded-md transition-all ${viewMode === 'all' ? 'bg-white text-blue-700 shadow shadow-blue-100' : 'text-slate-600 hover:text-slate-800'}`}
                  >Global</button>
                  <button
                    onClick={() => setViewMode('escenarioA')}
                    className={`px-3 py-1.5 text-sm font-semibold rounded-md transition-all ${viewMode === 'escenarioA' ? 'bg-white text-blue-700 shadow shadow-blue-100' : 'text-slate-600 hover:text-slate-800'}`}
                  >Sólidas (&gt;$50)</button>
                  <button
                    onClick={() => setViewMode('escenarioB')}
                    className={`px-3 py-1.5 text-sm font-semibold rounded-md transition-all ${viewMode === 'escenarioB' ? 'bg-white text-blue-700 shadow shadow-blue-100' : 'text-slate-600 hover:text-slate-800'}`}
                  >Rápidas ($5 - $20)</button>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-slate-100 border-b border-slate-200">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">Ticker</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">Precio & Upside</th>
                      <th className="px-4 py-3 text-center text-sm font-semibold text-slate-700">P/B Ratio</th>
                      <th className="px-4 py-3 text-center text-sm font-semibold text-slate-700">Asimetrías</th>
                      <th className="px-4 py-3 text-center text-sm font-semibold text-slate-700">Acción</th>
                    </tr>
                  </thead>
                  <tbody>
                    {isLoading ? (
                      <tr>
                        <td colSpan={5} className="px-4 py-12 text-center text-slate-500">
                          <RefreshCw size={24} className="animate-spin mx-auto mb-3 text-blue-500" />
                          Consultando Yahoo Finance y Deep Value Database...
                        </td>
                      </tr>
                    ) : error ? (
                      <tr>
                        <td colSpan={5} className="px-4 py-12 text-center text-red-500">
                          <AlertCircle size={24} className="mx-auto mb-3" />
                          {error}
                        </td>
                      </tr>
                    ) : filteredStocks.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="px-4 py-12 text-center text-slate-500">
                          Ninguna acción cumple con los filtros activos.
                        </td>
                      </tr>
                    ) : filteredStocks.map((stock: any, idx: number) => {
                      const upsidePct = ((stock.targetPrice - stock.price) / stock.price) * 100;
                      return (
                        <tr
                          key={stock.ticker}
                          className={`border-b border-slate-100 hover:bg-blue-50 cursor-pointer transition-colors ${idx % 2 === 0 ? 'bg-white' : 'bg-slate-50'
                            }`}
                          onClick={() => setSelectedStock(stock)}
                        >
                          <td className="px-4 py-3">
                            <div className="font-bold text-slate-800">{stock.ticker}</div>
                            <div className="text-xs text-slate-500 truncate max-w-[150px]">{stock.sector}</div>
                          </td>
                          <td className="px-4 py-3">
                            <div className="font-semibold text-slate-800">${stock.price.toFixed(2)}</div>
                            <div className={`text-xs font-bold ${upsidePct >= 30 ? 'text-green-600' : 'text-slate-500'}`}>
                              Tgt: ${stock.targetPrice.toFixed(2)} (+{upsidePct.toFixed(0)}%)
                            </div>
                          </td>
                          <td className="px-4 py-3 text-center">
                            <div className={`font-semibold ${stock.pbRatio < 1.0 ? 'text-green-600' : 'text-slate-600'}`}>
                              {stock.pbRatio.toFixed(2)}
                            </div>
                          </td>
                          <td className="px-4 py-3 text-center">
                            <div className={`inline-flex items-center justify-center w-8 h-8 rounded-full border text-sm font-bold ${getAsymmetryColor(stock.asymmetriesPresent.length)
                              }`}>
                              {stock.asymmetriesPresent.length}
                            </div>
                          </td>
                          <td className="px-4 py-3 text-center">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                addToWatchlist(stock);
                              }}
                              className="text-blue-600 hover:text-blue-700 p-2 hover:bg-blue-50 rounded-lg transition-colors mx-auto"
                              title="Agregar a watchlist"
                            >
                              <Plus size={18} />
                            </button>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Right Sidebar - Detail View & Watchlist */}
          <div className="space-y-6">
            {/* Selected Stock Detail */}
            {selectedStock ? (
              <div className="bg-white rounded-xl shadow-lg p-6 border border-slate-200">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-2xl font-bold text-slate-800">{selectedStock.ticker}</h3>
                    <p className="text-sm text-slate-600">{selectedStock.name}</p>
                  </div>
                  <button
                    onClick={() => setSelectedStock(null)}
                    className="text-slate-400 hover:text-slate-600"
                  >
                    ✕
                  </button>
                </div>

                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-slate-50 p-3 rounded-lg">
                      <div className="text-xs text-slate-600 mb-1">Precio</div>
                      <div className="text-xl font-bold text-slate-800">${selectedStock.price}</div>
                    </div>
                    <div className="bg-slate-50 p-3 rounded-lg">
                      <div className="text-xs text-slate-600 mb-1">Market Cap</div>
                      <div className="text-xl font-bold text-slate-800">${selectedStock.marketCap}B</div>
                    </div>
                  </div>

                  <div className="border-t border-slate-200 pt-4">
                    <div className="text-sm font-semibold text-slate-700 mb-3">Asimetrías Presentes:</div>
                    <div className="space-y-2">
                      {selectedStock.asymmetriesPresent.map((id: number) => {
                        const asym = asymmetries.find((a: any) => a.id === id);
                        if (!asym) return null;
                        return (
                          <div key={id} className="flex items-center gap-2 bg-blue-50 p-2 rounded-lg">
                            <span className="text-xl">{asym.icon}</span>
                            <div>
                              <div className="text-sm font-semibold text-slate-800">{asym.name}</div>
                              <div className="text-xs text-slate-600">{asym.description}</div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  <div className="border-t border-slate-200 pt-4">
                    <div className="text-sm font-semibold text-slate-700 mb-3">Métricas Cuantitativas (Deep Value):</div>
                    <div className="space-y-2 text-sm bg-gradient-to-r from-slate-50 to-white p-3 rounded-lg border border-slate-200">
                      <div className="flex justify-between items-center">
                        <span className="text-slate-600">Sector:</span>
                        <span className="font-semibold text-slate-800 bg-slate-200 px-2 py-0.5 rounded text-xs">{selectedStock.sector}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-slate-600">P/B Ratio:</span>
                        <span className={`font-semibold ${selectedStock.pbRatio < 1.0 ? 'text-green-600' : 'text-slate-700'}`}>
                          {selectedStock.pbRatio.toFixed(2)} {selectedStock.pbRatio < 1.0 && '🔥'}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-slate-600">Precio Objetivo:</span>
                        <span className="font-semibold text-blue-600">${selectedStock.targetPrice.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-slate-600">Score Analistas:</span>
                        <span className={`font-semibold ${selectedStock.analystScore <= 2.0 ? 'text-green-600' : 'text-slate-700'}`}>
                          {selectedStock.analystScore.toFixed(1)} (1=Strong Buy)
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="border-t border-slate-200 pt-4">
                    <div className="text-sm font-semibold text-slate-700 mb-3">Métricas de Asimetría Clave:</div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-600">ROIC:</span>
                        <span className="font-semibold text-green-600">{selectedStock.roic}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600">Insider Ownership:</span>
                        <span className="font-semibold">{selectedStock.insiderOwnership}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600">Cobertura Analistas:</span>
                        <span className="font-semibold">{selectedStock.analystCoverage} activos</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600">Insider Buys (90d):</span>
                        <span className="font-semibold">{selectedStock.recentInsiderBuys} transacciones</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600">Adquisiciones/año:</span>
                        <span className="font-semibold">{selectedStock.acquisitionsYearly}</span>
                      </div>
                    </div>
                  </div>

                  <div className="border-t border-slate-200 pt-4">
                    <div className="text-sm text-slate-600 italic bg-yellow-50 p-3 rounded-lg border border-yellow-200">
                      📝 {selectedStock.notes}
                    </div>
                  </div>

                  <button
                    onClick={() => addToWatchlist(selectedStock)}
                    className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition-colors font-semibold flex items-center justify-center gap-2"
                  >
                    <Plus size={18} /> Agregar a Watchlist
                  </button>
                </div>
              </div>
            ) : (
              <div className="bg-slate-100 rounded-xl p-8 text-center border border-slate-200">
                <Eye size={48} className="mx-auto text-slate-400 mb-4" />
                <p className="text-slate-600">
                  Haz clic en una acción para ver detalles completos
                </p>
              </div>
            )}

            {/* Watchlist */}
            <div className="bg-white rounded-xl shadow-lg border border-slate-200">
              <div className="p-4 border-b border-slate-200 bg-green-50">
                <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                  <CheckCircle className="text-green-600" /> Mi Watchlist
                </h3>
              </div>
              <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
                {watchlist.length === 0 ? (
                  <p className="text-slate-500 text-center py-8 text-sm">
                    No hay acciones en watchlist. <br />Agrega desde la tabla principal.
                  </p>
                ) : (
                  watchlist.map(stock => (
                    <div key={stock.ticker} className="bg-slate-50 p-3 rounded-lg border border-slate-200 hover:border-blue-300 transition-colors">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <div className="font-bold text-slate-800">{stock.ticker}</div>
                          <div className="text-xs text-slate-500">Agregado: {stock.addedDate}</div>
                        </div>
                        <button
                          onClick={() => removeFromWatchlist(stock.ticker)}
                          className="text-red-500 hover:text-red-700 p-1"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-semibold text-slate-700">${stock.price}</span>
                        <span className={`text-xs px-2 py-1 rounded-full ${getAsymmetryColor(stock.asymmetriesPresent.length)}`}>
                          {stock.asymmetriesPresent.length} asim.
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Footer Instructions */}
        <div className="mt-6 bg-gradient-to-r from-blue-900 to-blue-800 rounded-xl shadow-lg p-6 text-white">
          <h3 className="text-xl font-bold mb-4">🎯 Cómo Usar Este Dashboard</h3>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <div className="font-semibold mb-2">1. Filtrar por Asimetrías</div>
              <p className="text-blue-100">Haz clic en las 7 asimetrías arriba para filtrar acciones que cumplan criterios específicos.</p>
            </div>
            <div>
              <div className="font-semibold mb-2">2. Identificar "Perfect Storm"</div>
              <p className="text-blue-100">Busca acciones con 4+ asimetrías. Estas son candidatas de alta convicción (5-10% portfolio).</p>
            </div>
            <div>
              <div className="font-semibold mb-2">3. Actualizar Semanalmente</div>
              <p className="text-blue-100">Revisa cada lunes: insider buying, earnings beats, nuevas adquisiciones anunciadas.</p>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-blue-700 text-sm text-blue-100">
            💡 <strong>Recuerda:</strong> Las asimetrías se cierran en AÑOS, no semanas. Paciencia y proceso antes de resultados.
          </div>
        </div>
      </div>
    </div>
  );
};

export default AsymmetryDashboard;