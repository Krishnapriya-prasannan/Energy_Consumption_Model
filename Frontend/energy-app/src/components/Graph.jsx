import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import './Graph.css';  // Add this for styling

const weatherData = [
  { month: 'Jan', temp: 15, humidity: 65, windSpeed: 10 },
  { month: 'Feb', temp: 18, humidity: 60, windSpeed: 12 },
  { month: 'Mar', temp: 22, humidity: 58, windSpeed: 14 },
  { month: 'Apr', temp: 27, humidity: 55, windSpeed: 16 },
  { month: 'May', temp: 30, humidity: 50, windSpeed: 18 },
];

const consumptionData = [
  { month: 'Jan', units: 110 },
  { month: 'Feb', units: 150 },
  { month: 'Mar', units: 170 },
  { month: 'Apr', units: 190 },
  { month: 'May', units: 210 },
];

const pastData = [
  { month: 'Jan', pastUnits: 90 },
  { month: 'Feb', pastUnits: 110 },
  { month: 'Mar', pastUnits: 130 },
  { month: 'Apr', pastUnits: 150 },
  { month: 'May', pastUnits: 170 },
];

const featureImportance = [
  { name: 'Appliance A', value: 40 },
  { name: 'Appliance B', value: 30 },
  { name: 'Appliance C', value: 20 },
  { name: 'Appliance D', value: 10 },
];

const COLORS = ['#00008B', '#008000','#8B0000', '#900C3F'];

const EnergyGraphs = () => {
    return (
      <div className="graphs-container">
        {/* Weather Trends */}
        <div className="graph-box">
          <h3 style={{ color: 'black' }}>Weather Trends</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={weatherData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" tick={{ fill: 'black', fontWeight: 'bold' }} />
              <YAxis tick={{ fill: 'black', fontWeight: 'bold' }} />
              <Tooltip contentStyle={{ backgroundColor: 'white', color: 'black' }} />
              <Legend wrapperStyle={{ color: 'black', fontWeight: 'bold' }} />
              <Line type="monotone" dataKey="temp" stroke="yellow" strokeWidth={2} name="Temperature (°C)" />
              <Line type="monotone" dataKey="humidity" stroke="lightblue" strokeWidth={2} name="Humidity (%)" />
              <Line type="monotone" dataKey="windSpeed" stroke="purple" strokeWidth={2} name="Wind Speed (km/h)" />
            </LineChart>
          </ResponsiveContainer>
        </div>
  
        {/* Units Consumed */}
        <div className="graph-box">
          <h3 style={{ color: 'black' }}>Units Consumed</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={consumptionData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" tick={{ fill: 'black', fontWeight: 'bold' }} />
              <YAxis tick={{ fill: 'black', fontWeight: 'bold' }} />
              <Tooltip contentStyle={{ backgroundColor: 'white', color: 'black' }} />
              <Legend wrapperStyle={{ color: 'black', fontWeight: 'bold' }} />
              <Bar dataKey="units" fill="lightgreen" />
            </BarChart>
          </ResponsiveContainer>
        </div>
  
        {/* Past Consumption */}
        <div className="graph-box">
          <h3 style={{ color: 'black' }}>Past Consumption</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={pastData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" tick={{ fill: 'black', fontWeight: 'bold' }} />
              <YAxis tick={{ fill: 'black', fontWeight: 'bold' }} />
              <Tooltip contentStyle={{ backgroundColor: 'white', color: 'black' }} />
              <Legend wrapperStyle={{ color: 'black', fontWeight: 'bold' }} />
              <Line type="monotone" dataKey="pastUnits" stroke="blue" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
  
        {/* Feature Importance */}
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
      </div>
    );
  };
  
  export default EnergyGraphs;
  