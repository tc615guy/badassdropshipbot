#!/bin/bash

echo "🚀 Badass Dropship Bot - Setup Script"
echo "======================================"
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

if [ $? -ne 0 ]; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✓ Python 3 found"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment"
    exit 1
fi

echo "✓ Virtual environment created"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✓ Dependencies installed"
echo ""

# Create necessary directories
echo "Creating directories..."
mkdir -p logs data exports reports

echo "✓ Directories created"
echo ""

# Initialize database
echo "Initializing database..."
python main.py init

if [ $? -ne 0 ]; then
    echo "❌ Failed to initialize database"
    exit 1
fi

echo "✓ Database initialized"
echo ""

# Check .env file
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found"
    echo "Please create .env file from .env.example and add your API keys"
    echo ""
    echo "Required API keys:"
    echo "  - ANTHROPIC_API_KEY (for AI content generation)"
    echo "  - Other platform API keys (see .env.example)"
else
    echo "✓ .env file found"
fi

echo ""
echo "======================================"
echo "✓ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your Anthropic API key"
echo "2. Run: source venv/bin/activate"
echo "3. Run: python main.py scout --help"
echo "4. See USAGE_GUIDE.md for detailed instructions"
echo ""
echo "Quick start:"
echo "  python main.py scout --source aliexpress --limit 10"
echo "  python main.py list"
echo "  python main.py autopilot --help"
echo ""
echo "🚀 Happy dropshipping!"
