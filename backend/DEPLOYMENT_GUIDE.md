# TradingAgents API Deployment Guide

## 🍎 App Store Deployment Strategy

This guide provides deployment instructions for publishing the TradingAgents iOS app to the Apple App Store.

### **Phase 1: Railway Deployment (App Store Submission)**

Railway provides the quickest path to production with automatic HTTPS - perfect for App Store submission.

## 🚀 Quick Start (5 minutes)

### **Step 1: Prepare Repository**

1. **Ensure all files are committed to GitHub:**
   ```bash
   git add .
   git commit -m "Prepare for Railway deployment"
   git push origin main
   ```

### **Step 2: Deploy to Railway**

1. **Go to [Railway.app](https://railway.app)**
2. **Sign up/Login** with your GitHub account
3. **Click "New Project"** → **"Deploy from GitHub repo"**
4. **Select your TradingAgents repository**
5. **Railway will auto-detect** the Python app and start building

### **Step 3: Configure Environment Variables**

In the Railway dashboard:

1. **Go to your project** → **Variables tab**
2. **Add these required variables:**
   ```
   OPENAI_API_KEY=your_actual_openai_key
   FINNHUB_API_KEY=your_actual_finnhub_key
   SERPAPI_API_KEY=your_actual_serpapi_key (optional but recommended)
   ```

3. **Optional variables for better performance:**
   ```
   DEEP_THINK_MODEL=gpt-4o
   QUICK_THINK_MODEL=gpt-4o-mini
   MAX_DEBATE_ROUNDS=3
   MAX_RISK_DISCUSS_ROUNDS=2
   ```

### **Step 4: Get Your Production URL**

1. **In Railway dashboard**, go to **Settings** → **Domains**
2. **Copy the railway.app URL** (e.g., `https://tradingagents-production.up.railway.app`)
3. **Optional:** Add a custom domain later

### **Step 5: Test Your Deployed API**

```bash
# Test the health endpoint
curl https://your-app.railway.app/health

# Test analysis endpoint
curl -X POST https://your-app.railway.app/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL"}'
```

## 📱 Update iOS App for Production

### **Step 1: Update API Configuration**

In your iOS project, update the `TradingAgentsService.swift`:

```swift
// Replace localhost URL with your Railway URL
private let baseURL = "https://your-app.railway.app"
```

### **Step 2: Configure for App Store**

1. **Update app version** in Xcode
2. **Test with production API** thoroughly
3. **Ensure all network calls use HTTPS**
4. **Update app privacy settings** if needed

## 🔒 Production Security Setup

### **Step 1: Configure CORS (Optional)**

To restrict API access to your app only:

1. **In Railway dashboard**, add variable:
   ```
   CORS_ORIGINS=https://your-custom-domain.com
   ```

### **Step 2: Monitor Usage**

1. **Check Railway dashboard** for usage metrics
2. **Monitor API response times**
3. **Set up alerts** for downtime

## 📊 Performance Optimization

### **Railway Configuration**

Railway automatically handles:
- ✅ **HTTPS/SSL certificates**
- ✅ **Auto-scaling based on usage**
- ✅ **Health checks and restarts**
- ✅ **CDN for faster global access**

### **Expected Performance**

- **Startup time:** ~30-60 seconds (cold start)
- **Analysis time:** 2-8 minutes per request
- **Concurrent users:** Railway free tier handles 10-20 concurrent users

## 🔧 Troubleshooting

### **Common Issues**

1. **Build failures:**
   - Check requirements.txt is valid
   - Ensure Python version compatibility

2. **Runtime errors:**
   - Verify all environment variables are set
   - Check Railway logs for detailed errors

3. **API timeouts:**
   - Railway has 100-second request timeout
   - Consider implementing streaming for long analyses

### **Monitoring Commands**

```bash
# Check Railway logs
railway logs

# Check service status
railway status

# Restart service
railway redeploy
```

## 📈 Scaling for App Store Success

### **Free Tier Limits**
- **Execution time:** 500 hours/month
- **Memory:** 512MB
- **Storage:** 1GB

### **When to Upgrade**
- **> 100 daily users:** Consider Pro plan ($5/month)
- **> 1000 daily users:** Plan migration to VPS

### **Migration Path**
When your app grows, migrate to:
1. **Railway Pro** (simple upgrade)
2. **Docker + VPS** (full control)
3. **AWS/GCP** (enterprise scale)

## ✅ Pre-App Store Checklist

- [ ] API deployed and accessible via HTTPS
- [ ] All endpoints return expected responses
- [ ] iOS app updated with production URL
- [ ] App tested with production API
- [ ] Error handling tested (network issues, API timeouts)
- [ ] App Store privacy policy updated
- [ ] Terms of service mention third-party APIs

## 🆘 Support

- **Railway Documentation:** [docs.railway.app](https://docs.railway.app)
- **Railway Discord:** Join for community support
- **GitHub Issues:** Report bugs in your repository

---

**🎉 Congratulations!** Your TradingAgents API is now ready for App Store submission with a production-grade backend hosted on Railway. 