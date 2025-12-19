import streamlit as st
import pandas as pd
import plotly.express as px
from data_gen import generate_all_datasets
from ingest import ingest_to_memory
import retail_analytics as ra

st.set_page_config(layout='wide', page_title='Retail Hackathon Dashboard')

@st.cache_data
def load_data():
    ds = generate_all_datasets(seed=42)
    return ingest_to_memory(ds)

header, lines, stores, products, customers, promotions, loyalty_rules, inventory = load_data()

st.title('Retail Data Processing — Hackathon')
tab = st.tabs([
    'Data Overview',
    'Promotion Effectiveness',
    'Loyalty Engine',
    'Promotion Funnel',
    'Segmentation (RFM+Loyalty)',
    'Event Log',
    'Notifications',
    'Inventory & Store Performance'
])

with tab[0]:
    st.header('Data Overview')
    st.write('Stores', stores.shape)
    st.write('Products', products.shape)
    st.write('Customers', customers.shape)
    st.write('Sales headers sample')
    st.dataframe(header.head())
    st.write('Sales lines sample')
    st.dataframe(lines.head())
    st.write('Promotions sample')
    st.dataframe(promotions.head())
    st.write('Products sample')
    st.dataframe(products.head())
    # Charts: Histogram of transaction amounts
    try:
        st.subheader('Sales Amount Distribution')
        fig_hist = px.histogram(header, x='total_amount', nbins=50, title='Transaction Amount Distribution')
        st.plotly_chart(fig_hist, width='stretch')
    except Exception:
        pass
    # Chart: Product category distribution (pie)
    try:
        st.subheader('Product Category Distribution')
        cat_counts = products['product_category'].value_counts().reset_index()
        cat_counts.columns = ['product_category','count']
        fig_pie = px.pie(cat_counts, names='product_category', values='count', title='Product Categories')
        st.plotly_chart(fig_pie, width='stretch')
    except Exception:
        pass

with tab[1]:
    st.header('Promotion Performance Analysis (Pre/During/Post)')
    try:
        promo_perf = ra.promotion_analysis(header, lines, promotions, metric='units')
        st.dataframe(promo_perf.head(20))
        st.write('Toggle metric:')
        metric = st.radio('Metric', ['units','revenue'], horizontal=True, key='promo_metric')
        promo_perf2 = ra.promotion_analysis(header, lines, promotions, metric=metric)
        st.dataframe(promo_perf2.head(20))
        # Promotion charts (if aggregated output exists)
        try:
            if not promo_perf2.empty:
                if 'period' in promo_perf2.columns:
                    agg = promo_perf2.groupby('period').agg(units_sold=('units_sold','sum') if 'units_sold' in promo_perf2.columns else ('revenue','sum')).reset_index()
                    if 'units_sold' in promo_perf2.columns:
                        fig_line = px.line(agg, x='period', y='units_sold', title='Units Sold by Period')
                        st.plotly_chart(fig_line, width='stretch')
                    if 'revenue' in promo_perf2.columns:
                        agg_rev = promo_perf2.groupby('period').agg(revenue=('revenue','sum')).reset_index()
                        fig_bar = px.bar(agg_rev, x='period', y='revenue', title='Revenue by Period')
                        st.plotly_chart(fig_bar, width='stretch')
        except Exception:
            pass
    except Exception as e:
        st.error(f"Error in promotion analysis: {e}")

with tab[2]:
    st.header('SuperCoins Loyalty Engine')
    try:
        loyalty_df = ra.loyalty_engine(header, customers)
        st.dataframe(loyalty_df.head(20))
        st.write('Customer loyalty snapshot')
        st.dataframe(customers.head())
    except Exception as e:
        st.error(f"Error in loyalty engine: {e}")

with tab[3]:
    st.header('Promotion Funnel (Amplitude-Style)')
    try:
        funnel = ra.promotion_funnel(header, lines, promotions)
        st.dataframe(funnel)
    except Exception as e:
        st.error(f"Error in promotion funnel: {e}")

with tab[4]:
    st.header('Customer Segmentation (RFM + Loyalty Overlay)')
    try:
        rfm = ra.rfm_segmentation(header, customers)
        st.dataframe(rfm.head(20))
        seg_counts = rfm['segment'].value_counts().reset_index(name='count')
        seg_counts.columns = ['segment','count']
        fig = px.bar(seg_counts, x='segment', y='count', labels={'segment':'segment','count':'count'})
        st.plotly_chart(fig, width='stretch')
        # Donut chart for segment distribution
        try:
            fig_donut = px.pie(seg_counts, names='segment', values='count', hole=0.4, title='Segment Distribution')
            st.plotly_chart(fig_donut, width='stretch')
        except Exception:
            pass
    except Exception as e:
        st.error(f"Error in RFM segmentation: {e}")

with tab[5]:
    st.header('Event Log (Mixpanel-Inspired)')
    try:
        # Use loyalty_df and rfm from previous tabs if available
        if 'loyalty_df' not in locals():
            loyalty_df = ra.loyalty_engine(header, customers)
        if 'rfm' not in locals():
            rfm = ra.rfm_segmentation(header, customers)
        events = ra.event_log(header, lines, loyalty_df, rfm)
        st.dataframe(events.head(30))
    except Exception as e:
        st.error(f"Error in event log: {e}")
with tab[6]:
    st.header('Automated Loyalty Notification System (Simulated)')
    try:
        if 'loyalty_df' not in locals():
            loyalty_df = ra.loyalty_engine(header, customers)
        if 'rfm' not in locals():
            rfm = ra.rfm_segmentation(header, customers)
        notif = ra.notification_simulator(loyalty_df, rfm)
        st.dataframe(notif.head(20))
    except Exception as e:
        st.error(f"Error in notification simulator: {e}")
with tab[7]:
    st.header('Inventory & Store Performance Correlation')
    try:
        inv = ra.inventory_risk_analysis(header, lines, inventory, stores)
        st.dataframe(inv.head(30))
        # Inventory charts: risk distribution and avg days by region
        try:
            if not inv.empty and 'risk' in inv.columns:
                risk_counts = inv['risk'].value_counts().reset_index()
                risk_counts.columns = ['risk','count']
                fig_inv = px.pie(risk_counts, names='risk', values='count', hole=0.4, title='Inventory Risk Distribution')
                st.plotly_chart(fig_inv, width='stretch')
        except Exception:
            pass
        try:
            if not inv.empty and 'store_region' in inv.columns and 'days_of_inventory_left' in inv.columns:
                region_avg = inv.groupby('store_region', as_index=False)['days_of_inventory_left'].mean()
                fig_region = px.bar(region_avg, x='store_region', y='days_of_inventory_left', title='Avg Days of Inventory by Region')
                st.plotly_chart(fig_region, width='stretch')
        except Exception:
            pass
    except Exception as e:
        st.error(f"Error in inventory risk analysis: {e}")

st.sidebar.markdown('---')
st.sidebar.write('Use this app to explore the generated sample data and demo pipelines for the hackathon and analytics modules.')

if __name__ == '__main__':
    st.write('Run `streamlit run app.py` to start the dashboard')
