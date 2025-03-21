import React, { useState } from "react";
import EnergyApp from "./components/EnergyApp";


const App = () => {
  const [predictionData, setPredictionData] = useState(null);

  return (
    <div>
      <EnergyApp setPredictionData={setPredictionData} />
      
    </div>
  );
};

export default App;
