import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)

class BudgetAnalyzer:
    def __init__(self):
        # Enhanced categories with cultural adaptations
        self.categories = {
            'housing': {
                'keywords': ['rent', 'mortgage', 'utilities', 'internet', 'cable', 'electricity', 'gas', 'water'],
                'patterns': ['housing', 'rent', 'mortgage']
            },
            'groceries': {
                'keywords': ['grocery', 'supermarket', 'whole foods', 'trader joe', 'safeway', 'food', 'mart'],
                'patterns': ['grocery', 'food', 'market']
            },
            'transport': {
                'keywords': ['gas', 'uber', 'lyft', 'parking', 'metro', 'bus', 'taxi', 'petrol', 'fuel'],
                'patterns': ['transport', 'travel', 'commute']
            },
            'dining': {
                'keywords': ['restaurant', 'coffee', 'starbucks', 'delivery', 'takeout', 'dining', 'cafe'],
                'patterns': ['restaurant', 'dining', 'food delivery']
            },
            'entertainment': {
                'keywords': ['netflix', 'spotify', 'movie', 'theater', 'gaming', 'streaming', 'concert'],
                'patterns': ['entertainment', 'streaming', 'movies']
            },
            'shopping': {
                'keywords': ['amazon', 'target', 'walmart', 'clothing', 'retail', 'shopping', 'store'],
                'patterns': ['shopping', 'retail', 'purchase']
            },
            'healthcare': {
                'keywords': ['pharmacy', 'doctor', 'hospital', 'medical', 'dental', 'health', 'medicine'],
                'patterns': ['healthcare', 'medical', 'doctor']
            },
            'childcare': {
                'keywords': ['daycare', 'babysitter', 'school', 'tuition', 'childcare', 'kids'],
                'patterns': ['childcare', 'education', 'school']
            },
            'subscriptions': {
                'keywords': ['subscription', 'membership', 'annual fee', 'monthly fee', 'premium'],
                'patterns': ['subscription', 'membership', 'recurring']
            },
            'debt': {
                'keywords': ['credit card', 'loan payment', 'student loan', 'car payment', 'mortgage payment'],
                'patterns': ['payment', 'loan', 'credit']
            },
            'savings': {
                'keywords': ['savings', 'transfer', 'deposit', 'investment', 'retirement'],
                'patterns': ['savings', 'investment', 'transfer']
            },
            'miscellaneous': {
                'keywords': ['atm', 'fee', 'charge', 'misc', 'other'],
                'patterns': ['fee', 'charge', 'other']
            }
        }
        
        # Indian-specific categories and terms
        self.indian_categories = {
            'festival_expenses': {
                'keywords': ['diwali', 'holi', 'eid', 'christmas', 'pongal', 'durga puja', 'festival'],
                'patterns': ['festival', 'celebration', 'religious']
            },
            'gold_jewelry': {
                'keywords': ['gold', 'jewelry', 'ornaments', 'tanishq', 'kalyan'],
                'patterns': ['gold', 'jewelry', 'ornament']
            },
            'domestic_help': {
                'keywords': ['maid', 'cook', 'driver', 'domestic help', 'household help'],
                'patterns': ['domestic', 'household', 'help']
            }
        }
    
    async def analyze_budget(
        self,
        transactions: List[Dict],
        user_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Analyze budget from transaction data"""
        try:
            if not transactions:
                return self._empty_analysis()
            
            # Convert to DataFrame
            df = pd.DataFrame(transactions)
            df['date'] = pd.to_datetime(df['date'])
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
            
            # Remove invalid transactions
            df = df.dropna(subset=['amount', 'date'])
            
            if len(df) == 0:
                return self._empty_analysis()
            
            # Categorize transactions
            df['category'] = df['description'].apply(self._categorize_transaction)
            
            # Calculate analysis
            analysis = await self._perform_analysis(df, user_context)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Budget analysis failed: {e}")
            return self._empty_analysis()
    
    def _categorize_transaction(self, description: str) -> str:
        """Categorize a single transaction"""
        if pd.isna(description):
            return 'miscellaneous'
        
        description_lower = description.lower()
        
        # Check all categories
        all_categories = {**self.categories, **self.indian_categories}
        
        for category, config in all_categories.items():
            keywords = config.get('keywords', [])
            patterns = config.get('patterns', [])
            
            # Check keywords
            if any(keyword in description_lower for keyword in keywords):
                return category
            
            # Check patterns
            if any(pattern in description_lower for pattern in patterns):
                return category
        
        return 'miscellaneous'
    
    async def _perform_analysis(self, df: pd.DataFrame, user_context: Optional[Dict]) -> Dict[str, Any]:
        """Perform comprehensive budget analysis"""
        
        # Basic aggregations
        df['amount_abs'] = df['amount'].abs()
        categories = df.groupby('category')['amount_abs'].sum().to_dict()
        
        # Time-based analysis
        date_range = (df['date'].max() - df['date'].min()).days
        total_spending = df['amount_abs'].sum()
        avg_daily = total_spending / max(1, date_range)
        
        # Transaction frequency
        transaction_count = len(df)
        avg_transaction = total_spending / transaction_count if transaction_count > 0 else 0
        
        # Find anomalies
        anomalies = self._find_anomalies(df)
        
        # Generate insights
        insights = self._generate_insights(df, categories)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(df, categories, user_context)
        
        # Monthly projections
        monthly_estimate = avg_daily * 30
        
        # Top merchants
        top_merchants = df.groupby('description')['amount_abs'].sum().sort_values(ascending=False).head(10)
        
        return {
            "summary": {
                "total_spending": float(total_spending),
                "transaction_count": transaction_count,
                "avg_transaction": float(avg_transaction),
                "avg_daily_spending": float(avg_daily),
                "monthly_estimate": float(monthly_estimate),
                "analysis_period_days": date_range,
                "top_category": max(categories, key=categories.get) if categories else 'none'
            },
            "categories": {k: float(v) for k, v in categories.items()},
            "anomalies": anomalies,
            "insights": insights,
            "recommendations": recommendations,
            "top_merchants": {k: float(v) for k, v in top_merchants.to_dict().items()},
            "trends": self._calculate_trends(df)
        }
    
    def _find_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Find unusual transactions"""
        anomalies = []
        
        try:
            for category in df['category'].unique():
                cat_data = df[df['category'] == category]['amount_abs']
                
                if len(cat_data) > 2:
                    mean = cat_data.mean()
                    std = cat_data.std()
                    threshold = mean + (2 * std)
                    
                    outliers = df[
                        (df['category'] == category) & 
                        (df['amount_abs'] > threshold)
                    ]
                    
                    for _, row in outliers.iterrows():
                        anomalies.append({
                            'date': row['date'].strftime('%Y-%m-%d'),
                            'description': row['description'],
                            'amount': float(row['amount_abs']),
                            'category': category,
                            'reason': f'Unusually high for {category} (avg: ${mean:.2f})',
                            'deviation': float((row['amount_abs'] - mean) / std) if std > 0 else 0
                        })
        
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
        
        return sorted(anomalies, key=lambda x: x['deviation'], reverse=True)[:10]
    
    def _generate_insights(self, df: pd.DataFrame, categories: Dict[str, float]) -> List[Dict[str, Any]]:
        """Generate budget insights with evidence"""
        insights = []
        total_spending = df['amount_abs'].sum()
        
        try:
            # Top spending categories
            sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
            
            for category, amount in sorted_categories[:5]:
                percentage = (amount / total_spending) * 100 if total_spending > 0 else 0
                cat_data = df[df['category'] == category]
                
                insight = {
                    'title': f'${amount:.2f} spent on {category.replace("_", " ").title()}',
                    'description': f'This represents {percentage:.1f}% of your total spending',
                    'category': category,
                    'amount': float(amount),
                    'percentage': float(percentage),
                    'evidence': {
                        'transaction_count': len(cat_data),
                        'avg_transaction': float(amount / len(cat_data)) if len(cat_data) > 0 else 0,
                        'top_merchants': cat_data.groupby('description')['amount_abs'].sum().head(3).to_dict()
                    },
                    'type': 'spending_category'
                }
                insights.append(insight)
            
            # Frequency insights
            if 'dining' in categories and categories['dining'] > total_spending * 0.15:
                dining_data = df[df['category'] == 'dining']
                insights.append({
                    'title': 'High Dining Out Frequency',
                    'description': f'You dined out {len(dining_data)} times, spending ${categories["dining"]:.2f}',
                    'category': 'dining',
                    'amount': float(categories['dining']),
                    'evidence': {
                        'frequency': len(dining_data),
                        'avg_meal_cost': float(categories['dining'] / len(dining_data)) if len(dining_data) > 0 else 0
                    },
                    'type': 'frequency_alert'
                })
            
            # Subscription insights
            subscription_transactions = df[df['category'] == 'subscriptions']
            if len(subscription_transactions) > 3:
                insights.append({
                    'title': 'Multiple Subscriptions Detected',
                    'description': f'{len(subscription_transactions)} subscription charges found',
                    'category': 'subscriptions',
                    'amount': float(categories.get('subscriptions', 0)),
                    'evidence': {
                        'subscription_count': len(subscription_transactions),
                        'services': list(subscription_transactions['description'].unique())
                    },
                    'type': 'subscription_alert'
                })
        
        except Exception as e:
            logger.error(f"Insight generation failed: {e}")
        
        return insights
    
    def _generate_recommendations(
        self, 
        df: pd.DataFrame, 
        categories: Dict[str, float], 
        user_context: Optional[Dict]
    ) -> List[Dict[str, Any]]:
        """Generate actionable recommendations"""
        recommendations = []
        total_spending = df['amount_abs'].sum()
        
        try:
            # Category-specific recommendations
            if categories.get('dining', 0) > total_spending * 0.2:
                dining_count = len(df[df['category'] == 'dining'])
                avg_meal = categories['dining'] / dining_count if dining_count > 0 else 0
                
                recommendations.append({
                    'title': 'Reduce Dining Out',
                    'description': 'Your dining expenses are high relative to total spending',
                    'action': f'Try cooking at home more often. You could save ~${categories["dining"] * 0.3:.2f} monthly',
                    'category': 'dining',
                    'potential_savings': float(categories['dining'] * 0.3),
                    'priority': 'high',
                    'type': 'spending_reduction'
                })
            
            if categories.get('subscriptions', 0) > 0:
                sub_count = len(df[df['category'] == 'subscriptions'])
                if sub_count > 2:
                    recommendations.append({
                        'title': 'Review Subscriptions',
                        'description': f'You have {sub_count} active subscriptions',
                        'action': 'Cancel unused subscriptions to save money monthly',
                        'category': 'subscriptions',
                        'potential_savings': float(categories['subscriptions'] * 0.4),
                        'priority': 'medium',
                        'type': 'subscription_optimization'
                    })
            
            # Emergency fund recommendation
            monthly_expenses = total_spending * (30 / max(1, (df['date'].max() - df['date'].min()).days))
            if monthly_expenses > 0:
                recommendations.append({
                    'title': 'Build Emergency Fund',
                    'description': f'Aim for 3-6 months of expenses (${monthly_expenses * 3:.2f} - ${monthly_expenses * 6:.2f})',
                    'action': f'Start saving ${monthly_expenses * 0.1:.2f} monthly for emergencies',
                    'category': 'savings',
                    'target_amount': float(monthly_expenses * 3),
                    'monthly_savings_needed': float(monthly_expenses * 0.1),
                    'priority': 'high',
                    'type': 'savings_goal'
                })
            
            # Persona-specific recommendations
            if user_context and user_context.get('persona') == 'family':
                if categories.get('childcare', 0) > 0:
                    recommendations.append({
                        'title': 'Childcare Tax Benefits',
                        'description': 'You may be eligible for childcare tax credits',
                        'action': 'Consult a tax professional about dependent care FSA or tax credits',
                        'category': 'childcare',
                        'priority': 'medium',
                        'type': 'tax_optimization'
                    })
            
        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
        
        return recommendations
    
    def _calculate_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate spending trends"""
        try:
            # Daily spending trend
            daily_spending = df.groupby(df['date'].dt.date)['amount_abs'].sum()
            
            # Weekly comparison
            df['week'] = df['date'].dt.isocalendar().week
            weekly_spending = df.groupby('week')['amount_abs'].sum()
            
            # Month-over-month if data spans multiple months
            df['month'] = df['date'].dt.to_period('M')
            monthly_spending = df.groupby('month')['amount_abs'].sum()
            
            return {
                'daily_average': float(daily_spending.mean()) if len(daily_spending) > 0 else 0,
                'weekly_trend': 'increasing' if len(weekly_spending) > 1 and weekly_spending.iloc[-1] > weekly_spending.iloc[0] else 'stable',
                'spending_velocity': float(daily_spending.std()) if len(daily_spending) > 1 else 0,
                'peak_spending_day': daily_spending.idxmax().strftime('%A') if len(daily_spending) > 0 else 'Unknown',
                'monthly_growth': float((monthly_spending.pct_change().mean() * 100)) if len(monthly_spending) > 1 else 0
            }
            
        except Exception as e:
            logger.error(f"Trend calculation failed: {e}")
            return {'daily_average': 0, 'weekly_trend': 'stable', 'spending_velocity': 0}
    
    def _empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis structure"""
        return {
            "summary": {
                "total_spending": 0.0,
                "transaction_count": 0,
                "avg_transaction": 0.0,
                "avg_daily_spending": 0.0,
                "monthly_estimate": 0.0,
                "analysis_period_days": 0,
                "top_category": 'none'
            },
            "categories": {},
            "anomalies": [],
            "insights": [],
            "recommendations": [],
            "top_merchants": {},
            "trends": {}
        }

# Global instance
budget_analyzer = BudgetAnalyzer()

