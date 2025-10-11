#!/bin/bash
set -e

ollama serve &

PID=$!

echo "Server Ollama avviato in background con PID: $PID"
sleep 5 

echo "Inizio il download dei modelli (verrà eseguito solo se non sono già presenti)..."

ollama pull gpt-oss:20b
ollama pull nomic-embed-text

echo "Download dei modelli completato. gpt-oss:20b, nomic-embed-text"
wait $PID