from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class ScenarioRequest(BaseModel):
    user_data: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None

class ScenarioResponse(BaseModel):
    analysis: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    insights: List[Dict[str, Any]]
    next_actions: List[str]

class BaseScenario(ABC):
    """Base class for all financial scenarios"""
    
    def __init__(self):
        self.name: str = ""
        self.display_name: str = ""
        self.description: str = ""
        self.category: str = ""
        self.version: str = "1.0.0"
        self.required_fields: List[str] = []
        self.optional_fields: List[str] = []
    
    @abstractmethod
    async def analyze(self, request: ScenarioRequest) -> ScenarioResponse:
        """Perform scenario analysis"""
        pass
    
    @abstractmethod
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input data for this scenario"""
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """Get JSON schema for this scenario"""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "category": self.category,
            "required_fields": self.required_fields,
            "optional_fields": self.optional_fields
        }
    
    def get_ui_components(self) -> List[Dict[str, Any]]:
        """Get UI component definitions for Streamlit"""
        return []

class InvestmentPlanningScenario(BaseScenario):
    """Example future scenario - Investment Planning"""
    
    def __init__(self):
        super().__init__()
        self.name = "investment_planning"
        self.display_name = "📈 Investment Planning"
        self.description = "Analyze investment portfolio and provide optimization recommendations"
        self.category = "investment"
        self.required_fields = ["age", "risk_tolerance", "investment_timeline"]
        self.optional_fields = ["current_portfolio", "investment_goals"]
    
    async def analyze(self, request: ScenarioRequest) -> ScenarioResponse:
        """Analyze investment scenario"""
        # Placeholder implementation
        return ScenarioResponse(
            analysis={"portfolio_health": "good", "diversification_score": 75},
            recommendations=[{"title": "Increase equity allocation", "description": "Consider adding more stocks"}],
            insights=[{"title": "Well diversified", "type": "positive"}],
            next_actions=["Rebalance portfolio quarterly", "Review expense ratios"]
        )
    
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate investment planning input"""
        required_present = all(field in data for field in self.required_fields)
        age_valid = isinstance(data.get('age'), (int, float)) and 18 <= data.get('age', 0) <= 100
        return required_present and age_valid

