"""
Analytics - Financial Reports and Analysis
Displays:
- Monthly summary with visualization
- Category spending with breakdown
- Trend analysis with charts
- Quick insights and KPIs
- Comprehensive report generation (PDF/CSV)
"""

import streamlit as st
import sys
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pywallet.modules.data_manager import DataManager
from pywallet.modules.analytics import Analytics
from pywallet.modules.report_generator import ReportGenerator
from pywallet import config
from pywallet.security.auth_utils import require_login, show_user_info

st.set_page_config(page_title="Analytics - PyWallet", page_icon=config.STREAMLIT_PAGE_ICON)

# Check authentication
require_login()
show_user_info()

st.title("Analytics")
st.markdown("Track, analyze, and visualize your spending patterns")

df = DataManager.load_dataframe()

if df.empty:
    st.warning("No data available. Add some expenses first to see analytics!")
    st.info("Go to **Manage Expenses** to record your first transaction.")
    st.stop()

# ============================================================================
#                           Display Key Insights
# ============================================================================

st.subheader("Quick Insights")

col1, col2, col3, col4, col5 = st.columns(5)

# Calculate key metrics
total_spending = df['amount'].sum()
avg_transaction = int(total_spending / len(df)) if len(df) > 0 else 0
transaction_count = len(df)
unique_categories = df['category'].nunique()
max_category = df.groupby('category')['amount'].sum().idxmax() if len(df) > 0 else "N/A"

with col1:
    st.metric("Total Spending", f"PKR {int(total_spending)}")
with col2:
    st.metric("Avg Transaction", f"PKR {avg_transaction}")
with col3:
    st.metric("Total Transactions", transaction_count)
with col4:
    st.metric("Categories", unique_categories)
with col5:
    st.metric("Top Category", max_category)

st.divider()

# ============================================================================
#                      Monthly analysis with visuals
# ============================================================================

st.subheader("Monthly Summary")

col1, col2 = st.columns(2)
with col1:
    year = st.number_input("Year", min_value=2000, max_value=2100, value=2025, step=1, help="Select year")
with col2:
    month = st.selectbox("Month", options=range(1, 13), format_func=lambda x: config.MONTHS_ABBREVIATION[x-1], help="Select month")

monthly = Analytics.monthly_summary(year=year, month=month)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total", f"PKR {int(monthly['total'])}")
with col2:
    st.metric("Transactions", int(monthly['transaction_count']))
with col3:
    st.metric("Categories", len(monthly['by_category']))
with col4:
    avg_per_day = int(monthly['total'] / 30) if monthly['total'] > 0 else 0
    st.metric("Daily Avg", f"PKR {avg_per_day}")

# Category breakdown charts
if monthly['by_category']:
    col1, col2 = st.columns(2)
    
    with col1:
        fig_pie = px.pie(
            values=list(monthly['by_category'].values()),
            names=list(monthly['by_category'].keys()),
            title=f"Distribution - {config.MONTHS_ABBREVIATION[month-1]} {year}"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        fig_bar = px.bar(
            x=list(monthly['by_category'].keys()),
            y=list(monthly['by_category'].values()),
            title=f"Amount by Category - {config.MONTHS_ABBREVIATION[month-1]} {year}",
            labels={'x': 'Category', 'y': 'Amount (PKR)'}
        )
        st.plotly_chart(fig_bar, use_container_width=True)
else:
    st.info(f"No expenses recorded for {config.MONTHS_ABBREVIATION[month-1]} {year}")

st.divider()

# ============================================================================
#                    Category analysis with visuals
# ============================================================================

st.subheader("Spending by Category")

col1, col2 = st.columns(2)
with col1:
    start = st.date_input("From Date:", value=None, help="Leave blank for all data")
with col2:
    end = st.date_input("To Date:", value=None, help="Leave blank for all data")

start_str = start.strftime("%Y-%m-%d") if start else None
end_str = end.strftime("%Y-%m-%d") if end else None

category_sum = Analytics.category_summary(start_date=start_str, end_date=end_str)

if category_sum:
    # Statistics
    total_all = sum(stats['total'] for stats in category_sum.values())
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Period Spend", f"PKR {int(total_all)}")
    with col2:
        avg_cat = int(total_all / len(category_sum)) if category_sum else 0
        st.metric("Avg per Category", f"PKR {avg_cat}")
    with col3:
        st.metric("Categories Used", len(category_sum))
    
    # Table
    cat_data = []
    for cat, stats in category_sum.items():
        cat_data.append({
            'Category': cat,
            'Total': f"PKR {int(stats['total'])}",
            'Transactions': int(stats['count']),
            'Average': f"PKR {int(stats['average'])}",
            '% of Total': f"{stats['percentage']:.1f}%"
        })
    
    st.dataframe(
        pd.DataFrame(cat_data).sort_values('Total', ascending=False, key=lambda x: x.str.replace('PKR ', '').astype(int) if x.name == 'Total' else x),
        use_container_width=True,
        hide_index=True
    )
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        totals = [int(s['total']) for s in category_sum.values()]
        labels = list(category_sum.keys())
        
        fig_bar = px.bar(
            x=labels,
            y=totals,
            title="Spending by Category",
            labels={'x': 'Category', 'y': 'Amount (PKR)'},
            color=totals,
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        fig_pie = px.pie(
            values=totals,
            names=labels,
            title="Category Distribution"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
else:
    st.info("No category data available for the selected period.")

st.divider()

# ============================================================================
#                              Trend Analysis
# ============================================================================

st.subheader("Spending Trends")

months = st.slider("Analyze last N months:", min_value=1, max_value=12, value=3, help="Number of months to analyze for trends")

trends = Analytics.detect_trends(months=months)

if 'trends' in trends and trends['trends']:
    st.markdown(f"**Top 5 Spending Trends (Last {months} month(s))**")
    
    # Sort by percent change magnitude
    sorted_trends = sorted(trends['trends'].items(), 
                          key=lambda x: abs(x[1]['percent_change']), 
                          reverse=True)[:5]
    
    # Display trends with better formatting
    for idx, (category, trend_data) in enumerate(sorted_trends, 1):
        col1, col2, col3, col4 = st.columns(4)
                
        with col1:
            st.metric(
                f"{idx}. {category}",
                f"PKR {int(trend_data['current_average'])}",
                delta=f"{trend_data['percent_change']:+.1f}%"
            )
        with col2:
            st.metric("Trend", f" {trend_data['direction'].title()}")
        with col3:
            st.metric("Previous Avg", f"PKR {int(trend_data['previous_average'])}")
        with col4:
            change_amount = int(trend_data['current_average'] - trend_data['previous_average'])
            st.metric("Change", f"PKR {change_amount:+d}")
    
    # Add trend visualization chart
    st.subheader("Trend Comparison Chart")
    
    trend_data_for_chart = []
    for category, trend_info in sorted_trends:
        trend_data_for_chart.append({
            'Category': category,
            'Previous Average': int(trend_info['previous_average']),
            'Current Average': int(trend_info['current_average']),
            'Change %': round(trend_info['percent_change'], 1)
        })
    
    df_trends = pd.DataFrame(trend_data_for_chart)
    
    # Create grouped bar chart
    fig_trends = px.bar(
        df_trends,
        x='Category',
        y=['Previous Average', 'Current Average'],
        title='Spending Trend Comparison',
        labels={'value': 'Amount (PKR)', 'variable': 'Period'},
        barmode='group',
        color_discrete_map={'Previous Average': '#636EFA', 'Current Average': '#EF553B'}
    )
    st.plotly_chart(fig_trends, use_container_width=True)
    
    # Create percent change chart
    fig_pct = px.bar(
        df_trends,
        x='Category',
        y='Change %',
        title='Percentage Change by Category',
        labels={'Change %': 'Change (%)', 'Category': 'Category'},
        color='Change %',
        color_continuous_scale='RdYlGn_r',
        text='Change %'
    )
    fig_pct.update_traces(textposition='auto')
    st.plotly_chart(fig_pct, use_container_width=True)
    
    st.divider()
    st.info("**Insight:** Identify spending patterns and adjust your budget to optimize savings.")
else:
    st.warning(f"Insufficient data for trend analysis. Need at least {months + 1} months of data.")

st.divider()

# ============================================================================
#                          Compare Monthly Patterns
# ============================================================================

st.subheader("Month-over-Month Comparison")

from datetime import datetime

comparison_months = st.slider(
    "Compare last N months",
    min_value=1,
    max_value=12,
    value=3
)

current_year = datetime.now().year
current_month = datetime.now().month

# Generate month range
months_range = []
for i in range(comparison_months):
    month = current_month - i
    year = current_year
    if month <= 0:
        month += 12
        year -= 1
    months_range.append((year, month))

months_range.reverse()

# Collect monthly data
monthly_data = []
for year, month in months_range:
    monthly_info = Analytics.monthly_summary(year=year, month=month)
    month_name = datetime(year, month, 1).strftime("%b %Y")
    monthly_data.append({
        'Month': month_name,
        'Total': monthly_info['total'],
        'Transactions': monthly_info.get('transactions', monthly_info.get('transaction_count', 0))
    })

df_monthly = pd.DataFrame(monthly_data)

# Display metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    avg_spending = df_monthly['Total'].mean()
    st.metric("Avg Monthly", f"PKR {int(avg_spending):,}")
with col2:
    max_spending = df_monthly['Total'].max()
    st.metric("Highest", f"PKR {int(max_spending):,}")
with col3:
    min_spending = df_monthly['Total'].min()
    st.metric("Lowest", f"PKR {int(min_spending):,}")
with col4:
    variance = max_spending - min_spending
    st.metric("Variance", f"PKR {int(variance):,}")

# Trend line chart
fig_monthly = px.line(
    df_monthly,
    x='Month',
    y='Total',
    markers=True,
    title='Monthly Spending Trend',
    labels={'Total': 'Amount (PKR)', 'Month': 'Month'},
    height=350
)
fig_monthly.update_traces(line=dict(color='indianred', width=3), marker=dict(size=10))
st.plotly_chart(fig_monthly, use_container_width=True)

st.info("Use this view to identify seasonal spending patterns and set realistic budgets.")

# ============================================================================
#                           Generate PDF Reports
# ============================================================================

st.markdown("---")
st.subheader("Download PDF Report")
st.markdown("Get a report of your finances")

col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    report_type = st.radio("Report Type:", ["Monthly", "Yearly"], horizontal=True)

if report_type == "Monthly":
    with col2:
        report_year = st.selectbox("Year", range(datetime.now().year, 2019, -1), key="my")
    with col3:
        report_month = st.selectbox("Month", range(1, 13), 
                                   format_func=lambda m: datetime(2024, m, 1).strftime("%B"),
                                   key="mm")
    
    if st.button("Generate Monthly PDF Report", use_container_width=True, type="primary"):
        try:
            from reportlab.platypus import Table, TableStyle, Image, Paragraph, Spacer, PageBreak
            from reportlab.lib import colors
            from reportlab.lib.units import inch
            from io import BytesIO
            import io
            import matplotlib.pyplot as plt
            
            # Generate report data
            monthly = Analytics.monthly_summary(year=report_year, month=report_month)
            period = datetime(report_year, report_month, 1).strftime("%B %Y")
            daily_avg = monthly['total'] / 30 if monthly['total'] > 0 else 0
            
            # Create PDF in memory
            pdf_buffer = BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, topMargin=0.4*inch, bottomMargin=0.4*inch, leftMargin=0.4*inch, rightMargin=0.4*inch)
            story = []
            styles = getSampleStyleSheet()
            
            # Create custom styles
            title_style = styles['Heading1']
            title_style.fontSize = 20
            title_style.spaceAfter = 2
            title_style.textColor = colors.HexColor('#1A5276')
            
            subtitle_style = styles['Heading3']
            subtitle_style.fontSize = 12
            subtitle_style.textColor = colors.HexColor('#2874A6')
            subtitle_style.spaceAfter = 1
            
            heading_style = styles['Heading2']
            heading_style.fontSize = 11
            heading_style.spaceAfter = 4
            heading_style.textColor = colors.HexColor('#154360')
            heading_style.fontName = 'Helvetica-Bold'
            
            section_style = styles['Normal']
            section_style.fontSize = 8
            
            # Enhanced Header with description
            header_table_data = [
                [Paragraph(f"<b>PyWallet Monthly Financial Report</b>", title_style)],
                [Paragraph(f"<font color='#2874A6'>{period} • Generated {datetime.now().strftime('%b %d, %Y')}</font>", subtitle_style)],
            ]
            header_table = Table(header_table_data, colWidths=[7.0*inch])
            header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#D6EAF8')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1A5276')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('BORDER', (0, 0), (-1, -1), 1, colors.HexColor('#2874A6')),
            ]))
            story.append(header_table)
            story.append(Spacer(1, 0.12*inch))
            
            # Load data
            df = DataManager.load_dataframe()
            month_data = df[(df['date'].dt.year == report_year) & (df['date'].dt.month == report_month)]
            trans_by_cat = month_data.groupby('category').size().to_dict() if not month_data.empty else {}
            
            # LEFT COLUMN: Overview & Category Table
            left_content = []
            left_content.append(Paragraph("<b>Financial Summary</b>", heading_style))
            
            summary_data = [
                ['Total Spending', f'PKR {int(monthly["total"]):,}'],
                ['Transactions', str(monthly['transaction_count'])],
                ['Daily Average', f'PKR {int(daily_avg):,}'],
            ]
            summary_table = Table(summary_data, colWidths=[1.8*inch, 1.2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#D5F4E6')),
                ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#A9DFBF')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#0B5345')),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#27AE60')),
                ('ROWBACKGROUNDS', (1, 1), (1, -1), [colors.HexColor('#A9DFBF')]),
            ]))
            left_content.append(summary_table)
            left_content.append(Spacer(1, 0.1*inch))
            
            # Category breakdown
            left_content.append(Paragraph("<b>By Category</b>", heading_style))
            cat_data = [['Category', 'Amount', '%']]
            total = monthly['total'] if monthly['total'] > 0 else 1
            
            for cat, amount in sorted(monthly['by_category'].items(), key=lambda x: x[1], reverse=True)[:8]:
                pct = (amount / total) * 100
                cat_data.append([cat[:12], f'PKR {int(amount):,}', f'{pct:.0f}%'])
            
            cat_table = Table(cat_data, colWidths=[1.3*inch, 1.2*inch, 0.5*inch])
            cat_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F618D')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 0.8, colors.HexColor('#5DADE2')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#D6EAF8')]),
            ]))
            left_content.append(cat_table)
            left_content.append(Spacer(1, 0.1*inch))
            
            # Top transactions
            left_content.append(Paragraph("<b>Top Transactions</b>", heading_style))
            top_trans = month_data.nlargest(4, 'amount')[['date', 'category', 'amount']].values.tolist() if not month_data.empty else []
            
            top_data = [['Date', 'Category', 'Amount']]
            for row in top_trans:
                date_str = pd.to_datetime(row[0]).strftime('%m/%d')
                top_data.append([date_str, str(row[1])[:10], f'PKR {int(row[2]):,}'])
            
            if len(top_data) > 1:
                top_table = Table(top_data, colWidths=[0.6*inch, 1.0*inch, 1.3*inch])
                top_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#A93226')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('ALIGN', (0, 0), (1, -1), 'CENTER'),
                    ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('GRID', (0, 0), (-1, -1), 0.8, colors.HexColor('#E74C3C')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5B7B1')]),
                ]))
                left_content.append(top_table)
            
            # RIGHT COLUMN: Charts
            right_content = []
            
            # Daily spending chart
            if monthly['daily_breakdown']:
                fig, ax = plt.subplots(figsize=(3.3, 2.8))
                days = sorted(monthly['daily_breakdown'].keys())
                amounts = [monthly['daily_breakdown'][d] for d in days]
                ax.bar(days, amounts, color='#2ECC71', edgecolor='#27AE60', linewidth=0.8, alpha=0.8)
                ax.set_xlabel('Day', fontsize=8, fontweight='bold')
                ax.set_ylabel('PKR', fontsize=8, fontweight='bold')
                ax.grid(axis='y', alpha=0.2, linestyle='--', linewidth=0.3)
                ax.set_facecolor('#F8F9FA')
                ax.tick_params(labelsize=7)
                plt.tight_layout()
                
                chart_buffer = io.BytesIO()
                fig.savefig(chart_buffer, format='png', dpi=80, bbox_inches='tight', facecolor='white')
                chart_buffer.seek(0)
                plt.close(fig)
                
                chart_img = Image(chart_buffer, width=3.3*inch, height=2.8*inch)
                right_content.append(Paragraph("<b>Daily Trend</b>", heading_style))
                right_content.append(chart_img)
                right_content.append(Spacer(1, 0.08*inch))
            
            # Pie chart
            if monthly['by_category']:
                fig, ax = plt.subplots(figsize=(3.3, 2.8))
                cats = list(monthly['by_category'].keys())[:6]
                amounts = [monthly['by_category'][c] for c in cats]
                colors_pie = ['#3498DB', '#E74C3C', '#2ECC71', '#F39C12', '#9B59B6', '#1ABC9C']
                wedges, texts, autotexts = ax.pie(amounts, labels=cats, autopct='%1.0f%%', colors=colors_pie[:len(cats)], startangle=90)
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
                    autotext.set_fontsize(6)
                for text in texts:
                    text.set_fontsize(7)
                ax.set_facecolor('#F8F9FA')
                plt.tight_layout()
                
                chart_buffer2 = io.BytesIO()
                fig.savefig(chart_buffer2, format='png', dpi=80, bbox_inches='tight', facecolor='white')
                chart_buffer2.seek(0)
                plt.close(fig)
                
                chart_img2 = Image(chart_buffer2, width=3.3*inch, height=2.8*inch)
                right_content.append(Paragraph("<b>Distribution</b>", heading_style))
                right_content.append(chart_img2)
            
            # Create two-column layout
            col_width = 3.5*inch
            left_table_data = [[left_content]]
            right_table_data = [[right_content]]
            
            layout_table = Table([[left_table_data[0][0], right_table_data[0][0]]], colWidths=[col_width, col_width])
            layout_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ]))
            story.append(layout_table)
            story.append(Spacer(1, 0.12*inch))
            
            # Add insights section
            story.append(Paragraph("<b>Key Insights & Analysis</b>", heading_style))
            insights = []
            
            # Highest spending category
            if monthly['by_category']:
                top_cat = max(monthly['by_category'], key=monthly['by_category'].get)
                top_amount = monthly['by_category'][top_cat]
                top_pct = (top_amount / monthly['total'] * 100) if monthly['total'] > 0 else 0
                insights.append(f"<b>Top Category:</b> {top_cat} accounts for PKR {int(top_amount):,} ({top_pct:.1f}%)")
                
                # Second highest
                sorted_cats = sorted(monthly['by_category'].items(), key=lambda x: x[1], reverse=True)
                if len(sorted_cats) > 1:
                    second_cat, second_amt = sorted_cats[1]
                    second_pct = (second_amt / monthly['total'] * 100) if monthly['total'] > 0 else 0
                    insights.append(f"<b>Second Category:</b> {second_cat} with PKR {int(second_amt):,} ({second_pct:.1f}%)")
            
            # Daily spending patterns
            if monthly['daily_breakdown']:
                max_day = max(monthly['daily_breakdown'], key=monthly['daily_breakdown'].get)
                max_amount = monthly['daily_breakdown'][max_day]
                min_day = min(monthly['daily_breakdown'], key=monthly['daily_breakdown'].get)
                min_amount = monthly['daily_breakdown'][min_day]
                avg_daily = monthly['total'] / len(monthly['daily_breakdown'])
                insights.append(f"<b>Daily Range:</b> PKR {int(min_amount):,} (day {min_day}) to PKR {int(max_amount):,} (day {max_day})")
                insights.append(f"<b>Daily Average:</b> PKR {int(avg_daily):,} per day")
            
            # Transaction frequency
            if monthly['transaction_count'] > 0:
                days_with_trans = len(monthly['daily_breakdown'])
                avg_per_day = monthly['transaction_count'] / days_with_trans if days_with_trans > 0 else 0
                insights.append(f"<b>Transaction Activity:</b> {monthly['transaction_count']} total transactions (~{avg_per_day:.1f} per day)")
            
            # Budget status
            try:
                total_budget = sum(config.DEFAULT_BUDGETS.values())
                budget_remaining = total_budget - monthly['total']
                budget_status_pct = (monthly['total'] / total_budget * 100) if total_budget > 0 else 0
                if budget_remaining >= 0:
                    insights.append(f"<b>Budget Status:</b> PKR {int(budget_remaining):,} remaining ({100-budget_status_pct:.1f}% of budget left)")
                else:
                    insights.append(f"<b>Budget Status:</b> OVER by PKR {int(abs(budget_remaining)):,} ({budget_status_pct:.1f}% of budget used)")
            except:
                pass
            
            # Category diversity
            if monthly['by_category']:
                num_categories = len(monthly['by_category'])
                insights.append(f"<b>Spending Spread:</b> Across {num_categories} different categories this month")
            
            # Monthly summary
            insights.append(f"<b>Total Spending:</b> PKR {int(monthly['total']):,} in {period}")
            
            insights_style = styles['Normal']
            insights_style.fontSize = 7.5
            insights_style.spaceAfter = 2
            
            for insight in insights:
                story.append(Paragraph(insight, insights_style))
            
            # Build PDF
            doc.build(story)
            pdf_buffer.seek(0)
            st.download_button(
                label="Download Monthly Report PDF",
                data=pdf_buffer.getvalue(),
                file_name=f"PyWallet_Report_{period.replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key=f"monthly_download_{report_year}_{report_month}"
            )
            st.success(f"Report ready for {period}!")
            
        except Exception as e:
            st.error(f"Error generating PDF: {str(e)}")
            import traceback
            st.write(traceback.format_exc())

else:  # Yearly
    with col2:
        report_year_y = st.selectbox("Year", range(datetime.now().year, 2019, -1), key="yy")
    
    if st.button("Generate Yearly PDF Report", use_container_width=True, type="primary"):
        try:
            from reportlab.platypus import Table, TableStyle, Image
            import io
            import matplotlib.pyplot as plt
            
            # Create PDF in memory
            pdf_buffer = BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, topMargin=0.35*inch, bottomMargin=0.35*inch, leftMargin=0.35*inch, rightMargin=0.35*inch)
            story = []
            styles = getSampleStyleSheet()
            
            # Create custom style
            title_style = styles['Heading1']
            title_style.fontSize = 16
            heading_style = styles['Heading2']
            heading_style.spaceAfter = 6
            
            # Header
            story.append(Paragraph(f"<b>PyWallet Annual Financial Report</b>", title_style))
            story.append(Paragraph(f"Year: <b>{report_year_y}</b>", styles['Heading3']))
            story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
            story.append(Spacer(1, 0.08*inch))
            
            # Collect yearly data
            yearly_total = 0
            yearly_by_cat = {}
            monthly_data = []
            yearly_totals_by_month = []
            
            for month in range(1, 13):
                monthly = Analytics.monthly_summary(year=report_year_y, month=month)
                month_name = datetime(report_year_y, month, 1).strftime("%b")
                monthly_data.append([month_name, f"PKR {int(monthly['total']):,}", str(monthly['transaction_count'])])
                yearly_totals_by_month.append(monthly['total'])
                yearly_total += monthly['total']
                for cat, amt in monthly['by_category'].items():
                    yearly_by_cat[cat] = yearly_by_cat.get(cat, 0) + amt
            
            # Year Overview
            story.append(Paragraph("<b>Annual Summary</b>", heading_style))
            annual_summary = [
                ['Metric', 'Value'],
                ['Total Spending', f'PKR {int(yearly_total):,}'],
                ['Monthly Average', f'PKR {int(yearly_total/12):,}'],
                ['Daily Average', f'PKR {int(yearly_total/365):,}'],
                ['Total Categories', str(len(yearly_by_cat))]
            ]
            annual_table = Table(annual_summary, colWidths=[2.5*inch, 2.5*inch])
            annual_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#D5D8DC')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ECF0F1')]),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor('#2C3E50')),
                ('RIGHTPADDING', (1, 0), (1, -1), 12),
            ]))
            story.append(annual_table)
            story.append(Spacer(1, 0.2*inch))
            
            # Monthly Spending Trend Chart
            story.append(Paragraph("<b>Monthly Trend</b>", heading_style))
            fig, ax = plt.subplots(figsize=(5.5, 2.5))
            months_short = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            ax.plot(months_short, yearly_totals_by_month, marker='o', linewidth=2.5, markersize=6, color='#3498DB', label='Spending')
            ax.fill_between(range(len(months_short)), yearly_totals_by_month, alpha=0.2, color='#3498DB')
            avg_line = [yearly_total/12] * 12
            ax.plot(months_short, avg_line, linestyle='--', linewidth=2, color='#E74C3C', label='Monthly Average')
            ax.set_xlabel('Month', fontsize=9, fontweight='bold')
            ax.set_ylabel('Amount (PKR)', fontsize=9, fontweight='bold')
            ax.grid(True, alpha=0.3, linestyle='--')
            ax.legend(fontsize=8)
            plt.xticks(rotation=45, fontsize=8)
            plt.tight_layout()
            
            chart_buffer = io.BytesIO()
            fig.savefig(chart_buffer, format='png', dpi=100, bbox_inches='tight', facecolor='white')
            chart_buffer.seek(0)
            plt.close(fig)
            
            chart_img2 = Image(chart_buffer2, width=4.5*inch, height=4.5*inch)
            story.append(chart_img2)
            story.append(Spacer(1, 0.15*inch))
            
            # Monthly Breakdown Table
            story.append(Paragraph("<b>Monthly Breakdown</b>", heading_style))
            monthly_table_data = [['Month', 'Spending', 'Transactions']]
            monthly_table_data.extend(monthly_data)
            monthly_table = Table(monthly_table_data, colWidths=[1.7*inch, 1.7*inch, 1.7*inch])
            monthly_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#D5D8DC')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ECF0F1')]),
            ]))
            story.append(monthly_table)
            story.append(Spacer(1, 0.08*inch))
            
            # Category Distribution - Pie Chart
            story.append(Paragraph("<b>Spending Distribution</b>", heading_style))
            fig, ax = plt.subplots(figsize=(4.5, 4.5))
            cats = list(yearly_by_cat.keys())
            amounts = list(yearly_by_cat.values())
            colors_pie = ['#3498DB', '#E74C3C', '#2ECC71', '#F39C12', '#9B59B6', '#1ABC9C', '#34495E', '#E67E22', '#16A085', '#C0392B']
            wedges, texts, autotexts = ax.pie(amounts, labels=cats, autopct='%1.1f%%', colors=colors_pie[:len(cats)], startangle=90)
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(8)
            for text in texts:
                text.set_fontsize(8)
            ax.set_facecolor('#F8F9FA')
            plt.tight_layout()
            
            chart_buffer2 = io.BytesIO()
            fig.savefig(chart_buffer2, format='png', dpi=100, bbox_inches='tight', facecolor='white')
            chart_buffer2.seek(0)
            plt.close(fig)
            
            chart_img2 = Image(chart_buffer2, width=4.0*inch, height=4.0*inch)
            story.append(chart_img2)
            story.append(Spacer(1, 0.05*inch))
            
            # Category Analysis
            story.append(Paragraph("<b>Category Analysis</b>", heading_style))
            cat_data = [['Category', 'Total Amount', 'Percentage', 'Monthly Avg']]
            for cat, amount in sorted(yearly_by_cat.items(), key=lambda x: x[1], reverse=True):
                pct = (amount / yearly_total * 100) if yearly_total > 0 else 0
                monthly_avg = amount / 12
                cat_data.append([cat, f'PKR {int(amount):,}', f'{pct:.1f}%', f'PKR {int(monthly_avg):,}'])
            
            cat_table = Table(cat_data, colWidths=[1.3*inch, 1.5*inch, 1.0*inch, 1.3*inch])
            cat_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27AE60')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#ABEBC6')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#D5F4E6')]),
                ('RIGHTPADDING', (1, 0), (-1, -1), 10),
            ]))
            story.append(cat_table)
            story.append(Spacer(1, 0.08*inch))
            
            # Key Insights
            story.append(Paragraph("<b>Annual Highlights</b>", heading_style))
            insights = []
            
            # Highest spending month
            max_month_idx = yearly_totals_by_month.index(max(yearly_totals_by_month))
            max_month_name = datetime(report_year_y, max_month_idx + 1, 1).strftime("%B")
            max_amount = yearly_totals_by_month[max_month_idx]
            insights.append(f"• Highest spending month: <b>{max_month_name}</b> — PKR {int(max_amount):,}")
            
            # Lowest spending month
            min_month_idx = yearly_totals_by_month.index(min(yearly_totals_by_month))
            min_month_name = datetime(report_year_y, min_month_idx + 1, 1).strftime("%B")
            min_amount = yearly_totals_by_month[min_month_idx]
            insights.append(f"• Lowest spending month: <b>{min_month_name}</b> — PKR {int(min_amount):,}")
            
            # Top category
            top_cat = max(yearly_by_cat, key=yearly_by_cat.get)
            top_amount = yearly_by_cat[top_cat]
            top_pct = (top_amount / yearly_total) * 100
            insights.append(f"• Top spending category: <b>{top_cat}</b> — PKR {int(top_amount):,} ({top_pct:.1f}%)")
            
            # Spending volatility
            std_dev = np.std(yearly_totals_by_month)
            if std_dev < yearly_total / 24:
                consistency = "Very Consistent"
            elif std_dev < yearly_total / 12:
                consistency = "Consistent"
            else:
                consistency = "Variable"
            insights.append(f"• Spending pattern: <b>{consistency}</b> (Std Dev: PKR {int(std_dev):,})")
            
            # Year-over-year projection (if applicable)
            insights.append(f"• Average spending rate: <b>PKR {int(yearly_total/12):,}/month</b> or <b>PKR {int(yearly_total/365):,}/day</b>")
            
            for insight in insights:
                story.append(Paragraph(insight, styles['Normal']))
            
            story.append(Spacer(1, 0.15*inch))
            
            # Footer
            story.append(Paragraph("<i>This comprehensive annual report was automatically generated by PyWallet. All figures are based on transaction data stored in the system. For more detailed analysis or custom date ranges, visit the Analytics section.</i>", styles['Normal']))
            
            # Build PDF
            doc.build(story)
            pdf_buffer.seek(0)
            
            # Download button
            st.download_button(
                label="Download Annual Report PDF",
                data=pdf_buffer.getvalue(),
                file_name=f"PyWallet_Annual_Report_{report_year_y}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key=f"annual_download_{report_year_y}"
            )
            st.success(f"Annual report ready for {report_year_y}!")
            
        except Exception as e:
            st.error(f"Error generating PDF: {str(e)}")
            import traceback
            st.write(traceback.format_exc())

