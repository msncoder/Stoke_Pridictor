import React from 'react';
import { TrendingUp, TrendingDown, Minus, Calendar, Target } from 'lucide-react';

const PredictionCard = ({ latest }) => {
  const getStatusColor = (direction) => {
    switch (direction) {
      case 'BUY': return 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20';
      case 'SELL': return 'text-rose-400 bg-rose-400/10 border-rose-400/20';
      default: return 'text-slate-400 bg-slate-400/10 border-slate-400/20';
    }
  };

  const getIcon = (direction) => {
    switch (direction) {
      case 'BUY': return <TrendingUp size={24} />;
      case 'SELL': return <TrendingDown size={24} />;
      default: return <Minus size={24} />;
    }
  };

  return (
    <div className="space-y-6">
      <div className={`flex items-center justify-center gap-3 p-4 rounded-xl border-2 ${getStatusColor(latest.direction)}`}>
        {getIcon(latest.direction)}
        <span className="text-2xl font-black tracking-wider uppercase">{latest.direction}</span>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="p-3 bg-slate-800/50 rounded-lg border border-slate-700">
          <div className="text-xs text-slate-500 flex items-center gap-1 mb-1">
            <Target size={12} /> Target Price
          </div>
          <div className="text-lg font-bold text-white">
            {parseFloat(latest.predicted_value).toLocaleString()}
          </div>
        </div>
        
        <div className="p-3 bg-slate-800/50 rounded-lg border border-slate-700">
          <div className="text-xs text-slate-500 flex items-center gap-1 mb-1">
            <Calendar size={12} /> Target Date
          </div>
          <div className="text-lg font-bold text-white">
            {latest.target_period}
          </div>
        </div>
      </div>

      <div className="text-xs text-slate-400 bg-slate-800/30 p-2 rounded italic text-center">
        Model: {latest.model_type} | Predicted: {new Date(latest.predicted_at).toLocaleDateString()}
      </div>
    </div>
  );
};

export default PredictionCard;
