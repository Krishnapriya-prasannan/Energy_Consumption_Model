import React from "react";
import Calendar from "react-calendar";
import "react-calendar/dist/Calendar.css";
import "./CustomCalendar.css"; // Import the CSS file

const CustomCalendar = ({ selectedDates = [], setSelectedDates }) => {
  // Function to handle date selection
  const handleDateChange = (date) => {
    const dateString = date.toDateString();
    setSelectedDates((prev) =>
      prev && prev.includes(dateString)
        ? prev.filter((d) => d !== dateString) // Unselect if already selected
        : [...(prev || []), dateString] // Add if not selected
    );
  };

return (
    <div className="calendar-container">
        <h3 style={{ textAlign: "center" }}>Select Usage Dates :</h3>
        <Calendar
            onClickDay={handleDateChange}
            tileClassName={({ date }) =>
                Array.isArray(selectedDates) && selectedDates.includes(date.toDateString())
                    ? "selected-date"
                    : null
            }
        />
    </div>
);
};

export default CustomCalendar;
