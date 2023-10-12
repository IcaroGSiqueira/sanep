module.exports = {
  apps: [
    {
      name: 'iwater-main',
      script: 'get-mqtt.py',
      interpreter: 'python3',
    },
    {
      name: 'iwater-alert-bot',
      script: 'alert-bot.py',
      interpreter: 'python3',
    },
  ],
};