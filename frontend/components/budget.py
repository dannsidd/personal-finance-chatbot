import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import io
import logging
from utils.api_client import APIError
from utils.helpers import (
    format_currency, format_date, display_error_message, 
    display_success_message, get_financial_emoji, generate_colors
)

logger = logging.getLogger(__name__)

def render_budget():
    """Render budget analysis interface"""
    st.markdown("### 📊 Budget Insights")
    
    # Check if user has existing budget analysis
    if 'budget_analysis' in st.session_state and st.session_state.budget_analysis:
        display_budget_analysis(st.session_state.budget_analysis)
    else:
        render_budget_upload_interface()

def render_budget_upload_interface():
    """Render budget data upload interface"""
    st.markdown("""
    <div style='text-align: center; padding: 2rem; background: #F8F9FA; border-radius: 10px; margin: 1rem 0;'>
        <h3 style='color: #2E8B57; margin-bottom: 1rem;'>📈 Analyze Your Spending</h3>
        <p style='color: #666; margin-bottom: 2rem;'>Upload your transaction data or use sample data to get personalized insights</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Upload options
    col1, col2 = st.columns(2)
    
    with col1:
        render_csv_upload()
    
    with col2:
        render_sample_data_option()

def render_csv_upload():
    """Render CSV file upload"""
    st.markdown("#### 📁 Upload Transaction CSV")
    
    uploaded_file = st.file_uploader(
        "Choose your transaction file",
        type=['csv'],
        help="Upload a CSV with columns: date, description, amount",
        key="budget_csv_upload"
    )
    
    if uploaded_file is not None:
        try:
            # Show file info
            st.success(f"✅ File uploaded: {uploaded_file.name} ({uploaded_file.size} bytes)")
            
            # Preview data
            df = pd.read_csv(uploaded_file)
            
            with st.expander("📋 Data Preview"):
                st.dataframe(df.head(10))
                st.info(f"Found {len(df)} transactions")
            
            # Validate columns
            required_columns = ['date', 'description', 'amount']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"❌ Missing required columns: {', '.join(missing_columns)}")
                st.info("Your CSV should have columns: date, description, amount")
                return
            
            # Analyze button
            if st.button("🔍 Analyze My Budget", type="primary", use_container_width=True):
                analyze_uploaded_budget(df)
                
        except Exception as e:
            logger.error(f"CSV upload error: {e}")
            display_error_message("Failed to read CSV file", "Please check your file format")

def render_sample_data_option():
    """Render sample data option"""
    st.markdown("#### 🎮 Try Sample Data")
    
    st.markdown("""
    <div style='background: #E8F5E8; padding: 1rem; border-radius: 8px; margin: 1rem 0;'>
        <p style='margin: 0; color: #2E8B57;'>
            <strong>📊 Explore with demo data</strong><br>
            See how the budget analyzer works with realistic transaction data
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚀 Load Sample Transactions", use_container_width=True):
        load_sample_budget_data()

def analyze_uploaded_budget(df):
    """Analyze uploaded budget data"""
    try:
        with st.spinner("🔍 Analyzing your budget..."):
            # Convert DataFrame to API format
            transactions = []
            
            for _, row in df.iterrows():
                try:
                    transaction_date = pd.to_datetime(row['date'])
                    transactions.append({
                        'date': transaction_date.isoformat(),
                        'description': str(row['description']),
                        'amount': float(row['amount'])
                    })
                except Exception as e:
                    logger.warning(f"Skipping invalid transaction: {e}")
                    continue
            
            if not transactions:
                display_error_message("No valid transactions found", "Please check your data format")
                return
            
            # Call API
            if st.session_state.api_client:
                request_data = {
                    'transactions': transactions,
                    'analysis_name': f"Budget Analysis - {datetime.now().strftime('%m/%d/%Y')}",
                    'include_insights': True,
                    'include_recommendations': True
                }
                
                result = st.session_state.api_client.analyze_budget(request_data)
                st.session_state.budget_analysis = result
                
                display_success_message(
                    "Budget analyzed successfully!",
                    f"Found insights from {len(transactions)} transactions"
                )
                st.rerun()
            else:
                display_error_message("API not available", "Please check your connection")
                
    except APIError as e:
        display_error_message("Budget analysis failed", e.message)
    except Exception as e:
        logger.error(f"Budget analysis error: {e}")
        display_error_message("Analysis failed", str(e))

def load_sample_budget_data():
    """Load sample budget data for demonstration"""
    try:
        with st.spinner("📊 Loading sample data..."):
            # Generate sample transactions
            sample_data = generate_sample_transactions()
            
            # Analyze sample data
            if st.session_state.api_client:
                request_data = {
                    'transactions': sample_data,
                    'analysis_name': "Sample Budget Analysis",
                    'include_insights': True,
                    'include_recommendations': True
                }
                
                result = st.session_state.api_client.analyze_budget(request_data)
                st.session_state.budget_analysis = result
                
                display_success_message(
                    "Sample data loaded!",
                    f"Analyzing {len(sample_data)} sample transactions"
                )
                st.rerun()
            else:
                # Offline mode - generate mock analysis
                st.session_state.budget_analysis = generate_mock_budget_analysis()
                display_success_message("Sample data loaded!", "Using offline analysis")
                st.rerun()
                
    except Exception as e:
        logger.error(f"Sample data loading error: {e}")
        display_error_message("Failed to load sample data", str(e))

def display_budget_analysis(analysis):
    """Display comprehensive budget analysis"""
    summary = analysis.get('summary', {})
    categories = analysis.get('categories', {})
    insights = analysis.get('insights', [])
    recommendations = analysis.get('recommendations', [])
    anomalies = analysis.get('anomalies', [])
    trends = analysis.get('trends', {})
    
    # Header with key metrics
    render_budget_metrics(summary)
    
    # Main analysis sections
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_spending_breakdown(categories, summary)
        render_spending_timeline(trends)
    
    with col2:
        render_insights_panel(insights)
        render_recommendations_panel(recommendations)
    
    # Additional sections
    if anomalies:
        render_anomalies_section(anomalies)
    
    # Action buttons
    render_budget_actions(analysis)

def render_budget_metrics(summary):
    """Render key budget metrics"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "💰 Total Spending",
            format_currency(summary.get('total_spending', 0)),
            delta=f"${summary.get('avg_daily_spending', 0):.2f}/day"
        )
    
    with col2:
        st.metric(
            "📅 Transactions", 
            f"{summary.get('transaction_count', 0):,}",
            delta=f"{summary.get('analysis_period_days', 0)} days"
        )
    
    with col3:
        avg_transaction = summary.get('total_spending', 0) / max(1, summary.get('transaction_count', 1))
        st.metric(
            "📊 Avg Transaction",
            format_currency(avg_transaction),
            delta=f"${summary.get('monthly_estimate', 0):,.0f}/month"
        )
    
    with col4:
        top_category = summary.get('top_category', 'none').replace('_', ' ').title()
        st.metric(
            "🏆 Top Category",
            top_category,
            delta="Highest spending"
        )

def render_spending_breakdown(categories, summary):
    """Render spending breakdown charts"""
    st.markdown("#### 🏷️ Spending by Category")
    
    if not categories:
        st.info("No spending categories found")
        return
    
    # Prepare data for charts
    cat_names = []
    cat_amounts = []
    cat_colors = []
    
    for category, amount in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        if amount > 0:  # Only show categories with spending
            cat_names.append(category.replace('_', ' ').title())
            cat_amounts.append(amount)
    
    if not cat_names:
        st.info("No spending data to display")
        return
    
    # Generate colors
    colors = generate_colors(len(cat_names))
    
    # Tabs for different chart views
    chart_tab1, chart_tab2 = st.tabs(["🥧 Pie Chart", "📊 Bar Chart"])
    
    with chart_tab1:
        # Pie chart
        fig_pie = px.pie(
            values=cat_amounts,
            names=cat_names,
            title="Spending Distribution",
            color_discrete_sequence=colors
        )
        fig_pie.update_traces(
            textposition='inside', 
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>Amount: $%{value:,.2f}<br>Percentage: %{percent}<extra></extra>'
        )
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with chart_tab2:
        # Bar chart
        fig_bar = px.bar(
            x=cat_amounts,
            y=cat_names,
            orientation='h',
            title="Spending by Category",
            color=cat_amounts,
            color_continuous_scale='Viridis'
        )
        fig_bar.update_traces(
            hovertemplate='<b>%{y}</b><br>Amount: $%{x:,.2f}<extra></extra>'
        )
        fig_bar.update_layout(
            height=400,
            yaxis={'categoryorder': 'total ascending'}
        )
        st.plotly_chart(fig_bar, use_container_width=True)

def render_spending_timeline(trends):
    """Render spending timeline"""
    st.markdown("#### 📈 Spending Trends")
    
    # Mock timeline data for demonstration
    dates = pd.date_range(start=date.today() - timedelta(days=30), end=date.today(), freq='D')
    import random
    amounts = [random.uniform(50, 300) for _ in dates]
    
    timeline_df = pd.DataFrame({
        'Date': dates,
        'Daily Spending': amounts
    })
    
    # Create timeline chart
    fig_timeline = px.line(
        timeline_df,
        x='Date',
        y='Daily Spending',
        title='Daily Spending Trend (Last 30 Days)',
        markers=True
    )
    
    # Add moving average
    timeline_df['7-Day Average'] = timeline_df['Daily Spending'].rolling(window=7).mean()
    
    fig_timeline.add_scatter(
        x=timeline_df['Date'],
        y=timeline_df['7-Day Average'],
        mode='lines',
        name='7-Day Average',
        line=dict(dash='dash', color='red')
    )
    
    fig_timeline.update_layout(height=300)
    st.plotly_chart(fig_timeline, use_container_width=True)

def render_insights_panel(insights):
    """Render insights panel"""
    st.markdown("#### 💡 Key Insights")
    
    if not insights:
        st.info("No specific insights available")
        return
    
    for i, insight in enumerate(insights[:5]):  # Show top 5 insights
        title = insight.get('title', 'Insight')
        description = insight.get('description', '')
        insight_type = insight.get('type', 'general')
        
        # Choose icon based on type
        icons = {
            'spending_category': '💳',
            'frequency_alert': '⚠️',
            'subscription_alert': '📱',
            'positive': '✅',
            'warning': '⚠️',
            'general': '💡'
        }
        icon = icons.get(insight_type, '💡')
        
        with st.expander(f"{icon} {title}"):
            st.write(description)
            
            # Show evidence if available
            evidence = insight.get('evidence', {})
            if evidence:
                st.markdown("**Supporting data:**")
                for key, value in evidence.items():
                    if isinstance(value, dict):
                        st.write(f"• **{key.replace('_', ' ').title()}:**")
                        for sub_key, sub_value in value.items():
                            st.write(f"  - {sub_key}: ${sub_value:.2f}")
                    else:
                        st.write(f"• **{key.replace('_', ' ').title()}:** {value}")

def render_recommendations_panel(recommendations):
    """Render recommendations panel"""
    st.markdown("#### 🎯 Recommendations")
    
    if not recommendations:
        st.info("No specific recommendations available")
        return
    
    for i, rec in enumerate(recommendations[:5]):  # Show top 5 recommendations
        title = rec.get('title', 'Recommendation')
        description = rec.get('description', '')
        action = rec.get('action', '')
        priority = rec.get('priority', 'medium')
        potential_savings = rec.get('potential_savings', 0)
        
        # Priority styling
        priority_colors = {
            'high': '🔴',
            'medium': '🟡', 
            'low': '🟢'
        }
        priority_icon = priority_colors.get(priority, '🟡')
        
        with st.expander(f"{priority_icon} {title} ({priority.title()} Priority)"):
            st.write(description)
            
            if action:
                st.markdown(f"**Action:** {action}")
            
            if potential_savings > 0:
                st.success(f"💰 Potential monthly savings: {format_currency(potential_savings)}")

def render_anomalies_section(anomalies):
    """Render anomalies section"""
    st.markdown("#### ⚠️ Unusual Transactions")
    
    if not anomalies:
        return
    
    anomaly_df = pd.DataFrame(anomalies)
    
    # Format for display
    display_df = anomaly_df.copy()
    if 'date' in display_df.columns:
        display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%m/%d/%Y')
    if 'amount' in display_df.columns:
        display_df['amount'] = display_df['amount'].apply(lambda x: f"${x:.2f}")
    
    st.dataframe(
        display_df[['date', 'description', 'amount', 'reason']],
        use_container_width=True,
        hide_index=True
    )

def render_budget_actions(analysis):
    """Render budget action buttons"""
    st.markdown("---")
    st.markdown("#### 🔧 Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📥 Export Analysis", use_container_width=True):
            export_budget_analysis(analysis)
    
    with col2:
        if st.button("📊 New Analysis", use_container_width=True):
            start_new_budget_analysis()
    
    with col3:
        if st.button("🎯 Set Goals", use_container_width=True):
            st.session_state.active_tab = "Goal Planner"
            st.rerun()
    
    with col4:
        if st.button("💳 Plan Debt", use_container_width=True):
            st.session_state.active_tab = "Debt Navigator"
            st.rerun()

def export_budget_analysis(analysis):
    """Export budget analysis to downloadable format"""
    try:
        # Create comprehensive export
        export_data = {
            'export_date': datetime.now().isoformat(),
            'analysis': analysis,
            'user_info': {
                'persona': st.session_state.persona,
                'language': st.session_state.language
            }
        }
        
        import json
        json_str = json.dumps(export_data, indent=2, default=str)
        
        st.download_button(
            label="📥 Download Budget Analysis",
            data=json_str,
            file_name=f"budget_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
        
        display_success_message("Analysis exported successfully!")
        
    except Exception as e:
        logger.error(f"Export failed: {e}")
        display_error_message("Export failed", str(e))

def start_new_budget_analysis():
    """Start a new budget analysis"""
    if 'budget_analysis' in st.session_state:
        del st.session_state.budget_analysis
    
    display_success_message("Ready for new analysis!")
    st.rerun()

def generate_sample_transactions():
    """Generate sample transaction data"""
    import random
    
    merchants = {
        'groceries': ['Whole Foods Market', 'Safeway', 'Trader Joes', 'Local Grocery'],
        'dining': ['Starbucks Coffee', 'Chipotle Mexican', 'Local Restaurant', 'Pizza Palace'],
        'transport': ['Shell Gas Station', 'Uber Technologies', 'City Parking', 'Metro Transit'],
        'shopping': ['Amazon.com', 'Target Store', 'Best Buy Electronics', 'Local Retail'],
        'utilities': ['Pacific Gas Electric', 'Comcast Internet', 'City Water Dept', 'Mobile Phone'],
        'entertainment': ['Netflix Subscription', 'AMC Theaters', 'Spotify Premium', 'Concert Venue'],
        'healthcare': ['CVS Pharmacy', 'Dr. Smith Office', 'Health Insurance', 'Dental Care']
    }
    
    transactions = []
    start_date = date.today() - timedelta(days=90)
    
    for i in range(120):  # 120 transactions over 90 days
        transaction_date = start_date + timedelta(days=random.randint(0, 90))
        category = random.choice(list(merchants.keys()))
        merchant = random.choice(merchants[category])
        
        # Different amount ranges by category
        amount_ranges = {
            'groceries': (25, 120),
            'dining': (8, 45),
            'transport': (15, 60),
            'shopping': (20, 150),
            'utilities': (40, 180),
            'entertainment': (10, 80),
            'healthcare': (30, 200)
        }
        
        min_amt, max_amt = amount_ranges[category]
        amount = round(random.uniform(min_amt, max_amt), 2)
        
        transactions.append({
            'date': transaction_date.isoformat(),
            'description': merchant,
            'amount': -amount  # Negative for expenses
        })
    
    return sorted(transactions, key=lambda x: x['date'])

def generate_mock_budget_analysis():
    """Generate mock budget analysis for offline mode"""
    return {
        'summary': {
            'total_spending': 3245.67,
            'transaction_count': 87,
            'avg_daily_spending': 36.87,
            'monthly_estimate': 1106.0,
            'analysis_period_days': 88,
            'top_category': 'groceries'
        },
        'categories': {
            'groceries': 856.34,
            'dining': 432.18,
            'transport': 298.45,
            'shopping': 387.92,
            'utilities': 456.78,
            'entertainment': 234.56,
            'healthcare': 189.44,
            'miscellaneous': 390.00
        },
        'insights': [
            {
                'title': 'High Grocery Spending',
                'description': 'Your grocery expenses are above average for your income level',
                'type': 'spending_category',
                'evidence': {
                    'transaction_count': 23,
                    'avg_transaction': 37.23,
                    'percentage_of_total': 26.4
                }
            },
            {
                'title': 'Frequent Dining Out',
                'description': 'You dined out 18 times this month',
                'type': 'frequency_alert',
                'evidence': {
                    'frequency': 18,
                    'avg_meal_cost': 24.01
                }
            }
        ],
        'recommendations': [
            {
                'title': 'Meal Planning',
                'description': 'Plan weekly meals to reduce grocery and dining costs',
                'action': 'Create a weekly meal plan and shopping list',
                'priority': 'high',
                'potential_savings': 180.00,
                'type': 'spending_reduction'
            },
            {
                'title': 'Subscription Review',
                'description': 'Review entertainment subscriptions for unused services',
                'action': 'Cancel unused streaming services and memberships',
                'priority': 'medium',
                'potential_savings': 35.00,
                'type': 'subscription_optimization'
            }
        ],
        'anomalies': [
            {
                'date': '2024-01-15',
                'description': 'Electronics Store',
                'amount': 599.99,
                'category': 'shopping',
                'reason': 'Unusually high for shopping (avg: $38.79)'
            }
        ],
        'trends': {
            'daily_average': 36.87,
            'weekly_trend': 'stable',
            'spending_velocity': 15.23
        }
    }

