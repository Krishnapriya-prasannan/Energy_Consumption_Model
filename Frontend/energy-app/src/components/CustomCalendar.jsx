import React from "react";
import Calendar from "react-calendar";
import "react-calendar/dist/Calendar.css";
import "./CustomCalendar.css"; // Import the CSS file

const CustomCalendar = ({ selectedDates = [], setSelectedDates }) => {
  const handleDateChange = (date) => {
    const dateString = date.toDateString();

    if (selectedDates.length === 0) {
      setSelectedDates([dateString]); // First date selection
    } else if (selectedDates.length === 1) {
      const startDate = new Date(selectedDates[0]);
      const endDate = new Date(date);

      if (startDate > endDate) {
        [startDate, endDate] = [endDate, startDate]; // Ensure start is before end
      }

      const newSelectedDates = [];
      let currentDate = new Date(startDate);

      while (currentDate <= endDate) {
        newSelectedDates.push(currentDate.toDateString());
        currentDate.setDate(currentDate.getDate() + 1);
      }

      setSelectedDates(newSelectedDates);
    } else {
      setSelectedDates([dateString]); // Reset selection if a third date is clicked
    }
  };

  return (
    <div className="calendar-container">
      <h3 style={{ textAlign: "center" }}>Select Usage Dates :</h3>
      <Calendar
        onClickDay={handleDateChange}
        tileClassName={({ date }) =>
          selectedDates.includes(date.toDateString()) ? "selected-date" : null
        }
      />
    </div>
  );
};

export default CustomCalendar;
