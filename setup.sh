#!/bin/bash

echo "🚀 Installing LangGraph Conversation System..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Installation complete!"
echo ""
echo "📝 Next steps:"
echo "1. Configure your .env file with API keys"
echo "2. Start Redis server: redis-server"
echo "3. Run demo: python demo.py"
echo "4. Or start API server: python main.py"
