#!/bin/bash
#
# msgmodel Smoke Test Script
# Tests all three providers with a simple query
#
# Usage: ./msgmodel-smoke-test.sh
#
# Prerequisites:
#   - Set environment variables OR pass keys as arguments:
#     OPENAI_API_KEY, GOOGLE_API_KEY, ANTHROPIC_API_KEY
#

set -e

MSGMODEL_DIR="$HOME/source/msgmodel"
cd "$MSGMODEL_DIR"

echo "========================================="
echo "  msgmodel Smoke Test"
echo "========================================="
echo ""

# Show version
echo "Version:"
python -m msgmodel --version
echo ""

# Run full test suite
echo "-----------------------------------------"
echo "Running full test suite..."
echo "-----------------------------------------"
python -m pytest tests/ -q
echo -e "✅ Test Suite: OK\n"

# Test OpenAI
echo "-----------------------------------------"
echo "Testing OpenAI (provider: o)..."
echo "-----------------------------------------"
if [ -n "$OPENAI_API_KEY" ]; then
    python -m msgmodel -p o "Say 'OpenAI test passed' in exactly 4 words" && echo -e "\n✅ OpenAI: OK\n" || echo -e "\n❌ OpenAI: FAILED\n"
else
    echo "⚠️  Skipped: OPENAI_API_KEY not set"
fi
echo ""

# Test Gemini
echo "-----------------------------------------"
echo "Testing Gemini (provider: g)..."
echo "-----------------------------------------"
if [ -n "$GOOGLE_API_KEY" ]; then
    python -m msgmodel -p g "Say 'Gemini test passed' in exactly 4 words" && echo -e "\n✅ Gemini: OK\n" || echo -e "\n❌ Gemini: FAILED\n"
else
    echo "⚠️  Skipped: GOOGLE_API_KEY not set"
fi
echo ""

# Test Anthropic/Claude
echo "-----------------------------------------"
echo "Testing Anthropic (provider: a)..."
echo "-----------------------------------------"
if [ -n "$ANTHROPIC_API_KEY" ]; then
    python -m msgmodel -p a "Say 'Anthropic test passed' in exactly 4 words" && echo -e "\n✅ Anthropic: OK\n" || echo -e "\n❌ Anthropic: FAILED\n"
else
    echo "⚠️  Skipped: ANTHROPIC_API_KEY not set"
fi
echo ""

# Test streaming (pick first available provider)
echo "-----------------------------------------"
echo "Testing streaming..."
echo "-----------------------------------------"
if [ -n "$OPENAI_API_KEY" ]; then
    echo "Streaming from OpenAI:"
    python -m msgmodel -p o "Count from 1 to 5, one number per line" --stream
    echo -e "\n✅ Streaming: OK\n"
elif [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "Streaming from Anthropic:"
    python -m msgmodel -p a "Count from 1 to 5, one number per line" --stream
    echo -e "\n✅ Streaming: OK\n"
elif [ -n "$GOOGLE_API_KEY" ]; then
    echo "Streaming from Gemini:"
    python -m msgmodel -p g "Count from 1 to 5, one number per line" --stream
    echo -e "\n✅ Streaming: OK\n"
else
    echo "⚠️  Skipped: No API keys available"
fi

echo ""
echo "========================================="
echo "  Smoke Test Complete"
echo "========================================="
