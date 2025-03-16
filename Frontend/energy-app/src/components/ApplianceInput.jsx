import React, { useState } from "react";
import axios from "axios";  // Import axios
import "./ApplianceInput.css";

const appliancesList = [
  "Dishwasher",
  "Air Conditioner",
  "Heater",
  "Computer Devices",
  "Refrigertor",
  "Washing Machine",
  "Fans",
  "Chimney",
  "Food Processor",
  "Induction Cooktop",
  "Lights",
  "Water Pump",
  "Microwave",
  "TV"
];

const timeOptions = ["Morning", "Noon", "Evening", "Night"];

const ApplianceInput = () => {
  const [selectedAppliances, setSelectedAppliances] = useState({});
  const [location, setLocation] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState("");

  // Handle checkbox change for appliance selection
  const handleCheckboxChange = (appliance) => {
    setSelectedAppliances((prev) => ({
      ...prev,
      [appliance]: prev[appliance]
        ? undefined
        : { power: "", count: 1, days: [], times: {}, usageTime: "" },
    }));
  };

  // Handle input field change for appliances
  const handleInputChange = (appliance, field, value) => {
    setSelectedAppliances((prev) => ({
      ...prev,
      [appliance]: { ...prev[appliance], [field]: value },
    }));
  };

  // Handle day selection for each appliance
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

  // Handle time selection for each appliance and day
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

  // Get user's geolocation
  const handleGetLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocation(`Lat: ${position.coords.latitude}, Lng: ${position.coords.longitude}`);
        },
        (error) => {
          console.error("Error getting location:", error);
          setLocation("Location access denied. Please enter location manually.");
        }
      );
    } else {
      setLocation("Geolocation not supported. Please enter location manually.");
    }
  };

  // Validate input before sending to backend
  const validateInputs = () => {
    // Ensure all appliances have valid data
    for (const appliance in selectedAppliances) {
      const applianceData = selectedAppliances[appliance];
      if (
        !applianceData.power ||
        !applianceData.count ||
        !applianceData.days.length ||
        !applianceData.usageTime
      ) {
        return false;
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
    };

    console.log("🔵 Sending data:", JSON.stringify(dataToSend, null, 2));

    try {
        const response = await axios.post("http://localhost:5000/submit", dataToSend);
        
        console.log("🟢 Response received:", response.data);
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
      <h2 className="title">Select Appliances</h2>
      <div className="location-container">
        <button onClick={handleGetLocation} className="location-btn">
          Get Location
        </button>
        <input
          type="text"
          placeholder="Enter location manually"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          className="input"
        />
      </div>

      <form onSubmit={handleSubmit}>
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

        <button type="submit" className="submit-btn" disabled={isLoading}>
          {isLoading ? "Submitting..." : "Submit"}
        </button>
        {message && <p>{message}</p>}
      </form>
    </div>
  );
};

export default ApplianceInput;
