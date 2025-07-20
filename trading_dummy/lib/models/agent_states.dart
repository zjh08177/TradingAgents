// Agent States for Trading Graph
// Mirrors the Python agent_states.py structure

class AgentState {
  String companyOfInterest;
  String tradeDate;
  
  // Analyst Reports
  String marketReport;
  String sentimentReport;
  String newsReport;
  String fundamentalsReport;
  
  // Investment Flow
  String investmentPlan;
  String traderInvestmentPlan;
  String finalTradeDecision;
  
  // Debate States
  InvestDebateState investmentDebateState;
  RiskDebateState riskDebateState;

  AgentState({
    required this.companyOfInterest,
    required this.tradeDate,
    this.marketReport = '',
    this.sentimentReport = '',
    this.newsReport = '',
    this.fundamentalsReport = '',
    this.investmentPlan = '',
    this.traderInvestmentPlan = '',
    this.finalTradeDecision = '',
    InvestDebateState? investmentDebateState,
    RiskDebateState? riskDebateState,
  }) : investmentDebateState = investmentDebateState ?? InvestDebateState(),
       riskDebateState = riskDebateState ?? RiskDebateState();

  AgentState copyWith({
    String? companyOfInterest,
    String? tradeDate,
    String? marketReport,
    String? sentimentReport,
    String? newsReport,
    String? fundamentalsReport,
    String? investmentPlan,
    String? traderInvestmentPlan,
    String? finalTradeDecision,
    InvestDebateState? investmentDebateState,
    RiskDebateState? riskDebateState,
  }) {
    return AgentState(
      companyOfInterest: companyOfInterest ?? this.companyOfInterest,
      tradeDate: tradeDate ?? this.tradeDate,
      marketReport: marketReport ?? this.marketReport,
      sentimentReport: sentimentReport ?? this.sentimentReport,
      newsReport: newsReport ?? this.newsReport,
      fundamentalsReport: fundamentalsReport ?? this.fundamentalsReport,
      investmentPlan: investmentPlan ?? this.investmentPlan,
      traderInvestmentPlan: traderInvestmentPlan ?? this.traderInvestmentPlan,
      finalTradeDecision: finalTradeDecision ?? this.finalTradeDecision,
      investmentDebateState: investmentDebateState ?? this.investmentDebateState,
      riskDebateState: riskDebateState ?? this.riskDebateState,
    );
  }
}

class InvestDebateState {
  String bullHistory;
  String bearHistory;
  String currentResponse;
  String judgeDecision;
  int count;

  InvestDebateState({
    this.bullHistory = '',
    this.bearHistory = '',
    this.currentResponse = '',
    this.judgeDecision = '',
    this.count = 0,
  });

  InvestDebateState copyWith({
    String? bullHistory,
    String? bearHistory,
    String? currentResponse,
    String? judgeDecision,
    int? count,
  }) {
    return InvestDebateState(
      bullHistory: bullHistory ?? this.bullHistory,
      bearHistory: bearHistory ?? this.bearHistory,
      currentResponse: currentResponse ?? this.currentResponse,
      judgeDecision: judgeDecision ?? this.judgeDecision,
      count: count ?? this.count,
    );
  }
}

class RiskDebateState {
  String riskyHistory;
  String safeHistory;
  String neutralHistory;
  String currentRiskyResponse;
  String currentSafeResponse;
  String currentNeutralResponse;
  String judgeDecision;
  int count;

  RiskDebateState({
    this.riskyHistory = '',
    this.safeHistory = '',
    this.neutralHistory = '',
    this.currentRiskyResponse = '',
    this.currentSafeResponse = '',
    this.currentNeutralResponse = '',
    this.judgeDecision = '',
    this.count = 0,
  });

  RiskDebateState copyWith({
    String? riskyHistory,
    String? safeHistory,
    String? neutralHistory,
    String? currentRiskyResponse,
    String? currentSafeResponse,
    String? currentNeutralResponse,
    String? judgeDecision,
    int? count,
  }) {
    return RiskDebateState(
      riskyHistory: riskyHistory ?? this.riskyHistory,
      safeHistory: safeHistory ?? this.safeHistory,
      neutralHistory: neutralHistory ?? this.neutralHistory,
      currentRiskyResponse: currentRiskyResponse ?? this.currentRiskyResponse,
      currentSafeResponse: currentSafeResponse ?? this.currentSafeResponse,
      currentNeutralResponse: currentNeutralResponse ?? this.currentNeutralResponse,
      judgeDecision: judgeDecision ?? this.judgeDecision,
      count: count ?? this.count,
    );
  }
} 