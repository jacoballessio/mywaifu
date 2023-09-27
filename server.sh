#!/bin/bash

# Define variables
APP_NAME="api_endpoint:app"
BIND_ADDRESS="0.0.0.0:8000"
TIMEOUT=120
NUM_WORKERS=2
PID_FILE="./gunicorn.pid"
LOG_FILE="./gunicorn.log"

start_gunicorn() {
  echo "Starting Gunicorn."
  exec gunicorn $APP_NAME \
    --bind $BIND_ADDRESS \
    --timeout $TIMEOUT \
    --workers $NUM_WORKERS \
    --pid $PID_FILE \
    --log-file $LOG_FILE \
    --access-logfile - \
    --error-logfile - 
}

stop_gunicorn() {
  if [ -f $PID_FILE ]; then
    echo "Stopping Gunicorn."
    kill -9 $(cat "$PID_FILE")
    rm -f "$PID_FILE"
  else
    echo "No Gunicorn process found."
  fi
}

restart_gunicorn() {
  stop_gunicorn
  start_gunicorn
}

# Main execution
case "$1" in
  start)
    start_gunicorn
    ;;
  stop)
    stop_gunicorn
    ;;
  restart)
    restart_gunicorn
    ;;
  *)
    echo "Usage: $0 {start|stop|restart}"
    exit 1
esac
