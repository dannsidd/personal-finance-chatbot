from typing import List, Dict, Any, Optional
import math
import logging
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class DebtStrategy(str, Enum):
    AVALANCHE = "avalanche"
    SNOWBALL = "snowball"
    HYBRID = "hybrid"

class DebtPlanner:
    def __init__(self):
        pass
    
    async def create_debt_plan(
        self,
        debts: List[Dict[str, Any]],
        extra_payment: float = 0.0,
        strategy: DebtStrategy = DebtStrategy.AVALANCHE,
        user_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create comprehensive debt payoff plan"""
        try:
            if not debts:
                return self._empty_debt_plan()
            
            # Validate and clean debt data
            cleaned_debts = self._validate_debts(debts)
            if not cleaned_debts:
                return self._empty_debt_plan()
            
            # Calculate baseline (minimum payments only)
            baseline_plan = self._calculate_minimum_only_plan(cleaned_debts)
            
            # Calculate optimized plan with strategy
            optimized_plan = self._calculate_strategy_plan(cleaned_debts, extra_payment, strategy)
            
            # Calculate savings
            baseline_total_interest = sum(debt['total_interest'] for debt in baseline_plan)
            optimized_total_interest = sum(debt['total_interest'] for debt in optimized_plan)
            interest_saved = baseline_total_interest - optimized_total_interest
            
            baseline_max_months = max((debt['months_to_payoff'] for debt in baseline_plan), default=0)
            optimized_max_months = max((debt['months_to_payoff'] for debt in optimized_plan), default=0)
            months_saved = baseline_max_months - optimized_max_months
            
            # Generate insights and recommendations
            insights = self._generate_debt_insights(cleaned_debts, optimized_plan, strategy)
            recommendations = self._generate_debt_recommendations(cleaned_debts, optimized_plan, user_context)
            
            # Calculate total debt summary
            total_balance = sum(debt['balance'] for debt in cleaned_debts)
            total_minimum = sum(debt['minimum_payment'] for debt in cleaned_debts)
            
            return {
                "summary": {
                    "total_debt": float(total_balance),
                    "total_minimum_payment": float(total_minimum),
                    "extra_payment": float(extra_payment),
                    "strategy_used": strategy.value,
                    "total_monthly_payment": float(total_minimum + extra_payment),
                    "debt_count": len(cleaned_debts)
                },
                "savings": {
                    "interest_saved": float(max(0, interest_saved)),
                    "months_saved": int(max(0, months_saved)),
                    "total_saved": float(max(0, interest_saved))
                },
                "payoff_plan": optimized_plan,
                "baseline_plan": baseline_plan,
                "insights": insights,
                "recommendations": recommendations,
                "next_action": self._get_next_action(optimized_plan, strategy),
                "milestones": self._calculate_milestones(optimized_plan)
            }
            
        except Exception as e:
            logger.error(f"Debt planning failed: {e}")
            return self._empty_debt_plan()
    
    def _validate_debts(self, debts: List[Dict]) -> List[Dict]:
        """Validate and clean debt data"""
        cleaned = []
        
        for debt in debts:
            try:
                balance = float(debt.get('balance', 0))
                apr = float(debt.get('apr', 0))
                minimum_payment = float(debt.get('minimum_payment', 0))
                name = str(debt.get('name', 'Unknown Debt')).strip()
                
                # Skip invalid debts
                if balance <= 0 or minimum_payment <= 0:
                    continue
                
                # Ensure APR is reasonable (0-50%)
                if apr < 0:
                    apr = 0
                elif apr > 50:
                    apr = 50
                
                cleaned.append({
                    'name': name,
                    'balance': balance,
                    'apr': apr,
                    'minimum_payment': minimum_payment,
                    'monthly_interest_rate': apr / 100 / 12
                })
                
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping invalid debt: {e}")
                continue
        
        return cleaned
    
    def _calculate_minimum_only_plan(self, debts: List[Dict]) -> List[Dict]:
        """Calculate payoff with minimum payments only"""
        plan = []
        
        for debt in debts:
            months, total_interest = self._calculate_payoff_time(
                balance=debt['balance'],
                monthly_payment=debt['minimum_payment'],
                monthly_interest_rate=debt['monthly_interest_rate']
            )
            
            plan.append({
                'debt_name': debt['name'],
                'balance': debt['balance'],
                'apr': debt['apr'],
                'monthly_payment': debt['minimum_payment'],
                'months_to_payoff': months,
                'total_interest': total_interest,
                'total_payments': debt['minimum_payment'] * months,
                'payoff_order': len(plan) + 1
            })
        
        return plan
    
    def _calculate_strategy_plan(
        self,
        debts: List[Dict],
        extra_payment: float,
        strategy: DebtStrategy
    ) -> List[Dict]:
        """Calculate payoff plan using specified strategy"""
        
        # Sort debts based on strategy
        if strategy == DebtStrategy.AVALANCHE:
            # Highest APR first
            sorted_debts = sorted(debts, key=lambda x: x['apr'], reverse=True)
        elif strategy == DebtStrategy.SNOWBALL:
            # Lowest balance first
            sorted_debts = sorted(debts, key=lambda x: x['balance'])
        else:  # HYBRID
            # Score based on APR/balance ratio for balance of both factors
            for debt in debts:
                debt['score'] = (debt['apr'] / 100) / max(debt['balance'] / 10000, 1)
            sorted_debts = sorted(debts, key=lambda x: x['score'], reverse=True)
        
        plan = []
        remaining_extra = extra_payment
        
        for i, debt in enumerate(sorted_debts):
            # First debt gets all extra payment
            if i == 0:
                payment = debt['minimum_payment'] + remaining_extra
                remaining_extra = 0
            else:
                payment = debt['minimum_payment']
            
            months, total_interest = self._calculate_payoff_time(
                balance=debt['balance'],
                monthly_payment=payment,
                monthly_interest_rate=debt['monthly_interest_rate']
            )
            
            plan.append({
                'debt_name': debt['name'],
                'balance': debt['balance'],
                'apr': debt['apr'],
                'monthly_payment': payment,
                'months_to_payoff': months,
                'total_interest': total_interest,
                'total_payments': payment * months,
                'payoff_order': i + 1,
                'strategy_priority': i + 1
            })
        
        return plan
    
    def _calculate_payoff_time(
        self,
        balance: float,
        monthly_payment: float,
        monthly_interest_rate: float
    ) -> tuple[int, float]:
        """Calculate months to payoff and total interest"""
        
        if monthly_payment <= 0:
            return float('inf'), float('inf')
        
        if monthly_interest_rate <= 0:
            # No interest
            months = math.ceil(balance / monthly_payment)
            total_interest = 0.0
        else:
            # Check if payment covers interest
            monthly_interest = balance * monthly_interest_rate
            if monthly_payment <= monthly_interest:
                # Payment doesn't cover interest - debt never paid off
                return float('inf'), float('inf')
            
            # Calculate using amortization formula
            try:
                months = math.ceil(
                    -math.log(1 - (balance * monthly_interest_rate) / monthly_payment) /
                    math.log(1 + monthly_interest_rate)
                )
            except (ValueError, ZeroDivisionError):
                months = math.ceil(balance / monthly_payment)
            
            total_payments = monthly_payment * months
            total_interest = total_payments - balance
        
        return int(months), float(max(0, total_interest))
    
    def _generate_debt_insights(
        self,
        debts: List[Dict],
        plan: List[Dict],
        strategy: DebtStrategy
    ) -> List[Dict[str, Any]]:
        """Generate insights about the debt situation"""
        insights = []
        
        try:
            # High-interest debt alert
            high_interest_debts = [d for d in debts if d['apr'] > 18.0]
            if high_interest_debts:
                total_high_interest = sum(d['balance'] for d in high_interest_debts)
                insights.append({
                    'title': 'High Interest Debt Alert',
                    'description': f'${total_high_interest:,.2f} in debt with APR > 18%',
                    'type': 'warning',
                    'priority': 'high',
                    'action': 'Consider debt consolidation or balance transfer'
                })
            
            # Strategy effectiveness
            fastest_payoff = min((debt['months_to_payoff'] for debt in plan), default=0)
            if fastest_payoff > 0:
                insights.append({
                    'title': f'{strategy.value.title()} Strategy Selected',
                    'description': f'First debt paid off in {fastest_payoff} months',
                    'type': 'info',
                    'priority': 'medium',
                    'details': self._get_strategy_explanation(strategy)
                })
            
            # Payment-to-balance ratio
            total_balance = sum(d['balance'] for d in debts)
            total_minimum = sum(d['minimum_payment'] for d in debts)
            payment_ratio = (total_minimum / total_balance) * 100 if total_balance > 0 else 0
            
            if payment_ratio < 3:  # Less than 3% of balance
                insights.append({
                    'title': 'Low Payment Ratio',
                    'description': f'Monthly payments are {payment_ratio:.1f}% of total debt',
                    'type': 'warning',
                    'priority': 'medium',
                    'action': 'Consider increasing payments to accelerate payoff'
                })
            
        except Exception as e:
            logger.error(f"Debt insight generation failed: {e}")
        
        return insights
    
    def _generate_debt_recommendations(
        self,
        debts: List[Dict],
        plan: List[Dict],
        user_context: Optional[Dict]
    ) -> List[Dict[str, Any]]:
        """Generate actionable debt recommendations"""
        recommendations = []
        
        try:
            # Extra payment recommendation
            total_minimum = sum(d['minimum_payment'] for d in debts)
            suggested_extra = total_minimum * 0.2  # Suggest 20% more
            
            recommendations.append({
                'title': 'Increase Monthly Payments',
                'description': f'Adding ${suggested_extra:.2f}/month could significantly reduce payoff time',
                'action': f'Try to pay ${total_minimum + suggested_extra:.2f} total monthly',
                'type': 'payment_increase',
                'priority': 'high',
                'potential_benefit': 'Faster payoff and reduced interest'
            })
            
            # Balance transfer recommendation
            high_apr_debts = [d for d in debts if d['apr'] > 15.0]
            if high_apr_debts and len(high_apr_debts) > 1:
                total_high_apr = sum(d['balance'] for d in high_apr_debts)
                recommendations.append({
                    'title': 'Consider Balance Transfer',
                    'description': f'${total_high_apr:,.2f} in high-APR debt could benefit from consolidation',
                    'action': 'Look for 0% APR balance transfer offers',
                    'type': 'consolidation',
                    'priority': 'medium',
                    'potential_benefit': 'Lower interest rates'
                })
            
            # Emergency fund warning
            if user_context and user_context.get('has_emergency_fund', False) is False:
                recommendations.append({
                    'title': 'Build Small Emergency Fund First',
                    'description': 'Consider building a $1,000 emergency fund before aggressive debt payoff',
                    'action': 'Balance debt payoff with emergency savings',
                    'type': 'emergency_fund',
                    'priority': 'high',
                    'potential_benefit': 'Avoid taking on more debt for emergencies'
                })
            
            # Family-specific recommendations
            if user_context and user_context.get('persona') == 'family':
                recommendations.append({
                    'title': 'Family Debt Strategy',
                    'description': 'Involve your partner in debt payoff planning',
                    'action': 'Set up automatic payments and regular progress reviews',
                    'type': 'family_planning',
                    'priority': 'medium',
                    'potential_benefit': 'Better accountability and success'
                })
            
        except Exception as e:
            logger.error(f"Debt recommendation generation failed: {e}")
        
        return recommendations
    
    def _get_strategy_explanation(self, strategy: DebtStrategy) -> str:
        """Get explanation of debt strategy"""
        explanations = {
            DebtStrategy.AVALANCHE: "Pays minimum on all debts, extra goes to highest APR debt. Saves the most money on interest.",
            DebtStrategy.SNOWBALL: "Pays minimum on all debts, extra goes to smallest balance. Provides psychological wins and motivation.",
            DebtStrategy.HYBRID: "Balances interest rates and balances for a middle-ground approach between avalanche and snowball."
        }
        return explanations.get(strategy, "Custom debt payoff strategy")
    
    def _get_next_action(self, plan: List[Dict], strategy: DebtStrategy) -> str:
        """Generate next action recommendation"""
        if not plan:
            return "Add your debts to create a payoff plan!"
        
        # Find the debt with the highest priority (lowest payoff_order)
        priority_debt = min(plan, key=lambda x: x.get('payoff_order', float('inf')))
        
        return (
            f"Focus on '{priority_debt['debt_name']}' using {strategy.value} strategy. "
            f"Pay ${priority_debt['monthly_payment']:.2f}/month to eliminate it in "
            f"{priority_debt['months_to_payoff']} months."
        )
    
    def _calculate_milestones(self, plan: List[Dict]) -> List[Dict[str, Any]]:
        """Calculate debt payoff milestones"""
        milestones = []
        
        try:
            # Sort by payoff order
            sorted_plan = sorted(plan, key=lambda x: x.get('payoff_order', 0))
            
            cumulative_months = 0
            cumulative_freed_payment = 0
            
            for debt in sorted_plan:
                cumulative_months = max(cumulative_months, debt['months_to_payoff'])
                cumulative_freed_payment += debt['monthly_payment']
                
                milestone_date = datetime.now() + timedelta(days=cumulative_months * 30)
                
                milestones.append({
                    'debt_name': debt['debt_name'],
                    'target_date': milestone_date.strftime('%B %Y'),
                    'months_from_now': cumulative_months,
                    'freed_cash_flow': cumulative_freed_payment,
                    'celebration_message': f"🎉 {debt['debt_name']} paid off! You've freed up ${debt['monthly_payment']:.2f}/month!"
                })
        
        except Exception as e:
            logger.error(f"Milestone calculation failed: {e}")
        
        return milestones
    
    def _empty_debt_plan(self) -> Dict[str, Any]:
        """Return empty debt plan structure"""
        return {
            "summary": {
                "total_debt": 0.0,
                "total_minimum_payment": 0.0,
                "extra_payment": 0.0,
                "strategy_used": "none",
                "total_monthly_payment": 0.0,
                "debt_count": 0
            },
            "savings": {
                "interest_saved": 0.0,
                "months_saved": 0,
                "total_saved": 0.0
            },
            "payoff_plan": [],
            "baseline_plan": [],
            "insights": [],
            "recommendations": [],
            "next_action": "Add your debts to get started with a personalized payoff plan!",
            "milestones": []
        }

# Global instance
debt_planner = DebtPlanner()

