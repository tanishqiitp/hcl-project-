import streamlit as st
import pandas as pd
import plotly.express as px
from data_gen import generate_all_datasets
from ingest import ingest_to_memory
from analytics import promo_effectiveness, top_products
from loyalty import calculate_loyalty_for_batch
from segmentation import compute_rfm_and_segments
from inventory import inventory_correlation
from notify import simulate_notifications

st.set_page_config(layout='wide', page_title='Retail Hackathon Dashboard')

@st.cache_data
def load_data():
    ds = generate_all_datasets(seed=42)
    return ingest_to_memory(ds)

header, lines, stores, products, customers, promotions, loyalty_rules, inventory = load_data()

st.title('Retail Data Processing — Hackathon')
tab = st.tabs(['Data Overview','Promotion Effectiveness','Loyalty','Segmentation','Notifications','Inventory'])

with tab[0]:
    st.header('Data Overview')
    st.write('Stores', stores.shape)
    st.write('Products', products.shape)
    st.write('Customers', customers.shape)
    st.write('Sales headers sample')
    st.dataframe(header.head())
    st.write('Sales lines sample')
    st.dataframe(lines.head())

with tab[1]:
    st.header('Promotion Effectiveness')
    pe = promo_effectiveness(lines, promotions, products)
    st.dataframe(pe.head(20))
    st.subheader('Top Products')
    st.dataframe(top_products(lines, products))

with tab[2]:
    st.header('Loyalty Calculation')
    accrued = calculate_loyalty_for_batch(header.head(50), lines[lines['transaction_id'].isin(header.head(50)['transaction_id'])], customers, loyalty_rules)
    st.dataframe(accrued.head())
    st.write('Customer points snapshot')
    st.dataframe(customers.head())

with tab[3]:
    st.header('Segmentation (RFM)')
    rfm = compute_rfm_and_segments(header, customers)
    st.dataframe(rfm.head())
    seg_counts = rfm['segment'].value_counts().reset_index(name='count')
    seg_counts.columns = ['segment','count']
    fig = px.bar(seg_counts, x='segment', y='count', labels={'segment':'segment','count':'count'})
    st.plotly_chart(fig, use_container_width=True)

with tab[4]:
    st.header('Notifications (Simulated)')
    accrued_small = calculate_loyalty_for_batch(header.head(10), lines[lines['transaction_id'].isin(header.head(10)['transaction_id'])], customers, loyalty_rules)
    msgs = simulate_notifications(accrued_small, customers)
    for m in msgs[:10]:
        st.markdown(f"**To:** {m['email']}  \n**Subject:** {m['subject']}  \n{m['body']}")

with tab[5]:
    st.header('Inventory & Store Performance Correlation')
    inv = inventory_correlation(lines, inventory, products)
    st.dataframe(inv.head())

st.sidebar.markdown('---')
st.sidebar.write('Use this app to explore the generated sample data and demo pipelines for the six use cases.')

if __name__ == '__main__':
    st.write('Run `streamlit run app.py` to start the dashboard')
