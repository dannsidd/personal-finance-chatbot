import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import logging
from utils.api_client import APIError
from utils.helpers import (
    format_currency, format_date, format_duration,
    display_error_message, display_success_message, get_financial_emoji
)

logger = logging.getLogger(__name__)

def render_goals():
    """Render goal planning interface"""
    st.markdown("### 🎯 Goal Planner")
    
    # Initialize goals in session state
    if 'goals' not in st.session_state:
        st.session_state.goals = []
    
    # Check if we have a goal plan
    if 'goal_plan' in st.session_state and st.session_state.goal_plan:
        display_goal_plan(st.session_state.goal_plan)
    else:
        render_goal_input_interface()

def render_goal_input_interface():
    """Render goal input interface"""
    st.markdown("""
    <div style='text-align: center; padding: 2rem; background: #E8F5E8; border-radius: 10px; margin: 1rem 0;'>
        <h3 style='color: #2E8B57; margin-bottom: 1rem;'>🎯 Plan Your Financial Future</h3>
        <p style='color: #666; margin-bottom: 2rem;'>Set your financial goals and create a roadmap to achieve them</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Financial overview section
    render_financial_overview_input()
    
    # Goals management section
    render_goals_input_form()
    
    if st.session_state.goals:
        render_current_goals_summary()
        render_goal_analysis_button()

def render_financial_overview_input():
    """Render financial overview input"""
    st.markdown("#### 💰 Monthly Financial Overview")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        monthly_income = st.number_input(
            "💵 Monthly Income ($)",
            min_value=0.0,
            step=100.0,
            value=5000.0 if 'monthly_income' not in st.session_state else st.session_state.monthly_income,
            help="After-tax take-home pay",
            key="monthly_income"
        )
    
    with col2:
        monthly_expenses = st.number_input(
            "💸 Monthly Expenses ($)",
            min_value=0.0,
            step=100.0,
            value=3500.0 if 'monthly_expenses' not in st.session_state else st.session_state.monthly_expenses,
            help="Total fixed + variable expenses",
            key="monthly_expenses"
        )
    
    with col3:
        available = monthly_income - monthly_expenses
        color = "normal" if available > 0 else "inverse"
        delta_text = "Available for goals" if available > 0 else "⚠️ Budget deficit"
        
        st.metric(
            "💰 Available Monthly",
            format_currency(available),
            delta=delta_text,
            delta_color=color
        )
    
    if available <= 0:
        st.error("⚠️ Your expenses exceed your income. Consider expense reduction or increasing income before setting savings goals.")
        return False
    
    return True

def render_goals_input_form():
    """Render goals input form"""
    st.markdown("#### 🎯 Add Your Financial Goals")
    
    with st.expander("Add New Goal", expanded=len(st.session_state.goals) == 0):
        with st.form("add_goal_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                goal_name = st.text_input(
                    "Goal Name *",
                    placeholder="e.g., Emergency Fund, Vacation, New Car",
                    help="Give your goal a specific, meaningful name"
                )
                
                target_amount = st.number_input(
                    "Target Amount ($) *",
                    min_value=1.0,
                    step=100.0,
                    format="%.2f",
                    help="How much money do you need?"
                )
            
            with col2:
                timeline_months = st.number_input(
                    "Timeline (months) *",
                    min_value=1,
                    max_value=600,  # 50 years max
                    value=12,
                    step=1,
                    help="When do you want to achieve this goal?"
                )
                
                priority = st.slider(
                    "Priority (1=highest)",
                    min_value=1,
                    max_value=10,
                    value=3,
                    help="How important is this goal relative to others?"
                )
            
            # Goal category selection
            goal_category = st.selectbox(
                "Goal Category",
                options=[
                    'emergency_fund', 'debt_payoff', 'major_purchase', 
                    'vacation', 'education', 'retirement', 'investment', 'other'
                ],
                format_func=lambda x: {
                    'emergency_fund': '🚨 Emergency Fund',
                    'debt_payoff': '💳 Debt Payoff',
                    'major_purchase': '🏠 Major Purchase',
                    'vacation': '✈️ Vacation/Travel',
                    'education': '🎓 Education',
                    'retirement': '🏖️ Retirement',
                    'investment': '📈 Investment',
                    'other': '📦 Other'
                }[x],
                help="What type of goal is this?"
            )
            
            # Goal description
            goal_description = st.text_area(
                "Description (optional)",
                placeholder="Add more details about your goal...",
                height=60
            )
            
            submitted = st.form_submit_button("🎯 Add Goal", type="primary", use_container_width=True)
            
            if submitted:
                add_goal_to_list(goal_name, target_amount, timeline_months, priority, goal_category, goal_description)

def add_goal_to_list(name, target_amount, timeline_months, priority, category, description):
    """Add goal to the session state list"""
    # Validation
    if not name.strip():
        display_error_message("Goal name is required")
        return
    
    if target_amount <= 0:
        display_error_message("Target amount must be greater than 0")
        return
    
    if timeline_months <= 0:
        display_error_message("Timeline must be at least 1 month")
        return
    
    # Check for duplicate names
    if any(goal['name'].lower() == name.strip().lower() for goal in st.session_state.goals):
        display_error_message("A goal with this name already exists")
        return
    
    # Calculate monthly requirement
    monthly_required = target_amount / timeline_months
    
    # Add goal
    new_goal = {
        'name': name.strip(),
        'target_amount': float(target_amount),
        'timeline_months': int(timeline_months),
        'priority': int(priority),
        'category': category,
        'description': description.strip(),
        'monthly_required': monthly_required,
        'id': len(st.session_state.goals)
    }
    
    st.session_state.goals.append(new_goal)
    display_success_message(f"Added goal: {name}")
    st.rerun()

def render_current_goals_summary():
    """Render current goals summary"""
    st.markdown("#### 📋 Your Financial Goals")
    
    # Summary metrics
    total_target = sum(goal['target_amount'] for goal in st.session_state.goals)
    total_monthly_needed = sum(goal['monthly_required'] for goal in st.session_state.goals)
    available_monthly = st.session_state.monthly_income - st.session_state.monthly_expenses
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🎯 Total Targets", format_currency(total_target))
    
    with col2:
        st.metric("📅 Monthly Needed", format_currency(total_monthly_needed))
    
    with col3:
        feasible = "✅ Feasible" if total_monthly_needed <= available_monthly else "⚠️ Over Budget"
        over_budget = total_monthly_needed - available_monthly if total_monthly_needed > available_monthly else 0
        delta_text = f"Over by {format_currency(over_budget)}" if over_budget > 0 else "Within budget"
        
        st.metric("💡 Feasibility", feasible, delta=delta_text)
    
    # Goals list with progress indicators
    for i, goal in enumerate(st.session_state.goals):
        render_goal_card(goal, i, available_monthly)
    
    # Quick actions
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📋 Load Sample Goals", use_container_width=True):
            load_sample_goals()
    
    with col2:
        if st.button("🗑️ Clear All Goals", use_container_width=True):
            st.session_state.goals = []
            if 'goal_plan' in st.session_state:
                del st.session_state.goal_plan
            st.rerun()

def render_goal_card(goal, index, available_monthly):
    """Render individual goal card"""
    emoji = get_financial_emoji(goal['category'])
    
    with st.container():
        # Goal header
        col1, col2, col3, col4, col5, col6 = st.columns([2, 1, 1, 1, 1, 0.5])
        
        with col1:
            st.markdown(f"**{emoji} {goal['name']}**")
            if goal['description']:
                st.caption(goal['description'])
        
        with col2:
            st.write(format_currency(goal['target_amount']))
        
        with col3:
            st.write(format_currency(goal['monthly_required']))
        
        with col4:
            st.write(format_duration(goal['timeline_months']))
        
        with col5:
            priority_colors = {1: "🔴", 2: "🟠", 3: "🟡", 4: "🟢"}
            priority_color = priority_colors.get(min(goal['priority'], 4), "⚪")
            st.write(f"{priority_color} {goal['priority']}")
        
        with col6:
            if st.button("🗑️", key=f"delete_goal_{index}", help="Delete goal"):
                st.session_state.goals.pop(index)
                st.rerun()
        
        # Feasibility indicator
        is_feasible = goal['monthly_required'] <= available_monthly
        feasibility_color = "🟢" if is_feasible else "🔴"
        feasibility_text = "Feasible" if is_feasible else "Needs adjustment"
        
        col1, col2 = st.columns([3, 1])
        with col1:
            # Progress bar (mock progress for demonstration)
            progress = min(0.1, (goal['monthly_required'] / available_monthly) if available_monthly > 0 else 0)
            st.progress(progress)
        with col2:
            st.caption(f"{feasibility_color} {feasibility_text}")

def render_goal_analysis_button():
    """Render goal analysis button"""
    st.markdown("#### 🧮 Goal Analysis")
    
    if st.button("📊 Analyze Goal Feasibility", type="primary", use_container_width=True):
        analyze_goals()

def analyze_goals():
    """Analyze goal feasibility"""
    if not st.session_state.goals:
        display_error_message("Please add at least one goal")
        return
    
    monthly_income = st.session_state.get('monthly_income', 0)
    monthly_expenses = st.session_state.get('monthly_expenses', 0)
    
    if monthly_income <= 0:
        display_error_message("Please enter your monthly income")
        return
    
    try:
        with st.spinner("🧮 Analyzing your goals..."):
            # Prepare goal data for API
            goal_data = []
            for goal in st.session_state.goals:
                goal_data.append({
                    'name': goal['name'],
                    'target_amount': goal['target_amount'],
                    'timeline_months': goal['timeline_months'],
                    'priority': goal['priority'],
                    'category': goal.get('category', 'other')
                })
            
            # Call API or use offline calculation
            if st.session_state.api_client:
                request_data = {
                    'monthly_income': monthly_income,
                    'monthly_expenses': monthly_expenses,
                    'goals': goal_data
                }
                
                result = st.session_state.api_client.create_goal_plan(request_data)
                st.session_state.goal_plan = result
                
                display_success_message(
                    "Goals analyzed!",
                    f"Analyzed {len(goal_data)} goals with optimization recommendations"
                )
            else:
                # Offline calculation
                st.session_state.goal_plan = calculate_offline_goal_plan(
                    monthly_income, monthly_expenses, goal_data
                )
                display_success_message("Goals analyzed!", "Using offline calculation")
            
            st.rerun()
            
    except APIError as e:
        display_error_message("Goal analysis failed", e.message)
    except Exception as e:
        logger.error(f"Goal analysis error: {e}")
        display_error_message("Analysis failed", str(e))

def display_goal_plan(plan):
    """Display comprehensive goal plan"""
    financial_overview = plan.get('financial_overview', {})
    goal_analysis = plan.get('goal_analysis', {})
    individual_goals = plan.get('individual_goals', {})
    optimized_plan = plan.get('optimized_plan', {})
    insights = plan.get('insights', [])
    recommendations = plan.get('recommendations', [])
    milestones = plan.get('milestones', [])
    action_plan = plan.get('action_plan', {})
    
    # Header with key metrics
    render_goal_plan_summary(financial_overview, goal_analysis)
    
    # Main sections
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_individual_goal_analysis(individual_goals)
        render_goal_allocation_chart(optimized_plan)
    
    with col2:
        render_goal_insights(insights)
        render_goal_recommendations(recommendations)
    
    # Additional sections
    if milestones:
        render_goal_milestones(milestones)
    
    if action_plan:
        render_action_plan(action_plan)
    
    # Action buttons
    render_goal_plan_actions(plan)

def render_goal_plan_summary(financial_overview, goal_analysis):
    """Render goal plan summary"""
    st.markdown("### 🎯 Your Goal Achievement Plan")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        available = financial_overview.get('available_monthly', 0)
        st.metric(
            "💰 Available Monthly",
            format_currency(available),
            delta=f"{financial_overview.get('savings_rate', 0):.1f}% savings rate"
        )
    
    with col2:
        total_goals = goal_analysis.get('total_goals', 0)
        feasibility_score = goal_analysis.get('feasibility_score', 0)
        st.metric(
            "🎯 Total Goals",
            f"{total_goals}",
            delta=f"{feasibility_score:.0f}% feasible"
        )
    
    with col3:
        total_target = goal_analysis.get('total_target_amount', 0)
        st.metric(
            "💎 Target Amount",
            format_currency(total_target),
            delta="All goals combined"
        )
    
    with col4:
        monthly_required = goal_analysis.get('total_monthly_required', 0)
        available_monthly = financial_overview.get('available_monthly', 0)
        over_under = monthly_required - available_monthly
        delta_text = f"Over by ${abs(over_under):.2f}" if over_under > 0 else f"Under by ${abs(over_under):.2f}"
        
        st.metric(
            "📅 Monthly Required",
            format_currency(monthly_required),
            delta=delta_text,
            delta_color="inverse" if over_under > 0 else "normal"
        )

def render_individual_goal_analysis(individual_goals):
    """Render individual goal analysis"""
    st.markdown("#### 📊 Individual Goal Analysis")
    
    if not individual_goals:
        st.info("No individual goal analysis available")
        return
    
    # Create DataFrame for display
    goal_data = []
    for goal_id, analysis in individual_goals.items():
        goal_data.append({
            'Goal': analysis.get('goal_name', ''),
            'Target': format_currency(analysis.get('target_amount', 0)),
            'Requested Timeline': f"{analysis.get('requested_timeline', 0)} months",
            'Realistic Timeline': format_duration(analysis.get('realistic_timeline', 0)),
            'Monthly Required': format_currency(analysis.get('monthly_required', 0)),
            'Feasible': '✅' if analysis.get('is_feasible', False) else '⚠️',
            'Status': 'On Track' if analysis.get('is_feasible', False) else 'Needs Adjustment'
        })
    
    if goal_data:
        df = pd.DataFrame(goal_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

def render_goal_allocation_chart(optimized_plan):
    """Render goal allocation visualization"""
    st.markdown("#### 🥧 Optimized Monthly Allocation")
    
    allocations = optimized_plan.get('allocations', {})
    
    if not allocations:
        st.info("No allocation data available")
        return
    
    # Prepare data for pie chart
    labels = []
    values = []
    colors = []
    
    for goal_id, allocation in allocations.items():
        monthly_allocation = allocation.get('monthly_allocation', 0)
        if monthly_allocation > 0:
            labels.append(f"{allocation.get('goal_name', 'Goal')}: ${monthly_allocation:.0f}")
            values.append(monthly_allocation)
    
    # Add remaining budget if any
    remaining_budget = optimized_plan.get('remaining_budget', 0)
    if remaining_budget > 0:
        labels.append(f"Remaining: ${remaining_budget:.0f}")
        values.append(remaining_budget)
    
    if values:
        # Create pie chart
        fig = px.pie(
            values=values,
            names=labels,
            title="Monthly Budget Allocation"
        )
        
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>Amount: $%{value:,.2f}<extra></extra>'
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

def render_goal_insights(insights):
    """Render goal insights"""
    st.markdown("#### 💡 Insights")
    
    if not insights:
        st.info("No specific insights available")
        return
    
    for insight in insights[:3]:  # Show top 3 insights
        title = insight.get('title', 'Insight')
        description = insight.get('description', '')
        insight_type = insight.get('type', 'info')
        action = insight.get('action', '')
        
        # Choose styling based on type
        if insight_type == 'warning':
            st.warning(f"⚠️ **{title}**\n\n{description}")
        elif insight_type == 'opportunity':
            st.success(f"💡 **{title}**\n\n{description}")
        else:
            st.info(f"ℹ️ **{title}**\n\n{description}")
        
        if action:
            st.caption(f"💡 Action: {action}")

def render_goal_recommendations(recommendations):
    """Render goal recommendations"""
    st.markdown("#### 🎯 Recommendations")
    
    if not recommendations:
        st.info("No specific recommendations available")
        return
    
    for rec in recommendations[:3]:  # Show top 3 recommendations
        title = rec.get('title', 'Recommendation')
        description = rec.get('description', '')
        action = rec.get('action', '')
        priority = rec.get('priority', 'medium')
        implementation = rec.get('implementation', '')
        
        # Priority styling
        priority_colors = {
            'high': '🔴',
            'critical': '🚨',
            'medium': '🟡',
            'low': '🟢'
        }
        priority_icon = priority_colors.get(priority, '🟡')
        
        with st.expander(f"{priority_icon} {title}"):
            st.write(description)
            
            if action:
                st.markdown(f"**Action:** {action}")
            
            if implementation:
                st.markdown(f"**How to implement:** {implementation}")

def render_goal_milestones(milestones):
    """Render goal milestones"""
    st.markdown("#### 🏆 Your Achievement Milestones")
    
    # Sort milestones by timeline
    sorted_milestones = sorted(milestones, key=lambda x: x.get('months_from_now', float('inf')))
    
    for milestone in sorted_milestones[:5]:  # Show first 5 milestones
        goal_name = milestone.get('goal_name', '')
        target_date = milestone.get('target_date', '')
        months_from_now = milestone.get('months_from_now', 0)
        monthly_amount = milestone.get('monthly_amount', 0)
        milestone_type = milestone.get('milestone_type', 'completion')
        celebration = milestone.get('celebration_message', '')
        
        # Choose icon based on milestone type
        icons = {
            'completion': '🎯',
            'halfway': '⭐',
            'quarter': '🚀'
        }
        icon = icons.get(milestone_type, '🎯')
        
        with st.expander(f"{icon} {goal_name} - {target_date}"):
            st.write(celebration)
            
            if monthly_amount > 0:
                st.info(f"💰 Monthly contribution: {format_currency(monthly_amount)}")
            
            if months_from_now > 0:
                st.success(f"📅 {months_from_now} months from now")

def render_action_plan(action_plan):
    """Render action plan"""
    st.markdown("#### 📋 Your Action Plan")
    
    # Immediate actions
    immediate = action_plan.get('immediate_actions', [])
    if immediate:
        st.markdown("**🚀 This Week:**")
        for action in immediate:
            st.write(f"• {action}")
    
    # Monthly actions
    monthly = action_plan.get('monthly_actions', [])
    if monthly:
        st.markdown("**📅 Every Month:**")
        for action in monthly:
            st.write(f"• {action}")
    
    # Quarterly actions
    quarterly = action_plan.get('quarterly_actions', [])
    if quarterly:
        st.markdown("**📊 Every Quarter:**")
        for action in quarterly:
            st.write(f"• {action}")
    
    # Success factors
    success_factors = action_plan.get('success_factors', [])
    if success_factors:
        st.markdown("**🏆 Keys to Success:**")
        for factor in success_factors:
            st.write(f"✅ {factor}")

def render_goal_plan_actions(plan):
    """Render goal plan action buttons"""
    st.markdown("---")
    st.markdown("#### 🔧 Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📥 Export Plan", use_container_width=True):
            export_goal_plan(plan)
    
    with col2:
        if st.button("📊 New Plan", use_container_width=True):
            start_new_goal_plan()
    
    with col3:
        if st.button("📅 Set Reminders", use_container_width=True):
            setup_goal_reminders(plan)
    
    with col4:
        if st.button("💰 Track Progress", use_container_width=True):
            setup_goal_tracking(plan)

def load_sample_goals():
    """Load sample goal data"""
    sample_goals = [
        {
            'name': 'Emergency Fund',
            'target_amount': 10000.0,
            'timeline_months': 12,
            'priority': 1,
            'category': 'emergency_fund',
            'description': '6-month expense emergency fund',
            'monthly_required': 833.33,
            'id': 0
        },
        {
            'name': 'Vacation to Europe',
            'target_amount': 5000.0,
            'timeline_months': 8,
            'priority': 3,
            'category': 'vacation',
            'description': '2-week European vacation',
            'monthly_required': 625.0,
            'id': 1
        },
        {
            'name': 'New Laptop',
            'target_amount': 1500.0,
            'timeline_months': 4,
            'priority': 2,
            'category': 'major_purchase',
            'description': 'Work laptop replacement',
            'monthly_required': 375.0,
            'id': 2
        },
        {
            'name': 'House Down Payment',
            'target_amount': 40000.0,
            'timeline_months': 36,
            'priority': 1,
            'category': 'major_purchase',
            'description': '20% down payment for house',
            'monthly_required': 1111.11,
            'id': 3
        }
    ]
    
    st.session_state.goals = sample_goals
    display_success_message("Sample goals loaded!")
    st.rerun()

def calculate_offline_goal_plan(monthly_income, monthly_expenses, goals):
    """Calculate goal plan offline"""
    available_monthly = monthly_income - monthly_expenses
    
    # Simple feasibility calculation
    total_required = sum(goal['target_amount'] / goal['timeline_months'] for goal in goals)
    feasibility_score = min(100, (available_monthly / total_required) * 100) if total_required > 0 else 100
    
    # Mock individual analysis
    individual_goals = {}
    for i, goal in enumerate(goals):
        monthly_required = goal['target_amount'] / goal['timeline_months']
        is_feasible = monthly_required <= available_monthly
        
        individual_goals[f'goal_{i}'] = {
            'goal_name': goal['name'],
            'target_amount': goal['target_amount'],
            'requested_timeline': goal['timeline_months'],
            'monthly_required': monthly_required,
            'is_feasible': is_feasible,
            'realistic_timeline': goal['timeline_months'] if is_feasible else int(goal['target_amount'] / available_monthly * 1.2),
            'affordability_ratio': monthly_required / available_monthly if available_monthly > 0 else float('inf')
        }
    
    # Mock allocation
    allocations = {}
    remaining_budget = available_monthly
    
    for i, goal in enumerate(sorted(goals, key=lambda x: x['priority'])):
        allocation = min(goal['target_amount'] / goal['timeline_months'], remaining_budget * 0.4)
        allocations[f'goal_{i}'] = {
            'goal_name': goal['name'],
            'monthly_allocation': allocation,
            'timeline_months': int(goal['target_amount'] / allocation) if allocation > 0 else float('inf'),
            'priority_rank': goal['priority']
        }
        remaining_budget -= allocation
        if remaining_budget <= 0:
            break
    
    return {
        'financial_overview': {
            'monthly_income': monthly_income,
            'monthly_expenses': monthly_expenses,
            'available_monthly': available_monthly,
            'savings_rate': (available_monthly / monthly_income) * 100 if monthly_income > 0 else 0
        },
        'goal_analysis': {
            'total_goals': len(goals),
            'total_target_amount': sum(goal['target_amount'] for goal in goals),
            'total_monthly_required': total_required,
            'feasibility_score': feasibility_score
        },
        'individual_goals': individual_goals,
        'optimized_plan': {
            'allocations': allocations,
            'total_allocated': available_monthly - remaining_budget,
            'remaining_budget': max(0, remaining_budget)
        },
        'insights': [
            {
                'title': 'Goal Feasibility',
                'description': f'Your goals have a {feasibility_score:.0f}% feasibility score based on available income',
                'type': 'info' if feasibility_score > 80 else 'warning',
                'action': 'Consider adjusting timelines if feasibility is low'
            }
        ],
        'recommendations': [
            {
                'title': 'Automate Your Savings',
                'description': f'Set up automatic transfers for ${available_monthly * 0.8:.2f}/month',
                'action': 'Create automatic transfers on payday to separate goal accounts',
                'priority': 'high',
                'implementation': 'Set up in your banking app or with your employer'
            }
        ],
        'milestones': [
            {
                'goal_name': goals[0]['name'] if goals else 'First Goal',
                'target_date': f"{goals[0]['timeline_months'] if goals else 12} months from now",
                'months_from_now': goals[0]['timeline_months'] if goals else 12,
                'milestone_type': 'completion',
                'celebration_message': f"🎉 Congratulations! You've achieved your {goals[0]['name'] if goals else 'goal'}!"
            }
        ] if goals else [],
        'action_plan': {
            'immediate_actions': [
                'Open separate high-yield savings accounts for each goal',
                'Set up automatic transfers from checking to goal accounts'
            ],
            'monthly_actions': [
                'Review goal progress and adjust if needed',
                'Check account balances and celebrate milestones'
            ],
            'quarterly_actions': [
                'Reassess goal priorities based on life changes',
                'Compare actual vs. planned progress'
            ],
            'success_factors': [
                'Consistency in monthly contributions',
                'Regular progress monitoring',
                'Flexibility to adjust when life changes'
            ]
        }
    }

def export_goal_plan(plan):
    """Export goal plan"""
    try:
        import json
        
        export_data = {
            'export_date': datetime.now().isoformat(),
            'goal_plan': plan,
            'user_info': {
                'persona': st.session_state.persona,
                'language': st.session_state.language
            }
        }
        
        json_str = json.dumps(export_data, indent=2, default=str)
        
        st.download_button(
            label="📥 Download Goal Plan",
            data=json_str,
            file_name=f"goal_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
        
        display_success_message("Goal plan exported!")
        
    except Exception as e:
        logger.error(f"Export failed: {e}")
        display_error_message("Export failed", str(e))

def start_new_goal_plan():
    """Start new goal plan"""
    if 'goal_plan' in st.session_state:
        del st.session_state.goal_plan
    
    display_success_message("Ready for new goal plan!")
    st.rerun()

def setup_goal_reminders(plan):
    """Setup goal reminders"""
    st.info("📅 Reminder setup feature coming soon! For now, set calendar reminders for monthly goal reviews.")

def setup_goal_tracking(plan):
    """Setup goal tracking"""
    st.info("📊 Progress tracking feature coming soon! Export your plan and update it monthly to track progress.")

