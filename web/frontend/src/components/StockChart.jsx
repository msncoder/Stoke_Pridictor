import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const StockChart = ({ data, predictions }) => {
  // Merge historical data and predictions for the chart
  // Historical data format: { trade_date: '...', close_price: ... }
  // Prediction format: { target_period: '...', predicted_value: ... }
  
  const chartData = data.map(d => ({
    displayDate: d.trade_date,
    actual: d.close_price,
    predicted: null
  }));

  // Add future predictions if any
  const futurePredictions = predictions.filter(p => String(p.target_period).startsWith('future_'));
  
  futurePredictions.forEach(p => {
    chartData.push({
      displayDate: p.target_period,
      actual: null,
      predicted: p.predicted_value
    });
  });

  // Also overlay historical predictions for accuracy visualization if target_period matches date
  predictions.forEach(p => {
    if (!String(p.target_period).startsWith('future_')) {
      const match = chartData.find(d => d.displayDate === p.target_period);
      if (match) {
        match.predicted = p.predicted_value;
      }
    }
  });

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis 
          dataKey="displayDate" 
          stroke="#94a3b8" 
          tick={{ fontSize: 10 }}
          tickFormatter={(val) => String(val).slice(-5)}
        />
        <YAxis stroke="#94a3b8" domain={['auto', 'auto']} />
        <Tooltip 
          contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px' }}
          itemStyle={{ fontSize: '13px' }}
        />
        <Legend />
        <Line 
          name="Actual Price" 
          type="monotone" 
          dataKey="actual" 
          stroke="#3b82f6" 
          strokeWidth={2} 
          dot={false} 
        />
        <Line 
          name="LSTM Predicted" 
          type="monotone" 
          dataKey="predicted" 
          stroke="#10b981" 
          strokeWidth={2} 
          strokeDasharray="5 5"
          dot={false} 
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default StockChart;
