import React from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar
} from 'recharts';
import './Graph.css';

const getPreviousMonthAbbr = (month) => {
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const fullMonths = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  
  const index = fullMonths.indexOf(month);
  return index > 0 ? months[index - 1] : null; // Get previous month abbreviation
};

const formatPastConsumptionData = (data) => {
  return data.map((entry) => {
    const prevMonth = getPreviousMonthAbbr(entry.month);
    const curMonthAbbr = entry.month.substring(0, 3); // Convert to abbreviation
    return {
      ...entry,
      month: prevMonth ? `${prevMonth}-${curMonthAbbr}` : curMonthAbbr, // Format as "PrevMonth-CurMonth"
    };
  });
};


const EnergyGraphs = ({ data }) => {
  if (!data) return null;

  const { weatherData, pastConsumption, consumptionData, recommendations } = data;
  const formattedPastConsumption = formatPastConsumptionData(pastConsumption);

  return (
    <div className="graphs-container">
      
      {/* Weather Trends */}
      <div className="graph-box">
        <h2 className="graph-title">Weather Trends</h2>
        <ResponsiveContainer width="100%" height={450}>
          <LineChart data={weatherData} margin={{ top: 20, right: 50, left: 50, bottom: 20 }}>
            <CartesianGrid stroke="rgba(0, 0, 0, 0.3)" strokeWidth={1.5} strokeDasharray="5 5" />
            <XAxis dataKey="date" tick={{ fontSize: 14, fill: '#333', fontWeight: "bold" }} stroke="#333" />
            <YAxis tick={{ fontSize: 14, fill: '#333', fontWeight: "bold" }} stroke="#333" />
            <Tooltip contentStyle={{ fontSize: 14, background: "#fff", borderRadius: 8, border: "1.5px solid black" }} />
            <Legend wrapperStyle={{ fontSize: 16, fontWeight: 'bold', color: '#333' }} />
            <Line type="monotone" dataKey="temp" stroke="#FF5733" strokeWidth={3} dot={{ r: 3 }} />
            <Line type="monotone" dataKey="humidity" stroke="#3498db" strokeWidth={3} dot={{ r: 3 }} />
            <Line type="monotone" dataKey="windSpeed" stroke="#27ae60" strokeWidth={3} dot={{ r: 3 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Past Consumption */}
      <div className="graph-box">
        <h2 className="graph-title">Past Consumption</h2>
        <ResponsiveContainer width="100%" height={450}>
          <BarChart data={formattedPastConsumption} margin={{ top: 20, right: 50, left: 50, bottom: 20 }}>
            <CartesianGrid stroke="rgba(0, 0, 0, 0.3)" strokeWidth={1.5} strokeDasharray="5 5" />
            <XAxis dataKey="month" tick={{ fontSize: 14, fill: '#333', fontWeight: "bold" }} stroke="#333" />
            <YAxis tick={{ fontSize: 14, fill: '#333', fontWeight: "bold" }} stroke="#333" />
            <Tooltip contentStyle={{ fontSize: 14, background: "#fff", borderRadius: 8, border: "1.5px solid black" }} />
            <Legend wrapperStyle={{ fontSize: 16, fontWeight: 'bold', color: '#333' }} />
            <Bar dataKey="pastUnits" fill="#4caf50" barSize={50} radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div> 

      {/* Units Consumed */}
      <div className="graph-box">
        <h2 className="graph-title">Units Consumed</h2>
        <ResponsiveContainer width="100%" height={450}>
          <LineChart data={consumptionData} margin={{ top: 20, right: 50, left: 50, bottom: 20 }}>
            <CartesianGrid stroke="rgba(0, 0, 0, 0.3)" strokeWidth={1.5} strokeDasharray="5 5" />
            <XAxis dataKey="date" tick={{ fontSize: 14, fill: '#333', fontWeight: "bold" }} stroke="#333" />
            <YAxis tick={{ fontSize: 14, fill: '#333', fontWeight: "bold" }} stroke="#333" />
            <Tooltip contentStyle={{ fontSize: 14, background: "#fff", borderRadius: 8, border: "1.5px solid black" }} />
            <Legend wrapperStyle={{ fontSize: 16, fontWeight: 'bold', color: '#333' }} />
            <Line type="monotone" dataKey="units" stroke="#1E90FF" strokeWidth={3} dot={{ r: 3 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Recommendations */}
      <div className="recommendations-container">
        <h1 className="graph-title">Recommendations</h1>
        <ul>
          {recommendations?.map((rec, index) => (
            <li key={index}>{rec}</li>
          ))}
        </ul>
      </div>

    </div>
  );
};

export default EnergyGraphs;
