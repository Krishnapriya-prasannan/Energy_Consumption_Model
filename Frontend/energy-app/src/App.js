import React, { useState } from "react";
import EnergyApp from "./components/EnergyApp";
import EnergyGraphs from "./components/Graph";
import Recommendations from "./components/Recommendations";

const App = () => {
  const [predictionData, setPredictionData] = useState(null);

  console.log("Raw Prediction Data:", predictionData); // Debugging

  // Function to transform backend data into the expected format
  const transformData = (data) => {
    if (!data) return { weatherData: [], pastConsumption: [], consumptionData: [] };

    const weatherData = data.weatherData?.map((entry) => ({
      month: entry.month,
      temp: entry.avg_temperature,
      humidity: entry.avg_humidity,
      windSpeed: entry.avg_wind_speed,
    })) || [];

    const pastConsumption = Object.entries(data.pastConsumption || {}).map(([month, pastUnits]) => ({
      month,
      pastUnits,
    }));
    const consumptionData = data.prediction?.predicted_energy?.map((entry) => {
      const dateObj = new Date(entry.date);
      const formattedDate = `${String(dateObj.getDate()).padStart(2, '0')}-${String(dateObj.getMonth() + 1).padStart(2, '0')}`; // Format: DD-MM
      
      return {
        date: formattedDate, // Updated field name to "date" instead of "month"
        units: entry.predicted_use,
      };
    }) || [];

    return { weatherData, pastConsumption, consumptionData };
  };

    /*const consumptionData = data.prediction?.predicted_energy?.map((entry) => ({
      const dateObj = new Date(entry.date);
      const formattedDate = `${String(dateObj.getDate()).padStart(2, '0')}-${String(dateObj.getMonth() + 1).padStart(2, '0')}`; // Format: DD-MM
      
      return {
        date: formattedDate, // Updated field name to "date" instead of "month"
        units: entry.predicted_use,
      };
      //month: new Date(entry.date).toLocaleString('default', { month: 'long' }), // Extract month name
      //units: entry.predicted_use,
    })) || [];

    return { weatherData, pastConsumption, consumptionData };
  };
*/
  // Transform data before passing it to EnergyGraphs
  const transformedData = transformData(predictionData);

  return (
    <div>
      {/* Show EnergyApp form always */}
      <EnergyApp setPredictionData={setPredictionData} />
  
      {/* Show graphs and recommendations only after form submission */}
      {predictionData && (
        <>
          {console.log("Transformed Weather Data:", transformedData.weatherData)}
          {console.log("Transformed Past Consumption Data:", transformedData.pastConsumption)}
          {console.log("Transformed Consumption Data:", transformedData.consumptionData)}
  
          <EnergyGraphs data={transformedData} />
          <Recommendations recommendations={predictionData.recommendations} />
          
        </>
      )}
    </div>
  );
  
};

export default App;
