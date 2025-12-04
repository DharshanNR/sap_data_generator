# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
import numpy as np
import os
#import datetime as dt
# Import data preparation function
from dashboard_prep import load_and_preprocess_data

# --- Configuration and Styling ---
st.set_page_config(layout="wide", page_title="SAP Procurement Analytics")

# Inject custom CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("style.css") # Assuming style.css is in the same directory

# Colorblind-friendly palette (example)
COLORS = {
    "primary": "#0072B2",  # Blue
    "secondary": "#D55E00", # Orange
    "tertiary": "#CC79A7", # Pink
    "accent1": "#009E73",  # Green
    "accent2": "#F0E442",  # Yellow
    "background": "#f4f7f6",
    "text": "#333333",
    "success": "#28a745",
    "warning": "#ffc107",
    "danger": "#dc3545"
}

# --- Helper Functions for Trend Indicators ---
def calculate_trend(current_value, previous_value):
    if previous_value == 0:
        return "N/A", "off" #"neutral"
    change = ((current_value - previous_value) / previous_value) * 100
    if change > 0:
        return f"+{change:.1f}%", "normal"#"positive"
    elif change < 0:
        return f"{change:.1f}%", "inverse"#"negative"
    else:
        return "0.0%", "off" #"neutral"

def get_trend_icon(trend_status):
    if trend_status == "positive":
        return "▲"
    elif trend_status == "negative":
        return "▼"
    return "—"

# --- Data Loading (Cached) ---
data = load_and_preprocess_data()
df_po_items = data["df_po_items"]
df_ekbe_gr = data["df_ekbe_gr"]
lfa1 = data["lfa1"]
mara = data["mara"]
ekko = data["ekko"]
ekpo = data["ekpo"]
ekbe = data["ekbe"]
vendor_contracts = data["vendor_contracts"]

# --- Sidebar Navigation ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", [
    "Executive Overview",
    "Vendor Intelligence",
    "Savings & Opportunities",
    "Material & Category Analysis",
    "Performance Dashboard"
])

# --- Global Date Filter ---
st.sidebar.header("Global Filters")
min_date = df_po_items['AEDAT'].min().date() if not df_po_items.empty else datetime.date(2020, 1, 1)
max_date = df_po_items['AEDAT'].max().date() if not df_po_items.empty else datetime.date(2024, 12, 31)

date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date # Default to full range if only one date selected

# Filter data based on global date range
filtered_po_items = df_po_items[
    (df_po_items['AEDAT'].dt.date >= start_date) &
    (df_po_items['AEDAT'].dt.date <= end_date)
]
filtered_ekko = ekko[
    (ekko['AEDAT'].dt.date >= start_date) &
    (ekko['AEDAT'].dt.date <= end_date)
]
filtered_ekbe_gr = df_ekbe_gr[
    (df_ekbe_gr['BUDAT'].dt.date >= start_date) &
    (df_ekbe_gr['BUDAT'].dt.date <= end_date)
]

# --- Page Content ---

# --- Page 1: Executive Overview ---
if page == "Executive Overview":
    st.title("Executive Overview")

    # --- KPI Cards ---
    col1, col2, col3, col4 = st.columns(4)

    # Total Spend
    current_spend = filtered_po_items['TOTAL_SPEND'].sum()
    # Calculate prior year spend (simplified: last 12 months vs prior 12 months from end_date)
    prior_year_end = end_date - datetime.timedelta(days=365)
    prior_year_start = start_date - datetime.timedelta(days=365)
    prior_spend_df = df_po_items[
        (df_po_items['AEDAT'].dt.date >= prior_year_start) &
        (df_po_items['AEDAT'].dt.date <= prior_year_end)
    ]
    prior_spend = prior_spend_df['TOTAL_SPEND'].sum()
    spend_trend_val, spend_trend_status = calculate_trend(current_spend, prior_spend)
    
    
    with col1:
        st.metric(label="Total Spend", value=f"${current_spend:,.2f}", delta=spend_trend_val, delta_color=spend_trend_status)

    # Contract Compliance Rate
    total_filtered_pos = len(filtered_ekko)
    contract_filtered_pos = len(filtered_ekko[filtered_ekko['BSART'] == 'NB'])
    current_compliance_rate = (contract_filtered_pos / total_filtered_pos) if total_filtered_pos > 0 else 0

    prior_compliance_rate = data["contract_compliance_rate"] # Using global pre-calculated for simplicity
    compliance_trend_val, compliance_trend_status = calculate_trend(current_compliance_rate, prior_compliance_rate)

    with col2:
        st.metric(label="Contract Compliance Rate", value=f"{current_compliance_rate:.1%}", delta=compliance_trend_val, delta_color=compliance_trend_status)

    # On-Time Delivery Rate
    total_deliveries = len(filtered_ekbe_gr)
    late_deliveries = filtered_ekbe_gr['IS_LATE'].sum()
    current_otd_rate = (1 - (late_deliveries / total_deliveries)) if total_deliveries > 0 else 0

    # Prior OTD rate (simplified: using global pre-calculated)
    prior_total_deliveries = len(df_ekbe_gr)
    prior_late_deliveries = df_ekbe_gr['IS_LATE'].sum()
    prior_otd_rate = (1 - (prior_late_deliveries / prior_total_deliveries)) if prior_total_deliveries > 0 else 0
    otd_trend_val, otd_trend_status = calculate_trend(current_otd_rate, prior_otd_rate)

    with col3:
        st.metric(label="On-Time Delivery Rate", value=f"{current_otd_rate:.1%}", delta=otd_trend_val, delta_color=otd_trend_status)

    # Active Vendors
    current_active_vendors = filtered_ekko['LIFNR'].nunique()
    prior_active_vendors = ekko['LIFNR'].nunique() # Using global for simplicity
    active_vendors_trend_val, active_vendors_trend_status = calculate_trend(current_active_vendors, prior_active_vendors)

    with col4:
        st.metric(label="Active Vendors", value=f"{current_active_vendors}", delta=active_vendors_trend_val, delta_color=active_vendors_trend_status)

    st.markdown("---")

    # --- Key Visualizations ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Monthly Spend Trend (Last 24 Months)")
        # Filter monthly spend for the last 24 months relative to end_date
        
        monthly_spend_filtered = data["monthly_spend"][
            (data["monthly_spend"]['MONTH'].dt.date >= ((end_date - pd.DateOffset(months=23)).replace(day=1)).date()) &
            (data["monthly_spend"]['MONTH'].dt.date <= (end_date.replace(day=1)))
        ]
        fig_monthly_spend = px.line(monthly_spend_filtered, x='MONTH', y='SPEND', title='Monthly Spend',
                                    color_discrete_sequence=[COLORS["primary"]])
        fig_monthly_spend.update_layout(hovermode="x unified")
        st.plotly_chart(fig_monthly_spend, use_container_width=True)

    with col2:
        st.subheader("Spend by Category")
        fig_spend_category = px.pie(data["spend_by_category"], values='TOTAL_SPEND', names='CATEGORY', title='Spend by Category',
                                    color_discrete_sequence=px.colors.sequential.RdBu) # Example color sequence
        st.plotly_chart(fig_spend_category, use_container_width=True)

    st.subheader("Top 5 Vendors by Spend")
    top_vendors = data["vendor_summary"].sort_values(by='TOTAL_SPEND', ascending=False).head(5)
    st.dataframe(top_vendors[['NAME1', 'TOTAL_SPEND', 'TOTAL_SPEND_PERCENT', 'ON_TIME_DELIVERY_RATE']].style.format({
        'TOTAL_SPEND': "${:,.2f}",
        'TOTAL_SPEND_PERCENT': "{:.2%}",
        'ON_TIME_DELIVERY_RATE': "{:.1%}"
    }), use_container_width=True)

    st.subheader("Savings Opportunities Summary")
    savings_df = pd.DataFrame(data["savings_opportunities"].items(), columns=['Opportunity Type', 'Potential Savings'])
    fig_savings = px.bar(savings_df, x='Opportunity Type', y='Potential Savings', title='Savings Opportunities',
                         color_discrete_sequence=[COLORS["accent1"]])
    st.plotly_chart(fig_savings, use_container_width=True)

# --- Page 2: Vendor Intelligence ---
elif page == "Vendor Intelligence":
    st.title("Vendor Intelligence")

    # --- Vendor Search/Filter Panel ---
    st.sidebar.header("Vendor Filters")
    vendor_name_search = st.sidebar.text_input("Search by Vendor Name")
    vendor_country_filter = st.sidebar.multiselect("Filter by Country", lfa1['LAND1'].unique())
    vendor_type_filter = st.sidebar.multiselect("Filter by Vendor Type", lfa1['KTOKK'].unique())
    
    # Performance tier (example: based on OTD rate)
    performance_tier_options = ["All", "High (OTD > 90%)", "Medium (OTD 70-90%)", "Low (OTD < 70%)"]
    performance_tier_selected = st.sidebar.selectbox("Filter by Performance Tier", performance_tier_options)

    min_spend, max_spend = float(data["vendor_summary"]['TOTAL_SPEND'].min()), float(data["vendor_summary"]['TOTAL_SPEND'].max())
    spend_range_filter = st.sidebar.slider("Filter by Spend Range", min_spend, max_spend, (min_spend, max_spend))

    filtered_vendors = data["vendor_summary"].copy()

    if vendor_name_search:
        filtered_vendors = filtered_vendors[filtered_vendors['NAME1'].str.contains(vendor_name_search, case=False, na=False)]
    if vendor_country_filter:
        filtered_vendors = filtered_vendors[filtered_vendors['LAND1'].isin(vendor_country_filter)]
    if vendor_type_filter:
        filtered_vendors = filtered_vendors[filtered_vendors['KTOKK'].isin(vendor_type_filter)]
    
    if performance_tier_selected == "High (OTD > 90%)":
        filtered_vendors = filtered_vendors[filtered_vendors['ON_TIME_DELIVERY_RATE'] > 0.9]
    elif performance_tier_selected == "Medium (OTD 70-90%)":
        filtered_vendors = filtered_vendors[(filtered_vendors['ON_TIME_DELIVERY_RATE'] >= 0.7) & (filtered_vendors['ON_TIME_DELIVERY_RATE'] <= 0.9)]
    elif performance_tier_selected == "Low (OTD < 70%)":
        filtered_vendors = filtered_vendors[filtered_vendors['ON_TIME_DELIVERY_RATE'] < 0.7]

    filtered_vendors = filtered_vendors[
        (filtered_vendors['TOTAL_SPEND'] >= spend_range_filter[0]) &
        (filtered_vendors['TOTAL_SPEND'] <= spend_range_filter[1])
    ]

    st.subheader("Vendor Comparison Table")
    # Add # of POs to vendor_summary
    vendor_po_counts = filtered_ekko.groupby('LIFNR')['EBELN'].nunique().reset_index(name='NUM_POS')
    filtered_vendors = pd.merge(filtered_vendors, vendor_po_counts, left_on='LIFNR', right_on='LIFNR', how='left').fillna({'NUM_POS': 0})

    # Placeholder for Price Competitiveness Score and Risk Level
    filtered_vendors['PRICE_COMPETITIVENESS_SCORE'] = np.random.rand(len(filtered_vendors)) * 100 # Dummy score
    filtered_vendors['RISK_LEVEL'] = np.random.choice(['Low', 'Medium', 'High'], len(filtered_vendors), p=[0.6, 0.3, 0.1]) # Dummy risk

    display_cols = ['NAME1', 'LAND1', 'TOTAL_SPEND', 'NUM_POS', 'ON_TIME_DELIVERY_RATE', 'PRICE_COMPETITIVENESS_SCORE', 'RISK_LEVEL']
    st.dataframe(filtered_vendors[display_cols].style.format({
        'TOTAL_SPEND': "${:,.2f}",
        'ON_TIME_DELIVERY_RATE': "{:.1%}",
        'PRICE_COMPETITIVENESS_SCORE': "{:.0f}"
    }), use_container_width=True)

    # --- Selected Vendor Detail View ---
    st.subheader("Selected Vendor Detail")
    selected_vendor_name = st.selectbox("Select a Vendor for Details", filtered_vendors['NAME1'].unique())

    if selected_vendor_name:
        selected_vendor_data = filtered_vendors[filtered_vendors['NAME1'] == selected_vendor_name].iloc[0]
        st.write(f"**Vendor Name:** {selected_vendor_data['NAME1']}")
        st.write(f"**Vendor ID:** {selected_vendor_data['LIFNR']}")
        st.write(f"**Country:** {selected_vendor_data['LAND1']}")
        st.write(f"**Type:** {selected_vendor_data['KTOKK']}")
        st.write(f"**Blocked:** {'Yes' if selected_vendor_data['SPERR'] == 'X' else 'No'}")

        col_det1, col_det2 = st.columns(2)
        with col_det1:
            st.write("#### Spend Trend Over Time")
            vendor_spend_trend = filtered_po_items[filtered_po_items['LIFNR_header'] == selected_vendor_data['LIFNR']].set_index('AEDAT').resample('MS')['TOTAL_SPEND'].sum().reset_index()
            fig_vendor_spend_trend = px.line(vendor_spend_trend, x='AEDAT', y='TOTAL_SPEND', title=f'Spend Trend for {selected_vendor_name}',
                                            color_discrete_sequence=[COLORS["primary"]])
            st.plotly_chart(fig_vendor_spend_trend, use_container_width=True)
        
        with col_det2:
            st.write("#### Performance Metrics")
            st.table(pd.DataFrame({
                "Metric": ["Total Spend", "# of POs", "On-Time Delivery Rate", "Price Competitiveness Score", "Risk Level"],
                "Value": [
                    f"${selected_vendor_data['TOTAL_SPEND']:,.2f}",
                    f"{selected_vendor_data['NUM_POS']}",
                    f"{selected_vendor_data['ON_TIME_DELIVERY_RATE']:.1%}",
                    f"{selected_vendor_data['PRICE_COMPETITIVENESS_SCORE']:.0f}",
                    selected_vendor_data['RISK_LEVEL']
                ]
            }))

        st.write("#### Top 10 Materials Supplied")
        vendor_materials = filtered_po_items[filtered_po_items['LIFNR_header'] == selected_vendor_data['LIFNR']]
        top_materials = vendor_materials.groupby('MAKTX')['TOTAL_SPEND'].sum().nlargest(10).reset_index()
        st.dataframe(top_materials.style.format({'TOTAL_SPEND': "${:,.2f}"}), use_container_width=True)

        st.write("#### Recent Transactions")
        recent_transactions = filtered_po_items[filtered_po_items['LIFNR'] == selected_vendor_data['LIFNR']].sort_values('AEDAT', ascending=False).head(10)
        st.dataframe(recent_transactions[['EBELN', 'AEDAT', 'MATNR', 'MAKTX', 'MENGE', 'NETPR', 'TOTAL_SPEND']].style.format({
            'TOTAL_SPEND': "${:,.2f}", 'NETPR': "${:,.2f}"
        }), use_container_width=True)

    st.markdown("---")

    # --- Vendor Analytics Charts ---
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.subheader("Spend vs Performance Scatter Plot")
        fig_spend_perf = px.scatter(filtered_vendors, x='TOTAL_SPEND', y='ON_TIME_DELIVERY_RATE',
                                    hover_name='NAME1', size='TOTAL_SPEND', color='RISK_LEVEL',
                                    title='Vendor Spend vs On-Time Delivery Rate',
                                    color_discrete_map={'Low': COLORS["accent1"], 'Medium': COLORS["warning"], 'High': COLORS["danger"]})
        st.plotly_chart(fig_spend_perf, use_container_width=True)

    with col_chart2:
        st.subheader("Delivery Performance Distribution")
        fig_delivery_dist = px.histogram(filtered_vendors, x='ON_TIME_DELIVERY_RATE', nbins=20,
                                         title='Distribution of Vendor On-Time Delivery Rates',
                                         color_discrete_sequence=[COLORS["primary"]])
        st.plotly_chart(fig_delivery_dist, use_container_width=True)

    st.subheader("Vendor Risk Matrix (Spend vs Performance)")
    # Create bins for spend and performance
    spend_bins = pd.qcut(filtered_vendors['TOTAL_SPEND'], q=2, labels=['Low Spend', 'High Spend'])
    performance_bins = pd.qcut(filtered_vendors['ON_TIME_DELIVERY_RATE'], q=2, labels=['Low Performance', 'High Performance'])
    
    risk_matrix_data = filtered_vendors.groupby([spend_bins, performance_bins]).size().unstack(fill_value=0)
    
    fig_risk_matrix = px.imshow(risk_matrix_data, text_auto=True, color_continuous_scale='Viridis',
                                 labels=dict(x="Performance", y="Spend", color="Number of Vendors"),
                                 title="Vendor Risk Matrix")
    st.plotly_chart(fig_risk_matrix, use_container_width=True)


# --- Page 3: Savings & Opportunities ---
elif page == "Savings & Opportunities":
    st.title("Savings & Opportunities")

    # --- Opportunity Cards ---
    col1, col2, col3 = st.columns(3)
    total_savings_potential = sum(data["savings_opportunities"].values())
    num_opportunities = len([s for s in data["savings_opportunities"].values() if s > 0])
    estimated_roi = 0.15 # Placeholder

    with col1:
        st.metric(label="Total Savings Potential", value=f"${total_savings_potential:,.2f}")
    with col2:
        st.metric(label="Number of Opportunities", value=f"{num_opportunities}")
    with col3:
        st.metric(label="Estimated ROI %", value=f"{estimated_roi:.1%}")

    st.markdown("---")

    # --- Filters ---
    st.sidebar.header("Opportunity Filters")
    category_filter = st.sidebar.multiselect("Filter by Category", data["spend_by_category"]['CATEGORY'].unique())
    min_savings_threshold = st.sidebar.number_input("Minimum Savings Threshold ($)", min_value=0.0, value=1000.0)
    opportunity_type_filter = st.sidebar.multiselect("Filter by Opportunity Type", list(data["savings_opportunities"].keys()))

    # --- Opportunity Breakdown ---
    st.subheader("Maverick Spend by Category")
    # This requires more detailed data prep to link maverick spend to categories.
    # For now, a dummy chart.
    maverick_by_cat_data = data["spend_by_category"].copy()
    maverick_by_cat_data['Maverick Spend'] = maverick_by_cat_data['TOTAL_SPEND'] * np.random.uniform(0.05, 0.15, len(maverick_by_cat_data))
    fig_maverick = px.bar(maverick_by_cat_data, x='Maverick Spend', y='CATEGORY', orientation='h',
                          title='Maverick Spend by Category', color_discrete_sequence=[COLORS["secondary"]])
    st.plotly_chart(fig_maverick, use_container_width=True)

    st.subheader("Price Variance Opportunities")
    # This needs actual price variance data per material.
    # For now, a dummy table.
    price_variance_table = pd.DataFrame({
        'Material': mara['MAKTX'].sample(5).tolist(),
        'Variance %': np.random.uniform(5, 20, 5),
        'Potential Savings': np.random.uniform(1000, 10000, 5)
    }).style.format({'Variance %': "{:.1%}", 'Potential Savings': "${:,.2f}"})
    st.dataframe(price_variance_table, use_container_width=True)

    st.subheader("Consolidation Opportunities")
    # Dummy table
    consolidation_table = pd.DataFrame({
        'Material': mara['MAKTX'].sample(5).tolist(),
        '# Vendors': np.random.randint(3, 10, 5),
        'Recommended Action': ['Consolidate to 1-2 vendors'] * 5
    })
    st.dataframe(consolidation_table, use_container_width=True)

    st.subheader("Contract Gaps")
    # Dummy table
    contract_gaps_table = pd.DataFrame({
        'Material': mara['MAKTX'].sample(5).tolist(),
        'Annual Spend': np.random.uniform(5000, 50000, 5),
        'Priority': np.random.choice(['High', 'Medium', 'Low'], 5)
    }).style.format({'Annual Spend': "${:,.2f}"})
    st.dataframe(contract_gaps_table, use_container_width=True)

    st.markdown("---")

    # --- Detailed Analysis ---
    col_det_opp1, col_det_opp2 = st.columns(2)
    with col_det_opp1:
        st.subheader("Price Variance Distribution")
        # This needs actual price variance data.
        # For now, a dummy histogram.
        fig_price_var_dist = px.histogram(x=np.random.normal(0, 10, 1000), nbins=30,
                                          title='Price Variance Distribution (%)',
                                          labels={'x': 'Price Variance (%)'},
                                          color_discrete_sequence=[COLORS["tertiary"]])
        st.plotly_chart(fig_price_var_dist, use_container_width=True)

    with col_det_opp2:
        st.subheader("Savings by Opportunity Type")
        savings_df_chart = pd.DataFrame(data["savings_opportunities"].items(), columns=['Opportunity Type', 'Savings'])
        fig_savings_waterfall = go.Figure(go.Waterfall(
            name="Savings",
            orientation="v",
            measure=["relative"] * len(savings_df_chart),
            x=savings_df_chart['Opportunity Type'],
            y=savings_df_chart['Savings'],
            connector={"line": {"color": "rgb(63, 63, 63)"}},
        ))
        fig_savings_waterfall.update_layout(title_text="Savings by Opportunity Type", showlegend=True)
        st.plotly_chart(fig_savings_waterfall, use_container_width=True)

    st.subheader("Priority Matrix (Impact vs Effort)")
    # Dummy data for impact/effort
    priority_data = pd.DataFrame({
        'Opportunity': ['Maverick Spend', 'Price Variance', 'Consolidation', 'Contract Gaps', 'Supplier Development'],
        'Impact': np.random.randint(1, 10, 5),
        'Effort': np.random.randint(1, 10, 5)
    })
    fig_priority_matrix = px.scatter(priority_data, x='Effort', y='Impact', text='Opportunity',
                                     title='Opportunity Priority Matrix',
                                     color_discrete_sequence=[COLORS["accent2"]])
    fig_priority_matrix.update_traces(textposition='top center')
    st.plotly_chart(fig_priority_matrix, use_container_width=True)


# --- Page 4: Material & Category Analysis ---
elif page == "Material & Category Analysis":
    st.title("Material & Category Analysis")

    # --- Category Overview ---
    st.subheader("Spend by Category")
    fig_cat_spend = px.bar(data["spend_by_category"], x='CATEGORY', y='TOTAL_SPEND', title='Spend by Category',
                           color_discrete_sequence=[COLORS["primary"]])
    st.plotly_chart(fig_cat_spend, use_container_width=True)

    st.subheader("Category Trends")
    # This needs more complex data prep to get trends for each category.
    # For now, a dummy line chart.
    category_trend_data = pd.DataFrame({
        'Month': pd.to_datetime(pd.date_range(start='2023-01-01', periods=12, freq='M')),
        'Electronics': np.random.rand(12) * 100000,
        'Office Supplies': np.random.rand(12) * 50000,
        'Raw Materials': np.random.rand(12) * 75000,
        'Services': np.random.rand(12) * 120000
    }).melt(id_vars=['Month'], var_name='Category', value_name='Spend')
    fig_cat_trends = px.line(category_trend_data, x='Month', y='Spend', color='Category',
                             title='Category Spend Trends',
                             color_discrete_sequence=[COLORS["primary"], COLORS["secondary"], COLORS["accent1"], COLORS["tertiary"]])
    st.plotly_chart(fig_cat_trends, use_container_width=True)

    st.subheader("Category Performance Scorecard")
    # Dummy scorecard
    category_scorecard = pd.DataFrame({
        'Category': data["spend_by_category"]['CATEGORY'].tolist(),
        'Spend Share': data["spend_by_category"]['TOTAL_SPEND'] / data["spend_by_category"]['TOTAL_SPEND'].sum(),
        'Avg OTD': np.random.uniform(0.8, 0.99, len(data["spend_by_category"])),
        'Avg Price Competitiveness': np.random.uniform(70, 95, len(data["spend_by_category"]))
    }).style.format({'Spend Share': "{:.1%}", 'Avg OTD': "{:.1%}", 'Avg Price Competitiveness': "{:.0f}"})
    st.dataframe(category_scorecard, use_container_width=True)

    st.markdown("---")

    # --- Material Search & Detail ---
    st.subheader("Material Search & Detail")
    material_search_term = st.text_input("Search Material by Description or ID")
    
    filtered_materials = mara.copy()
    if material_search_term:
        filtered_materials = filtered_materials[
            filtered_materials['MAKTX'].str.contains(material_search_term, case=False, na=False) |
            filtered_materials['MATNR'].str.contains(material_search_term, case=False, na=False)
        ]
    
    st.dataframe(filtered_materials[['MATNR', 'MAKTX', 'MATKL', 'MTART', 'MEINS']], use_container_width=True)

    selected_matnr = st.selectbox("Select a Material for Details", filtered_materials['MATNR'].unique())

    if selected_matnr:
        st.write(f"#### Details for Material: {selected_matnr}")
        material_detail = mara[mara['MATNR'] == selected_matnr].iloc[0]
        st.write(f"**Description:** {material_detail['MAKTX']}")
        st.write(f"**Category:** {material_detail['MATKL']}")
        st.write(f"**Type:** {material_detail['MTART']}")
        st.write(f"**Unit:** {material_detail['MEINS']}")

        material_po_items = filtered_po_items[filtered_po_items['MATNR'] == selected_matnr]

        col_mat_det1, col_mat_det2 = st.columns(2)
        with col_mat_det1:
            st.write("##### Purchase History (Prices Over Time)")
            price_history = material_po_items.groupby('AEDAT')['NETPR'].mean().reset_index()
            fig_price_history = px.line(price_history, x='AEDAT', y='NETPR', title='Average Price Over Time',
                                        color_discrete_sequence=[COLORS["primary"]])
            st.plotly_chart(fig_price_history, use_container_width=True)
        
        with col_mat_det2:
            st.write("##### Price Statistics")
            if not material_po_items.empty:
                st.table(pd.DataFrame({
                    "Statistic": ["Min Price", "Max Price", "Avg Price", "Std Dev Price"],
                    "Value": [
                        f"${material_po_items['NETPR'].min():,.2f}",
                        f"${material_po_items['NETPR'].max():,.2f}",
                        f"${material_po_items['NETPR'].mean():,.2f}",
                        f"${material_po_items['NETPR'].std():,.2f}"
                    ]
                }))
            else:
                st.info("No purchase history for this material in the selected date range.")

        st.write("##### Vendor Comparison for this Material")
       
        vendor_comp_mat = material_po_items.groupby('NAME1').agg(
            TotalSpend=('TOTAL_SPEND', 'sum'),
            AvgPrice=('NETPR', 'mean'),
            NumPOs=('EBELN', 'nunique')
        ).reset_index().sort_values('TotalSpend', ascending=False)
        st.dataframe(vendor_comp_mat.style.format({'TotalSpend': "${:,.2f}", 'AvgPrice': "${:,.2f}"}), use_container_width=True)

        st.write("##### Contract Status")
        material_contracts = vendor_contracts[vendor_contracts['MATNR'] == selected_matnr]
        if not material_contracts.empty:
            st.dataframe(material_contracts[['LIFNR', 'CONTRACT_PRICE', 'VALID_FROM', 'VALID_TO', 'CONTRACT_TYPE']].style.format({
                'CONTRACT_PRICE': "${:,.2f}"
            }), use_container_width=True)
        else:
            st.info("No active contracts for this material.")

    st.markdown("---")

    # --- Category Deep Dive ---
    st.subheader("Category Deep Dive")
    selected_category = st.selectbox("Select a Category for Deep Dive", data["spend_by_category"]['CATEGORY'].unique())

    if selected_category:
        category_po_items = filtered_po_items[filtered_po_items['MATKL_material'] == selected_category]

        col_cat_deep1, col_cat_deep2 = st.columns(2)
        with col_cat_deep1:
            st.write(f"##### Top Materials by Spend in {selected_category}")
            top_materials_in_cat = category_po_items.groupby('MAKTX')['TOTAL_SPEND'].sum().nlargest(10).reset_index()
            fig_top_materials = px.bar(top_materials_in_cat, x='TOTAL_SPEND', y='MAKTX', orientation='h',
                                       title=f'Top Materials in {selected_category}',
                                       color_discrete_sequence=[COLORS["accent1"]])
            st.plotly_chart(fig_top_materials, use_container_width=True)
        
        with col_cat_deep2:
            st.write(f"##### Vendor Concentration in {selected_category}")
            vendor_concentration = category_po_items.groupby('NAME1')['TOTAL_SPEND'].sum().nlargest(10).reset_index()
            fig_vendor_conc = px.pie(vendor_concentration, values='TOTAL_SPEND', names='NAME1',
                                     title=f'Vendor Spend Share in {selected_category}',
                                     color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig_vendor_conc, use_container_width=True)

        st.write(f"##### Price Trends by Material in {selected_category}")
        # This needs to show multiple lines for top materials
        top_materials_list = top_materials_in_cat['MAKTX'].tolist()
        price_trends_cat = category_po_items[category_po_items['MAKTX'].isin(top_materials_list)].groupby(['AEDAT', 'MAKTX'])['NETPR'].mean().reset_index()
        fig_price_trends_cat = px.line(price_trends_cat, x='AEDAT', y='NETPR', color='MAKTX',
                                       title=f'Price Trends for Top Materials in {selected_category}',
                                       color_discrete_sequence=px.colors.qualitative.Plotly)
        st.plotly_chart(fig_price_trends_cat, use_container_width=True)


# --- Page 5: Performance Dashboard ---
elif page == "Performance Dashboard":
    st.title("Performance Dashboard")
    total_deliveries = len(filtered_ekbe_gr)
    late_deliveries = filtered_ekbe_gr['IS_LATE'].sum()
    current_otd_rate = (1 - (late_deliveries / total_deliveries)) if total_deliveries > 0 else 0

    # --- Performance Metrics Overview ---
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Overall OTD%")
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=current_otd_rate,
            title={'text': "Overall On-Time Delivery Rate"},
            gauge={'axis': {'range': [0, 1]},
                   'bar': {'color': COLORS["primary"]},
                   'steps': [
                       {'range': [0, 0.7], 'color': COLORS["danger"]},
                       {'range': [0.7, 0.9], 'color': COLORS["warning"]},
                       {'range': [0.9, 1], 'color': COLORS["success"]}],
                   'threshold': {'line': {'color': "black", 'width': 4}, 'thickness': 0.75, 'value': current_otd_rate}}
        ))
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col2:
        st.subheader("Average Delivery Delay")
        avg_delay = filtered_ekbe_gr[filtered_ekbe_gr['IS_LATE'] == 1]['DELIVERY_DELAY_DAYS'].mean()
        st.metric(label="Avg. Delay (Days)", value=f"{avg_delay:.1f}" if not pd.isna(avg_delay) else "0.0")

    with col3:
        st.subheader("Performance Trend (Last 12 Months)")
        # Monthly OTD rate
        monthly_otd = filtered_ekbe_gr.set_index('BUDAT').resample('MS').agg(
            total_deliveries=('EBELN', 'count'),
            late_deliveries=('IS_LATE', 'sum')
        ).reset_index()
        monthly_otd['OTD_RATE'] = (1 - (monthly_otd['late_deliveries'] / monthly_otd['total_deliveries'])).fillna(0)
        
        monthly_otd_filtered = monthly_otd[
            (monthly_otd['BUDAT'].dt.date >= (end_date - pd.DateOffset(months=11)).replace(day=1).date()) &
            (monthly_otd['BUDAT'].dt.date <= end_date.replace(day=1))
        ]
        fig_otd_trend = px.line(monthly_otd_filtered, x='BUDAT', y='OTD_RATE', title='Monthly OTD Rate',
                                color_discrete_sequence=[COLORS["accent1"]])
        st.plotly_chart(fig_otd_trend, use_container_width=True)

    st.markdown("---")

    # --- Vendor Performance Analysis ---
    st.subheader("Performance by Vendor (Top 20 by Spend)")
    top_20_vendors_by_spend = data["vendor_summary"].sort_values('TOTAL_SPEND', ascending=False).head(20)
    fig_vendor_perf = px.bar(top_20_vendors_by_spend, x='ON_TIME_DELIVERY_RATE', y='NAME1', orientation='h',
                             title='On-Time Delivery Rate by Vendor',
                             color='ON_TIME_DELIVERY_RATE',
                             color_continuous_scale=[COLORS["danger"], COLORS["warning"], COLORS["success"]],
                             labels={'ON_TIME_DELIVERY_RATE': 'OTD Rate'})
    st.plotly_chart(fig_vendor_perf, use_container_width=True)

    st.subheader("Performance Distribution")
    fig_perf_dist = px.histogram(data["vendor_summary"], x='ON_TIME_DELIVERY_RATE', nbins=20,
                                 title='Distribution of Vendor OTD Rates',
                                 color_discrete_sequence=[COLORS["primary"]])
    st.plotly_chart(fig_perf_dist, use_container_width=True)

    st.subheader("Vendors Below Threshold (OTD < 80%)")
    below_threshold_vendors = data["vendor_summary"][data["vendor_summary"]['ON_TIME_DELIVERY_RATE'] < 0.8]
    if not below_threshold_vendors.empty:
        st.dataframe(below_threshold_vendors[['NAME1', 'ON_TIME_DELIVERY_RATE', 'TOTAL_SPEND']].style.format({
            'ON_TIME_DELIVERY_RATE': "{:.1%}", 'TOTAL_SPEND': "${:,.2f}"
        }).apply(lambda x: ['background-color: #f8d7da' if x.name == 'ON_TIME_DELIVERY_RATE' and x.iloc[0] < 0.8 else '' for _ in x], axis=1),
        use_container_width=True)
    else:
        st.info("No vendors currently below the 80% OTD threshold.")

    st.markdown("---")

    # --- Delivery Analysis ---
    st.subheader("Delivery Analysis")
    col_del_an1, col_del_an2 = st.columns(2)

    with col_del_an1:
        st.write("##### Late Deliveries by Reason/Category")
        # This needs a 'reason' field in EKBE or a way to infer.
        # For now, let's use material category as a proxy.
        late_deliveries_by_cat = filtered_po_items[filtered_po_items['EBELN'].isin(filtered_ekbe_gr[filtered_ekbe_gr['IS_LATE'] == 1]['EBELN'].unique())]
        late_deliveries_by_cat_agg = late_deliveries_by_cat.groupby('MATKL_material').size().reset_index(name='Late Count')
        fig_late_by_cat = px.bar(late_deliveries_by_cat_agg, x='Late Count', y='MATKL_material', orientation='h',
                                 title='Late Deliveries by Material Category',
                                 color_discrete_sequence=[COLORS["danger"]])
        st.plotly_chart(fig_late_by_cat, use_container_width=True)

    with col_del_an2:
        st.write("##### Delivery Variance Box Plot by Vendor")
        # Filter for vendors with at least some late deliveries
        vendors_with_delays = filtered_ekbe_gr[filtered_ekbe_gr['DELIVERY_DELAY_DAYS'] > 0]['LIFNR'].unique()
        delay_data_for_plot = filtered_ekbe_gr[filtered_ekbe_gr['LIFNR'].isin(vendors_with_delays)]
        
        if not delay_data_for_plot.empty:
            fig_delay_boxplot = px.box(delay_data_for_plot, x='LIFNR', y='DELIVERY_DELAY_DAYS',
                                       title='Delivery Delay (Days) by Vendor',
                                       color_discrete_sequence=[COLORS["secondary"]])
            st.plotly_chart(fig_delay_boxplot, use_container_width=True)
        else:
            st.info("No delivery delays to plot.")

    st.subheader("Monthly Performance Heatmap (Vendors × Months)")
    # This is complex. Let's simplify to OTD rate per vendor per month.
    vendor_monthly_otd = filtered_ekbe_gr.groupby([filtered_ekbe_gr['BUDAT'].dt.to_period('M'), 'LIFNR']).agg(
        total_deliveries=('EBELN', 'count'),
        late_deliveries=('IS_LATE', 'sum')
    ).reset_index()
    vendor_monthly_otd['OTD_RATE'] = (1 - (vendor_monthly_otd['late_deliveries'] / vendor_monthly_otd['total_deliveries'])).fillna(0)
    
    # Pivot for heatmap
    heatmap_data = vendor_monthly_otd.pivot_table(index='LIFNR', columns='BUDAT', values='OTD_RATE').fillna(0)
    
    if not heatmap_data.empty:
        fig_heatmap = px.imshow(heatmap_data,
                                 labels=dict(x="Month", y="Vendor", color="OTD Rate"),
                                 x=heatmap_data.columns.astype(str).tolist(),
                                 y=heatmap_data.index.tolist(),
                                 color_continuous_scale='RdYlGn', # Red-Yellow-Green for performance
                                 title="Monthly OTD Rate Heatmap by Vendor")
        st.plotly_chart(fig_heatmap, use_container_width=True)
    else:
        st.info("Not enough data to generate monthly performance heatmap.")

    st.subheader("Quality Indicators (Placeholder)")
    st.info("Order accuracy metrics, response time analysis, and trend indicators would be implemented here with relevant data.")