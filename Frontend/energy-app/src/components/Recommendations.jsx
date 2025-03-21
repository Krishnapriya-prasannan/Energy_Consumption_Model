import React from 'react';
import './Recommendations.css';

const Recommendations = ({ recommendations }) => {
  return (
    <div className="recommendations-container">
      <h2>AI-Based Energy-Saving Recommendations</h2>
      <ul>
        {recommendations.length > 0 ? (
          recommendations.map((tip, index) => <li key={index}>✅ {tip}</li>)
        ) : (
          <li>No recommendations available. Please enter appliance details.</li>
        )}
      </ul>
    </div>
  );
};

export default Recommendations;
