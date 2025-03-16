require('dotenv').config(); // Load environment variables
const express = require('express');
const axios = require('axios');
const mysql = require('mysql2');
const { exec } = require('child_process');
const cors = require('cors'); // CORS middleware
const fs = require('fs'); // File system to save CSV

const app = express();
app.use(express.json());
app.use(cors()); // Enable CORS

// MySQL Database connection
const db = mysql.createConnection({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    database: process.env.DB_NAME
});

// Connect to MySQL
db.connect((err) => {
    if (err) {
        console.error("Database connection failed:", err);
        return;
    }
    console.log("Connected to MySQL database");
});

// Function to fetch and store weather data
async function fetchAndStoreWeatherData(location, locationId) {
    try {
        const match = location.match(/Lat:\s*([\d.-]+),\s*Lng:\s*([\d.-]+)/);
        if (!match) throw new Error("Invalid location format");

        const [lat, lon] = [match[1], match[2]];
        const response = await axios.get("http://api.openweathermap.org/data/2.5/weather", {
            params: { lat, lon, appid: process.env.OPENWEATHER_API_KEY, units: "metric" },
        });

        const weatherData = response.data;

        // Extracting required weather parameters
        const temperature = weatherData.main?.temp || null;
        const humidity = weatherData.main?.humidity || null;
        const windSpeed = weatherData.wind?.speed || null;
        const visibility = weatherData.visibility || null;
        const pressure = weatherData.main?.pressure || null;
        const cloudCover = weatherData.clouds?.all || null;
        const windBearing = weatherData.wind?.deg || null;
        const precipIntensity = weatherData.rain?.["1h"] || 0; // Rainfall in last 1 hour
        const precipProbability = weatherData.rain ? 1 : 0; // Assume rain presence as probability

        // Get date & time components
        const currentDate = new Date();
        const month = currentDate.getMonth() + 1; // JS months are 0-indexed
        const day = currentDate.getDate();
        const hour = currentDate.getHours();
        const weekday = currentDate.getDay();

        // Insert or update weather data in MySQL
        db.query(
            `INSERT INTO weather_data (location_id, temperature, humidity, wind_speed, visibility, pressure, cloud_cover, wind_bearing, precip_intensity, precip_probability, month, day, hour, weekday)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
             ON DUPLICATE KEY UPDATE temperature=?, humidity=?, wind_speed=?, visibility=?, pressure=?, cloud_cover=?, wind_bearing=?, precip_intensity=?, precip_probability=?, month=?, day=?, hour=?, weekday=?`,
            [
                locationId, temperature, humidity, windSpeed, visibility, pressure, cloudCover,
                windBearing, precipIntensity, precipProbability, month, day, hour, weekday, // Insert values
                temperature, humidity, windSpeed, visibility, pressure, cloudCover,
                windBearing, precipIntensity, precipProbability, month, day, hour, weekday  // Update values
            ],
            (err) => {
                if (err) {
                    console.error("Error inserting weather data:", err);
                    return;
                }
                console.log("Weather data inserted successfully");
            }
        );

        return weatherData;
    } catch (error) {
        console.error("Error fetching weather data:", error.message);
        return null;
    }
}

app.post('/predict-energy', async (req, res) => {
    const { appliances, location } = req.body;

    db.query('INSERT INTO locations (location_name) VALUES (?)', [location], async (err, result) => {
        if (err) return res.status(500).json({ error: "Error inserting location into database" });

        const locationId = result.insertId;
        const weatherData = await fetchAndStoreWeatherData(location, locationId);
        if (!weatherData) return res.status(400).json({ error: "Could not fetch weather data" });

        Object.keys(appliances).forEach(applianceName => {
            const appliance = appliances[applianceName];
            db.query(
                'INSERT INTO appliances (name, power_rating, count, usage_hours, usage_days, time_of_usage) VALUES (?, ?, ?, ?, ?, ?)',
                [
                    applianceName,
                    parseFloat(appliance.power), // Convert to float
                    parseInt(appliance.count),   // Convert to integer
                    parseFloat(appliance.usageTime.replace(/[^0-9.]/g, '')), // Remove non-numeric chars from usage hours
                    JSON.stringify(appliance.days), 
                    JSON.stringify(appliance.times)
                ],
                (err, result) => {
                    if (err) {
                        console.error("Error inserting appliance into database:", err);
                        return;
                    }
                    console.log("Appliance inserted into database:", result);
                }
            );
        });

        const simulatedData = generateSimulatedData(appliances, weatherData);
        if (!simulatedData) return res.status(400).json({ error: "Error generating simulated data" });

        const csvFilePath = saveDataToCSV(simulatedData);
        if (!csvFilePath) return res.status(500).json({ error: "Error saving data to CSV" });

        exec(`python3 ${__dirname}/predict_energy.py`, (error, stdout) => {
            if (error) return res.status(500).json({ error: "Prediction failed" });

            let predictionResult;
            try {
                predictionResult = JSON.parse(stdout);
            } catch (parseError) {
                return res.status(500).json({ error: "Prediction result parsing failed" });
            }

            res.json({
                prediction: predictionResult,
                billAmount: calculateBillAmount(predictionResult),
                recommendations: getRecommendations(predictionResult)
            });
        });
    });
});

app.post('/submit', async (req, res) => {
    try {
        const { location, appliances } = req.body;
        const energyResponse = await axios.post('http://localhost:5000/predict-energy', { location, appliances });
        res.json(energyResponse.data);
    } catch (error) {
        res.status(500).json({ error: "Error predicting energy consumption" });
    }
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));

// Helper functions
function generateSimulatedData(appliances, weatherData) {
    return Object.keys(appliances).map(applianceName => {
        const appliance = appliances[applianceName];
        return {
            applianceName,
            energyUsage: appliance.usageTime * (weatherData.main.temp / 300)
        };
    });
}

function saveDataToCSV(data) {
    const csvHeader = 'applianceName,energyUsage\n';
    const csvRows = data.map(item => `${item.applianceName},${item.energyUsage}`).join('\n');
    const filePath = './simulated_data.csv';
    fs.writeFileSync(filePath, csvHeader + csvRows);
    return filePath;
}

function calculateBillAmount(prediction) {
    return prediction.totalEnergyUsage * 0.10;
}

function getRecommendations(prediction) {
    const recommendations = [];
    if (prediction.totalEnergyUsage > 100) recommendations.push("Use energy-efficient appliances.");
    if (prediction.totalEnergyUsage > 200) recommendations.push("Shift usage to off-peak hours.");
    return recommendations;
}
