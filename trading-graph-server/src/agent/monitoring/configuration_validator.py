#!/usr/bin/env python3
"""
Configuration Validator - Comprehensive startup and runtime configuration validation
Prevents configuration-related failures through early detection and validation
"""

import logging
import os
import requests
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from pathlib import Path
import asyncio
import time

logger = logging.getLogger(__name__)

@dataclass
class ConfigValidationResult:
    """Configuration validation result"""
    is_valid: bool
    component: str
    message: str
    severity: str  # info, warning, error, critical
    details: Dict[str, Any] = None

class ConfigurationValidator:
    """Validates system configuration at startup and runtime"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ConfigurationValidator")
        self.validation_results: List[ConfigValidationResult] = []
        
    def validate_environment_setup(self) -> List[ConfigValidationResult]:
        """Validate environment configuration and setup"""
        results = []
        
        # Check Python version
        import sys
        python_version = sys.version_info
        if python_version < (3, 8):
            results.append(ConfigValidationResult(
                is_valid=False,
                component="python_version",
                message=f"Python version {python_version.major}.{python_version.minor} is too old (minimum 3.8)",
                severity="critical"
            ))
        else:
            results.append(ConfigValidationResult(
                is_valid=True,
                component="python_version", 
                message=f"Python version {python_version.major}.{python_version.minor}.{python_version.micro} is compatible",
                severity="info"
            ))
        
        # Check .env file exists
        env_path = Path(".env")
        if not env_path.exists():
            results.append(ConfigValidationResult(
                is_valid=False,
                component="env_file",
                message=".env file not found",
                severity="critical"
            ))
        else:
            results.append(ConfigValidationResult(
                is_valid=True,
                component="env_file",
                message=".env file found",
                severity="info"
            ))
        
        # Check working directory
        cwd = Path.cwd()
        expected_files = ['requirements.txt', 'src', 'debug_local.sh']
        missing_files = [f for f in expected_files if not (cwd / f).exists()]
        
        if missing_files:
            results.append(ConfigValidationResult(
                is_valid=False,
                component="working_directory",
                message=f"Missing expected files: {missing_files}",
                severity="error",
                details={"missing_files": missing_files, "cwd": str(cwd)}
            ))
        else:
            results.append(ConfigValidationResult(
                is_valid=True,
                component="working_directory",
                message="Working directory structure is valid",
                severity="info"
            ))
        
        return results
    
    def validate_api_keys(self) -> List[ConfigValidationResult]:
        """Validate all required API keys are present and potentially valid"""
        results = []
        
        # Required API keys
        required_keys = {
            'OPENAI_API_KEY': {'required': True, 'test_endpoint': None},
            'FINNHUB_API_KEY': {'required': True, 'test_endpoint': 'https://finnhub.io/api/v1/quote?symbol=AAPL'},
            'LANGCHAIN_API_KEY': {'required': False, 'test_endpoint': None},
            'SERPER_API_KEY': {'required': True, 'test_endpoint': None},
            'REDDIT_CLIENT_ID': {'required': True, 'test_endpoint': None},
            'REDDIT_CLIENT_SECRET': {'required': True, 'test_endpoint': None},
        }
        
        for key_name, config in required_keys.items():
            key_value = os.getenv(key_name)
            
            if not key_value:
                severity = "critical" if config['required'] else "warning"
                results.append(ConfigValidationResult(
                    is_valid=False,
                    component=f"api_key_{key_name.lower()}",
                    message=f"API key {key_name} is missing",
                    severity=severity
                ))
            else:
                # Check key format
                is_valid_format = True
                format_issues = []
                
                if key_name == 'OPENAI_API_KEY':
                    if not key_value.startswith('sk-'):
                        is_valid_format = False
                        format_issues.append("OpenAI key should start with 'sk-'")
                elif key_name == 'FINNHUB_API_KEY':
                    if len(key_value) < 10:
                        is_valid_format = False
                        format_issues.append("Finnhub key seems too short")
                
                if not is_valid_format:
                    results.append(ConfigValidationResult(
                        is_valid=False,
                        component=f"api_key_{key_name.lower()}",
                        message=f"API key {key_name} format issues: {format_issues}",
                        severity="error",
                        details={"format_issues": format_issues}
                    ))
                else:
                    results.append(ConfigValidationResult(
                        is_valid=True,
                        component=f"api_key_{key_name.lower()}",
                        message=f"API key {key_name} is present and format looks valid",
                        severity="info"
                    ))
        
        return results
    
    def validate_api_connectivity(self) -> List[ConfigValidationResult]:
        """Test connectivity to critical external APIs"""
        results = []
        
        # Test OpenAI API
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            try:
                headers = {'Authorization': f'Bearer {openai_key}'}
                response = requests.get('https://api.openai.com/v1/models', headers=headers, timeout=10)
                
                if response.status_code == 200:
                    results.append(ConfigValidationResult(
                        is_valid=True,
                        component="openai_connectivity",
                        message="OpenAI API connectivity test passed",
                        severity="info"
                    ))
                elif response.status_code == 401:
                    results.append(ConfigValidationResult(
                        is_valid=False,
                        component="openai_connectivity",
                        message="OpenAI API key is invalid",
                        severity="critical"
                    ))
                else:
                    results.append(ConfigValidationResult(
                        is_valid=False,
                        component="openai_connectivity",
                        message=f"OpenAI API returned status {response.status_code}",
                        severity="error",
                        details={"status_code": response.status_code}
                    ))
            except Exception as e:
                results.append(ConfigValidationResult(
                    is_valid=False,
                    component="openai_connectivity",
                    message=f"OpenAI API connectivity test failed: {str(e)}",
                    severity="error",
                    details={"exception": str(e)}
                ))
        
        # Test Finnhub API
        finnhub_key = os.getenv('FINNHUB_API_KEY')
        if finnhub_key:
            try:
                response = requests.get(f'https://finnhub.io/api/v1/quote?symbol=AAPL&token={finnhub_key}', timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'c' in data:  # Current price should be present
                        results.append(ConfigValidationResult(
                            is_valid=True,
                            component="finnhub_connectivity",
                            message="Finnhub API connectivity test passed",
                            severity="info"
                        ))
                    else:
                        results.append(ConfigValidationResult(
                            is_valid=False,
                            component="finnhub_connectivity",
                            message="Finnhub API returned unexpected data format",
                            severity="warning",
                            details={"response_data": data}
                        ))
                elif response.status_code == 401:
                    results.append(ConfigValidationResult(
                        is_valid=False,
                        component="finnhub_connectivity",
                        message="Finnhub API key is invalid",
                        severity="critical"
                    ))
                else:
                    results.append(ConfigValidationResult(
                        is_valid=False,
                        component="finnhub_connectivity",
                        message=f"Finnhub API returned status {response.status_code}",
                        severity="error",
                        details={"status_code": response.status_code}
                    ))
            except Exception as e:
                results.append(ConfigValidationResult(
                    is_valid=False,
                    component="finnhub_connectivity",
                    message=f"Finnhub API connectivity test failed: {str(e)}",
                    severity="error",
                    details={"exception": str(e)}
                ))
        
        return results
    
    def validate_langsmith_setup(self) -> List[ConfigValidationResult]:
        """Validate LangSmith tracing configuration"""
        results = []
        
        langchain_key = os.getenv('LANGCHAIN_API_KEY')
        langchain_tracing = os.getenv('LANGCHAIN_TRACING_V2', '').lower()
        langchain_project = os.getenv('LANGCHAIN_PROJECT')
        
        if langchain_tracing == 'true':
            if not langchain_key:
                results.append(ConfigValidationResult(
                    is_valid=False,
                    component="langsmith_tracing",
                    message="LangSmith tracing enabled but API key missing",
                    severity="warning"
                ))
            elif not langchain_project:
                results.append(ConfigValidationResult(
                    is_valid=False,
                    component="langsmith_tracing",
                    message="LangSmith tracing enabled but project name missing",
                    severity="warning"
                ))
            else:
                results.append(ConfigValidationResult(
                    is_valid=True,
                    component="langsmith_tracing",
                    message="LangSmith tracing is properly configured",
                    severity="info"
                ))
        else:
            results.append(ConfigValidationResult(
                is_valid=True,
                component="langsmith_tracing",
                message="LangSmith tracing is disabled",
                severity="info"
            ))
        
        return results
    
    def validate_required_packages(self) -> List[ConfigValidationResult]:
        """Validate that all required Python packages are installed"""
        results = []
        
        required_packages = [
            'langchain',
            'langchain_openai', 
            'langgraph',
            'httpx',
            'aiohttp',
            'pandas',
            'numpy',
            'yfinance',
            'praw',  # Reddit
            'requests',
            'python-dotenv'
        ]
        
        missing_packages = []
        version_issues = []
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            results.append(ConfigValidationResult(
                is_valid=False,
                component="required_packages",
                message=f"Missing required packages: {missing_packages}",
                severity="critical",
                details={"missing_packages": missing_packages}
            ))
        else:
            results.append(ConfigValidationResult(
                is_valid=True,
                component="required_packages",
                message="All required packages are installed",
                severity="info"
            ))
        
        return results
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run all validation checks and return comprehensive results"""
        start_time = time.time()
        
        self.logger.info("🔍 Starting comprehensive configuration validation...")
        
        all_results = []
        
        # Run all validation categories
        validation_categories = [
            ("Environment Setup", self.validate_environment_setup),
            ("API Keys", self.validate_api_keys),
            ("API Connectivity", self.validate_api_connectivity),
            ("LangSmith Setup", self.validate_langsmith_setup),
            ("Required Packages", self.validate_required_packages)
        ]
        
        for category_name, validation_func in validation_categories:
            self.logger.info(f"🔍 Validating {category_name}...")
            try:
                category_results = validation_func()
                all_results.extend(category_results)
                
                # Log category summary
                passed = sum(1 for r in category_results if r.is_valid)
                total = len(category_results)
                self.logger.info(f"✅ {category_name}: {passed}/{total} checks passed")
                
            except Exception as e:
                self.logger.error(f"❌ {category_name} validation failed: {str(e)}")
                all_results.append(ConfigValidationResult(
                    is_valid=False,
                    component=f"{category_name.lower().replace(' ', '_')}_validation",
                    message=f"Validation category failed: {str(e)}",
                    severity="critical",
                    details={"exception": str(e)}
                ))
        
        # Store results
        self.validation_results = all_results
        
        # Generate summary
        total_checks = len(all_results)
        passed_checks = sum(1 for r in all_results if r.is_valid)
        failed_checks = total_checks - passed_checks
        
        critical_issues = [r for r in all_results if r.severity == "critical" and not r.is_valid]
        error_issues = [r for r in all_results if r.severity == "error" and not r.is_valid]
        warning_issues = [r for r in all_results if r.severity == "warning" and not r.is_valid]
        
        execution_time = time.time() - start_time
        
        summary = {
            "validation_timestamp": time.time(),
            "execution_time": round(execution_time, 3),
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "success_rate": round(passed_checks / total_checks * 100, 1) if total_checks > 0 else 0,
            "critical_issues": len(critical_issues),
            "error_issues": len(error_issues),
            "warning_issues": len(warning_issues),
            "overall_status": "HEALTHY" if critical_issues == 0 and error_issues == 0 else "ISSUES_DETECTED",
            "can_proceed": len(critical_issues) == 0,
            "issues_by_severity": {
                "critical": [{"component": r.component, "message": r.message} for r in critical_issues],
                "error": [{"component": r.component, "message": r.message} for r in error_issues],
                "warning": [{"component": r.component, "message": r.message} for r in warning_issues]
            },
            "all_results": [
                {
                    "component": r.component,
                    "is_valid": r.is_valid,
                    "message": r.message,
                    "severity": r.severity,
                    "details": r.details
                }
                for r in all_results
            ]
        }
        
        # Log summary
        if summary["overall_status"] == "HEALTHY":
            self.logger.info(f"✅ Configuration validation PASSED: {passed_checks}/{total_checks} checks successful")
        else:
            self.logger.error(f"❌ Configuration validation FAILED: {failed_checks}/{total_checks} checks failed")
            if critical_issues:
                self.logger.critical(f"🚨 {len(critical_issues)} CRITICAL issues must be resolved before proceeding")
            if error_issues:
                self.logger.error(f"🚨 {len(error_issues)} ERROR issues should be resolved")
            if warning_issues:
                self.logger.warning(f"⚠️ {len(warning_issues)} WARNING issues detected")
        
        return summary

# Global configuration validator instance
global_config_validator = ConfigurationValidator()

def validate_startup_configuration() -> Dict[str, Any]:
    """Validate configuration at startup"""
    return global_config_validator.run_comprehensive_validation()

def get_configuration_status() -> Dict[str, Any]:
    """Get current configuration validation status"""
    if not global_config_validator.validation_results:
        return {"status": "not_validated", "message": "Configuration validation has not been run"}
    
    return {
        "status": "validated",
        "last_validation": max(r.details.get("timestamp", 0) if r.details else 0 
                              for r in global_config_validator.validation_results),
        "results_count": len(global_config_validator.validation_results),
        "summary": global_config_validator.run_comprehensive_validation()
    }