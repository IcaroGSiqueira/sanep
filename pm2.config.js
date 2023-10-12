module.exports = {
  apps: [
    {
      name: 'iwater-main',
      script: 'get-mqtt.py',
      interpreter: 'python3',
      watch: true,
      min_uptime: 5000,
      max_restarts: 3,
    },
    {
      name: 'iwater-alert-bot',
      script: 'alert-bot.py',
      interpreter: 'python3',
      watch: true,
      min_uptime: 5000,
      max_restarts: 3,
    },
  ],
};