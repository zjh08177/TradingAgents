import '../models/agent_states.dart';
import 'langchain_service.dart';

// Individual Trading Agents - Simple LLM Calls
// Each agent performs a single LLM call and updates the state

class TradingAgents {
  final LangChainService _llmService;

  TradingAgents(this._llmService);

  // ==================== ANALYST AGENTS ====================

  Future<AgentState> marketAnalyst(AgentState state) async {
    const prompt = '''
You are a Market Analyst. Analyze the technical aspects of \${company} on \${date}.

Provide a concise market analysis covering:
- Current stock price trends
- Technical indicators 
- Volume analysis
- Support/resistance levels
- Market sentiment

Company: \${company}
Date: \${date}

Keep response under 200 words.
''';

    final analysis = await _llmService.generateTradingInsight(
      prompt
          .replaceAll('\${company}', state.companyOfInterest)
          .replaceAll('\${date}', state.tradeDate),
    );

    return state.copyWith(marketReport: analysis);
  }

  Future<AgentState> socialMediaAnalyst(AgentState state) async {
    const prompt = '''
You are a Social Media Analyst. Analyze social sentiment for \${company} on \${date}.

Provide analysis covering:
- Reddit sentiment trends
- Twitter/X discussions
- Social media buzz
- Retail investor sentiment
- Community opinions

Company: \${company}
Date: \${date}

Keep response under 200 words.
''';

    final analysis = await _llmService.generateTradingInsight(
      prompt
          .replaceAll('\${company}', state.companyOfInterest)
          .replaceAll('\${date}', state.tradeDate),
    );

    return state.copyWith(sentimentReport: analysis);
  }

  Future<AgentState> newsAnalyst(AgentState state) async {
    const prompt = '''
You are a News Analyst. Analyze recent news impact for \${company} on \${date}.

Provide analysis covering:
- Recent company news
- Industry developments
- Regulatory updates
- Market-moving events
- News sentiment impact

Company: \${company}
Date: \${date}

Keep response under 200 words.
''';

    final analysis = await _llmService.generateTradingInsight(
      prompt
          .replaceAll('\${company}', state.companyOfInterest)
          .replaceAll('\${date}', state.tradeDate),
    );

    return state.copyWith(newsReport: analysis);
  }

  Future<AgentState> fundamentalsAnalyst(AgentState state) async {
    const prompt = '''
You are a Fundamentals Analyst. Analyze financial fundamentals for \${company} on \${date}.

Provide analysis covering:
- Financial statements analysis
- Revenue and earnings trends
- Balance sheet strength
- Cash flow analysis
- Valuation metrics

Company: \${company}
Date: \${date}

Keep response under 200 words.
''';

    final analysis = await _llmService.generateTradingInsight(
      prompt
          .replaceAll('\${company}', state.companyOfInterest)
          .replaceAll('\${date}', state.tradeDate),
    );

    return state.copyWith(fundamentalsReport: analysis);
  }

  // ==================== RESEARCH TEAM ====================

  Future<AgentState> bullResearcher(AgentState state) async {
    const prompt = '''
You are a Bull Researcher. Make a bullish case for \${company} based on the analysis.

Market Analysis: \${market}
News Analysis: \${news}  
Social Sentiment: \${social}
Fundamentals: \${fundamentals}

Previous Bear Argument: \${bearHistory}

Provide strong bullish arguments focusing on:
- Growth opportunities
- Positive catalysts
- Market advantages
- Financial strengths

Keep response under 150 words.
''';

    final analysis = await _llmService.generateTradingInsight(
      prompt
          .replaceAll('\${company}', state.companyOfInterest)
          .replaceAll('\${market}', state.marketReport)
          .replaceAll('\${news}', state.newsReport)
          .replaceAll('\${social}', state.sentimentReport)
          .replaceAll('\${fundamentals}', state.fundamentalsReport)
          .replaceAll('\${bearHistory}', state.investmentDebateState.bearHistory),
    );

    final newDebateState = state.investmentDebateState.copyWith(
      bullHistory: '${state.investmentDebateState.bullHistory}\n$analysis',
      currentResponse: analysis,
      count: state.investmentDebateState.count + 1,
    );

    return state.copyWith(investmentDebateState: newDebateState);
  }

  Future<AgentState> bearResearcher(AgentState state) async {
    const prompt = '''
You are a Bear Researcher. Make a bearish case for \${company} based on the analysis.

Market Analysis: \${market}
News Analysis: \${news}
Social Sentiment: \${social}
Fundamentals: \${fundamentals}

Previous Bull Argument: \${bullHistory}

Provide strong bearish arguments focusing on:
- Risk factors
- Market headwinds
- Competitive threats
- Financial concerns

Keep response under 150 words.
''';

    final analysis = await _llmService.generateTradingInsight(
      prompt
          .replaceAll('\${company}', state.companyOfInterest)
          .replaceAll('\${market}', state.marketReport)
          .replaceAll('\${news}', state.newsReport)
          .replaceAll('\${social}', state.sentimentReport)
          .replaceAll('\${fundamentals}', state.fundamentalsReport)
          .replaceAll('\${bullHistory}', state.investmentDebateState.bullHistory),
    );

    final newDebateState = state.investmentDebateState.copyWith(
      bearHistory: '${state.investmentDebateState.bearHistory}\n$analysis',
      currentResponse: analysis,
      count: state.investmentDebateState.count + 1,
    );

    return state.copyWith(investmentDebateState: newDebateState);
  }

  Future<AgentState> researchManager(AgentState state) async {
    const prompt = '''
You are a Research Manager. Judge the bull vs bear debate and make an investment decision.

Bull Arguments: \${bullHistory}

Bear Arguments: \${bearHistory}

Based on the debate, provide:
- Summary of key points from both sides
- Your investment decision (BUY/SELL/HOLD)
- Reasoning for the decision
- Confidence level (1-10)

Keep response under 200 words.
''';

    final decision = await _llmService.generateTradingInsight(
      prompt
          .replaceAll('\${bullHistory}', state.investmentDebateState.bullHistory)
          .replaceAll('\${bearHistory}', state.investmentDebateState.bearHistory),
    );

    final newDebateState = state.investmentDebateState.copyWith(
      judgeDecision: decision,
    );

    return state.copyWith(
      investmentPlan: decision,
      investmentDebateState: newDebateState,
    );
  }

  // ==================== TRADER ====================

  Future<AgentState> trader(AgentState state) async {
    const prompt = '''
You are a Trader. Create a specific trading plan based on the investment decision.

Investment Decision: \${investmentPlan}

Provide a specific trading plan including:
- Exact action (BUY/SELL/HOLD)
- Position sizing recommendation
- Entry/exit strategy
- Stop loss levels
- Target prices

Keep response under 150 words.
''';

    final tradingPlan = await _llmService.generateTradingInsight(
      prompt.replaceAll('\${investmentPlan}', state.investmentPlan),
    );

    return state.copyWith(traderInvestmentPlan: tradingPlan);
  }

  // ==================== RISK MANAGEMENT TEAM ====================

  Future<AgentState> aggressiveRiskAnalyst(AgentState state) async {
    const prompt = '''
You are an Aggressive Risk Analyst. Evaluate the trading plan from a high-risk, high-reward perspective.

Trading Plan: \${tradingPlan}

Provide analysis focusing on:
- Aggressive position sizing
- Maximum profit potential  
- Leveraged opportunities
- Growth-focused approach

Keep response under 100 words.
''';

    final analysis = await _llmService.generateTradingInsight(
      prompt.replaceAll('\${tradingPlan}', state.traderInvestmentPlan),
    );

    final newRiskState = state.riskDebateState.copyWith(
      riskyHistory: '${state.riskDebateState.riskyHistory}\n$analysis',
      currentRiskyResponse: analysis,
      count: state.riskDebateState.count + 1,
    );

    return state.copyWith(riskDebateState: newRiskState);
  }

  Future<AgentState> conservativeRiskAnalyst(AgentState state) async {
    const prompt = '''
You are a Conservative Risk Analyst. Evaluate the trading plan from a risk-averse perspective.

Trading Plan: \${tradingPlan}

Provide analysis focusing on:
- Capital preservation
- Risk mitigation strategies
- Conservative position sizing
- Downside protection

Keep response under 100 words.
''';

    final analysis = await _llmService.generateTradingInsight(
      prompt.replaceAll('\${tradingPlan}', state.traderInvestmentPlan),
    );

    final newRiskState = state.riskDebateState.copyWith(
      safeHistory: '${state.riskDebateState.safeHistory}\n$analysis',
      currentSafeResponse: analysis,
      count: state.riskDebateState.count + 1,
    );

    return state.copyWith(riskDebateState: newRiskState);
  }

  Future<AgentState> neutralRiskAnalyst(AgentState state) async {
    const prompt = '''
You are a Neutral Risk Analyst. Evaluate the trading plan from a balanced perspective.

Trading Plan: \${tradingPlan}

Provide analysis focusing on:
- Balanced risk-reward
- Moderate position sizing
- Diversification considerations
- Neutral market approach

Keep response under 100 words.
''';

    final analysis = await _llmService.generateTradingInsight(
      prompt.replaceAll('\${tradingPlan}', state.traderInvestmentPlan),
    );

    final newRiskState = state.riskDebateState.copyWith(
      neutralHistory: '${state.riskDebateState.neutralHistory}\n$analysis',
      currentNeutralResponse: analysis,
      count: state.riskDebateState.count + 1,
    );

    return state.copyWith(riskDebateState: newRiskState);
  }

  Future<AgentState> riskManager(AgentState state) async {
    const prompt = '''
You are the Risk Manager. Make the final trading decision based on all risk analyses.

Aggressive Analysis: \${aggressiveAnalysis}

Conservative Analysis: \${conservativeAnalysis}

Neutral Analysis: \${neutralAnalysis}

Trading Plan: \${tradingPlan}

Provide final decision including:
- Final action (BUY/SELL/HOLD)
- Final position size
- Risk management strategy
- Rationale for decision

Keep response under 200 words.
''';

    final finalDecision = await _llmService.generateTradingInsight(
      prompt
          .replaceAll('\${aggressiveAnalysis}', state.riskDebateState.riskyHistory)
          .replaceAll('\${conservativeAnalysis}', state.riskDebateState.safeHistory)
          .replaceAll('\${neutralAnalysis}', state.riskDebateState.neutralHistory)
          .replaceAll('\${tradingPlan}', state.traderInvestmentPlan),
    );

    final newRiskState = state.riskDebateState.copyWith(
      judgeDecision: finalDecision,
    );

    return state.copyWith(
      finalTradeDecision: finalDecision,
      riskDebateState: newRiskState,
    );
  }
} 