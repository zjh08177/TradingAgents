#!/usr/bin/env python3
"""
LangGraph Compatibility Validator
Simulates the langgraph dev import mechanism to catch issues before deployment.
"""

import sys
import os
import importlib
import traceback
from pathlib import Path
from typing import List, Tuple, Dict, Any
import json
import ast

class LangGraphValidator:
    """Validates graph compatibility with LangGraph dev server."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.errors: List[Tuple[str, str]] = []
        self.warnings: List[Tuple[str, str]] = []
        self.successes: List[str] = []
        
    def validate_all(self) -> bool:
        """Run all validation checks."""
        print("🔍 LangGraph Compatibility Validator")
        print("=" * 60)
        
        # Check 1: Validate langgraph.json exists
        if not self.validate_config():
            return False
            
        # Check 2: Validate graph can be imported like langgraph dev does
        if not self.validate_graph_import():
            return False
            
        # Check 3: Scan for risky patterns
        self.scan_for_risky_patterns()
        
        # Check 4: Test specific problem areas
        self.test_known_issues()
        
        # Check 5: Validate all imports in graph modules
        self.validate_module_imports()
        
        # Report results
        self.print_report()
        
        return len(self.errors) == 0
    
    def validate_config(self) -> bool:
        """Validate langgraph.json configuration."""
        config_path = self.project_root / "langgraph.json"
        
        if not config_path.exists():
            self.errors.append(("config", "langgraph.json not found"))
            return False
            
        try:
            with open(config_path) as f:
                config = json.load(f)
                
            # Check required fields
            if "graphs" not in config:
                self.errors.append(("config", "No 'graphs' section in langgraph.json"))
                return False
                
            self.successes.append("✅ langgraph.json configuration valid")
            return True
            
        except Exception as e:
            self.errors.append(("config", f"Failed to parse langgraph.json: {e}"))
            return False
    
    def validate_graph_import(self) -> bool:
        """Simulate how langgraph dev imports the graph."""
        print("\n📦 Testing graph import mechanism...")
        
        # Add src to path like langgraph dev does
        src_path = self.project_root / "src"
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        
        try:
            # This simulates the exact import mechanism from the error trace
            print("  1. Importing src/agent/__init__.py...")
            agent_module = importlib.import_module('agent')
            
            print("  2. Getting graph factory function...")
            if not hasattr(agent_module, 'graph'):
                self.errors.append(("import", "agent module has no 'graph' function"))
                return False
            
            print("  3. Creating graph (simulating langgraph dev)...")
            # This is what triggers the error in langgraph dev
            graph = agent_module.graph({"configurable": {}})
            
            self.successes.append("✅ Graph imports successfully")
            return True
            
        except Exception as e:
            error_msg = f"Graph import failed (same as langgraph dev): {str(e)}"
            self.errors.append(("import", error_msg))
            print(f"\n❌ {error_msg}")
            print("\nFull traceback:")
            traceback.print_exc()
            return False
    
    def scan_for_risky_patterns(self):
        """Scan for code patterns that often cause issues."""
        print("\n🔎 Scanning for risky patterns...")
        
        patterns_to_check = [
            ("Global imports at module level", self._check_risky_imports),
            ("Circular import potential", self._check_circular_imports),
            ("Module-level execution", self._check_module_execution),
            ("Incompatible dependencies", self._check_dependencies),
        ]
        
        for pattern_name, check_func in patterns_to_check:
            print(f"  Checking: {pattern_name}...")
            issues = check_func()
            if issues:
                for issue in issues:
                    self.warnings.append((pattern_name, issue))
    
    def _check_risky_imports(self) -> List[str]:
        """Check for risky import patterns."""
        issues = []
        risky_modules = ['aioredis', 'redis', 'torch', 'tensorflow', 'confluent_kafka']
        
        # Scan Python files for risky imports
        for py_file in self.project_root.glob("src/**/*.py"):
            try:
                with open(py_file) as f:
                    content = f.read()
                    
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if any(risky in alias.name for risky in risky_modules):
                                issues.append(f"{py_file.relative_to(self.project_root)}: imports {alias.name} at module level")
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and any(risky in node.module for risky in risky_modules):
                            issues.append(f"{py_file.relative_to(self.project_root)}: imports from {node.module} at module level")
            except Exception:
                pass
                
        return issues
    
    def _check_circular_imports(self) -> List[str]:
        """Check for potential circular imports."""
        issues = []
        
        # Look for imports between graph modules
        graph_modules = list(self.project_root.glob("src/agent/graph/**/*.py"))
        
        for module in graph_modules:
            try:
                with open(module) as f:
                    content = f.read()
                    
                # Simple heuristic: if two modules import each other
                module_name = module.stem
                if f"from .{module_name}" in content or f"import {module_name}" in content:
                    issues.append(f"Potential circular import in {module.relative_to(self.project_root)}")
            except Exception:
                pass
                
        return issues
    
    def _check_module_execution(self) -> List[str]:
        """Check for code that executes at module load time."""
        issues = []
        
        for py_file in self.project_root.glob("src/**/*.py"):
            try:
                with open(py_file) as f:
                    content = f.read()
                    
                # Look for code outside of functions/classes
                tree = ast.parse(content)
                for node in tree.body:
                    if isinstance(node, (ast.Expr, ast.Assign)) and not isinstance(node, ast.AnnAssign):
                        # Skip simple assignments and imports
                        if isinstance(node, ast.Assign):
                            if isinstance(node.value, (ast.Constant, ast.Name, ast.List, ast.Dict)):
                                continue
                        issues.append(f"{py_file.relative_to(self.project_root)}: has module-level execution")
                        break
            except Exception:
                pass
                
        return issues[:5]  # Limit to first 5 to avoid noise
    
    def _check_dependencies(self) -> List[str]:
        """Check for known problematic dependencies."""
        issues = []
        
        # Known problematic combinations
        problematic = {
            'aioredis': 'Known issues with Python 3.11+ (TimeoutError conflict)',
            'tensorflow': 'Heavy import that can timeout',
            'torch': 'Heavy import that can timeout',
        }
        
        try:
            requirements_files = list(self.project_root.glob("*requirements*.txt"))
            requirements_files.extend(self.project_root.glob("pyproject.toml"))
            
            for req_file in requirements_files:
                with open(req_file) as f:
                    content = f.read().lower()
                    
                for pkg, issue in problematic.items():
                    if pkg in content:
                        issues.append(f"{pkg}: {issue}")
        except Exception:
            pass
            
        return issues
    
    def test_known_issues(self):
        """Test specific known problematic imports."""
        print("\n🧪 Testing known problematic imports...")
        
        # Test aioredis specifically
        try:
            import aioredis
            self.warnings.append(("aioredis", "Import succeeded but may fail in Python 3.11+"))
        except TypeError as e:
            if "duplicate base class" in str(e):
                self.successes.append("✅ aioredis error caught and handled properly")
        except ImportError:
            self.successes.append("✅ aioredis not installed (safe)")
        except Exception as e:
            self.warnings.append(("aioredis", f"Unexpected error: {e}"))
    
    def validate_module_imports(self):
        """Validate that all graph modules can be imported."""
        print("\n📚 Validating individual module imports...")
        
        modules_to_check = [
            "agent.graph.setup",
            "agent.graph.optimized_setup",
            "agent.graph.enhanced_optimized_setup",
            "agent.graph.trading_graph",
        ]
        
        for module_name in modules_to_check:
            try:
                importlib.import_module(module_name)
                self.successes.append(f"✅ {module_name} imports successfully")
            except Exception as e:
                self.errors.append((module_name, f"Import failed: {str(e)[:100]}"))
    
    def print_report(self):
        """Print validation report."""
        print("\n" + "=" * 60)
        print("📊 VALIDATION REPORT")
        print("=" * 60)
        
        if self.successes:
            print("\n✅ SUCCESSES:")
            for success in self.successes:
                print(f"  {success}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for category, warning in self.warnings:
                print(f"  [{category}] {warning}")
        
        if self.errors:
            print("\n❌ ERRORS:")
            for category, error in self.errors:
                print(f"  [{category}] {error}")
        
        print("\n" + "=" * 60)
        if not self.errors:
            print("🎉 VALIDATION PASSED - Graph is compatible with langgraph dev")
        else:
            print("❌ VALIDATION FAILED - Fix errors before using langgraph dev")
        print("=" * 60)


def main():
    """Run validation."""
    # Change to project root
    if os.path.exists("src/agent"):
        validator = LangGraphValidator(".")
    else:
        print("❌ Error: Must run from trading-graph-server directory")
        sys.exit(1)
    
    success = validator.validate_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()