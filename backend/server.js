require('dotenv').config({ path: '../.env' }); // Load .env file at the very top
const express = require('express');
const mysql = require('mysql2');

const app = express();
app.use(express.json()); // Ensure express can parse JSON

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

// Example API to test database connection
app.get('/test-db', (req, res) => {
    db.query("SELECT 1", (err, results) => {
        if (err) {
            console.error("Error connecting to database:", err);
            return res.status(500).json({ error: "Database connection failed" });
        }
        res.json({ message: "Database connected successfully", data: results });
    });
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
