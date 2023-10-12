module.exports = {
  apps: [
    {
      name: 'get-mqtt',
      script: 'get-mqtt.py',
      interpreter: 'python3',
    },
    {
      name: 'alert-bot',
      script: 'alert-bot.py',
      interpreter: 'python3',
    },
  ],
};