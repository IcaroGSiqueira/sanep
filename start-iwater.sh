pm2 start get-mqtt.py --name iwater-main --interpreter=python3 --watch &&
pm2 start alert-bot.py --name iwater-alert-bot --interpreter=python3 --watch