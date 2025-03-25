import React, { useState } from "react";
import "./EnergyApp.css";
import Graphs from "./Graph";
import Recommendations from "./Recommendations";
import CustomCalendar from "./CustomCalendar";
import axios from "axios";
const EnergyPredictionApp = ({setPredictionData}) => {
  const [location, setLocation] = useState("");
  const [consumerNo, setConsumerNo] = useState("");
  const [phase, setPhase] = useState("1-Phase");
  const [selectedAppliances, setSelectedAppliances] = useState({});
  const [billAmount, setBillAmount] = useState(null);
  const [selectedDates, setSelectedDates] = useState([]); // ✅ Define state
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState("");
  
  const appliancesList = [
    "Dishwasher", "Air Conditioner", "Heater", "Computer Devices", "Refrigerator",
    "Washing Machine", "Fans", "Chimney", "Food Processor", "Induction Cooktop",
    "Lights", "Water Pump", "Microwave", "TV"
  ];

  const daysOfWeek = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
  const timesOfDay = ["Morning", "Noon", "Evening", "Night"];

  const handleApplianceSelect = (appliance) => {
    setSelectedAppliances((prev) => {
      const updated = { ...prev };
      if (updated[appliance]) {
        delete updated[appliance];
      } else {
        updated[appliance] = { power: "", count: "", usage: "", days: [], times: {} };
      }
      return updated;
    });
  };

  const handleApplianceChange = (appliance, field, value) => {
    setSelectedAppliances((prev) => ({
      ...prev,
      [appliance]: { ...prev[appliance], [field]: value },
    }));
  };

  const toggleDaySelection = (appliance, day) => {
    setSelectedAppliances((prev) => {
      const updated = { ...prev };

      if (!updated[appliance]) {
        updated[appliance] = { power: "", count: "", usage: "", days: [], times: {} };
      }

      let updatedDays = [...updated[appliance].days];

      if (updatedDays.includes(day)) {
        updatedDays = updatedDays.filter((d) => d !== day);
        delete updated[appliance].times[day];
      } else {
        updatedDays.push(day);
        updated[appliance].times[day] = updated[appliance].times[day] || [];
      }

      updated[appliance] = { ...updated[appliance], days: updatedDays };

      return { ...updated };
    });
  };

  const selectAllAppliances = () => {
    setSelectedAppliances((prev) => {
      if (Object.keys(prev).length === appliancesList.length) {
        return {};
      }
      const allSelected = {};
      appliancesList.forEach((appliance) => {
        allSelected[appliance] = { power: "", count: "", usage: "", days: [], times: {} };
      });
      return allSelected;
    });
  };

  const fetchLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocation(`Lat: ${position.coords.latitude}, Lng: ${position.coords.longitude}`);
        },
        (error) => {
          alert("Error fetching location: " + error.message);
        }
      );
    } else {
      alert("Geolocation is not supported by this browser.");
    }
  };

  const validateInputs = () => {
    for (const appliance in selectedAppliances) {
      const applianceData = selectedAppliances[appliance];
  
      if (!applianceData) continue; // Skip if undefined
  
      // Ensure numeric values are positive and required fields are filled
      if (
        !applianceData.power || isNaN(applianceData.power) || applianceData.power <= 0 ||
        !applianceData.count || isNaN(applianceData.count) || applianceData.count <= 0 ||
        !applianceData.usage || applianceData.usage.trim() === "" ||
        !Array.isArray(applianceData.days) || applianceData.days.length === 0
      ) {
        return false;
      }
  
      // Ensure at least one time slot is selected for each chosen day
      for (const day of applianceData.days) {
        if (!applianceData.times || !applianceData.times[day] || applianceData.times[day].length === 0) {
          return false;
        }
      }
    }
    return true;
  };
  
  
  // Handle form submission and send data to backend
  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage("");

    if (!validateInputs()) {
        setIsLoading(false);
        setMessage("Please fill in all the fields correctly.");
        return;
    }

    const dataToSend = {
        location,
        appliances: selectedAppliances,
        consumerNo,
        phase,
        selectedDates,
    };

    console.log("🔵 Sending data:", JSON.stringify(dataToSend, null, 2));

    try {
        const response = await axios.post("http://localhost:5000/submit", dataToSend);
        
        console.log("🟢 Response received:", response.data);
        setPredictionData(response.data);
        setMessage("Data submitted successfully!");
    } catch (error) {
        console.error("🔴 Error sending data:", error.response?.data || error.message);
        setMessage("There was an error submitting the data.");
    } finally {
        setIsLoading(false);
    }
};


  

  return (
    <div className="container">
      <h1>Energy Consumption Prediction</h1>
      <div className="input-section">
        <label>Location:</label>
        <input type="text" value={location} readOnly placeholder="Fetching location..." />
        <button onClick={fetchLocation}>Get Location</button>

        <label>Consumer Number:</label>
        <input type="text" value={consumerNo} onChange={(e) => setConsumerNo(e.target.value)} placeholder="Enter Consumer Number" />

        <label>Phase:</label>
        <select value={phase} onChange={(e) => setPhase(e.target.value)}>
          <option>1-Phase</option>
          <option>3-Phase</option>
        </select>
        
        <div className="calendar-container">
          <CustomCalendar selectedDates={selectedDates} setSelectedDates={setSelectedDates} />
        </div>
        
        <label>Select Appliances:</label>
        <button onClick={selectAllAppliances} className="select-all-btn">
          {Object.keys(selectedAppliances).length === appliancesList.length ? "Deselect All" : "Select All"}
        </button>
        <div className="appliance-grid">
          {appliancesList.map((appliance) => (
            <div key={appliance} className="appliance-item">
              <label>
                <input
                  type="checkbox"
                  checked={!!selectedAppliances[appliance]}
                  onChange={() => handleApplianceSelect(appliance)}
                />
                {appliance}
              </label>
            </div>
          ))}
        </div>

        {Object.keys(selectedAppliances).map((appliance) => (
          <div key={appliance} className="appliance-details">
            <h3>{appliance}</h3>
            <input type="number" placeholder="Power Rating (W)" value={selectedAppliances[appliance].power} onChange={(e) => handleApplianceChange(appliance, "power", e.target.value)} />
            <input type="number" placeholder="Count" value={selectedAppliances[appliance].count} onChange={(e) => handleApplianceChange(appliance, "count", e.target.value)} />
            <input type="text" placeholder="Usage Time (e.g., 2h30m)" value={selectedAppliances[appliance].usage} onChange={(e) => handleApplianceChange(appliance, "usage", e.target.value)} />
            <div className="days-selection">
              <button onClick={() => toggleDaySelection(appliance, "all")}>Select All Days</button>
              <div className="days-grid">
                {daysOfWeek.map((day) => (
                  <div key={day} className="day-item">
                    <label>
                      <input
                        type="checkbox"
                        checked={selectedAppliances[appliance].days.includes(day)}
                        onChange={() => toggleDaySelection(appliance, day)}
                      />
                      {day}
                    </label>
                    {selectedAppliances[appliance].days.includes(day) && (
                      <div className="times-of-day">
                        {timesOfDay.map((time) => (
                          <label key={time}>
                            <input
                              type="checkbox"
                              checked={selectedAppliances[appliance].times[day]?.includes(time)}
                              onChange={() => {
                                const updatedTimes = selectedAppliances[appliance].times[day] || [];
                                if (updatedTimes.includes(time)) {
                                  updatedTimes.splice(updatedTimes.indexOf(time), 1);
                                } else {
                                  updatedTimes.push(time);
                                }
                                handleApplianceChange(appliance, "times", {
                                  ...selectedAppliances[appliance].times,
                                  [day]: updatedTimes,
                                });
                              }}
                            />
                            {time}
                          </label>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
        <button type="button" className="submit-btn" disabled={isLoading} onClick={handleSubmit}>
  {isLoading ? "Submitting..." : "Submit"}
</button>

        {message && <p>{message}</p>}
      </div>

      {billAmount !== null && (
        <div className="bill-display">
          <h2>Estimated Electricity Bill</h2>
          <p>₹ {billAmount}</p>
        </div>
      )}

      <Graphs />
      <Recommendations recommendations={["Turn off lights when not in use", "Use energy-efficient appliances"]} />
     
    </div>
  );
};

export default EnergyPredictionApp;
