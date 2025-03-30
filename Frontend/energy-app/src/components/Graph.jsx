import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import './Graph.css';

const COLORS = ['#00008B', '#008000', '#8B0000', '#900C3F'];

const EnergyGraphs = ({ data }) => {
  if (!data) return null;
  
  const { weatherData, pastConsumption, consumptionData /* , featureImportance */ } = data;

  return (
    <div className="graphs-container">
      {/* Weather Trends */}
      <div className="graph-box">
  <h2 className="graph-title">Weather Trends</h2>
  <ResponsiveContainer width="100%" height={300}>
    <LineChart data={weatherData}>
      <CartesianGrid strokeDasharray="3 3" stroke="gray" />
      <XAxis dataKey="date" tick={{ fontSize: 14, fill: 'black' }} />
      <YAxis tick={{ fontSize: 14, fill: 'black' }} />
      <Tooltip contentStyle={{ fontSize: 14 }} />
      <Legend wrapperStyle={{ fontSize: 16, fontWeight: 'bold', color: 'black' }} />
      <Line type="monotone" dataKey="temp" stroke="#FF4500" strokeWidth={3} /> {/* Orange */}
      <Line type="monotone" dataKey="humidity" stroke="#00BFFF" strokeWidth={3} /> {/* Deep Sky Blue */}
      <Line type="monotone" dataKey="windSpeed" stroke="#DC143C" strokeWidth={3} /> {/* Crimson */}
    </LineChart>
  </ResponsiveContainer>
</div>


      {/* Past Consumption */}
      <div className="graph-box">
        <h2 className="graph-title">Past Consumption</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={pastConsumption}>
            <CartesianGrid strokeDasharray="3 3" stroke="gray" />
            <XAxis dataKey="month" tick={{ fontSize: 14, fill: 'black' }} />
            <YAxis tick={{ fontSize: 14, fill: 'black' }} />
            <Tooltip contentStyle={{ fontSize: 14 }} />
            <Legend wrapperStyle={{ fontSize: 16, fontWeight: 'bold', color: 'black' }} />
            <Bar dataKey="pastUnits" fill="green" barSize={40} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Units Consumed */}
      <div className="graph-box">
        <h2 className="graph-title" style={{ color: "black" }}>Units Consumed</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={consumptionData}>
            <CartesianGrid strokeDasharray="3 3" stroke="gray" />
            <XAxis dataKey="date" tick={{ fontSize: 14, fill: 'black' }} />
            <YAxis tick={{ fontSize: 14, fill: 'black' }} />
            <Tooltip contentStyle={{ fontSize: 14 }} />
            <Legend wrapperStyle={{ fontSize: 16, fontWeight: 'bold', color: 'black' }} />
            <Line type="monotone" dataKey="units" stroke="blue" strokeWidth={3} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      {/* Feature Importance (Currently Disabled) */}
      {/* 
      <div className="graph-box">
        <h3 style={{ color: 'black' }}>Feature Importance</h3>
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie data={featureImportance} cx="50%" cy="50%" outerRadius={80} fill="black" dataKey="value" label>
              {featureImportance.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Legend wrapperStyle={{ color: 'black', fontWeight: 'bold' }} />
          </PieChart>
        </ResponsiveContainer>
      </div>
      */}
    </div>
  );
};

export default EnergyGraphs;
