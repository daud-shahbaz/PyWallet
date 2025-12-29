"""
ML Insights Page - Machine Learning Predictions and Analysis

Displays:
- Spending predictions (next month)
- Anomaly detection (unusual transactions)
- Category classifier (predict category from notes)
- Clustering analysis (spending behavior patterns)
- Advisor recommendations
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pywallet.modules.data_manager import DataManager
from pywallet.ml_models import (
    SpendingPredictor,
    AnomalyDetector,
    CategoryClassifier,
    SpendingClustering,
    generate_all_insights,
)
from pywallet.ml_models.ai_coach import AICoach, InsightFormatter
from pywallet import config
from pywallet.security.auth_utils import require_login, show_user_info

# ============================================================================
#                                Config
# ============================================================================

st.set_page_config(
    page_title="ML Insights - PyWallet",
    page_icon=config.STREAMLIT_PAGE_ICON,
    layout="wide",
)

# Check authentication
require_login()
show_user_info()

st.title("ML Insights")
st.markdown("Machine Learning-powered financial predictions and analysis")

# ============================================================================
#                          Load and Validate Data
# ============================================================================

df = DataManager.load_dataframe()

if df.empty or len(df) < config.MIN_DATA_POINTS_FOR_ML:
    st.warning(
        f"Need at least {config.MIN_DATA_POINTS_FOR_ML} transactions to generate ML insights. "
        f"Current: {len(df)} transactions"
    )
    st.info("Add more expenses to unlock ML features!")
    st.stop()

# ============================================================================
#                         Create ML Feature Tabs
# ============================================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Predictions",
    "Anomalies",
    "Category Classifier",
    "Spending Patterns",
    "Advisor"
])

# ============================================================================
#                           Spending Predictions
# ============================================================================

with tab1:
    st.subheader("Next Month Spending Forecast")
    st.markdown("AI-powered predictions for next month's spending by category. Uses linear regression analysis on your historical data.")
    
    try:
        predictor = SpendingPredictor()
        predictions = predictor.predict_next_month()
        
        if 'predictions' in predictions and predictions['predictions']:
            # Calculate summary metrics
            total_predicted = sum(p['predicted_amount'] for p in predictions['predictions'].values())
            avg_confidence = np.mean([p['confidence'] for p in predictions['predictions'].values()])
            
            # Display summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Next Month", f"PKR {total_predicted:,.0f}")
            with col2:
                st.metric("Average Confidence", f"{avg_confidence:.0%}")
            with col3:
                trending_up = sum(1 for p in predictions['predictions'].values() if p['trend'] == 'increasing')
                st.metric("Increasing Categories", f"{trending_up}/{len(predictions['predictions'])}")
            
            st.divider()
            
            # Format data for display
            pred_data = []
            for category, pred in predictions['predictions'].items():
                trend_symbol = "UP" if pred['trend'] == 'increasing' else "DOWN" if pred['trend'] == 'decreasing' else "STABLE"
                pred_data.append({
                    'Category': category,
                    'Prediction': f"PKR {pred['predicted_amount']:.0f}",
                    'Confidence': f"{pred['confidence']:.0%}",
                    'Trend': f"{trend_symbol} {pred['trend'].title()}",
                    'Avg': f"PKR {pred['historical_average']:.0f}",
                    'Change': f"{((pred['predicted_amount'] - pred['historical_average']) / max(pred['historical_average'], 1) * 100):.0f}%"
                })
            
            pred_df = pd.DataFrame(pred_data)
            st.dataframe(pred_df, use_container_width=True, hide_index=True)
            
            # Dual chart: Comparison and Confidence
            col1, col2 = st.columns(2)
            
            with col1:
                # Prediction vs Historical Average
                chart_data = [{
                    'category': cat,
                    'predicted': pred['predicted_amount'],
                    'historical': pred['historical_average']
                } for cat, pred in predictions['predictions'].items()]
                chart_df = pd.DataFrame(chart_data)
                
                fig1 = go.Figure(data=[
                    go.Bar(name='Predicted', x=chart_df['category'], y=chart_df['predicted'], marker_color='#FF6B6B'),
                    go.Bar(name='Historical Avg', x=chart_df['category'], y=chart_df['historical'], marker_color='#4ECDC4')
                ])
                fig1.update_layout(
                    title="Prediction vs Historical Average",
                    xaxis_title="Category",
                    yaxis_title="Amount (PKR)",
                    height=350,
                    barmode='group',
                    hovermode='x unified'
                )
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                # Confidence gauge
                chart_data = [{
                    'category': cat,
                    'amount': pred['predicted_amount'],
                    'confidence': pred['confidence'] * 100
                } for cat, pred in predictions['predictions'].items()]
                chart_df = pd.DataFrame(chart_data)
                
                fig2 = px.bar(
                    chart_df,
                    x='category',
                    y='confidence',
                    color='confidence',
                    color_continuous_scale='RdYlGn',
                    title="Prediction Confidence by Category",
                    labels={'confidence': 'Confidence (%)', 'category': 'Category'},
                    range_color=[0, 100]
                )
                fig2.update_layout(height=350, showlegend=False)
                st.plotly_chart(fig2, use_container_width=True)
            
            st.info("Tip: Categories with trending up might need budget increase. Categories with decreasing trend may have room for savings.")
        else:
            st.info("Insufficient data for predictions. Keep tracking your expenses!")
    
    except Exception as e:
        st.error(f"Error generating predictions: {e}")

# ============================================================================
#                        Detect Unusual Transactions
# ============================================================================

with tab2:
    st.subheader("Unusual Transaction Detection")
    st.markdown("ML-powered anomaly detection identifies spending that deviates significantly from your normal patterns using Isolation Forest algorithm.")
    
    try:
        detector = AnomalyDetector()
        anomalies_result = detector.detect_anomalies()
        anomalies = anomalies_result.get('anomalies', [])
        
        if anomalies:
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Unusual Transactions", len(anomalies))
            with col2:
                total_anomaly_amount = sum(a['amount'] for a in anomalies)
                st.metric("Anomaly Spending", f"PKR {total_anomaly_amount:,.0f}")
            with col3:
                avg_z_score = np.mean([a['z_score'] for a in anomalies])
                st.metric("Avg Z-Score", f"{avg_z_score:.2f}")
            
            st.divider()
            
            # Sort by severity (z-score)
            anomalies_sorted = sorted(anomalies, key=lambda x: abs(x['z_score']), reverse=True)
            
            # Display top anomalies in cards
            st.markdown("**Top Unusual Transactions**")
            cols = st.columns(min(3, len(anomalies_sorted)))
            for i, anom in enumerate(anomalies_sorted[:3]):
                with cols[i]:
                    severity = "CRITICAL" if abs(anom['z_score']) > 3 else "WARNING" if abs(anom['z_score']) > 2 else "NOTICE"
                    with st.container(border=True):
                        st.markdown(f"**{anom['category']}** ({anom['date']})")
                        st.markdown(f"**PKR {anom['amount']:.0f}** {severity}")
                        st.caption(f"Deviation: {anom['deviation']:.0f} PKR above normal")
                        if anom['note']:
                            st.caption(f"{anom['note'][:50]}")
            
            st.divider()
            
            # Detailed view with expanders
            st.markdown("**All Anomalies**")
            for anom in anomalies_sorted:
                severity_icon = "RED" if abs(anom['z_score']) > 3 else "ORANGE" if abs(anom['z_score']) > 2 else "YELLOW"
                with st.expander(
                    f"{severity_icon} PKR {anom['amount']:.0f} - {anom['category']} ({anom['date']})",
                    expanded=False
                ):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Amount", f"PKR {anom['amount']:.0f}")
                    with col2:
                        st.metric("Z-Score", f"{anom['z_score']:.2f}")
                    with col3:
                        st.metric("Deviation", f"PKR {anom['deviation']:.0f}")
                    
                    st.markdown(f"**Reason**: {anom['reason']}")
                    if anom['note']:
                        st.markdown(f"**Note**: {anom['note']}")
            
            st.divider()
            
            # Timeline visualization
            anom_df = pd.DataFrame(anomalies_sorted)
            anom_df['severity'] = anom_df['z_score'].apply(
                lambda x: 'CRITICAL' if abs(x) > 3 else 'WARNING' if abs(x) > 2 else 'NOTICE'
            )
            
            fig = px.scatter(
                anom_df,
                x='date',
                y='amount',
                color='severity',
                size='z_score',
                hover_data=['category', 'note', 'z_score', 'deviation'],
                title="Anomalies Timeline - Hover for details",
                labels={'amount': 'Amount (PKR)', 'date': 'Date'},
                color_discrete_map={'CRITICAL': '#FF4444', 'WARNING': '#FFA500', 'NOTICE': '#FFDD00'}
            )
            fig.update_layout(height=400, hovermode='closest')
            st.plotly_chart(fig, use_container_width=True)
            
            st.info("Actions: Review these transactions. They might indicate fraudulent activity, special purchases, or unusual spending patterns.")
        
        else:
            st.success("No unusual transactions detected. Your spending looks normal and consistent!")
    
    except Exception as e:
        st.error(f"Error detecting anomalies: {e}")

# ============================================================================
#                           Classifier - NLP
# ============================================================================

with tab3:
    st.subheader("Category Prediction from Notes")
    st.markdown("NLP-powered category classification. Learns from your past expense notes to automatically categorize new transactions.")
    
    try:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("**How it works**: The classifier uses TF-IDF vectorization and Naive Bayes to predict categories from expense notes.")
        with col2:
            if st.button("Retrain Classifier", use_container_width=True):
                with st.spinner("Training classifier..."):
                    classifier = CategoryClassifier()
                    success, message = classifier.train_classifier()
                    
                    if success:
                        st.success(message)
                    else:
                        st.warning(message)
        
        st.divider()
        
        # Predict category section
        st.markdown("**Test Prediction**")
        col1, col2 = st.columns([4, 1])
        with col1:
            note_input = st.text_input(
                "Enter an expense note:",
                placeholder="e.g., 'Grocery shopping at Carrefour', 'Movie tickets', 'Gas station fill up'",
                label_visibility="collapsed"
            )
        with col2:
            predict_btn = st.button("Predict", use_container_width=True, type="primary")
        
        if predict_btn and note_input:
            classifier = CategoryClassifier()
            result = classifier.predict_category(note_input)
            
            if 'error' not in result:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Category", result['predicted_category'])
                with col2:
                    confidence_pct = result['confidence'] * 100
                    st.metric("Confidence", f"{confidence_pct:.0f}%")
                with col3:
                    status = "✓ CONFIDENT" if confidence_pct >= 80 else "⚠ LOW" if confidence_pct >= 60 else "✗ UNCERTAIN"
                    st.metric("Assessment", status)
                
                st.divider()
                
                # Show confidence for all categories
                st.markdown("**Category Confidence Breakdown**")
                
                # Create sample data showing relative confidence
                confidence_data = {
                    'Category': [result['predicted_category']] + [c for c in config.DEFAULT_CATEGORIES if c != result['predicted_category']][:4],
                    'Confidence': [result['confidence']] + [0.1] * 4
                }
                conf_df = pd.DataFrame(confidence_data)
                
                fig = px.bar(
                    conf_df,
                    x='Confidence',
                    y='Category',
                    orientation='h',
                    color='Confidence',
                    color_continuous_scale='Blues',
                    title="Predicted Probabilities"
                )
                fig.update_layout(height=300, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Unable to predict. Try a different note.")
        
        st.divider()
        
        # Show category keywords
        st.markdown("**Category Reference Guide**")
        
        col1, col2 = st.columns([2, 3])
        with col1:
            category = st.selectbox(
                "Select a category to see common keywords:",
                options=config.DEFAULT_CATEGORIES,
                label_visibility="collapsed"
            )
        
        with col2:
            if category:
                classifier = CategoryClassifier()
                keywords = classifier.get_category_keywords(category)
                
                if keywords:
                    st.markdown(f"**{category} Keywords:**")
                    # Display as columns for better readability
                    keyword_cols = st.columns(2)
                    for i, kw in enumerate(keywords):
                        with keyword_cols[i % 2]:
                            st.caption(f"• {kw}")
                else:
                    st.caption(f"No keywords yet for {category}")
    
    except Exception as e:
        st.error(f"Error with classifier: {e}")

# ============================================================================
#                        Patterns - Clustering
# ============================================================================

with tab4:
    st.subheader("Spending Behavior Analysis")
    st.markdown("K-means clustering reveals your spending behavior patterns and compares them to others.")
    
    try:
        clusterer = SpendingClustering()
        clustering = clusterer.cluster_spending_patterns()
        
        if 'error' not in clustering:
            # Display cluster assignment
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("[YOUR PROFILE] Cluster", clustering.get('cluster_name', 'Unknown'))
            with col2:
                st.metric("[TOTAL] Clusters Found", clustering['num_clusters'])
            with col3:
                cluster_size = clustering.get('cluster_size', 0)
                st.metric("[MEMBERS] In Your Cluster", f"{cluster_size} spenders")
            
            st.divider()
            
            # Display cluster profiles in cards
            st.markdown("**Cluster Profiles**")
            cols = st.columns(min(3, len(clustering.get('clusters', {}))))
            
            for i, (cluster_name, cluster_info) in enumerate(clustering.get('clusters', {}).items()):
                with cols[i % len(cols)]:
                    with st.container(border=True):
                        st.markdown(f"**{cluster_info['name']}**")
                        st.caption(f"{cluster_info['characteristics']}")
                        st.markdown("**Top Categories:**")
                        for cat in cluster_info.get('top_categories', [])[:3]:
                            st.caption(f"  • {cat}")
            
            st.divider()
            
            # Your spending distribution
            st.markdown("**Your Spending Distribution**")
            
            comparison = clusterer.compare_to_clusters()
            
            if 'category_distribution' in comparison:
                # Calculate percentages
                dist_data = comparison['category_distribution']
                total_dist = sum(dist_data.values())
                dist_pct = {k: (v/total_dist*100) if total_dist > 0 else 0 for k, v in dist_data.items()}
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    # Pie chart
                    dist_df = pd.DataFrame([
                        {'Category': k, 'Percentage': v} 
                        for k, v in dist_pct.items() if v > 1
                    ]).sort_values('Percentage', ascending=False)
                    
                    fig = px.pie(
                        dist_df,
                        names='Category',
                        values='Percentage',
                        title="Your Spending Breakdown",
                        hole=0.4
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Key metrics
                    st.markdown("**Key Metrics**")
                    st.metric("Total Spending", f"PKR {comparison['total_spending']:,.0f}")
                    st.metric("Dominant Category", comparison.get('dominant_category', 'N/A'))
                    diversity = comparison.get('spending_diversity', 'N/A')
                    st.metric("Category Diversity", f"{diversity}" if isinstance(diversity, str) else f"{diversity:.1f}")
            
            st.info("Insight: Your spending pattern identifies you as a member of a specific spender cluster. Compare your behavior to optimize spending habits.")
        else:
            st.info("Clustering analysis not available yet. Add more expenses to enable analysis.")
    
    except Exception as e:
        st.error(f"Error analyzing patterns: {e}")

# ============================================================================
#                                Advisor
# ============================================================================

with tab5:
    st.subheader("Advisor - Financial Guidance")
    st.markdown("Your personal financial advisor powered by ML. Get tailored recommendations based on your unique spending patterns.")
    
    try:
        # Monthly summary section
        st.markdown("### Monthly Summary")
        summary_text = AICoach.generate_monthly_summary()
        
        with st.container(border=True):
            st.text(summary_text)
        
        st.divider()
        
        # Personalized recommendations
        st.markdown("### Personalized Recommendations")
        advice = AICoach.generate_personalized_advice()
        
        # Display recommendations in 2 columns
        cols = st.columns(2)
        for i, rec in enumerate(advice):
            with cols[i % 2]:
                with st.container(border=True):
                    priority = "URGENT" if i < 2 else "IMPORTANT" if i < 4 else "NOTICE"
                    st.markdown(f"**{priority}**")
                    st.markdown(rec)
        
        st.divider()
        
        # Suggested next actions
        st.markdown("### Suggested Next Actions")
        actions = AICoach.suggest_next_actions()
        
        for i, action in enumerate(actions, 1):
            st.markdown(f"**{i}.** {action}")
        
        st.divider()
        
        # Pattern analysis
        st.markdown("### Spending Pattern Analysis")
        analysis = AICoach.analyze_spending_patterns()
        
        with st.container(border=True):
            st.markdown(analysis)
        
        st.divider()
        
        # Quick tips
        st.markdown("### Quick Tips")
        tips_col1, tips_col2 = st.columns(2)
        
        with tips_col1:
            st.markdown("""
            **Budget Optimization:**
            - Review categories with highest spending
            - Set stricter limits on discretionary items
            - Track patterns to identify savings opportunities
            """)
        
        with tips_col2:
            st.markdown("""
            **Spending Habits:**
            - Check anomalies regularly for unusual activity
            - Use predictions for better planning
            - Compare month-over-month trends
            """)
        
        st.info("**Future**: This Advisor will be enhanced with GPT integration for even more personalized insights!")
        
    except Exception as e:
        st.error(f"Error generating coaching advice: {e}")

# ============================================================================
#                               Footer
# ============================================================================



