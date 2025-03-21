import React, { useState } from "react";
import "./EnergyApp.css";
import Graphs from "./Graph"; 
import Recommendations from "./Recommendations";

const EnergyPredictionApp = () => {
  const [location, setLocation] = useState("");
  const [consumerNo, setConsumerNo] = useState("");
  const [phase, setPhase] = useState("1-Phase");
  const [selectedAppliances, setSelectedAppliances] = useState({});
  const [billAmount, setBillAmount] = useState(null);

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

  const toggleTimeSelection = (appliance, day, time) => {
    setSelectedAppliances((prev) => {
      const updated = { ...prev };

      if (!updated[appliance]) return prev;

      const currentTimes = updated[appliance].times[day] || [];
      const updatedTimes = currentTimes.includes(time)
        ? currentTimes.filter((t) => t !== time)
        : [...currentTimes, time];

      updated[appliance] = {
        ...updated[appliance],
        times: { ...updated[appliance].times, [day]: updatedTimes },
      };

      return { ...updated };
    });
  };

  const selectAllTimesForDay = (appliance, day) => {
    setSelectedAppliances((prev) => {
      const updated = { ...prev };

      if (!updated[appliance]) return prev;

      const allSelected = updated[appliance].times[day]?.length === timesOfDay.length;
      updated[appliance] = {
        ...updated[appliance],
        times: { ...updated[appliance].times, [day]: allSelected ? [] : [...timesOfDay] },
      };

      return { ...updated };
    });
  };

  const selectAllDays = (appliance) => {
    setSelectedAppliances((prev) => {
      const updated = { ...prev };
      updated[appliance].days = [...daysOfWeek];
      updated[appliance].times = daysOfWeek.reduce((acc, day) => ({ ...acc, [day]: [] }), {});
      return updated;
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

  const handleSubmit = () => {
    if (!location || !consumerNo || Object.keys(selectedAppliances).length === 0) {
      alert("Please fill in all required fields");
      return;
    }
    setBillAmount((Math.random() * 100).toFixed(2));
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

        <label>Select Appliances:</label>
        <div className="appliance-list">
          {appliancesList.map((appliance) => (
            <div key={appliance}>
              <label>
                <input
                  type="checkbox"
                  checked={!!selectedAppliances[appliance]}
                  onChange={() => handleApplianceSelect(appliance)}
                />
                {appliance}
              </label>
              {selectedAppliances[appliance] && (
                <div className="appliance-details">
                  <input type="number" placeholder="Power Rating (W)" value={selectedAppliances[appliance].power} onChange={(e) => handleApplianceChange(appliance, "power", e.target.value)} />
                  <input type="number" placeholder="Count" value={selectedAppliances[appliance].count} onChange={(e) => handleApplianceChange(appliance, "count", e.target.value)} />
                  <input type="text" placeholder="Usage Time (e.g., 2h30m)" value={selectedAppliances[appliance].usage} onChange={(e) => handleApplianceChange(appliance, "usage", e.target.value)} />

                  <div className="days-selection">
                    <label>Usage Days:</label>
                    <button onClick={() => selectAllDays(appliance)}>Select All</button>
                    <div className="horizontal-options">
                      {daysOfWeek.map((day) => (
                        <label key={day}>
                          <input type="checkbox" checked={selectedAppliances[appliance].days.includes(day)} onChange={() => toggleDaySelection(appliance, day)} />
                          {day}
                        </label>
                      ))}
                    </div>
                  </div>

                  {selectedAppliances[appliance].days.map((day) => (
                    <div key={day} className="times-selection">
                      <label>{day} - Time of Usage:</label>
                      <button onClick={() => selectAllTimesForDay(appliance, day)}>Select All</button>
                      <div className="horizontal-options">
                        {timesOfDay.map((time) => (
                          <label key={time}>
                            <input type="checkbox" checked={selectedAppliances[appliance].times[day]?.includes(time)} onChange={() => toggleTimeSelection(appliance, day, time)} />
                            {time}
                          </label>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
        <button onClick={handleSubmit} disabled={!location  || Object.keys(selectedAppliances).length === 0}>Submit</button>
      </div>
       {/* BILL DISPLAY COMPONENT */}
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
