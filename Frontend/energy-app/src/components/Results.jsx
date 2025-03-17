import React, { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend, CartesianGrid } from "recharts";
import "./Results.css";

const Results = ({ data }) => {
  const [energyData, setEnergyData] = useState([]);

  useEffect(() => {
    console.log("📡 Received data:", data);

    const min_use = 0; // Replace with actual min value from training data
    const max_use = 14.714567; // Replace with actual max value from training data

    if (data?.prediction?.predicted_energy?.length > 0) {
      console.log("✅ Using predicted_energy for chart:", data.prediction.predicted_energy);

      const formattedData = data.prediction.predicted_energy.map((item) => ({
        date: new Date(item.date).toLocaleDateString("en-IN", { day: "numeric", month: "short" }), // Indian format
        consumption: (item.predicted_use * (max_use - min_use)) + min_use, // Denormalization
      }));

      console.log("📊 Denormalized Energy Data:", formattedData);
      setEnergyData(formattedData);
    } else {
      console.warn("❌ No predicted energy usage data available", data?.prediction);
    }
  }, [data]);

  if (!data) return null;

  const billAmount = data?.billAmount || {};
  const prediction = data?.prediction || {};
  const featureImportance = prediction?.featureImportance || [];
  const recommendations = prediction?.recommendations || [];

  return (
    <div className="results-container">
      <h2 className="title">Energy Consumption Report</h2>

      {/* Bill Amount */}
      <div className="bill-section">
        <h3>Estimated Bill Amount</h3>
        <p className="bill-amount">
          {billAmount?.total_bill ? `Rs.${billAmount.total_bill.toFixed(2)}` : "Loading..."}
        </p>
      </div>

      {/* Energy Consumption Prediction (Line Chart) */}
      <div className="graph-section">
        <h3>Daily Energy Consumption (kWh)</h3>
        {energyData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={energyData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="consumption" stroke="#4CAF50" strokeWidth={3} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <p>Loading chart...</p>
        )}
      </div>

      {/* Feature Importance */}
      <div className="feature-section">
        <h3>Top Appliances Consuming Energy</h3>
        {featureImportance.length > 0 ? (
          <ul>
            {featureImportance.map((item, index) => (
              <li key={index}>
                <strong>{item.appliance}:</strong> {item.importance}%
              </li>
            ))}
          </ul>
        ) : (
          <p>No data available</p>
        )}
      </div>

      {/* AI-based Recommendations */}
      {recommendations.length > 0 && (
        <div className="recommendation-section">
          <h3>AI-based Recommendations</h3>
          <ul>
            {recommendations.map((rec, index) => (
              <li key={index}>{rec}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default Results;
