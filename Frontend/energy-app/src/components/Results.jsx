import React from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend, CartesianGrid } from "recharts";
import "./Results.css";

const Results = () => {
  // Sample constants for display
  const billAmount = 75.50;
  const energyData = [
    { day: "Mon", consumption: 12.5 },
    { day: "Tue", consumption: 15.3 },
    { day: "Wed", consumption: 18.2 },
    { day: "Thu", consumption: 13.6 },
    { day: "Fri", consumption: 17.8 },
    { day: "Sat", consumption: 19.5 },
    { day: "Sun", consumption: 16.0 },
  ];

  const featureImportance = [
    { appliance: "Air Conditioner", importance: 45 },
    { appliance: "Refrigerator", importance: 25 },
    { appliance: "Washing Machine", importance: 15 },
    { appliance: "Microwave", importance: 10 },
  ];

  const recommendations = [
    "Reduce AC usage by 1 hour per day to save 10% energy.",
    "Use LED bulbs instead of incandescent lights.",
    "Unplug appliances when not in use to prevent standby power loss.",
  ];

  return (
    <div className="results-container">
      <h2 className="title">Energy Consumption Report</h2>

      {/* Bill Amount */}
      <div className="bill-section">
        <h3>Estimated Bill Amount</h3>
        <p className="bill-amount">${billAmount}</p>
      </div>

      {/* Energy Consumption Prediction (Line Chart) */}
      <div className="graph-section">
        <h3>Daily Energy Consumption (kWh)</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={energyData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="day" label={{ value: "Days", position: "insideBottom", offset: -5 }} />
            <YAxis label={{ value: "Energy (kWh)", angle: -90, position: "insideLeft" }} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="consumption" stroke="#4CAF50" name="Energy (kWh)" strokeWidth={3} dot={{ r: 5 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Feature Importance */}
      <div className="feature-section">
        <h3>Top Appliances Consuming Energy</h3>
        <ul>
          {featureImportance.map((item, index) => (
            <li key={index}>
              <strong>{item.appliance}:</strong> {item.importance}%
            </li>
          ))}
        </ul>
      </div>

      {/* AI-based Recommendations */}
      <div className="recommendation-section">
        <h3>AI-based Recommendations</h3>
        <ul>
          {recommendations.map((rec, index) => (
            <li key={index}>{rec}</li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default Results;
