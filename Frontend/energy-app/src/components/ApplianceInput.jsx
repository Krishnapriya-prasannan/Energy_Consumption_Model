import React, { useState } from "react";
import "./ApplianceInput.css";

const appliancesList = [
  "Refrigerator",
  "Air Conditioner",
  "Washing Machine",
  "Microwave Oven",
  "Television",
  "Laptop",
  "Ceiling Fan",
  "Water Heater",
];

const timeOptions = ["Morning", "Noon", "Evening", "Night"];

const ApplianceInput = () => {
  const [selectedAppliances, setSelectedAppliances] = useState({});
  const [location, setLocation] = useState("");

  const handleCheckboxChange = (appliance) => {
    setSelectedAppliances((prev) => ({
      ...prev,
      [appliance]: prev[appliance]
        ? undefined
        : { power: "", count: 1, days: [], times: {}, usageTime: "" }, // Single text field for total usage time
    }));
  };

  const handleInputChange = (appliance, field, value) => {
    setSelectedAppliances((prev) => ({
      ...prev,
      [appliance]: { ...prev[appliance], [field]: value },
    }));
  };

  const handleDayChange = (appliance, day) => {
    setSelectedAppliances((prev) => {
      const updatedDays = prev[appliance].days.includes(day)
        ? prev[appliance].days.filter((d) => d !== day)
        : [...prev[appliance].days, day];
      return {
        ...prev,
        [appliance]: {
          ...prev[appliance],
          days: updatedDays,
          times: { ...prev[appliance].times, [day]: prev[appliance].times[day] || [] },
        },
      };
    });
  };

  const handleTimeChange = (appliance, day, value) => {
    setSelectedAppliances((prev) => {
      const updatedTimes = prev[appliance].times[day] || [];
      const newTimes = updatedTimes.includes(value)
        ? updatedTimes.filter((t) => t !== value)
        : [...updatedTimes, value];
      return {
        ...prev,
        [appliance]: {
          ...prev[appliance],
          times: {
            ...prev[appliance].times,
            [day]: newTimes,
          },
        },
      };
    });
  };

  const handleGetLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocation(`Lat: ${position.coords.latitude}, Lng: ${position.coords.longitude}`);
        },
        (error) => {
          console.error("Error getting location:", error);
          setLocation("Location access denied");
        }
      );
    } else {
      setLocation("Geolocation not supported");
    }
  };

  return (
    <div className="container">
      <h2 className="title">Select Appliances</h2>
      <div className="location-container">
        <button onClick={handleGetLocation} className="location-btn">Get Location</button>
        <input
          type="text"
          placeholder="Enter location manually"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          className="input"
        />
      </div>

      <div className="appliance-grid">
        {appliancesList.map((appliance) => (
          <label key={appliance} className="appliance-item">
            <input
              type="checkbox"
              checked={!!selectedAppliances[appliance]}
              onChange={() => handleCheckboxChange(appliance)}
            />
            {appliance}
          </label>
        ))}
      </div>

      {Object.keys(selectedAppliances).map(
        (appliance) =>
          selectedAppliances[appliance] && (
            <div key={appliance} className="appliance-details">
              <h3>{appliance}</h3>
              <label className="input-label">Power Rating (W):</label>
              <input
                type="number"
                className="input"
                value={selectedAppliances[appliance].power}
                onChange={(e) => handleInputChange(appliance, "power", e.target.value)}
              />
              <label className="input-label">Count:</label>
              <input
                type="number"
                className="input"
                min="1"
                value={selectedAppliances[appliance].count}
                onChange={(e) => handleInputChange(appliance, "count", e.target.value)}
              />

              <h4 className="subtitle">Usage Days:</h4>
              <div className="day-grid">
                {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((day) => (
                  <label key={day} className="day-item">
                    <input
                      type="checkbox"
                      checked={selectedAppliances[appliance].days.includes(day)}
                      onChange={() => handleDayChange(appliance, day)}
                    />
                    {day}
                  </label>
                ))}
              </div>

              {selectedAppliances[appliance].days.map((day) => (
                <div key={day} className="day-time">
                  <label>{day} Usage Time:</label>
                  <div className="time-options">
                    {timeOptions.map((time) => (
                      <label key={time} className="time-item">
                        <input
                          type="checkbox"
                          checked={selectedAppliances[appliance].times[day]?.includes(time) || false}
                          onChange={() => handleTimeChange(appliance, day, time)}
                        />
                        {time}
                      </label>
                    ))}
                  </div>
                </div>
              ))}

              <h4 className="subtitle">Total Usage Time (Hours & Minutes):</h4>
              <input
                type="text"
                placeholder="e.g., 2h 30m"
                className="input"
                value={selectedAppliances[appliance].usageTime}
                onChange={(e) => handleInputChange(appliance, "usageTime", e.target.value)}
              />
            </div>
          )
      )}
    </div>
  );
};

export default ApplianceInput;
