# HMO Tenant Analysis Dashboard - Streamlit App
# Find the best tenants for your rental properties

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Configure page
st.set_page_config(
    page_title="HMO Tenant Analysis Dashboard",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    body {
        color: #333333;
    }
    .main-header {
        font-size: 3rem;
        color: #1f4e79;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #1f4e79;
    }
    .tenant-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    .tenant-card h4,
    .tenant-card div {
        color: #333333;
    }
    .excellent-tenant {
        border-left: 5px solid #28a745;
    }
    .good-tenant {
        border-left: 5px solid #17a2b8;
    }
    .average-tenant {
        border-left: 5px solid #ffc107;
    }
    .poor-tenant {
        border-left: 5px solid #dc3545;
    }
</style>
""", unsafe_allow_html=True)

# Title and description
st.markdown('<h1 class="main-header">🏠 HMO Tenant Analysis Dashboard</h1>', unsafe_allow_html=True)
st.markdown("### Find the Best Tenants for Your Rental Properties")
st.markdown("---")

# Tenant scoring function
@st.cache_data
def calculate_tenant_score(row):
    """Calculate comprehensive tenant quality score (0-100)"""
    score = 0
    
    # Payment reliability (30 points max)
    if row['Rent Paid On Time'] == 'Yes':
        score += 25
    if row['Late Payments'] == 0:
        score += 5
    elif row['Late Payments'] <= 2:
        score += 2
    
    # Property care (25 points max)
    if row['Damage To Property'] == 'No':
        score += 15
    if row['Noise Complaints'] == 0:
        score += 5
    elif row['Noise Complaints'] <= 1:
        score += 2
    
    # Cleanliness (5 points max)
    cleanliness_scores = {'Excellent': 5, 'Good': 3, 'Average': 1, 'Poor': 0}
    score += cleanliness_scores.get(row['Room Cleanliness'], 0)
    
    # Stability indicators (20 points max)
    if row['Tenancy Duration (Months)'] >= 12:
        score += 10
    elif row['Tenancy Duration (Months)'] >= 6:
        score += 5
    
    if row['Employment Duration (Years)'] >= 2:
        score += 5
    elif row['Employment Duration (Years)'] >= 1:
        score += 3
    
    if row['Eviction Notice'] == 'No':
        score += 5
    
    # Financial stability (15 points max)
    if row['Credit Score'] >= 750:
        score += 8
    elif row['Credit Score'] >= 650:
        score += 5
    elif row['Credit Score'] >= 550:
        score += 2
    
    # Reference score (5 points max)
    score += min(row['Reference Score (1-10)'] * 0.5, 5)
    
    # Lifestyle factors
    if row['Smoking Status'] == 'Non-smoker':
        score += 2
    if row['Pet Owner'] == 'No':
        score += 2
    
    return min(score, 100)

def categorize_tenant(score):
    """Categorize tenant based on score"""
    if score >= 80:
        return "Excellent (Premium)"
    elif score >= 70:
        return "Very Good"
    elif score >= 60:
        return "Good"
    elif score >= 50:
        return "Average"
    else:
        return "Poor (High Risk)"

def get_category_color(category):
    """Get color for category"""
    colors = {
        "Excellent (Premium)": "#28a745",
        "Very Good": "#17a2b8", 
        "Good": "#20c997",
        "Average": "#ffc107",
        "Poor (High Risk)": "#dc3545"
    }
    return colors.get(category, "#6c757d")

# File upload
st.sidebar.header("📁 Upload Data")
uploaded_file = st.sidebar.file_uploader(
    "Upload HMO Tenant CSV file",
    type=['csv'],
    help="Upload your tenant data CSV file to begin analysis"
)

if uploaded_file is not None:
    # Load and process data
    try:
        df = pd.read_csv(uploaded_file)
        
        df['Damage To Property'] = df['Damage To Property'].fillna('Not Available')
        
        # Calculate scores
        df['Tenant_Quality_Score'] = df.apply(calculate_tenant_score, axis=1)
        df['Quality_Category'] = df['Tenant_Quality_Score'].apply(categorize_tenant)
        
        # Add age groups for analysis
        df['Age_Group'] = pd.cut(df['Age'], bins=[0, 25, 35, 45, 100], labels=['18-25', '26-35', '36-45', '45+'])
        
        st.success(f"✅ Data loaded successfully! Analyzing {len(df)} tenants.")
        
        # Sidebar filters
        st.sidebar.header("🔍 Filters")
        
        # Score filter
        min_score = st.sidebar.slider(
            "Minimum Quality Score",
            min_value=0,
            max_value=100,
            value=0,
            help="Filter tenants by minimum quality score"
        )
        
        # Category filter
        categories = st.sidebar.multiselect(
            "Quality Categories",
            options=df['Quality_Category'].unique(),
            default=df['Quality_Category'].unique(),
            help="Select tenant quality categories to display"
        )
        
        # Employment status filter
        employment_options = st.sidebar.multiselect(
            "Employment Status",
            options=df['Employment Status'].unique(),
            default=df['Employment Status'].unique()
        )
        
        # Payment reliability filter
        payment_filter = st.sidebar.selectbox(
            "Payment Reliability",
            options=['All', 'Pays On Time Only', 'Has Late Payments'],
            help="Filter by payment history"
        )
        
        # Apply filters
        filtered_df = df[
            (df['Tenant_Quality_Score'] >= min_score) &
            (df['Quality_Category'].isin(categories)) &
            (df['Employment Status'].isin(employment_options))
        ]
        
        if payment_filter == 'Pays On Time Only':
            filtered_df = filtered_df[filtered_df['Rent Paid On Time'] == 'Yes']
        elif payment_filter == 'Has Late Payments':
            filtered_df = filtered_df[filtered_df['Rent Paid On Time'] == 'No']
        
        # Main dashboard
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Tenants",
                len(filtered_df),
                delta=f"{len(filtered_df) - len(df)} from total"
            )
        
        with col2:
            avg_score = filtered_df['Tenant_Quality_Score'].mean()
            st.metric(
                "Average Score",
                f"{avg_score:.1f}",
                delta=f"{avg_score - df['Tenant_Quality_Score'].mean():.1f}"
            )
        
        with col3:
            excellent_count = len(filtered_df[filtered_df['Quality_Category'] == 'Excellent (Premium)'])
            st.metric(
                "Excellent Tenants",
                excellent_count,
                delta=f"{excellent_count/len(filtered_df)*100:.1f}%" if len(filtered_df) > 0 else "0%"
            )
        
        with col4:
            reliable_payers = len(filtered_df[filtered_df['Rent Paid On Time'] == 'Yes'])
            st.metric(
                "Reliable Payers",
                reliable_payers,
                delta=f"{reliable_payers/len(filtered_df)*100:.1f}%" if len(filtered_df) > 0 else "0%"
            )
        
        # Main content tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🏆 Top Tenants", 
            "📊 Analytics", 
            "🔍 Tenant Search", 
            "📈 Insights", 
            "📋 Full Report"
        ])
        
        with tab1:
            st.header("🏆 Top Performing Tenants")
            
            # Top tenants selection
            top_n = st.selectbox("Show top:", [5, 10, 15, 20], index=1)
            
            top_tenants = filtered_df.nlargest(top_n, 'Tenant_Quality_Score')
            
            for i, (idx, tenant) in enumerate(top_tenants.iterrows(), 1):
                category_class = {
                    "Excellent (Premium)": "excellent-tenant",
                    "Very Good": "good-tenant", 
                    "Good": "good-tenant",
                    "Average": "average-tenant",
                    "Poor (High Risk)": "poor-tenant"
                }.get(tenant['Quality_Category'], "average-tenant")
                
                st.markdown(f"""
                <div class="tenant-card {category_class}">
                    <h4>#{i} {tenant['Name']} - Score: {tenant['Tenant_Quality_Score']:.1f}/100</h4>
                    <div style="display: flex; gap: 20px; flex-wrap: wrap;">
                        <div><strong>Age:</strong> {tenant['Age']}</div>
                        <div><strong>Employment:</strong> {tenant['Employment Status']}</div>
                        <div><strong>Income:</strong> £{tenant['Monthly Salary (£)']}</div>
                        <div><strong>Credit Score:</strong> {tenant['Credit Score']}</div>
                    </div>
                    <div style="display: flex; gap: 20px; flex-wrap: wrap; margin-top: 10px;">
                        <div><strong>Pays On Time:</strong> {tenant['Rent Paid On Time']}</div>
                        <div><strong>Late Payments:</strong> {tenant['Late Payments']}</div>
                        <div><strong>Property Damage:</strong> {tenant['Damage To Property']}</div>
                        <div><strong>Tenancy:</strong> {tenant['Tenancy Duration (Months)']} months</div>
                    </div>
                    <div style="margin-top: 10px;">
                        <span style="background-color: {get_category_color(tenant['Quality_Category'])}; color: white; padding: 5px 10px; border-radius: 15px; font-size: 12px;">
                            {tenant['Quality_Category']}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        with tab2:
            st.header("📊 Tenant Analytics")
            
            # Create visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                # Score distribution
                fig_hist = px.histogram(
                    filtered_df, 
                    x='Tenant_Quality_Score',
                    title='Tenant Quality Score Distribution',
                    nbins=20,
                    color_discrete_sequence=['#1f4e79']
                )
                fig_hist.add_vline(
                    x=filtered_df['Tenant_Quality_Score'].mean(),
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"Average: {filtered_df['Tenant_Quality_Score'].mean():.1f}"
                )
                st.plotly_chart(fig_hist, use_container_width=True)
                
                # Payment reliability
                payment_counts = filtered_df['Rent Paid On Time'].value_counts()
                fig_pie = px.pie(
                    values=payment_counts.values,
                    names=payment_counts.index,
                    title='Payment Reliability Distribution',
                    color_discrete_map={'Yes': '#28a745', 'No': '#dc3545'}
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                # Quality categories
                category_counts = filtered_df['Quality_Category'].value_counts()
                fig_bar = px.bar(
                    x=category_counts.index,
                    y=category_counts.values,
                    title='Tenants by Quality Category',
                    color=category_counts.index,
                    color_discrete_map={
                        "Excellent (Premium)": "#28a745",
                        "Very Good": "#17a2b8", 
                        "Good": "#20c997",
                        "Average": "#ffc107",
                        "Poor (High Risk)": "#dc3545"
                    }
                )
                fig_bar.update_layout(showlegend=False)
                st.plotly_chart(fig_bar, use_container_width=True)
                
                # Income vs Score scatter
                fig_scatter = px.scatter(
                    filtered_df,
                    x='Annual Income (£)',
                    y='Tenant_Quality_Score',
                    color='Credit Score',
                    title='Income vs Quality Score',
                    hover_data=['Name', 'Employment Status']
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
        
        with tab3:
            st.header("🔍 Tenant Search & Details")
            
            # Search functionality
            search_term = st.text_input("🔍 Search by name:", placeholder="Enter tenant name...")
            
            if search_term:
                search_results = filtered_df[
                    filtered_df['Name'].str.contains(search_term, case=False, na=False)
                ]
            else:
                search_results = filtered_df
            
            # Sort options
            sort_by = st.selectbox(
                "Sort by:",
                ['Tenant_Quality_Score', 'Annual Income (£)', 'Credit Score', 'Age', 'Name']
            )
            sort_order = st.radio("Order:", ['Descending', 'Ascending'], horizontal=True)
            
            sorted_results = search_results.sort_values(
                sort_by, 
                ascending=(sort_order == 'Ascending')
            )
            
            # Display results
            st.write(f"Found {len(sorted_results)} tenants")
            
            # Detailed tenant cards
            for idx, tenant in sorted_results.iterrows():
                with st.expander(f"{tenant['Name']} - Score: {tenant['Tenant_Quality_Score']:.1f}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write("**Personal Info**")
                        st.write(f"Age: {tenant['Age']}")
                        st.write(f"Employment: {tenant['Employment Status']}")
                        st.write(f"Employment Duration: {tenant['Employment Duration (Years)']} years")
                        
                    with col2:
                        st.write("**Financial Info**")
                        st.write(f"Annual Income: £{tenant['Annual Income (£)']:,.0f}")
                        st.write(f"Monthly Salary: £{tenant['Monthly Salary (£)']:,.0f}")
                        st.write(f"Credit Score: {tenant['Credit Score']}")
                        
                    with col3:
                        st.write("**Rental History**")
                        st.write(f"Pays On Time: {tenant['Rent Paid On Time']}")
                        st.write(f"Late Payments: {tenant['Late Payments']}")
                        st.write(f"Property Damage: {tenant['Damage To Property']}")
                        st.write(f"Noise Complaints: {tenant['Noise Complaints']}")
                        st.write(f"Tenancy Duration: {tenant['Tenancy Duration (Months)']} months")
                        
                    st.write("**Additional Info**")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.write(f"Smoking: {tenant['Smoking Status']}")
                    with col2:
                        st.write(f"Pets: {tenant['Pet Owner']}")
                    with col3:
                        st.write(f"Cleanliness: {tenant['Room Cleanliness']}")
                    with col4:
                        st.write(f"Reference Score: {tenant['Reference Score (1-10)']}/10")
        
        with tab4:
            st.header("📈 Key Insights & Recommendations")
            
            # Key insights
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🎯 Employment Impact")
                employed = filtered_df[filtered_df['Employment Status'] != 'Unemployed']
                unemployed = filtered_df[filtered_df['Employment Status'] == 'Unemployed']
                
                if len(employed) > 0 and len(unemployed) > 0:
                    st.write(f"**Employed tenants average score:** {employed['Tenant_Quality_Score'].mean():.1f}")
                    st.write(f"**Unemployed tenants average score:** {unemployed['Tenant_Quality_Score'].mean():.1f}")
                    st.write(f"**Difference:** {employed['Tenant_Quality_Score'].mean() - unemployed['Tenant_Quality_Score'].mean():.1f} points")
                
                st.subheader("💰 Income Analysis")
                median_income = filtered_df['Annual Income (£)'].median()
                high_income = filtered_df[filtered_df['Annual Income (£)'] >= median_income]
                low_income = filtered_df[filtered_df['Annual Income (£)'] < median_income]
                
                st.write(f"**Median income:** £{median_income:,.0f}")
                if len(high_income) > 0 and len(low_income) > 0:
                    st.write(f"**High income group score:** {high_income['Tenant_Quality_Score'].mean():.1f}")
                    st.write(f"**Low income group score:** {low_income['Tenant_Quality_Score'].mean():.1f}")
            
            with col2:
                st.subheader("📊 Age Group Performance")
                age_performance = filtered_df.groupby('Age_Group')['Tenant_Quality_Score'].mean().sort_values(ascending=False)
                
                for age_group, score in age_performance.items():
                    st.write(f"**{age_group}:** {score:.1f} average score")
                
                st.subheader("💳 Credit Score Impact")
                excellent_credit = filtered_df[filtered_df['Credit Score'] >= 750]
                good_credit = filtered_df[(filtered_df['Credit Score'] >= 650) & (filtered_df['Credit Score'] < 750)]
                poor_credit = filtered_df[filtered_df['Credit Score'] < 650]
                
                if len(excellent_credit) > 0:
                    st.write(f"**Excellent credit (750+):** {excellent_credit['Tenant_Quality_Score'].mean():.1f}")
                if len(good_credit) > 0:
                    st.write(f"**Good credit (650-749):** {good_credit['Tenant_Quality_Score'].mean():.1f}")
                if len(poor_credit) > 0:
                    st.write(f"**Poor credit (<650):** {poor_credit['Tenant_Quality_Score'].mean():.1f}")
            
            # Recommendations
            st.subheader("💡 Screening Recommendations")
            
            excellent_count = len(filtered_df[filtered_df['Quality_Category'] == 'Excellent (Premium)'])
            very_good_count = len(filtered_df[filtered_df['Quality_Category'] == 'Very Good'])
            risky_count = len(filtered_df[filtered_df['Quality_Category'] == 'Poor (High Risk)'])
            
            st.success(f"🌟 **Priority Tenants (Score 80+):** {excellent_count} available - Lowest risk, highest reliability")
            st.info(f"✅ **Strong Tenants (Score 70-79):** {very_good_count} available - Solid choice with minor considerations")
            st.warning(f"⚠️ **High Risk Tenants (Score <50):** {risky_count} to avoid - Consider additional security or guarantors")
            
            st.write("**Key Screening Criteria:**")
            st.write("1. Payment history (most important)")
            st.write("2. Property care record")
            st.write("3. Employment stability")
            st.write("4. Credit score 650+")
            st.write("5. Positive references")
        
        with tab5:
            st.header("📋 Full Tenant Report")
            
            # Export options
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📥 Download Top 20 Tenants"):
                    top_20 = filtered_df.nlargest(20, 'Tenant_Quality_Score')
                    csv = top_20.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"top_20_tenants_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
            
            with col2:
                if st.button("📥 Download All Filtered"):
                    csv = filtered_df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"filtered_tenants_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
            
            with col3:
                if st.button("📥 Download Complete Dataset"):
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"complete_tenant_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
            
            # Full data table
            st.subheader("Complete Tenant Database")
            
            # Column selection for display
            display_columns = st.multiselect(
                "Select columns to display:",
                options=filtered_df.columns.tolist(),
                default=['Name', 'Age', 'Employment Status', 'Annual Income (£)', 
                        'Rent Paid On Time', 'Credit Score', 'Quality_Category', 'Tenant_Quality_Score']
            )
            
            if display_columns:
                st.dataframe(
                    filtered_df[display_columns].sort_values('Tenant_Quality_Score', ascending=False),
                    use_container_width=True,
                    height=400
                )
        
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.write("Please make sure your CSV file has the correct column names and format.")

else:
    # Landing page when no file is uploaded
    st.info("👆 Please upload your HMO tenant CSV file using the sidebar to begin analysis.")
    
    st.markdown("""
    ### 🏠 HMO Tenant Analysis Dashboard
    
    This dashboard helps you identify the best tenants for your rental properties by analyzing:
    
    #### 📊 **Scoring Criteria:**
    - **Payment Reliability** (30 points): On-time rent payments, minimal late payments
    - **Property Care** (25 points): No damage, minimal noise complaints
    - **Stability** (20 points): Long tenancy duration, stable employment
    - **Financial Strength** (15 points): Credit score assessment
    - **Cleanliness & References** (10 points): Room condition and reference scores
    
    #### 🎯 **Key Features:**
    - Interactive filtering and search
    - Comprehensive tenant scoring (0-100)
    - Visual analytics and insights
    - Export capabilities for decision making
    - Risk categorization and recommendations
    
    #### 📁 **Required CSV Columns:**
    Your CSV file should include: Name, Age, Employment Status, Annual Income, Rent Paid On Time, 
    Noise Complaints, Damage To Property, Tenancy Duration, Late Payments, Credit Score, Reference Score, etc.
    
    **Upload your data to get started!**
    """)
    
    # Sample data preview
    st.subheader("📋 Expected Data Format")
    sample_data = {
        'Name': ['John Smith', 'Sarah Johnson', 'Mike Brown'],
        'Age': [28, 35, 24],
        'Employment Status': ['Full-time', 'Part-time', 'Student'],
        'Annual Income (£)': [35000, 28000, 15000],
        'Rent Paid On Time': ['Yes', 'Yes', 'No'],
        'Credit Score': [720, 680, 550],
        'Tenancy Duration (Months)': [18, 12, 6]
    }
    st.dataframe(pd.DataFrame(sample_data), use_container_width=True)