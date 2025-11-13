# 📚 Badass Dropship Bot - Usage Guide

## 🚀 Quick Start

### 1. Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python main.py init

# Add your Anthropic API key to .env
# Edit .env and add: ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 2. Your First Product Discovery

```bash
# Discover winning products from AliExpress
python main.py scout --source aliexpress --limit 20 --min-score 75

# View discovered products
python main.py list
```

### 3. Generate AI Content

```bash
# Generate optimized content for product ID 1
python main.py generate 1

# Generate 3 variations for A/B testing
python main.py generate 1 --variations 3
```

### 4. Publish to Platforms

```bash
# Publish to TikTok Shop
python main.py publish 1 --platforms tiktok

# Publish to multiple platforms
python main.py publish 1 --platforms tiktok --platforms shopify
```

### 5. Full Autopilot Mode 🤖

```bash
# Complete automation: discover → generate → publish
python main.py autopilot --sources all --platforms tiktok --limit 10 --min-score 80
```

---

## 🔧 Advanced Usage

### Multi-Source Discovery

```bash
# Discover from all sources
python main.py scout --source all --category electronics --limit 50

# Discover only from CJ Dropshipping
python main.py scout --source cj --category fashion --min-score 70

# Discover from TikTok trending
python main.py scout --source tiktok --limit 30
```

### Content Generation Strategies

```bash
# Standard generation
python main.py generate 1

# Generate multiple variations for testing
python main.py generate 1 --variations 5

# The AI will create:
# - SEO-optimized titles
# - Compelling descriptions
# - Benefit-focused bullet points
# - Keyword-rich content
```

### Publishing Strategies

```bash
# Test on one platform first
python main.py publish 1 --platforms tiktok

# After validation, expand to more platforms
python main.py publish 1 --platforms tiktok --platforms shopify --platforms custom
```

### Autopilot Configurations

#### Conservative (High-Quality Only)
```bash
python main.py autopilot \
  --sources aliexpress \
  --platforms tiktok \
  --min-score 85 \
  --limit 5 \
  --category electronics
```

#### Aggressive (Volume)
```bash
python main.py autopilot \
  --sources all \
  --platforms tiktok \
  --platforms shopify \
  --min-score 70 \
  --limit 50
```

#### Niche Focus
```bash
python main.py autopilot \
  --sources all \
  --platforms tiktok \
  --min-score 75 \
  --limit 20 \
  --category beauty
```

---

## 🌐 API Server

### Start the Server

```bash
# Start with auto-reload (development)
python main.py serve

# Production mode
python main.py serve --host 0.0.0.0 --port 8000 --reload false
```

### API Endpoints

#### Discover Products
```bash
curl -X POST "http://localhost:8000/api/v1/products/scout" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "aliexpress",
    "category": "electronics",
    "limit": 20,
    "min_score": 75
  }'
```

#### Generate Content
```bash
curl -X POST "http://localhost:8000/api/v1/products/generate/1?variations=1"
```

#### Publish Product
```bash
curl -X POST "http://localhost:8000/api/v1/products/publish" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "platforms": ["tiktok"]
  }'
```

#### Run Autopilot
```bash
curl -X POST "http://localhost:8000/api/v1/autopilot/run" \
  -H "Content-Type: application/json" \
  -d '{
    "sources": ["all"],
    "platforms": ["tiktok"],
    "min_score": 75,
    "limit": 10
  }'
```

#### Get Analytics
```bash
# Dashboard stats
curl "http://localhost:8000/api/v1/analytics/dashboard"

# Product performance
curl "http://localhost:8000/api/v1/analytics/products/1?days=30"

# Platform performance
curl "http://localhost:8000/api/v1/analytics/platforms/tiktok?days=30"

# Trending products
curl "http://localhost:8000/api/v1/analytics/trending?limit=10"
```

---

## 📊 Analytics & Monitoring

### View Dashboard Stats

```bash
python main.py stats
```

This shows:
- Total products discovered
- Products published
- Revenue metrics (last 30 days)
- Platform breakdown
- Performance metrics

### List Products

```bash
# All products
python main.py list

# Filter by status
python main.py list --status discovered
python main.py list --status generated
python main.py list --status published

# Show more results
python main.py list --limit 50
```

---

## 🔔 Slack Notifications

The bot automatically sends Slack notifications for:
- **High-value products discovered** (score > 80)
- **Products published** (with success/failure status)
- **Daily summaries** (when using autopilot)
- **Errors and alerts**

To enable, add your Slack webhook URL to `.env`:
```
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

---

## 🎯 Best Practices

### 1. Product Discovery
- **Start with high scores**: Use `--min-score 80` for quality
- **Test categories**: Different categories have different competition
- **Multi-source**: Combine AliExpress + CJ for variety

### 2. Content Generation
- **Generate variations**: Use `--variations 3` for A/B testing
- **Review before publishing**: Check AI content quality
- **Customize prompts**: Edit `config.py` CONTENT_PROMPTS for your style

### 3. Publishing
- **Start small**: Test on one platform first
- **Monitor performance**: Check analytics daily
- **Iterate**: Use data to improve product selection

### 4. Automation
- **Schedule autopilot**: Use cron to run autopilot daily
- **Set appropriate limits**: Don't overwhelm platforms
- **Quality over quantity**: High min_score = better ROI

---

## 🔄 Automation Strategies

### Daily Discovery
```bash
# Add to crontab: Run every day at 2 AM
0 2 * * * cd /path/to/badassdropshipbot && python main.py scout --source all --min-score 80 --limit 100
```

### Weekly Autopilot
```bash
# Run full autopilot every Sunday
0 3 * * 0 cd /path/to/badassdropshipbot && python main.py autopilot --sources all --platforms tiktok --min-score 75 --limit 20
```

### Hourly Trending Check
```bash
# Check TikTok trending every hour
0 * * * * cd /path/to/badassdropshipbot && python main.py scout --source tiktok --limit 10 --min-score 85
```

---

## 🐛 Troubleshooting

### No products discovered
- Check API keys in `.env`
- Lower `--min-score` threshold
- Try different categories
- Check logs in `logs/` directory

### Content generation fails
- Verify `ANTHROPIC_API_KEY` is set
- Check Claude API credits
- Review error logs

### Publishing fails
- Verify platform API credentials
- Check product data completeness
- Review platform-specific requirements

### API server issues
- Check port 8000 is available
- Review FastAPI logs
- Verify database is initialized

---

## 💡 Pro Tips

1. **Start with discovery**: Build a database of products before autopilot
2. **Use analytics**: Track what works and double down
3. **A/B test everything**: Generate variations and measure
4. **Monitor competition**: Run competitor analysis regularly
5. **Optimize for SEO**: Use the keyword suggestions from SE Ranking
6. **Leverage Slack**: Set up notifications to stay informed
7. **Batch operations**: Use autopilot during off-peak hours
8. **Quality control**: Manually review high-score products before publishing

---

## 📈 Scaling Up

### High-Volume Operation
```bash
# Process 100 products/day
python main.py autopilot \
  --sources all \
  --platforms tiktok shopify \
  --min-score 70 \
  --limit 100
```

### Multi-Platform Strategy
```bash
# Publish to all platforms
python main.py autopilot \
  --sources aliexpress cj \
  --platforms tiktok shopify custom \
  --min-score 80 \
  --limit 50
```

### Niche Domination
```bash
# Focus on one category, maximize coverage
python main.py autopilot \
  --sources all \
  --platforms all \
  --min-score 75 \
  --limit 200 \
  --category electronics
```

---

## 🆘 Support

For issues:
1. Check logs in `logs/` directory
2. Review this guide
3. Check API credentials in `.env`
4. Open an issue on GitHub

---

**Happy dropshipping! 🚀💰**
