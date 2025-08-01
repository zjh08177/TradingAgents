"""Report validation framework to ensure quality and data backing"""
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class ReportValidator:
    """Validates analyst reports have real data and proper structure"""
    
    MIN_REPORT_LENGTH = 100
    REQUIRED_SECTIONS = {
        "market": ["price", "technical", "trend", "indicator", "analysis"],
        "news": ["news", "headline", "sentiment", "impact", "market"],
        "social": ["sentiment", "reddit", "social", "discussion", "trend"],
        "fundamentals": ["revenue", "earnings", "financial", "ratio", "balance", "income"]
    }
    
    DATA_CITATION_PHRASES = [
        "based on", "data shows", "according to", "source:", 
        "from the", "tool returned", "analysis of", "indicates",
        "measured at", "reported", "actual", "real"
    ]
    
    @staticmethod
    def validate_report(analyst_type: str, report: str, has_tool_data: bool) -> Dict[str, any]:
        """Validate report quality and data backing
        
        Returns dict with:
        - valid: bool - whether report passes validation
        - issues: List[str] - list of validation issues
        - score: float - quality score 0-1
        """
        issues = []
        
        # NEW: Reject reports without tool data
        if not has_tool_data:
            logger.error(f"❌ {analyst_type}: Report has no tool data backing!")
            issues.append("NO_TOOL_DATA: Report generated without calling any tools")
            return {"valid": False, "issues": issues, "score": 0.0}
            
        if not report or len(report.strip()) < ReportValidator.MIN_REPORT_LENGTH:
            logger.warning(f"⚠️ {analyst_type}: Report too short ({len(report)} chars)")
            issues.append(f"TOO_SHORT: Report only {len(report)} chars (min: {ReportValidator.MIN_REPORT_LENGTH})")
        
        # Check for required sections based on analyst type
        required = ReportValidator.REQUIRED_SECTIONS.get(analyst_type, [])
        report_lower = report.lower()
        missing = []
        
        for section in required:
            if section not in report_lower:
                missing.append(section)
        
        if missing:
            logger.warning(f"⚠️ {analyst_type}: Missing sections: {missing}")
            issues.append(f"MISSING_SECTIONS: {', '.join(missing)}")
            
        # Check for data citations
        has_citations = any(
            phrase in report_lower 
            for phrase in ReportValidator.DATA_CITATION_PHRASES
        )
        
        if not has_citations:
            logger.warning(f"⚠️ {analyst_type}: No data citations found")
            issues.append("NO_CITATIONS: Report doesn't reference tool data")
        
        # Check for specific data patterns
        has_numbers = any(char.isdigit() for char in report)
        if not has_numbers:
            logger.warning(f"⚠️ {analyst_type}: No numerical data in report")
            issues.append("NO_NUMBERS: Report contains no numerical data")
        
        # Calculate quality score
        score = 1.0
        score -= 0.3 if "NO_TOOL_DATA" in str(issues) else 0
        score -= 0.2 if "TOO_SHORT" in str(issues) else 0
        score -= 0.2 if "MISSING_SECTIONS" in str(issues) else 0
        score -= 0.2 if "NO_CITATIONS" in str(issues) else 0
        score -= 0.1 if "NO_NUMBERS" in str(issues) else 0
        score = max(0.0, score)
        
        valid = len(issues) == 0
        
        if valid:
            logger.info(f"✅ {analyst_type}: Report validation PASSED (score: {score:.2f})")
        else:
            logger.warning(f"⚠️ {analyst_type}: Report validation FAILED - {len(issues)} issues")
            
        return {
            "valid": valid,
            "issues": issues,
            "score": score
        }
    
    @classmethod
    def get_validation_summary(cls, validations: Dict[str, Dict]) -> str:
        """Generate a summary of all validation results"""
        lines = ["## Report Validation Summary\n"]
        
        total_valid = sum(1 for v in validations.values() if v["valid"])
        total_reports = len(validations)
        
        lines.append(f"**Overall**: {total_valid}/{total_reports} reports valid\n")
        
        for analyst, result in validations.items():
            status = "✅ VALID" if result["valid"] else "❌ INVALID"
            score = result["score"]
            lines.append(f"\n### {analyst.title()} Analyst")
            lines.append(f"- Status: {status}")
            lines.append(f"- Score: {score:.2f}/1.00")
            
            if result["issues"]:
                lines.append("- Issues:")
                for issue in result["issues"]:
                    lines.append(f"  - {issue}")
        
        return "\n".join(lines)