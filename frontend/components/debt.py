import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import logging
from utils.api_client import APIError
from utils.helpers import (
    format_currency, format_date, format_duration,
    display_error_message, display_success_message
)

logger = logging.getLogger(__name__)

def render_debt():
    """Render debt management interface"""
    st.markdown("### 💳 Family Debt Navigator")
    
    # Initialize debt list in session state
    if 'debts' not in st.session_state:
        st.session_state.debts = []
    
    # Check if we have a debt plan
    if 'debt_plan' in st.session_state and st.session_state.debt_plan:
        display_debt_plan(st.session_state.debt_plan)
    else:
        render_debt_input_interface()

def render_debt_input_interface():
    """Render debt input interface"""
    st.markdown("""
    <div style='text-align: center; padding: 2rem; background: #FFF3E0; border-radius: 10px; margin: 1rem 0;'>
        <h3 style='color: #E65100; margin-bottom: 1rem;'>💳 Plan Your Debt Freedom</h3>
        <p style='color: #666; margin-bottom: 2rem;'>Add your debts to create a personalized payoff strategy</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Debt management sections
    render_debt_input_form()
    
    if st.session_state.debts:
        render_current_debts_summary()
        render_debt_strategy_selection()

def render_debt_input_form():
    """Render debt input form"""
    st.markdown("#### ➕ Add Your Debts")
    
    with st.expander("Add New Debt", expanded=len(st.session_state.debts) == 0):
        with st.form("add_debt_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                debt_name = st.text_input(
                    "Debt Name *",
                    placeholder="e.g., Credit Card, Car Loan, Student Loan",
                    help="Give your debt a recognizable name"
                )
                
                balance = st.number_input(
                    "Current Balance ($) *",
                    min_value=0.01,
                    step=100.0,
                    format="%.2f",
                    help="How much do you currently owe?"
                )
            
            with col2:
                apr = st.number_input(
                    "Annual Interest Rate (%) *",
                    min_value=0.0,
                    max_value=50.0,
                    step=0.1,
                    format="%.2f",
                    help="Your debt's annual percentage rate"
                )
                
                minimum_payment = st.number_input(
                    "Minimum Monthly Payment ($) *",
                    min_value=0.01,
                    step=10.0,
                    format="%.2f",
                    help="Required minimum payment each month"
                )
            
            # Debt type selection for better categorization
            debt_type = st.selectbox(
                "Debt Type",
                options=['credit_card', 'student_loan', 'car_loan', 'mortgage', 'personal_loan', 'other'],
                format_func=lambda x: {
                    'credit_card': '💳 Credit Card',
                    'student_loan': '🎓 Student Loan',
                    'car_loan': '🚗 Car Loan',
                    'mortgage': '🏠 Mortgage',
                    'personal_loan': '📄 Personal Loan',
                    'other': '📋 Other'
                }[x]
            )
            
            submitted = st.form_submit_button("➕ Add Debt", type="primary", use_container_width=True)
            
            if submitted:
                add_debt_to_list(debt_name, balance, apr, minimum_payment, debt_type)

def add_debt_to_list(name, balance, apr, minimum_payment, debt_type):
    """Add debt to the session state list"""
    # Validation
    if not name.strip():
        display_error_message("Debt name is required")
        return
    
    if balance <= 0:
        display_error_message("Balance must be greater than 0")
        return
    
    if minimum_payment <= 0:
        display_error_message("Minimum payment must be greater than 0")
        return
    
    if minimum_payment > balance:
        display_error_message("Minimum payment cannot exceed balance")
        return
    
    # Check for duplicate names
    if any(debt['name'].lower() == name.strip().lower() for debt in st.session_state.debts):
        display_error_message("A debt with this name already exists")
        return
    
    # Add debt
    new_debt = {
        'name': name.strip(),
        'balance': float(balance),
        'apr': float(apr),
        'minimum_payment': float(minimum_payment),
        'debt_type': debt_type,
        'id': len(st.session_state.debts)
    }
    
    st.session_state.debts.append(new_debt)
    display_success_message(f"Added {name} to your debt list!")
    st.rerun()

def render_current_debts_summary():
    """Render current debts summary"""
    st.markdown("#### 📋 Your Current Debts")
    
    # Summary metrics
    total_balance = sum(debt['balance'] for debt in st.session_state.debts)
    total_minimum = sum(debt['minimum_payment'] for debt in st.session_state.debts)
    weighted_apr = sum(debt['balance'] * debt['apr'] for debt in st.session_state.debts) / total_balance if total_balance > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("💰 Total Debt", format_currency(total_balance))
    
    with col2:
        st.metric("📅 Monthly Minimums", format_currency(total_minimum))
    
    with col3:
        st.metric("📊 Weighted Avg APR", f"{weighted_apr:.1f}%")
    
    # Debt list with actions
    for i, debt in enumerate(st.session_state.debts):
        with st.container():
            col1, col2, col3, col4, col5, col6 = st.columns([2, 1, 1, 1, 1, 0.5])
            
            # Debt type emoji
            debt_emojis = {
                'credit_card': '💳',
                'student_loan': '🎓',
                'car_loan': '🚗',
                'mortgage': '🏠',
                'personal_loan': '📄',
                'other': '📋'
            }
            emoji = debt_emojis.get(debt['debt_type'], '📋')
            
            with col1:
                st.markdown(f"**{emoji} {debt['name']}**")
            
            with col2:
                st.write(format_currency(debt['balance']))
            
            with col3:
                st.write(f"{debt['apr']:.1f}%")
            
            with col4:
                st.write(format_currency(debt['minimum_payment']))
            
            with col5:
                # Calculate months to payoff with minimum payment
                if debt['apr'] > 0:
                    monthly_rate = debt['apr'] / 100 / 12
                    if debt['minimum_payment'] > debt['balance'] * monthly_rate:
                        import math
                        months = math.ceil(-math.log(1 - (debt['balance'] * monthly_rate) / debt['minimum_payment']) / math.log(1 + monthly_rate))
                        st.write(format_duration(months))
                    else:
                        st.write("Never")
                else:
                    months = math.ceil(debt['balance'] / debt['minimum_payment'])
                    st.write(format_duration(months))
            
            with col6:
                if st.button("🗑️", key=f"delete_debt_{i}", help="Delete debt"):
                    st.session_state.debts.pop(i)
                    st.rerun()
    
    # Quick actions
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📋 Load Sample Debts", use_container_width=True):
            load_sample_debts()
    
    with col2:
        if st.button("🗑️ Clear All Debts", use_container_width=True):
            st.session_state.debts = []
            if 'debt_plan' in st.session_state:
                del st.session_state.debt_plan
            st.rerun()

def render_debt_strategy_selection():
    """Render debt strategy selection and calculation"""
    st.markdown("#### 🎯 Choose Your Payoff Strategy")
    
    col1, col2 = st.columns(2)
    
    with col1:
        extra_payment = st.number_input(
            "💰 Extra Monthly Payment ($)",
            min_value=0.0,
            step=25.0,
            value=100.0,
            help="Additional amount you can pay beyond minimums"
        )
    
    with col2:
        strategy = st.selectbox(
            "🗂️ Payoff Strategy",
            options=['avalanche', 'snowball', 'hybrid'],
            format_func=lambda x: {
                'avalanche': '🏔️ Avalanche (Highest APR first)',
                'snowball': '❄️ Snowball (Lowest balance first)',
                'hybrid': '⚖️ Hybrid (Balanced approach)'
            }[x],
            help="Choose your debt elimination strategy"
        )
    
    # Strategy explanation
    strategy_explanations = {
        'avalanche': {
            'description': 'Pay minimums on all debts, put extra toward highest APR debt first.',
            'pros': ['Saves the most money on interest', 'Mathematically optimal'],
            'cons': ['May take longer to see first debt eliminated', 'Less motivating for some people'],
            'best_for': 'People focused on saving money and comfortable with long-term planning'
        },
        'snowball': {
            'description': 'Pay minimums on all debts, put extra toward smallest balance first.',
            'pros': ['Quick wins build motivation', 'Simplifies finances faster'],
            'cons': ['May cost more in interest', 'Not mathematically optimal'],
            'best_for': 'People who need motivation and prefer psychological wins'
        },
        'hybrid': {
            'description': 'Balance between interest rates and balances for a middle-ground approach.',
            'pros': ['Good balance of savings and motivation', 'Flexible approach'],
            'cons': ['Compromise solution', 'More complex to execute'],
            'best_for': 'People who want balance between savings and motivation'
        }
    }
    
    with st.expander(f"ℹ️ About {strategy.title()} Strategy"):
        info = strategy_explanations[strategy]
        st.write(f"**How it works:** {info['description']}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**✅ Pros:**")
            for pro in info['pros']:
                st.write(f"• {pro}")
        
        with col2:
            st.write("**⚠️ Cons:**")
            for con in info['cons']:
                st.write(f"• {con}")
        
        st.info(f"**Best for:** {info['best_for']}")
    
    # Calculate button
    if st.button("📊 Calculate Debt Payoff Plan", type="primary", use_container_width=True):
        calculate_debt_plan(extra_payment, strategy)

def calculate_debt_plan(extra_payment, strategy):
    """Calculate debt payoff plan"""
    if not st.session_state.debts:
        display_error_message("Please add at least one debt")
        return
    
    try:
        with st.spinner("📊 Calculating your debt freedom plan..."):
            # Prepare debt data for API
            debt_data = []
            for debt in st.session_state.debts:
                debt_data.append({
                    'name': debt['name'],
                    'balance': debt['balance'],
                    'apr': debt['apr'],
                    'minimum_payment': debt['minimum_payment']
                })
            
            # Call API or use offline calculation
            if st.session_state.api_client:
                request_data = {
                    'debts': debt_data,
                    'extra_payment': extra_payment,
                    'strategy': strategy
                }
                
                result = st.session_state.api_client.create_debt_plan(request_data)
                st.session_state.debt_plan = result
                
                display_success_message(
                    "Debt plan calculated!",
                    f"Using {strategy} strategy with ${extra_payment:.2f} extra payment"
                )
            else:
                # Offline calculation
                st.session_state.debt_plan = calculate_offline_debt_plan(debt_data, extra_payment, strategy)
                display_success_message("Debt plan calculated!", "Using offline calculation")
            
            st.rerun()
            
    except APIError as e:
        display_error_message("Debt planning failed", e.message)
    except Exception as e:
        logger.error(f"Debt planning error: {e}")
        display_error_message("Calculation failed", str(e))

def display_debt_plan(plan):
    """Display comprehensive debt plan"""
    summary = plan.get('summary', {})
    savings = plan.get('savings', {})
    payoff_plan = plan.get('payoff_plan', [])
    insights = plan.get('insights', [])
    recommendations = plan.get('recommendations', [])
    next_action = plan.get('next_action', '')
    milestones = plan.get('milestones', [])
    
    # Header with key results
    render_debt_plan_summary(summary, savings)
    
    # Main sections
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_payoff_schedule(payoff_plan)
        render_debt_timeline_chart(payoff_plan)
    
    with col2:
        render_debt_insights(insights)
        render_debt_recommendations(recommendations)
    
    # Milestones and next steps
    if milestones:
        render_debt_milestones(milestones)
    
    if next_action:
        render_next_action(next_action)
    
    # Action buttons
    render_debt_plan_actions(plan)

def render_debt_plan_summary(summary, savings):
    """Render debt plan summary metrics"""
    st.markdown("### 🎉 Your Debt Freedom Plan")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "💰 Interest Saved",
            format_currency(savings.get('interest_saved', 0)),
            delta="vs minimum payments"
        )
    
    with col2:
        st.metric(
            "⏰ Time Saved",
            f"{savings.get('months_saved', 0)} months",
            delta="faster payoff"
        )
    
    with col3:
        total_debt = summary.get('total_debt', 0)
        st.metric(
            "💳 Total Debt",
            format_currency(total_debt),
            delta=f"{summary.get('debt_count', 0)} debts"
        )
    
    with col4:
        monthly_payment = summary.get('total_monthly_payment', 0)
        st.metric(
            "📅 Monthly Payment",
            format_currency(monthly_payment),
            delta=f"${summary.get('extra_payment', 0):.2f} extra"
        )

def render_payoff_schedule(payoff_plan):
    """Render detailed payoff schedule"""
    st.markdown("#### 📋 Payoff Schedule")
    
    if not payoff_plan:
        st.info("No payoff schedule available")
        return
    
    # Create DataFrame for display
    schedule_data = []
    for debt in payoff_plan:
        schedule_data.append({
            'Debt': debt.get('debt_name', ''),
            'Balance': format_currency(debt.get('balance', 0)),
            'Monthly Payment': format_currency(debt.get('monthly_payment', 0)),
            'Payoff Time': format_duration(debt.get('months_to_payoff', 0)),
            'Total Interest': format_currency(debt.get('total_interest', 0)),
            'Priority': debt.get('payoff_order', 0)
        })
    
    df = pd.DataFrame(schedule_data)
    
    # Style the dataframe
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

def render_debt_timeline_chart(payoff_plan):
    """Render debt payoff timeline visualization"""
    st.markdown("#### 📊 Payoff Timeline")
    
    if not payoff_plan:
        return
    
    # Prepare data for chart
    debt_names = [debt.get('debt_name', '') for debt in payoff_plan]
    months_to_payoff = [debt.get('months_to_payoff', 0) for debt in payoff_plan]
    colors = px.colors.qualitative.Set3[:len(debt_names)]
    
    # Create bar chart
    fig = go.Figure()
    
    for i, (name, months, color) in enumerate(zip(debt_names, months_to_payoff, colors)):
        fig.add_trace(go.Bar(
            name=name,
            x=[name],
            y=[months],
            marker_color=color,
            text=f"{format_duration(months)}",
            textposition='auto',
            hovertemplate=f'<b>{name}</b><br>Payoff Time: {format_duration(months)}<extra></extra>'
        ))
    
    fig.update_layout(
        title="Debt Payoff Timeline",
        xaxis_title="Debts",
        yaxis_title="Months to Pay Off",
        showlegend=False,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_debt_insights(insights):
    """Render debt insights"""
    st.markdown("#### 💡 Insights")
    
    if not insights:
        st.info("No specific insights available")
        return
    
    for insight in insights[:3]:  # Show top 3 insights
        title = insight.get('title', 'Insight')
        description = insight.get('description', '')
        insight_type = insight.get('type', 'info')
        
        # Choose styling based on type
        if insight_type == 'warning':
            st.warning(f"⚠️ **{title}**\n\n{description}")
        elif insight_type == 'success':
            st.success(f"✅ **{title}**\n\n{description}")
        else:
            st.info(f"💡 **{title}**\n\n{description}")

def render_debt_recommendations(recommendations):
    """Render debt recommendations"""
    st.markdown("#### 🎯 Recommendations")
    
    if not recommendations:
        st.info("No specific recommendations available")
        return
    
    for rec in recommendations[:3]:  # Show top 3 recommendations
        title = rec.get('title', 'Recommendation')
        description = rec.get('description', '')
        action = rec.get('action', '')
        priority = rec.get('priority', 'medium')
        
        # Priority styling
        priority_colors = {
            'high': '🔴',
            'medium': '🟡',
            'low': '🟢'
        }
        priority_icon = priority_colors.get(priority, '🟡')
        
        with st.expander(f"{priority_icon} {title}"):
            st.write(description)
            if action:
                st.markdown(f"**Action:** {action}")

def render_debt_milestones(milestones):
    """Render debt payoff milestones"""
    st.markdown("#### 🏆 Your Debt Freedom Milestones")
    
    for milestone in milestones[:5]:  # Show first 5 milestones
        debt_name = milestone.get('debt_name', '')
        target_date = milestone.get('target_date', '')
        freed_cash = milestone.get('freed_cash_flow', 0)
        celebration = milestone.get('celebration_message', '')
        
        with st.expander(f"🎯 {debt_name} - {target_date}"):
            st.write(celebration)
            if freed_cash > 0:
                st.success(f"💰 Monthly cash flow freed up: {format_currency(freed_cash)}")

def render_next_action(next_action):
    """Render next action recommendation"""
    st.markdown("#### 🚀 Your Next Step")
    
    st.success(f"🎯 **Immediate Action:** {next_action}")

def render_debt_plan_actions(plan):
    """Render debt plan action buttons"""
    st.markdown("---")
    st.markdown("#### 🔧 Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📥 Export Plan", use_container_width=True):
            export_debt_plan(plan)
    
    with col2:
        if st.button("📊 New Plan", use_container_width=True):
            start_new_debt_plan()
    
    with col3:
        if st.button("📅 Set Reminders", use_container_width=True):
            setup_debt_reminders(plan)
    
    with col4:
        if st.button("💰 Track Progress", use_container_width=True):
            setup_progress_tracking(plan)

def load_sample_debts():
    """Load sample debt data"""
    sample_debts = [
        {
            'name': 'Credit Card 1',
            'balance': 8500.0,
            'apr': 18.9,
            'minimum_payment': 170.0,
            'debt_type': 'credit_card',
            'id': 0
        },
        {
            'name': 'Credit Card 2',
            'balance': 3200.0,
            'apr': 15.5,
            'minimum_payment': 80.0,
            'debt_type': 'credit_card',
            'id': 1
        },
        {
            'name': 'Car Loan',
            'balance': 15000.0,
            'apr': 5.2,
            'minimum_payment': 285.0,
            'debt_type': 'car_loan',
            'id': 2
        },
        {
            'name': 'Student Loan',
            'balance': 22000.0,
            'apr': 4.5,
            'minimum_payment': 250.0,
            'debt_type': 'student_loan',
            'id': 3
        }
    ]
    
    st.session_state.debts = sample_debts
    display_success_message("Sample debts loaded!")
    st.rerun()

def calculate_offline_debt_plan(debts, extra_payment, strategy):
    """Calculate debt plan offline"""
    # Simplified offline calculation
    import math
    
    total_balance = sum(debt['balance'] for debt in debts)
    total_minimum = sum(debt['minimum_payment'] for debt in debts)
    
    # Mock calculation results
    return {
        'summary': {
            'total_debt': total_balance,
            'total_minimum_payment': total_minimum,
            'extra_payment': extra_payment,
            'strategy_used': strategy,
            'total_monthly_payment': total_minimum + extra_payment,
            'debt_count': len(debts)
        },
        'savings': {
            'interest_saved': extra_payment * 24,  # Simplified calculation
            'months_saved': min(12, extra_payment // 50),
            'total_saved': extra_payment * 24
        },
        'payoff_plan': [
            {
                'debt_name': debt['name'],
                'balance': debt['balance'],
                'monthly_payment': debt['minimum_payment'] + (extra_payment if i == 0 else 0),
                'months_to_payoff': max(1, int(debt['balance'] / (debt['minimum_payment'] + (extra_payment if i == 0 else 0)))),
                'total_interest': debt['balance'] * debt['apr'] / 100 * 0.5,
                'payoff_order': i + 1
            }
            for i, debt in enumerate(debts)
        ],
        'insights': [
            {
                'title': 'Strategy Selected',
                'description': f'Using {strategy} strategy with ${extra_payment:.2f} extra payment',
                'type': 'info'
            }
        ],
        'recommendations': [
            {
                'title': 'Automate Payments',
                'description': 'Set up automatic payments to stay on track',
                'action': 'Configure automatic payments with your bank',
                'priority': 'high'
            }
        ],
        'next_action': f'Focus on {debts[0]["name"]} first. Pay ${debts[0]["minimum_payment"] + extra_payment:.2f}/month.',
        'milestones': []
    }

def export_debt_plan(plan):
    """Export debt plan"""
    try:
        import json
        
        export_data = {
            'export_date': datetime.now().isoformat(),
            'debt_plan': plan,
            'user_info': {
                'persona': st.session_state.persona,
                'language': st.session_state.language
            }
        }
        
        json_str = json.dumps(export_data, indent=2, default=str)
        
        st.download_button(
            label="📥 Download Debt Plan",
            data=json_str,
            file_name=f"debt_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
        
        display_success_message("Debt plan exported!")
        
    except Exception as e:
        logger.error(f"Export failed: {e}")
        display_error_message("Export failed", str(e))

def start_new_debt_plan():
    """Start new debt plan"""
    if 'debt_plan' in st.session_state:
        del st.session_state.debt_plan
    
    display_success_message("Ready for new debt plan!")
    st.rerun()

def setup_debt_reminders(plan):
    """Setup debt payment reminders"""
    st.info("💡 Reminder setup feature coming soon! For now, set up automatic payments with your bank.")

def setup_progress_tracking(plan):
    """Setup progress tracking"""
    st.info("📊 Progress tracking feature coming soon! Export your plan and update it monthly.")

