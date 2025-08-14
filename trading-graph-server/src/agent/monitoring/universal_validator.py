#!/usr/bin/env python3
"""
Universal Validation Framework - Comprehensive validation for all system interactions
Designed to catch ANY tool call, parsing, agent response, or integration issues

This module provides bulletproof validation across all system layers to prevent
the types of silent failures that occurred with news and fundamentals analysts.
"""

import logging
import json
import time
import traceback
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)

class ValidationSeverity(Enum):
    """Validation issue severity levels"""
    INFO = "info"
    WARNING = "warning" 
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ValidationResult:
    """Standardized validation result structure"""
    is_valid: bool
    severity: ValidationSeverity
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    validation_type: str = ""
    context: Dict[str, Any] = field(default_factory=dict)

class APIResponseValidator:
    """Validates API responses for structure, quality, and completeness"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.APIResponseValidator")
        
    def validate_json_structure(self, response: Any, expected_schema: Dict[str, Any], 
                              context: str = "") -> ValidationResult:
        """Validate JSON response against expected schema"""
        try:
            if not isinstance(response, dict):
                return ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"API response is not a dict: {type(response)}",
                    validation_type="json_structure",
                    context={"context": context, "response_type": str(type(response))}
                )
            
            missing_keys = []
            invalid_types = []
            
            for key, expected_type in expected_schema.items():
                if key not in response:
                    missing_keys.append(key)
                elif expected_type is not None and not isinstance(response[key], expected_type):
                    invalid_types.append({
                        "key": key, 
                        "expected": expected_type.__name__, 
                        "actual": type(response[key]).__name__
                    })
            
            if missing_keys or invalid_types:
                return ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"Schema validation failed for {context}",
                    validation_type="json_structure",
                    details={
                        "missing_keys": missing_keys,
                        "invalid_types": invalid_types,
                        "expected_schema": expected_schema
                    },
                    context={"context": context}
                )
            
            self.logger.info(f"✅ JSON structure validation passed: {context}")
            return ValidationResult(
                is_valid=True,
                severity=ValidationSeverity.INFO,
                message=f"JSON structure validation passed: {context}",
                validation_type="json_structure",
                context={"context": context}
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.CRITICAL,
                message=f"JSON structure validation exception: {str(e)}",
                validation_type="json_structure",
                details={"exception": str(e), "traceback": traceback.format_exc()},
                context={"context": context}
            )
    
    def validate_data_completeness(self, response: Dict[str, Any], 
                                 required_fields: List[str], 
                                 context: str = "") -> ValidationResult:
        """Validate that all required data fields are present and non-empty"""
        try:
            missing_fields = []
            empty_fields = []
            
            for field in required_fields:
                if field not in response:
                    missing_fields.append(field)
                elif not response[field] or (isinstance(response[field], (list, dict)) and len(response[field]) == 0):
                    empty_fields.append(field)
            
            if missing_fields or empty_fields:
                severity = ValidationSeverity.ERROR if missing_fields else ValidationSeverity.WARNING
                return ValidationResult(
                    is_valid=False,
                    severity=severity,
                    message=f"Data completeness validation failed for {context}",
                    validation_type="data_completeness",
                    details={
                        "missing_fields": missing_fields,
                        "empty_fields": empty_fields,
                        "required_fields": required_fields,
                        "available_fields": list(response.keys())
                    },
                    context={"context": context}
                )
            
            self.logger.info(f"✅ Data completeness validation passed: {context}")
            return ValidationResult(
                is_valid=True,
                severity=ValidationSeverity.INFO,
                message=f"Data completeness validation passed: {context}",
                validation_type="data_completeness",
                context={"context": context}
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.CRITICAL,
                message=f"Data completeness validation exception: {str(e)}",
                validation_type="data_completeness",
                details={"exception": str(e), "traceback": traceback.format_exc()},
                context={"context": context}
            )
    
    def validate_data_quality(self, response: Dict[str, Any], 
                            quality_metrics: Dict[str, Callable], 
                            context: str = "") -> ValidationResult:
        """Validate data quality using custom metrics"""
        try:
            quality_issues = []
            
            for metric_name, metric_function in quality_metrics.items():
                try:
                    result = metric_function(response)
                    if not result:
                        quality_issues.append(metric_name)
                except Exception as e:
                    quality_issues.append(f"{metric_name} (exception: {str(e)})")
            
            if quality_issues:
                return ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    message=f"Data quality issues found for {context}",
                    validation_type="data_quality",
                    details={"failed_metrics": quality_issues},
                    context={"context": context}
                )
            
            self.logger.info(f"✅ Data quality validation passed: {context}")
            return ValidationResult(
                is_valid=True,
                severity=ValidationSeverity.INFO,
                message=f"Data quality validation passed: {context}",
                validation_type="data_quality",
                context={"context": context}
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.CRITICAL,
                message=f"Data quality validation exception: {str(e)}",
                validation_type="data_quality",
                details={"exception": str(e), "traceback": traceback.format_exc()},
                context={"context": context}
            )

class ToolCallValidator:
    """Validates tool calls and their responses"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ToolCallValidator")
        
    def validate_tool_call_start(self, tool_name: str, tool_args: Dict[str, Any], 
                               context: str = "") -> ValidationResult:
        """Validate tool call initiation"""
        try:
            issues = []
            
            # Check tool name is valid
            if not tool_name or not isinstance(tool_name, str):
                issues.append(f"Invalid tool name: {tool_name}")
            
            # Check arguments are valid
            if not isinstance(tool_args, dict):
                issues.append(f"Tool args must be dict, got: {type(tool_args)}")
            
            # Check for required common arguments
            if 'ticker' in tool_name.lower() or 'stock' in tool_name.lower():
                if 'ticker' not in tool_args and 'symbol' not in tool_args:
                    issues.append("Missing ticker/symbol for stock-related tool")
            
            if issues:
                return ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"Tool call validation failed: {tool_name}",
                    validation_type="tool_call_start",
                    details={"issues": issues, "tool_name": tool_name, "tool_args": tool_args},
                    context={"context": context}
                )
            
            self.logger.info(f"✅ Tool call start validation passed: {tool_name}")
            return ValidationResult(
                is_valid=True,
                severity=ValidationSeverity.INFO,
                message=f"Tool call start validation passed: {tool_name}",
                validation_type="tool_call_start",
                context={"context": context, "tool_name": tool_name}
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.CRITICAL,
                message=f"Tool call start validation exception: {str(e)}",
                validation_type="tool_call_start",
                details={"exception": str(e), "traceback": traceback.format_exc()},
                context={"context": context, "tool_name": tool_name}
            )
    
    def validate_tool_call_response(self, tool_name: str, response: Any, 
                                  execution_time: float, context: str = "") -> ValidationResult:
        """Validate tool call response"""
        try:
            issues = []
            
            # Check response exists
            if response is None:
                issues.append("Tool response is None")
            
            # Check execution time is reasonable
            if execution_time < 0:
                issues.append(f"Negative execution time: {execution_time}")
            elif execution_time > 300:  # 5 minutes
                issues.append(f"Excessive execution time: {execution_time}s")
            
            # Tool-specific validations
            if 'news' in tool_name.lower():
                if isinstance(response, str) and ('0 articles' in response or 'No news' in response):
                    issues.append("News tool returned no articles")
                elif isinstance(response, list) and len(response) == 0:
                    issues.append("News tool returned empty list")
            
            if 'fundamental' in tool_name.lower():
                if isinstance(response, str) and 'N/A' in response:
                    issues.append("Fundamentals tool returned N/A values")
            
            if issues:
                severity = ValidationSeverity.ERROR if any('None' in issue for issue in issues) else ValidationSeverity.WARNING
                return ValidationResult(
                    is_valid=False,
                    severity=severity,
                    message=f"Tool call response validation failed: {tool_name}",
                    validation_type="tool_call_response",
                    details={
                        "issues": issues, 
                        "tool_name": tool_name, 
                        "execution_time": execution_time,
                        "response_type": str(type(response)),
                        "response_sample": str(response)[:200] if response else None
                    },
                    context={"context": context}
                )
            
            self.logger.info(f"✅ Tool call response validation passed: {tool_name} ({execution_time:.2f}s)")
            return ValidationResult(
                is_valid=True,
                severity=ValidationSeverity.INFO,
                message=f"Tool call response validation passed: {tool_name}",
                validation_type="tool_call_response",
                context={"context": context, "tool_name": tool_name, "execution_time": execution_time}
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.CRITICAL,
                message=f"Tool call response validation exception: {str(e)}",
                validation_type="tool_call_response",
                details={"exception": str(e), "traceback": traceback.format_exc()},
                context={"context": context, "tool_name": tool_name}
            )

class AgentStateValidator:
    """Validates agent state transitions and data integrity"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.AgentStateValidator")
        
    def validate_state_transition(self, old_state: Dict[str, Any], 
                                new_state: Dict[str, Any], 
                                transition: str) -> ValidationResult:
        """Validate state transition integrity"""
        try:
            issues = []
            
            # Check that required fields are preserved
            required_fields = ['company_of_interest', 'trade_date']
            for field in required_fields:
                if field in old_state and field not in new_state:
                    issues.append(f"Required field '{field}' lost during transition")
                elif field in old_state and field in new_state and old_state[field] != new_state[field]:
                    issues.append(f"Required field '{field}' changed unexpectedly")
            
            # Check for data corruption
            if 'company_of_interest' in new_state:
                if not isinstance(new_state['company_of_interest'], str) or len(new_state['company_of_interest']) == 0:
                    issues.append("company_of_interest is invalid")
            
            # Check for unexpected data loss
            old_keys = set(old_state.keys())
            new_keys = set(new_state.keys())
            lost_keys = old_keys - new_keys
            
            # Filter out expected temporary keys
            critical_lost_keys = [k for k in lost_keys if not k.startswith('_temp') and not k.endswith('_cache')]
            if critical_lost_keys:
                issues.append(f"Critical state keys lost: {critical_lost_keys}")
            
            if issues:
                return ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"State transition validation failed: {transition}",
                    validation_type="state_transition",
                    details={
                        "issues": issues,
                        "transition": transition,
                        "lost_keys": list(lost_keys),
                        "old_state_keys": list(old_keys),
                        "new_state_keys": list(new_keys)
                    }
                )
            
            self.logger.info(f"✅ State transition validation passed: {transition}")
            return ValidationResult(
                is_valid=True,
                severity=ValidationSeverity.INFO,
                message=f"State transition validation passed: {transition}",
                validation_type="state_transition"
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.CRITICAL,
                message=f"State transition validation exception: {str(e)}",
                validation_type="state_transition",
                details={"exception": str(e), "traceback": traceback.format_exc()}
            )

class UniversalValidator:
    """Comprehensive validation system for all system interactions"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.UniversalValidator")
        self.api_validator = APIResponseValidator()
        self.tool_validator = ToolCallValidator()
        self.state_validator = AgentStateValidator()
        self.validation_history: List[ValidationResult] = []
        
    def validate_comprehensive(self, validation_type: str, **kwargs) -> ValidationResult:
        """Route to appropriate validator based on type"""
        try:
            if validation_type == "api_response":
                result = self.api_validator.validate_json_structure(
                    kwargs.get('response'), 
                    kwargs.get('expected_schema', {}),
                    kwargs.get('context', '')
                )
            elif validation_type == "tool_call_start":
                result = self.tool_validator.validate_tool_call_start(
                    kwargs.get('tool_name', ''),
                    kwargs.get('tool_args', {}),
                    kwargs.get('context', '')
                )
            elif validation_type == "tool_call_response":
                result = self.tool_validator.validate_tool_call_response(
                    kwargs.get('tool_name', ''),
                    kwargs.get('response'),
                    kwargs.get('execution_time', 0),
                    kwargs.get('context', '')
                )
            elif validation_type == "state_transition":
                result = self.state_validator.validate_state_transition(
                    kwargs.get('old_state', {}),
                    kwargs.get('new_state', {}),
                    kwargs.get('transition', '')
                )
            else:
                result = ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"Unknown validation type: {validation_type}",
                    validation_type="unknown"
                )
            
            # Store validation result
            self.validation_history.append(result)
            
            # Log result
            if result.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]:
                self.logger.error(f"🚨 VALIDATION FAILED: {result.message}")
                if result.details:
                    self.logger.error(f"🚨 VALIDATION DETAILS: {result.details}")
            elif result.severity == ValidationSeverity.WARNING:
                self.logger.warning(f"⚠️ VALIDATION WARNING: {result.message}")
            else:
                self.logger.info(f"✅ VALIDATION PASSED: {result.message}")
            
            return result
            
        except Exception as e:
            result = ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.CRITICAL,
                message=f"Universal validation exception: {str(e)}",
                validation_type=validation_type,
                details={"exception": str(e), "traceback": traceback.format_exc()}
            )
            self.validation_history.append(result)
            self.logger.critical(f"🚨 VALIDATION EXCEPTION: {result.message}")
            return result
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of all validations performed"""
        total = len(self.validation_history)
        if total == 0:
            return {"total": 0, "summary": "No validations performed"}
        
        passed = sum(1 for v in self.validation_history if v.is_valid)
        failed = total - passed
        
        by_severity = {}
        by_type = {}
        
        for validation in self.validation_history:
            # Count by severity
            severity = validation.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1
            
            # Count by type
            vtype = validation.validation_type
            by_type[vtype] = by_type.get(vtype, 0) + 1
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "success_rate": round(passed / total * 100, 2),
            "by_severity": by_severity,
            "by_type": by_type,
            "latest_failures": [
                {"message": v.message, "severity": v.severity.value, "type": v.validation_type}
                for v in self.validation_history[-10:] if not v.is_valid
            ]
        }

# Global validator instance
global_validator = UniversalValidator()

def validate(validation_type: str, **kwargs) -> ValidationResult:
    """Global validation function"""
    return global_validator.validate_comprehensive(validation_type, **kwargs)

def get_validation_summary() -> Dict[str, Any]:
    """Get global validation summary"""
    return global_validator.get_validation_summary()