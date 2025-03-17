import React, { useState } from "react";
import ApplianceInput from "./components/ApplianceInput";
import Results from "./components/Results";

const App = () => {
  const [predictionData, setPredictionData] = useState(null);

  return (
    <div>
      <ApplianceInput setPredictionData={setPredictionData} />
      <Results data={predictionData} />
    </div>
  );
};

export default App;
