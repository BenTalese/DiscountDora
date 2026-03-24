#!/bin/bash

# DEV
python -m dora_api.startup &
python -m merchant_api.startup &
# python -m emailer.startup &
quasar serve /app/web_app/dist/spa -H 0.0.0.0 -p 5174 &

# quasar serve /app/web_app &

# PROD
# gunicorn -w 4 -b 0.0.0.0:5170 dora_api.startup:app &
# gunicorn -w 4 -b 0.0.0.0:5172 merchant_api.startup:app &
# nginx -g "daemon off;"

wait -n

exit $?
