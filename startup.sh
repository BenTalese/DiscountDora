#!/bin/bash

# DEV
python framework/dora_api/startup.py &
python framework/merchant_api/startup.py &
quasar serve /app/framework/web_app/dist/spa -H 0.0.0.0 -p 5174 &

# quasar serve /app/framework/web_app &
# python framework/emailer/startup.py &

# PROD
# gunicorn -w 4 -b 0.0.0.0:5170 framework.dora_api.startup:app &
# gunicorn -w 4 -b 0.0.0.0:5172 framework.merchant_api.startup:app &
# nginx -g "daemon off;"

wait -n

exit $?
