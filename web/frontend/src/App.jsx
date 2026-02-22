import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { TrendingUp, TrendingDown, RefreshCw, BarChart3, AlertCircle } from 'lucide-react'
import StockChart from './components/StockChart'
import PredictionCard from './components/PredictionCard'

function App() {
  const [stocks, setStocks] = useState([])
  const [selectedStock, setSelectedStock] = useState(null)
  const [predictions, setPredictions] = useState([])
  const [historicalData, setHistoricalData] = useState([])
  const [loading, setLoading] = useState(false)
  const [triggering, setTriggering] = useState(false)

  useEffect(() => {
    fetchStocks()
  }, [])

  useEffect(() => {
    if (selectedStock) {
      fetchStockData(selectedStock)
    }
  }, [selectedStock])

  const fetchStocks = async () => {
    try {
      const res = await axios.get('/api/stocks')
      setStocks(res.data.stocks)
      if (res.data.stocks.length > 0 && !selectedStock) {
        setSelectedStock(res.data.stocks[0])
      }
    } catch (err) {
      console.error("Error fetching stocks:", err)
    }
  }

  const fetchStockData = async (symbol) => {
    setLoading(true)
    try {
      const [predRes, histRes] = await Promise.all([
        axios.get(`/api/predictions/${symbol}`),
        axios.get(`/api/historical/${symbol}`)
      ])
      setPredictions(predRes.data.predictions)
      setHistoricalData(histRes.data.data)
    } catch (err) {
      console.error("Error fetching stock data:", err)
    } finally {
      setLoading(false)
    }
  }

  const handleTrigger = async () => {
    setTriggering(true)
    try {
      await axios.post('/api/trigger')
      alert("Automation pipeline triggered! It will run in the background.")
    } catch (err) {
      alert("Failed to trigger pipeline.")
    } finally {
      setTriggering(false)
    }
  }

  return (
    <div className="min-h-screen p-4 md:p-8">
      <header className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
            SMAP-FYP Stock Predictor
          </h1>
          <p className="text-slate-400">AI-Powered Sentiment & Price Analysis</p>
        </div>
        
        <div className="flex items-center gap-4">
          <select 
            className="bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 outline-none focus:ring-2 ring-blue-500"
            value={selectedStock || ''}
            onChange={(e) => setSelectedStock(e.target.value)}
          >
            {stocks.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          
          <button 
            onClick={handleTrigger}
            disabled={triggering}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 px-4 py-2 rounded-lg font-medium transition-all"
          >
            <RefreshCw className={triggering ? "animate-spin" : ""} size={18} />
            {triggering ? "Triggering..." : "Update All"}
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Chart Section */}
        <div className="lg:col-span-2 glass-card flex flex-col">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <BarChart3 className="text-blue-400" />
              {selectedStock} Price History & Forecast
            </h2>
            <div className="text-xs text-slate-500">Last 100 days + Future Projection</div>
          </div>
          
          <div className="flex-grow min-h-[400px]">
            {loading ? (
              <div className="flex items-center justify-center h-full">
                <RefreshCw className="animate-spin text-blue-400" size={48} />
              </div>
            ) : (
              <StockChart data={historicalData} predictions={predictions} />
            )}
          </div>
        </div>

        {/* Prediction Stats Section */}
        <div className="flex flex-col gap-6">
          <div className="glass-card">
            <h3 className="text-lg font-medium mb-4 flex items-center gap-2">
              <TrendingUp className="text-emerald-400" size={20} />
              Latest Signal
            </h3>
            {predictions.length > 0 ? (
              <PredictionCard latest={predictions[0]} />
            ) : (
              <div className="text-slate-500 italic">No prediction data available.</div>
            )}
          </div>

          <div className="glass-card flex-grow overflow-auto max-h-[500px]">
            <h3 className="text-lg font-medium mb-4">Recent Predictions</h3>
            <div className="space-y-4">
              {predictions.slice(1, 10).map((p, i) => (
                <div key={i} className="p-3 bg-slate-800/50 rounded-lg border border-slate-700 flex justify-between items-center">
                  <div>
                    <div className="text-sm font-medium">{p.target_period}</div>
                    <div className="text-xs text-slate-400">{new Date(p.predicted_at).toLocaleDateString()}</div>
                  </div>
                  <div className={`text-sm font-bold ${p.direction === 'BUY' ? 'text-emerald-400' : p.direction === 'SELL' ? 'text-rose-400' : 'text-slate-300'}`}>
                    {p.direction}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
      
      <footer className="max-w-7xl mx-auto mt-12 pt-8 border-t border-slate-800 flex justify-between text-slate-500 text-sm">
        <div>SMAP-FYP © 2026</div>
        <div className="flex items-center gap-1">
          <AlertCircle size={14} />
          Predictions are generated by LSTM model and are for informational purposes only.
        </div>
      </footer>
    </div>
  )
}

export default App
