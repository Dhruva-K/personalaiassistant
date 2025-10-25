#!/bin/bash

echo "🚀 Setting up Ollama for Privacy-Aware AI Assistant"

# Install Ollama
if ! command -v ollama &> /dev/null; then
    echo "📦 Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "✅ Ollama already installed"
fi

# Kill any existing Ollama processes
pkill ollama 2>/dev/null

# Start Ollama service
echo "🔄 Starting Ollama service..."
nohup ollama serve > /tmp/ollama.log 2>&1 &

# Wait for service to start
echo "⏳ Waiting for Ollama to be ready..."
sleep 5

# Check if service is running
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama service is running"
else
    echo "❌ Failed to start Ollama. Check /tmp/ollama.log"
    exit 1
fi

# Pull model if not exists
MODEL="llama3.2:3b"
if ! ollama list | grep -q "$MODEL"; then
    echo "📥 Pulling model: $MODEL (this may take 5-10 minutes)..."
    ollama pull $MODEL
else
    echo "✅ Model $MODEL already available"
fi

echo "🎉 Ollama setup complete!"
echo "💡 Model ready: $MODEL"
echo "📝 Logs: tail -f /tmp/ollama.log"