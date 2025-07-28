import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px


# Load your table (replace with your actual file or DataFrame)
# The table should have: 'host_name', 'ra', 'dec', 'companion_name', 'companion_ra', 'companion_dec'
df = pd.read_csv("table_companions_merged_final.csv")


# Step 1: Show interactive histogram with range slider
st.markdown("### 📊 Histogram of Separation (sep_kpc)")
fig = px.histogram(df, x='sep_kpc', nbins=30)
fig.update_layout(
    xaxis_title="Separation (kpc)",
    yaxis_title="Count",
    xaxis=dict(rangeslider=dict(visible=True))
)
st.plotly_chart(fig, use_container_width=True)


# Step 1: Get min and max of sep_kpc
min_sep = df['sep_kpc'].min()
max_sep = df['sep_kpc'].max()

# Step 2: Add slider to sidebar (or main area)
sep_range = st.slider("📏 Select separation range (kpc):", 
                      min_value=min_sep, 
                      max_value=max_sep, 
                      value=(min_sep, max_sep), 
                      step=1.0, width=1000)

# Step 3: Filter based on slider
filtered_df = df[(df['sep_kpc'] >= sep_range[0]) & (df['sep_kpc'] <= sep_range[1])]

# Step 4: Select host galaxy from filtered results
#host_options = filtered_df['host_gal'].unique()
#selected_host = st.selectbox("🔭 Choose a host galaxy within range:", host_options, width=1000)

# Sidebar: Pick a galaxy
#host_names = df['host_gal'].unique()
#selected_host = st.selectbox("🔭 Select a Galaxy", host_names,  width=1000)


num_hosts = filtered_df['host_gal'].nunique()
st.markdown(f"🧮 **Number of host galaxies in range:** `{num_hosts}`")

# Step 4: Build dropdown options with sep_kpc included
host_rows = filtered_df[['host_gal', 'sep_kpc']]
host_options = host_rows.drop_duplicates().apply(lambda row: f"{row['host_gal']} (sep: {row['sep_kpc']:.2f} kpc)", axis=1).tolist()

# Step 5: Select host galaxy
selected_entry = st.selectbox("🔭 Select a host galaxy (with sep_kpc):", host_options)

# Step 6: Extract the actual host name from the selected text
selected_host = selected_entry.split(" (")[0]


# Filter companions of the selected host
subset = df[df['host_gal'] == selected_host]

# Show companion list
st.write("🧲 Companion galaxies:")
st.dataframe(subset[['main_id', 'ra', 'dec','sep_kpc']],  width=1000)

# Get host coordinates (first row is enough)
host_ra = subset.iloc[0]['Primary_Ra']
host_dec = subset.iloc[0]['Primary_Dec']


D = subset.iloc[0]['redshift']*3e5/70
kpc_arc = np.tan(np.deg2rad(1./3600))*D*1e3

sep_kpc = np.max(subset['sep_kpc'])

arcdist = ((sep_kpc+10.)*2)/kpc_arc
fov = np.round(arcdist/3600.,4)

arcdist5 = (50)/kpc_arc
fov5 = arcdist5/3600.



# Aladin Lite embedded iframe
#aladin_iframe = f"""
#<iframe
#    src="https://aladin.u-strasbg.fr/AladinLite/?target={host_ra}%20{host_dec}&fov={fov}&survey=P%2FDSS2%2Fcolor"
#    width="1800"
#    height="600"
#    style="border:none;"
#></iframe>
#"""

aladin_iframe = f"""
<div id="aladin-lite-div" style="width: 700px; height: 800px;"></div>
<script type="text/javascript" src="https://aladin.cds.unistra.fr/AladinLite/api/v3/latest/aladin.js" charset="utf-8"></script>
<script type="text/javascript">
    A.init.then(() => {{
        aladin=A.aladin('#aladin-lite-div', {{
            survey: "P/SDSS9/color",
            fov: {fov},
            target: "{host_ra} {host_dec}"
        }});
        // Add 5R200 Circle
          var overlay = A.graphicOverlay({{color: '#ee2345', lineWidth: 2}});
          aladin.addOverlay(overlay);
          overlay.add(A.ellipse({host_ra}, {host_dec}, {fov5}, {fov5}, 0));  
"""

mark_gal = f"""
          var marker0 = A.marker({host_ra}, {host_dec}, {{popupTitle: '{selected_host}', popupDesc: 'Distance: {sep_kpc:.1f} kpc'}});
    """

for i in range(len(subset)):
    sep_kpc_gal = subset.iloc[i]['sep_kpc']
    ra = subset.iloc[i]['ra']
    dec = subset.iloc[i]['dec']
    name_comp = subset.iloc[i]['main_id']
    mark_galt = f"""
          var marker{i+1} = A.marker({ra}, {dec}, {{popupTitle: '{name_comp}', popupDesc: 'Distance: {sep_kpc:.1f} kpc'}});
    """
  
    mark_gal += mark_galt
                 
add_markers = """
          var markerLayer = A.catalog();
          aladin.addCatalog(markerLayer);
"""                        

temp = "markerLayer.addSources(["
for i in range(len(subset)+1):
    temp += f"marker{i}, "
temp = temp[:-2] + "]);"

mark_gal += add_markers + temp

mark_gal += """ 
});
</script>
"""
aladin_iframe += mark_gal

#print(aladin_iframe)


# Show embedded sky view
st.markdown("🛰️ **Aladin Lite view of the host galaxy**", unsafe_allow_html=True)
st.components.v1.html(aladin_iframe, height=800, width=1800)

