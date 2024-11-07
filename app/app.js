const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

app.get('/', (req, res) => {
    res.send('Node.js app is running');
});

// Endpoint for health check
app.get('/health', (req, res) => {
    res.status(200).json({ status: 'UP' });
});

app.listen(3000, '0.0.0.0', () => {
    console.log('App running on port 3000');
});


