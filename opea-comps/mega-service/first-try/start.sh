#!/bin/zsh

# setup environment variables for megaservice

export MEGA_SERVICE_PORT=8888
export LLM_SERVICE_HOST_IP="localhost"
export LLM_SERVICE_PORT=8008
export LLM_MODEL="google/gemma:2b"
export GUARDRAIL_SERVICE_HOST_IP="localhost"
export GUARDRAIL_SERVICE_PORT=80

uv run mega.py