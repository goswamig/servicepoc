const express = require('express');
const path = require('path');
const app = express();
const port = 8001;

// Serve the static log files from the logs directory
app.use('/logs', express.static(path.join(__dirname, '../logs')));

app.listen(port, () => {
  console.log(`Log server listening at http://localhost:${port}`);
});

