module.exports = {
  apps: [
    {
      name: 'get-mqtt-iwater',
      script: 'get-mqtt.py',
      interpreter: 'python3',
    },
    {
      name: 'alert-bot-iwater',
      script: 'alert-bot.py',
      interpreter: 'python3',
    },
  ],
};