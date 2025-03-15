import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import ApplianceInput from "./components/ApplianceInput";
import Results from "./components/Results";
/*import Forecasting from "./pages/Forecasting";
import Navbar from "./components/Navbar"; */

const App = () => {
  return (
    <Router>
      
      <Routes>
        <Route path="/" element={<ApplianceInput />} />
        <Route path="/result" element={<Results />} />        
      </Routes>
    </Router>
  );
};

export default App;