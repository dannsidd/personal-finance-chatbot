"""
Scenario management for Personal Finance Chatbot
"""

class ScenarioManager:
    def __init__(self):
        self.scenarios = {}
    
    def load_plugin_scenarios(self):
        """Load available financial scenarios"""
        self.scenarios = {
            'budget_analysis': 'Budget and expense analysis',
            'debt_planning': 'Debt payoff planning',
            'goal_planning': 'Financial goal planning',
            'general_advice': 'General financial advice'
        }
        print(f"Loaded {len(self.scenarios)} financial scenarios")

# Create global instance
scenario_manager = ScenarioManager()
