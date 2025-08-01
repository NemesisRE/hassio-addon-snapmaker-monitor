#!/usr/bin/with-contenv bashio

bashio::log.level "$(bashio::config 'option_log_level')"
bashio::log.info "Starte Snapmaker Monitor Addon..."
bashio::log.info "HA_TOKEN: ${HA_TOKEN}"
bashio::log.info "HA_WEBHOOK_URL: ${HA_WEBHOOK_URL}"
bashio::log.info "SM_IP: ${SM_IP}"
bashio::log.info "SM_PORT: ${SM_PORT}"
bashio::log.info "SM_TOKEN: ${SM_TOKEN}"

python3 /app/smStatus.py
