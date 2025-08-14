from typing import List, Dict, Any, Optional
import math
import logging
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class GoalPriority(int, Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

class GoalPlanner:
    def __init__(self):
        # Goal category definitions
        self.goal_categories = {
            'emergency_fund': {
                'priority_multiplier': 1.5,
                'recommended_amount': 'income * 3',
                'description': 'Essential financial safety net'
            },
            'debt_payoff': {
                'priority_multiplier': 1.3,
                'recommended_amount': 'existing_debt',
                'description': 'Eliminate high-interest debt'
            },
            'retirement': {
                'priority_multiplier': 1.2,
                'recommended_amount': 'income * 10',
                'description': 'Long-term financial security'
            },
            'major_purchase': {
                'priority_multiplier': 1.0,
                'recommended_amount': 'varies',
                'description': 'House, car, education, etc.'
            },
            'vacation': {
                'priority_multiplier': 0.8,
                'recommended_amount': 'varies',
                'description': 'Travel and leisure'
            },
            'luxury': {
                'priority_multiplier': 0.6,
                'recommended_amount': 'varies',
                'description': 'Non-essential purchases'
            }
        }
    
    async def create_goal_plan(
        self,
        income: float,
        expenses: float,
        goals: List[Dict[str, Any]],
        user_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create comprehensive financial goal plan"""
        try:
            if income <= 0:
                return self._empty_goal_plan("Income must be greater than zero")
            
            available_monthly = income - expenses
            
            if available_monthly <= 0:
                return self._create_deficit_plan(income, expenses, goals)
            
            # Validate and enhance goals
            enhanced_goals = self._enhance_goals(goals, income, user_context)
            
            # Calculate individual goal feasibility
            individual_analysis = self._analyze_individual_goals(enhanced_goals, available_monthly)
            
            # Optimize goal allocation
            optimized_allocation = self._optimize_goal_allocation(
                enhanced_goals, available_monthly, individual_analysis
            )
            
            # Generate insights and recommendations
            insights = self._generate_goal_insights(
                enhanced_goals, available_monthly, optimized_allocation
            )
            
            recommendations = self._generate_goal_recommendations(
                enhanced_goals, available_monthly, optimized_allocation, user_context
            )
            
            # Calculate progress tracking milestones
            milestones = self._calculate_goal_milestones(optimized_allocation)
            
            return {
                "financial_overview": {
                    "monthly_income": float(income),
                    "monthly_expenses": float(expenses),
                    "available_monthly": float(available_monthly),
                    "savings_rate": float((available_monthly / income) * 100) if income > 0 else 0
                },
                "goal_analysis": {
                    "total_goals": len(enhanced_goals),
                    "total_target_amount": sum(g['target_amount'] for g in enhanced_goals),
                    "total_monthly_required": sum(g['monthly_required'] for g in individual_analysis.values()),
                    "feasibility_score": self._calculate_feasibility_score(individual_analysis, available_monthly)
                },
                "individual_goals": individual_analysis,
                "optimized_plan": optimized_allocation,
                "insights": insights,
                "recommendations": recommendations,
                "milestones": milestones,
                "action_plan": self._create_action_plan(optimized_allocation)
            }
            
        except Exception as e:
            logger.error(f"Goal planning failed: {e}")
            return self._empty_goal_plan(f"Planning error: {str(e)}")
    
    def _enhance_goals(
        self,
        goals: List[Dict],
        income: float,
        user_context: Optional[Dict]
    ) -> List[Dict[str, Any]]:
        """Enhance goals with additional metadata and validation"""
        enhanced = []
        
        for i, goal in enumerate(goals):
            try:
                # Extract and validate basic fields
                name = str(goal.get('name', f'Goal {i+1}')).strip()
                target_amount = float(goal.get('target_amount', 0))
                timeline_months = int(goal.get('timeline_months', 12))
                priority = int(goal.get('priority', 3))
                
                if target_amount <= 0 or timeline_months <= 0:
                    continue
                
                # Determine goal category
                category = self._categorize_goal(name)
                
                # Calculate monthly requirement
                monthly_required = target_amount / timeline_months
                
                # Add enhanced metadata
                enhanced_goal = {
                    'name': name,
                    'target_amount': target_amount,
                    'timeline_months': timeline_months,
                    'priority': priority,
                    'category': category,
                    'monthly_required': monthly_required,
                    'category_info': self.goal_categories.get(category, {}),
                    'adjusted_priority': self._calculate_adjusted_priority(priority, category),
                    'urgency_score': self._calculate_urgency_score(timeline_months, category),
                    'id': f'goal_{i}'
                }
                
                enhanced.append(enhanced_goal)
                
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping invalid goal: {e}")
                continue
        
        return sorted(enhanced, key=lambda x: (x['adjusted_priority'], x['urgency_score']))
    
    def _categorize_goal(self, goal_name: str) -> str:
        """Categorize goal based on name"""
        name_lower = goal_name.lower()
        
        category_keywords = {
            'emergency_fund': ['emergency', 'emergency fund', 'rainy day'],
            'debt_payoff': ['debt', 'payoff', 'loan', 'credit card'],
            'retirement': ['retirement', '401k', 'ira', 'pension'],
            'major_purchase': ['house', 'car', 'home', 'down payment', 'laptop', 'computer'],
            'vacation': ['vacation', 'travel', 'trip', 'holiday'],
            'luxury': ['luxury', 'jewelry', 'watch', 'designer']
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in name_lower for keyword in keywords):
                return category
        
        return 'major_purchase'  # Default category
    
    def _calculate_adjusted_priority(self, user_priority: int, category: str) -> float:
        """Calculate priority adjusted by category importance"""
        category_info = self.goal_categories.get(category, {})
        multiplier = category_info.get('priority_multiplier', 1.0)
        
        # Lower numbers = higher priority, so divide by multiplier
        return user_priority / multiplier
    
    def _calculate_urgency_score(self, timeline_months: int, category: str) -> float:
        """Calculate urgency based on timeline and category"""
        # Shorter timelines = higher urgency
        base_urgency = 12 / max(timeline_months, 1)
        
        # Emergency fund is always urgent
        if category == 'emergency_fund':
            base_urgency *= 2
        elif category == 'debt_payoff':
            base_urgency *= 1.5
        
        return base_urgency
    
    def _analyze_individual_goals(
        self,
        goals: List[Dict],
        available_monthly: float
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze feasibility of each goal individually"""
        analysis = {}
        
        for goal in goals:
            goal_id = goal['id']
            monthly_required = goal['monthly_required']
            
            # Individual feasibility
            is_feasible = monthly_required <= available_monthly
            
            # Calculate realistic timeline
            if is_feasible:
                realistic_months = goal['timeline_months']
            else:
                realistic_months = math.ceil(goal['target_amount'] / available_monthly) if available_monthly > 0 else float('inf')
            
            # Calculate alternative scenarios
            scenarios = self._calculate_goal_scenarios(goal, available_monthly)
            
            analysis[goal_id] = {
                'goal_name': goal['name'],
                'target_amount': goal['target_amount'],
                'requested_timeline': goal['timeline_months'],
                'monthly_required': monthly_required,
                'is_feasible': is_feasible,
                'realistic_timeline': realistic_months,
                'affordability_ratio': (monthly_required / available_monthly) if available_monthly > 0 else float('inf'),
                'scenarios': scenarios,
                'category': goal['category'],
                'priority': goal['priority'],
                'adjusted_priority': goal['adjusted_priority']
            }
        
        return analysis
    
    def _calculate_goal_scenarios(self, goal: Dict, available_monthly: float) -> List[Dict]:
        """Calculate different scenarios for achieving the goal"""
        scenarios = []
        
        target = goal['target_amount']
        
        # Conservative scenario (30% of available income)
        conservative_monthly = available_monthly * 0.3
        if conservative_monthly > 0:
            conservative_months = math.ceil(target / conservative_monthly)
            scenarios.append({
                'name': 'Conservative',
                'monthly_amount': conservative_monthly,
                'timeline_months': conservative_months,
                'description': '30% of available income'
            })
        
        # Moderate scenario (50% of available income)
        moderate_monthly = available_monthly * 0.5
        if moderate_monthly > 0:
            moderate_months = math.ceil(target / moderate_monthly)
            scenarios.append({
                'name': 'Moderate',
                'monthly_amount': moderate_monthly,
                'timeline_months': moderate_months,
                'description': '50% of available income'
            })
        
        # Aggressive scenario (80% of available income)
        aggressive_monthly = available_monthly * 0.8
        if aggressive_monthly > 0:
            aggressive_months = math.ceil(target / aggressive_monthly)
            scenarios.append({
                'name': 'Aggressive',
                'monthly_amount': aggressive_monthly,
                'timeline_months': aggressive_months,
                'description': '80% of available income'
            })
        
        return scenarios
    
    def _optimize_goal_allocation(
        self,
        goals: List[Dict],
        available_monthly: float,
        individual_analysis: Dict
    ) -> Dict[str, Any]:
        """Optimize allocation across multiple goals"""
        
        # Sort goals by adjusted priority and urgency
        sorted_goals = sorted(goals, key=lambda x: (x['adjusted_priority'], x['urgency_score']))
        
        allocation = {}
        remaining_budget = available_monthly
        
        # First pass: Emergency fund and critical goals
        for goal in sorted_goals:
            goal_id = goal['id']
            category = goal['category']
            
            if category == 'emergency_fund' and remaining_budget > 0:
                # Allocate at least 20% to emergency fund if it exists
                emergency_allocation = min(
                    goal['monthly_required'],
                    remaining_budget * 0.2,
                    remaining_budget
                )
                
                allocation[goal_id] = {
                    'goal_name': goal['name'],
                    'monthly_allocation': emergency_allocation,
                    'timeline_months': math.ceil(goal['target_amount'] / emergency_allocation) if emergency_allocation > 0 else float('inf'),
                    'priority_rank': 1,
                    'allocation_reason': 'Emergency fund prioritization'
                }
                
                remaining_budget -= emergency_allocation
        
        # Second pass: Distribute remaining budget by priority
        non_emergency_goals = [g for g in sorted_goals if g['category'] != 'emergency_fund']
        
        for i, goal in enumerate(non_emergency_goals):
            goal_id = goal['id']
            
            if remaining_budget <= 0:
                # No budget left - calculate timeline with $0 allocation
                allocation[goal_id] = {
                    'goal_name': goal['name'],
                    'monthly_allocation': 0,
                    'timeline_months': float('inf'),
                    'priority_rank': i + 2,
                    'allocation_reason': 'Insufficient budget'
                }
            else:
                # Allocate proportional to priority
                if i == 0:  # Highest priority gets largest share
                    goal_allocation = min(
                        goal['monthly_required'],
                        remaining_budget * 0.6
                    )
                elif i == 1:  # Second priority gets moderate share
                    goal_allocation = min(
                        goal['monthly_required'],
                        remaining_budget * 0.3
                    )
                else:  # Remaining goals share the rest
                    remaining_goals = len(non_emergency_goals) - 2
                    goal_allocation = min(
                        goal['monthly_required'],
                        remaining_budget / max(remaining_goals, 1)
                    )
                
                timeline = math.ceil(goal['target_amount'] / goal_allocation) if goal_allocation > 0 else float('inf')
                
                allocation[goal_id] = {
                    'goal_name': goal['name'],
                    'monthly_allocation': goal_allocation,
                    'timeline_months': timeline,
                    'priority_rank': i + 2,
                    'allocation_reason': f'Priority-based allocation (rank {i + 1})'
                }
                
                remaining_budget -= goal_allocation
        
        return {
            'allocations': allocation,
            'total_allocated': available_monthly - remaining_budget,
            'remaining_budget': remaining_budget,
            'allocation_efficiency': ((available_monthly - remaining_budget) / available_monthly) * 100 if available_monthly > 0 else 0
        }
    
    def _generate_goal_insights(
        self,
        goals: List[Dict],
        available_monthly: float,
        allocation: Dict
    ) -> List[Dict[str, Any]]:
        """Generate insights about goal planning"""
        insights = []
        
        try:
            allocations = allocation.get('allocations', {})
            
            # Budget utilization insight
            utilization = allocation.get('allocation_efficiency', 0)
            if utilization < 80:
                insights.append({
                    'title': 'Opportunity for More Savings',
                    'description': f'Only {utilization:.1f}% of available income allocated to goals',
                    'type': 'opportunity',
                    'priority': 'medium',
                    'action': f'Consider allocating the remaining ${allocation.get("remaining_budget", 0):.2f}/month'
                })
            
            # Emergency fund insight
            emergency_goals = [g for g in goals if g['category'] == 'emergency_fund']
            if not emergency_goals:
                insights.append({
                    'title': 'Missing Emergency Fund',
                    'description': 'No emergency fund goal detected',
                    'type': 'warning',
                    'priority': 'high',
                    'action': 'Consider adding an emergency fund as your first priority'
                })
            
            # Timeline reality check
            long_timeline_goals = [
                alloc for alloc in allocations.values() 
                if alloc.get('timeline_months', 0) > 60
            ]
            if long_timeline_goals:
                insights.append({
                    'title': 'Very Long Goal Timelines',
                    'description': f'{len(long_timeline_goals)} goals will take over 5 years to complete',
                    'type': 'info',
                    'priority': 'low',
                    'action': 'Consider increasing monthly contributions or adjusting goal amounts'
                })
            
            # Goal prioritization insight
            high_priority_count = len([g for g in goals if g['adjusted_priority'] <= 2])
            total_goals = len(goals)
            
            if high_priority_count > 3:
                insights.append({
                    'title': 'Too Many High-Priority Goals',
                    'description': f'{high_priority_count} out of {total_goals} goals marked as high priority',
                    'type': 'warning',
                    'priority': 'medium',
                    'action': 'Consider focusing on 2-3 most important goals first'
                })
            
        except Exception as e:
            logger.error(f"Goal insight generation failed: {e}")
        
        return insights
    
    def _generate_goal_recommendations(
        self,
        goals: List[Dict],
        available_monthly: float,
        allocation: Dict,
        user_context: Optional[Dict]
    ) -> List[Dict[str, Any]]:
        """Generate actionable recommendations"""
        recommendations = []
        
        try:
            allocations = allocation.get('allocations', {})
            
            # Automation recommendation
            total_allocated = allocation.get('total_allocated', 0)
            if total_allocated > 0:
                recommendations.append({
                    'title': 'Automate Your Savings',
                    'description': f'Set up automatic transfers for ${total_allocated:.2f}/month',
                    'action': 'Create automatic transfers on payday to separate goal accounts',
                    'type': 'automation',
                    'priority': 'high',
                    'implementation': 'Set up in your banking app or with your employer'
                })
            
            # Account structure recommendation
            active_goals = len([a for a in allocations.values() if a.get('monthly_allocation', 0) > 0])
            if active_goals > 1:
                recommendations.append({
                    'title': 'Separate Savings Accounts',
                    'description': f'Create separate accounts for your {active_goals} active goals',
                    'action': 'Open high-yield savings accounts for each major goal',
                    'type': 'account_structure',
                    'priority': 'medium',
                    'implementation': 'Use online banks for better interest rates'
                })
            
            # Income optimization
            if available_monthly < sum(g['monthly_required'] for g in goals):
                recommendations.append({
                    'title': 'Consider Income Optimization',
                    'description': 'Your goals require more than current available income',
                    'action': 'Look for ways to increase income or reduce expenses',
                    'type': 'income_optimization',
                    'priority': 'high',
                    'implementation': 'Side hustle, skills training, or expense audit'
                })
            
            # Persona-specific recommendations
            if user_context:
                persona = user_context.get('persona')
                
                if persona == 'student':
                    recommendations.append({
                        'title': 'Student-Focused Strategy',
                        'description': 'Start with small, achievable goals to build momentum',
                        'action': 'Focus on emergency fund first, then larger goals',
                        'type': 'student_strategy',
                        'priority': 'medium'
                    })
                
                elif persona == 'family':
                    recommendations.append({
                        'title': 'Family Goal Coordination',
                        'description': 'Involve your partner in goal planning and progress tracking',
                        'action': 'Set up joint accounts and regular financial check-ins',
                        'type': 'family_strategy',
                        'priority': 'medium'
                    })
            
        except Exception as e:
            logger.error(f"Goal recommendation generation failed: {e}")
        
        return recommendations
    
    def _calculate_goal_milestones(self, allocation: Dict) -> List[Dict[str, Any]]:
        """Calculate milestone dates and celebrations"""
        milestones = []
        
        try:
            allocations = allocation.get('allocations', {})
            
            # Sort by timeline
            sorted_allocations = sorted(
                allocations.items(),
                key=lambda x: x[1].get('timeline_months', float('inf'))
            )
            
            for goal_id, alloc in sorted_allocations:
                timeline = alloc.get('timeline_months', 0)
                
                if timeline != float('inf') and timeline > 0:
                    target_date = datetime.now() + timedelta(days=timeline * 30)
                    
                    milestones.append({
                        'goal_id': goal_id,
                        'goal_name': alloc['goal_name'],
                        'target_date': target_date.strftime('%B %Y'),
                        'months_from_now': int(timeline),
                        'monthly_amount': alloc.get('monthly_allocation', 0),
                        'milestone_type': 'completion',
                        'celebration_message': f"🎉 Congratulations! You've reached your {alloc['goal_name']} goal!"
                    })
                    
                    # Add intermediate milestones for long-term goals
                                        # Add intermediate milestones for long-term goals
                    if timeline > 12:
                        halfway_date = datetime.now() + timedelta(days=(timeline * 15))  # Halfway point
                        milestones.append({
                            'goal_id': goal_id,
                            'goal_name': alloc['goal_name'],
                            'target_date': halfway_date.strftime('%B %Y'),
                            'months_from_now': int(timeline // 2),
                            'monthly_amount': alloc.get('monthly_allocation', 0),
                            'milestone_type': 'halfway',
                            'celebration_message': f"🎯 You're halfway to your {alloc['goal_name']} goal! Keep it up!"
                        })
        
        except Exception as e:
            logger.error(f"Milestone calculation failed: {e}")
        
        return milestones
    
    def _create_action_plan(self, allocation: Dict) -> Dict[str, Any]:
        """Create concrete action plan"""
        try:
            allocations = allocation.get('allocations', {})
            
            # Immediate actions (this week)
            immediate_actions = []
            if allocations:
                immediate_actions = [
                    "Open separate high-yield savings accounts for each goal",
                    "Set up automatic transfers from checking to goal accounts",
                    "Download a goal tracking app or create a spreadsheet"
                ]
            
            # Monthly actions
            monthly_actions = [
                "Review goal progress and adjust if needed",
                "Check account balances and celebrate milestones",
                "Look for opportunities to increase contributions"
            ]
            
            # Quarterly actions
            quarterly_actions = [
                "Reassess goal priorities based on life changes",
                "Compare actual vs. planned progress",
                "Consider rebalancing allocations"
            ]
            
            return {
                "immediate_actions": immediate_actions,
                "monthly_actions": monthly_actions,
                "quarterly_actions": quarterly_actions,
                "success_factors": [
                    "Consistency in monthly contributions",
                    "Regular progress monitoring",
                    "Flexibility to adjust when life changes"
                ]
            }
            
        except Exception as e:
            logger.error(f"Action plan creation failed: {e}")
            return {"immediate_actions": [], "monthly_actions": [], "quarterly_actions": []}
    
    def _create_deficit_plan(self, income: float, expenses: float, goals: List[Dict]) -> Dict[str, Any]:
        """Create plan when expenses exceed income"""
        deficit = expenses - income
        
        return {
            "financial_overview": {
                "monthly_income": float(income),
                "monthly_expenses": float(expenses),
                "available_monthly": float(income - expenses),
                "deficit_amount": float(deficit),
                "savings_rate": 0.0
            },
            "goal_analysis": {
                "feasibility_message": "Goals not feasible with current income vs expenses",
                "required_action": "Focus on expense reduction or income increase first"
            },
            "recommendations": [
                {
                    'title': 'Address Budget Deficit First',
                    'description': f'You have a ${deficit:.2f} monthly deficit',
                    'action': 'Focus on reducing expenses or increasing income before setting savings goals',
                    'type': 'budget_fix',
                    'priority': 'critical'
                },
                {
                    'title': 'Expense Audit Needed',
                    'description': 'Analyze spending to find reduction opportunities',
                    'action': 'Track all expenses for 30 days and identify cuts',
                    'type': 'expense_reduction',
                    'priority': 'high'
                }
            ],
            "insights": [
                {
                    'title': 'Budget Deficit Alert',
                    'description': 'Your expenses exceed your income',
                    'type': 'critical',
                    'priority': 'immediate'
                }
            ]
        }
    
    def _calculate_feasibility_score(self, individual_analysis: Dict, available_monthly: float) -> float:
        """Calculate overall feasibility score (0-100)"""
        if not individual_analysis or available_monthly <= 0:
            return 0.0
        
        total_required = sum(
            analysis['monthly_required'] 
            for analysis in individual_analysis.values()
        )
        
        if total_required == 0:
            return 100.0
        
        # Base score on how much of required amount is available
        base_score = min(100, (available_monthly / total_required) * 100)
        
        # Adjust for number of goals (fewer goals = higher feasibility)
        goal_count_penalty = max(0, len(individual_analysis) - 3) * 5
        
        # Adjust for emergency fund presence
        has_emergency_fund = any(
            analysis.get('category') == 'emergency_fund' 
            for analysis in individual_analysis.values()
        )
        emergency_bonus = 10 if has_emergency_fund else 0
        
        final_score = max(0, min(100, base_score - goal_count_penalty + emergency_bonus))
        return float(final_score)
    
    def _empty_goal_plan(self, message: str = "No goals provided") -> Dict[str, Any]:
        """Return empty goal plan structure"""
        return {
            "financial_overview": {
                "monthly_income": 0.0,
                "monthly_expenses": 0.0,
                "available_monthly": 0.0,
                "savings_rate": 0.0
            },
            "goal_analysis": {
                "total_goals": 0,
                "total_target_amount": 0.0,
                "total_monthly_required": 0.0,
                "feasibility_score": 0.0,
                "message": message
            },
            "individual_goals": {},
            "optimized_plan": {"allocations": {}, "total_allocated": 0.0, "remaining_budget": 0.0},
            "insights": [],
            "recommendations": [],
            "milestones": [],
            "action_plan": {"immediate_actions": [], "monthly_actions": [], "quarterly_actions": []}
        }

# Global instance
goal_planner = GoalPlanner()

