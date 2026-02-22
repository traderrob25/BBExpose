"use client";
import { useEffect, useState } from "react";

export default function Home() {
  const [data, setData] = useState([]);
  const [yosSignals, setYosSignals] = useState([]);
  const [yosMode, setYosMode] = useState("");
  const [loading, setLoading] = useState(true);

  const fetchScan = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/scan");
      const json = await res.json();
      if (json.status === "success") {
        setData(json.data);
        setYosSignals(json.yos_signals || []);
        setYosMode(json.yos_mode || "");
      }
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchScan();
  }, []);

  // Filtramos la data como en el script
  const reversiones = data.filter((d: any) => d.alerta_reversion);
  const largoPlazo = data.filter((d: any) => d.long_term_confluence);

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-10">
        <div className="flex justify-between items-center border-b border-gray-800 pb-6">
          <h1 className="text-3xl font-bold tracking-tight text-white">Hexada Scanner<span className="text-emerald-500">.</span>Live</h1>
          <button
            onClick={fetchScan}
            disabled={loading}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-md font-medium text-sm transition-all disabled:opacity-50"
          >
            {loading ? "Escaneando..." : "Actualizar Mercado"}
          </button>
        </div>

        {/* Section: YOS Bot Engine (Yoel & Cardona) */}
        <section className="space-y-4">
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-semibold text-purple-400">🤖 YOS Bot Engine Signals</h2>
            {yosMode && (
              <span className="px-3 py-1 bg-purple-900/40 text-purple-300 text-xs rounded-full border border-purple-700/50">
                Mode: {yosMode}
              </span>
            )}
          </div>

          {!loading && yosSignals.length === 0 && (
            <p className="text-gray-500 italic bg-gray-900 border border-gray-800 rounded-lg p-6">El motor YOS no detectó señales de alta calidad en este momento.</p>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {yosSignals.map((item: any) => (
              <div key={item.symbol + item.strategy} className={`p-6 rounded-xl border border-gray-800 shadow-lg ${item.direction === 'CALL' ? 'bg-gradient-to-br from-green-950/40 to-gray-900' : item.direction === 'PUT' ? 'bg-gradient-to-br from-red-950/40 to-gray-900' : 'bg-gray-900'}`}>
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-br from-white to-gray-200">{item.symbol}</h3>
                    <p className="text-purple-400 text-sm font-semibold mt-1">{item.strategy.replace(/#\d+\s/, '')}</p>
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <span className={`px-3 py-1 text-xs font-bold rounded-full ${item.direction === 'CALL' ? 'bg-green-500/20 text-green-400' : item.direction === 'PUT' ? 'bg-red-500/20 text-red-500' : 'bg-gray-500/20 text-gray-400'}`}>
                      {item.direction}
                    </span>
                    <span className="text-yellow-500 text-xs font-bold">
                      {item.strength} (Q: {item.quality}%)
                    </span>
                  </div>
                </div>

                <div className="space-y-2 mb-4 bg-black/20 p-3 rounded-lg border border-gray-800/50">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Entry:</span>
                    <span className="font-medium text-white">${item.entry !== null ? item.entry : 'N/A'}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Stop Loss:</span>
                    <span className="font-medium text-red-400">${item.stop !== null ? item.stop : 'N/A'}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Target:</span>
                    <span className="font-medium text-green-400">${item.target !== null ? item.target : 'N/A'}</span>
                  </div>
                </div>

                {item.confirmations && item.confirmations.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-gray-800">
                    <p className="text-xs text-gray-500 mb-2 uppercase tracking-wider font-semibold">Confirmaciones</p>
                    <ul className="space-y-1">
                      {item.confirmations.map((conf: string, i: number) => (
                        <li key={i} className="text-xs text-gray-400 flex items-start gap-1">
                          {conf.startsWith('✅') ? <span className="text-emerald-500">✅</span> : <span className="text-red-500">❌</span>}
                          <span>{conf.substring(2)}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>

        {/* Section: Overshoots / Scalping Reversions */}
        <section className="space-y-4">
          <h2 className="text-xl font-semibold text-emerald-400">🚨 Alertas de Reversión (Overshoot 15m)</h2>
          {!loading && reversiones.length === 0 && (
            <p className="text-gray-500 italic bg-gray-900 border border-gray-800 rounded-lg p-6">No hay acciones con Overshoot activo en 15m en este momento.</p>
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {reversiones.map((item: any) => (
              <div key={item.symbol} className={`p-6 rounded-xl border-l-4 shadow-lg ${item.pos_15m === 'UPPER' ? 'bg-red-950/30 border-red-500' : 'bg-emerald-950/30 border-emerald-500'}`}>
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-br from-white to-gray-400">{item.symbol}</h3>
                    <p className="text-gray-400 text-sm">Precio Act: ${item.price}</p>
                  </div>
                  <span className={`px-3 py-1 text-xs font-bold rounded-full ${item.pos_15m === 'UPPER' ? 'bg-red-500/20 text-red-500' : 'bg-emerald-500/20 text-emerald-500'}`}>
                    {item.pos_15m === 'UPPER' ? 'SHORT PULLBACK' : 'LONG REBOTE'}
                  </span>
                </div>

                <div className="space-y-2 mb-4">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Target SMA20 (15m):</span>
                    <span className="font-medium text-white">${item.target_sma20}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Dist. al Objetivo:</span>
                    <span className="font-medium text-white">{item.distancia_target_pct}%</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Posición 15m (%B):</span>
                    <span className="font-medium text-white">{item.pct_15m}%</span>
                  </div>
                </div>

                {item.confluencia_3tf !== "NINGUNA" && (
                  <div className="mt-4 p-3 bg-yellow-900/30 border border-yellow-700/50 rounded-lg">
                    <p className="text-xs text-yellow-500 font-semibold flex items-center gap-2">
                      ⚠️ TRIPLE CONFLUENCIA ( {item.confluencia_3tf} )
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>

        {/* Section: Largo Plazo */}
        <section className="space-y-4 pt-8">
          <h2 className="text-xl font-semibold text-blue-400">🎯 Escenario Largo Plazo (1W + 1M Pure Exposure)</h2>
          {!loading && largoPlazo.length === 0 && (
            <p className="text-gray-500 italic bg-gray-900 border border-gray-800 rounded-lg p-6">No hay acciones listadas en convergencia Semanal/Mensual actual.</p>
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {largoPlazo.map((item: any) => (
              <div key={item.symbol + '-long'} className="p-6 rounded-xl border border-gray-800 bg-gray-900 shadow-lg">
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-br from-white to-gray-400">{item.symbol}</h3>
                  <span className={`px-3 py-1 text-xs font-bold rounded-full ${item.long_term_type === 'UPPER' ? 'bg-red-500/20 text-red-500' : 'bg-emerald-500/20 text-emerald-500'}`}>
                    {item.long_term_type} (1W/1M)
                  </span>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Spread:</span>
                    <span className="font-medium text-white">{item.spread_pct}%</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Exposición 1Wk:</span>
                    <span className="font-medium text-white">{item.pct_1wk}%</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Exposición 1Mo:</span>
                    <span className="font-medium text-white">{item.pct_1mo}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
