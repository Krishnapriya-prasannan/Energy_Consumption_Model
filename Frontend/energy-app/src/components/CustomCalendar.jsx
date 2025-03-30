import React, { useState } from "react";
import Calendar from "react-calendar";
import "react-calendar/dist/Calendar.css";
import "./CustomCalendar.css";

const CustomCalendar = ({ selectedDates, setSelectedDates }) => {
  const [ranges, setRanges] = useState([]);
  const [currentRange, setCurrentRange] = useState([]);
  const [clickTimeout, setClickTimeout] = useState(null);

  // 🔥 Ensure selectedDates is a Set
  const selectedDatesSet = new Set(selectedDates);

  const handleDateChange = (date) => {
    const dateString = date.toDateString();

    if (selectedDatesSet.has(dateString)) {
      // Remove date
      setSelectedDates((prev) => {
        const updated = new Set(prev);
        updated.delete(dateString);
        return [...updated]; // Convert back to array for React state
      });

      setRanges((prev) =>
        prev.map((range) => range.filter((d) => d !== dateString)).filter((r) => r.length > 0)
      );

      return;
    }

    if (clickTimeout) {
      clearTimeout(clickTimeout);
      setClickTimeout(null);

      if (currentRange.length === 0) {
        setCurrentRange([dateString]);
      } else if (currentRange.length === 1) {
        let startDate = new Date(currentRange[0]);
        let endDate = new Date(dateString);

        if (startDate > endDate) [startDate, endDate] = [endDate, startDate];

        const newRange = [];
        let tempDate = new Date(startDate);
        while (tempDate <= endDate) {
          newRange.push(tempDate.toDateString());
          tempDate.setDate(tempDate.getDate() + 1);
        }

        setRanges((prev) => [...prev, newRange]);
        setSelectedDates((prev) => [...prev, ...newRange]); // Convert to array for React state
        setCurrentRange([]);
      }
    } else {
      setClickTimeout(
        setTimeout(() => {
          setClickTimeout(null);
          setSelectedDates((prev) => [...prev, dateString]); // Convert to array
        }, 250)
      );
    }
  };

  return (
    <div className="calendar-container">
      <h3 style={{ textAlign: "center" }}>Select Usage Dates :</h3>
      <Calendar
        onClickDay={handleDateChange}
        tileClassName={({ date }) =>
          selectedDatesSet.has(date.toDateString()) ? "selected-date" : "" // Now `has` works!
        }
      />
    </div>
  );
};

export default CustomCalendar;
