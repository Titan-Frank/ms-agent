#!/bin/bash

set -e  # Exit on error

echo "======================================"
echo "Setting up fin_research environment"
echo "======================================"

# Step 1: Create conda environment
echo ""
echo "[1/6] Creating conda environment 'fin_research' with Python 3.11..."
conda create -n fin_research python=3.11 -y

# Step 2: Activate conda environment
echo ""
echo "[2/6] Activating conda environment..."
eval "$(conda shell.bash hook)"
conda activate fin_research

# Step 3: Install framework requirements
echo ""
echo "[3/6] Installing framework requirements..."
pip install -r requirements/framework.txt

# Step 4: Install research requirements
echo ""
echo "[4/6] Installing research requirements..."
pip install -r requirements/research.txt

# Step 5: Install ms-agent in editable mode
echo ""
echo "[5/6] Installing ms-agent in editable mode..."
pip install -e .

# Step 6: Install additional packages
echo ""
echo "[6/6] Installing akshare and baostock..."
pip install akshare baostock

echo ""
echo "======================================"
echo "✓ Setup completed successfully!"
echo "======================================"
echo ""
echo "To activate the environment, run:"
echo "  conda activate fin_research"
echo ""
echo "To run the fin_research project, use:"
echo "  PYTHONPATH=. python ms_agent/cli/cli.py run --config projects/fin_research --query '<your query>' --trust_remote_code true"
