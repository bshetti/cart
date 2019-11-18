#!/bin/sh
until /usr/bin/redis-cli -h $REDIS_HOST -p $REDIS_PORT ping | grep -q 'PONG'; do
  >&2 echo "redis is unavailable - sleeping" then
  sleep 1
done
echo "Apply flask now"
python3 cart.py
exec "$@"
