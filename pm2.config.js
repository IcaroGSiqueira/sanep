module.exports = {
  apps: [
    {
      name: 'sanep-main',
      script: 'start-sanep.py',
      interpreter: 'python3',
      watch: true,
      min_uptime: 5000,
      max_restarts: 3,
    },
    {
      name: 'sanep-alert-bot',
      script: 'alert-bot.py',
      interpreter: 'python3',
      watch: true,
      min_uptime: 5000,
      max_restarts: 3,
    },
  ],
};