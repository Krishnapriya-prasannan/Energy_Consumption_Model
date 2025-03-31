import React, { useState } from "react";
import EnergyApp from "./components/EnergyApp";
import EnergyGraphs from "./components/Graph";

const App = () => {
  const [predictionData, setPredictionData] = useState(null);

  console.log("Raw Prediction Data:", predictionData); // Debugging

  // Function to transform backend data into the expected format
  const transformData = (data) => {
    if (!data) return { weatherData: [], pastConsumption: [], consumptionData: [], recommendations: [] };

    const weatherData = data.weatherData?.map((entry) => {
      const formattedDate = `${String(entry.day).padStart(2, '0')}-${String(entry.month).padStart(2, '0')}`;
      return {
        date: formattedDate,
        temp: entry.avg_temperature,
        humidity: entry.avg_humidity,
        windSpeed: entry.avg_wind_speed,
      };
    }) || [];
  
    let pastConsumption = Object.entries(data.pastConsumption || {}).map(([month, pastUnits]) => ({
      month,
      pastUnits,
    }));
    pastConsumption = pastConsumption.reverse(); // Reverse the array to show the most recent month first

    const consumptionData = data.prediction?.predicted_energy?.map((entry) => {
      const dateObj = new Date(entry.date);
      const formattedDate = `${String(dateObj.getDate()).padStart(2, '0')}-${String(dateObj.getMonth() + 1).padStart(2, '0')}`;
      return {
        date: formattedDate,
        units: entry.predicted_use,
      };
    }) || [];

    return { weatherData, pastConsumption, consumptionData, recommendations: data.recommendations || [] };
  };

  // Transform data before passing it to EnergyGraphs
  const transformedData = transformData(predictionData);
  const totalMonthlyForecast = predictionData?.totalMonthlyForecast || 0;
  const billAmount = predictionData?.billAmount || 0;

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
          <h2>Total Units Consumed: {totalMonthlyForecast} kWh</h2>
          <h2>Estimated Bill Amount: ₹{billAmount}</h2>
          <EnergyGraphs data={transformedData} />
        </>
      )}
    </div>
  );
};

export default App;
