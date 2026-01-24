"""
A2E Pro Configuration Validator

Validates Phase 1 configuration and ensures everything is correctly set up.
"""

import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class ConfigValidator:
    """Validates A2E Pro configuration"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.config_path = Path(__file__).parent.parent / "config" / "avatars" / "pro_plan_optimized.json"
    
    def validate(self):
        """Run all validation checks"""
        print("🔍 Validating A2E Pro Configuration...\n")
        
        self.check_config_file()
        self.check_pricing()
        self.check_daily_schedule()
        self.check_budget()
        self.check_characters()
        
        self.print_results()
        return len(self.errors) == 0
    
    def check_config_file(self):
        """Check if config file exists and is valid JSON"""
        if not self.config_path.exists():
            self.errors.append(f"Config file not found: {self.config_path}")
            return
        
        try:
            with open(self.config_path) as f:
                self.config = json.load(f)
            print("✅ Config file loaded successfully")
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in config file: {e}")
    
    def check_pricing(self):
        """Validate pricing configuration"""
        print("\n📊 Validating Pricing...")
        
        phase1 = self.config.get("phase1_strategy", {})
        
        # Check credits per reel
        credits_per_reel = phase1.get("credits_per_reel")
        if credits_per_reel != 15:
            self.errors.append(
                f"CRITICAL: credits_per_reel should be 15 (1 per second × 15s), "
                f"found: {credits_per_reel}"
            )
        else:
            print(f"  ✅ Credits per reel: {credits_per_reel} (correct)")
        
        # Check daily credits
        daily_needed = phase1.get("daily_credits_needed")
        if daily_needed != 60:
            self.errors.append(
                f"Daily credits should be 60 (4 reels × 15 credits), "
                f"found: {daily_needed}"
            )
        else:
            print(f"  ✅ Daily credits needed: {daily_needed} (correct)")
        
        # Check monthly cost
        monthly_cost = phase1.get("monthly_investment")
        if monthly_cost != 9.90:
            self.warnings.append(
                f"Monthly cost should be $9.90 for Pro plan, found: ${monthly_cost}"
            )
        else:
            print(f"  ✅ Monthly investment: ${monthly_cost} (correct)")
        
        # Check topup needed
        topup_needed = phase1.get("topup_needed")
        if topup_needed:
            self.errors.append(
                "CRITICAL: topup_needed should be false with Pro plan for 4 reels/day"
            )
        else:
            print(f"  ✅ Topup needed: {topup_needed} (correct)")
    
    def check_daily_schedule(self):
        """Validate daily schedule configuration"""
        print("\n📅 Validating Daily Schedule...")
        
        schedule = self.config.get("daily_schedule", {})
        
        expected_reels = 4
        actual_reels = sum(1 for key in schedule.keys() if key.startswith("reel_"))
        
        if actual_reels != expected_reels:
            self.warnings.append(
                f"Expected {expected_reels} scheduled reels, found {actual_reels}"
            )
        else:
            print(f"  ✅ Scheduled reels: {actual_reels} (correct)")
        
        # Check each reel
        total_credits = 0
        for i in range(1, 5):
            reel_key = f"reel_{i}_{'morning' if i==1 else 'afternoon' if i==2 else 'evening' if i==3 else 'night'}"
            reel = schedule.get(reel_key, {})
            
            duration = reel.get("duration_seconds", 0)
            credits = reel.get("credits_used", 0)
            
            if duration != 15:
                self.warnings.append(f"{reel_key}: duration should be 15s, found {duration}s")
            
            if credits != 15:
                self.errors.append(
                    f"{reel_key}: credits should be 15 (1/second × {duration}s), found {credits}"
                )
            else:
                total_credits += credits
                print(f"  ✅ {reel_key}: {credits} credits (correct)")
        
        # Check total
        totals = schedule.get("daily_totals", {})
        daily_total = totals.get("total_credits", 0)
        
        if daily_total != 60:
            self.errors.append(f"Daily total should be 60 credits, found {daily_total}")
        else:
            print(f"  ✅ Daily total: {daily_total} credits (correct)")
    
    def check_budget(self):
        """Validate budget scenarios"""
        print("\n💰 Validating Budget Scenarios...")
        
        scenarios = self.config.get("budget_scenarios", {})
        
        # Check conservative scenario
        conservative = scenarios.get("conservative", {})
        if conservative.get("monthly_cost") != 9.90:
            self.errors.append("Conservative scenario should cost $9.90/month")
        else:
            print(f"  ✅ Conservative: ${conservative.get('monthly_cost')}/month")
        
        # Check aggressive scenario
        aggressive = scenarios.get("aggressive", {})
        if aggressive.get("reels_per_day") == 8:
            if aggressive.get("monthly_cost") != 9.90:
                self.errors.append("Aggressive scenario (8 reels) should still cost $9.90")
            else:
                print(f"  ✅ Aggressive: {aggressive.get('reels_per_day')} reels/day, ${aggressive.get('monthly_cost')}/month")
    
    def check_characters(self):
        """Validate character configuration"""
        print("\n👥 Validating Characters...")
        
        schedule = self.config.get("daily_schedule", {})
        expected_characters = {
            "miyuki_sakura",
            "hana_nakamura",
            "airi_neo",
            "aiko_hayashi"
        }
        
        actual_characters = set()
        for key, reel in schedule.items():
            if key.startswith("reel_"):
                char = reel.get("character")
                if char:
                    actual_characters.add(char)
        
        if actual_characters != expected_characters:
            missing = expected_characters - actual_characters
            extra = actual_characters - expected_characters
            
            if missing:
                self.warnings.append(f"Missing characters in schedule: {missing}")
            if extra:
                self.warnings.append(f"Unexpected characters in schedule: {extra}")
        else:
            print(f"  ✅ All 4 characters configured: {', '.join(actual_characters)}")
    
    def print_results(self):
        """Print validation results"""
        print("\n" + "="*60)
        print("VALIDATION RESULTS")
        print("="*60)
        
        if not self.errors and not self.warnings:
            print("\n✅ ALL CHECKS PASSED")
            print("\nConfiguration is valid and ready for production!")
            print(f"\nExpected costs:")
            print(f"  - Daily: 60 credits (~$0.33)")
            print(f"  - Monthly: 1800 credits = $9.90")
            print(f"  - Per reel: 15 credits (~$0.08)")
            return
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
            print("\n⚠️  Please fix errors before proceeding to production!")


def main():
    """Run validation"""
    validator = ConfigValidator()
    is_valid = validator.validate()
    
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
