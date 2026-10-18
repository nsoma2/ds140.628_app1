import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(layout="wide")
st.title("MRICloud Brain Volume Sankey Diagram")

## Load in the hierarchy information (from the ds4bio interactive chapter)
url = "https://raw.githubusercontent.com/bcaffo/MRIcloudT1volumetrics/master/inst/extdata/multilevel_lookup_table.txt"
multilevel_lookup = pd.read_csv(url, sep = "\t").drop(['Level5'], axis = 1)
multilevel_lookup = multilevel_lookup.rename(columns = {
    "modify"   : "roi",
    "modify.1" : "level4",
    "modify.2" : "level3",
    "modify.3" : "level2",
    "modify.4" : "level1"})
multilevel_lookup = multilevel_lookup[['roi', 'level4', 'level3', 'level2', 'level1']]

## Strip stray whitespace
for col in multilevel_lookup.columns:
    multilevel_lookup[col] = multilevel_lookup[col].astype(str).str.strip()

## Now load in the subject data (Type = 1, subject 127)
id = 127
subjectData = pd.read_csv("https://raw.githubusercontent.com/smart-stats/ds4bio_book/main/book/assetts/kirby21AllLevels.csv")
subjectData = subjectData.loc[(subjectData.type == 1) & (subjectData.level == 5) & (subjectData.id == id)]
subjectData = subjectData[['roi', 'volume']]
## Merge the subject data with the multilevel data
subjectData = pd.merge(subjectData, multilevel_lookup, on = "roi")
subjectData = subjectData.assign(icv = "ICV")
subjectData = subjectData.assign(comp = subjectData.volume / np.sum(subjectData.volume))

subjectData.head()

path = ['icv', 'level1', 'level2', 'level3', 'level4', 'roi']

## Build nodes keyed on (level, name) so a name that repeats across levels
node_id = {}
labels  = []
def get_node(level, name):
    key = (level, name)
    if key not in node_id:
        node_id[key] = len(labels)
        labels.append(name)
    return node_id[key]

sources, targets, values = [], [], []
for parent, child in zip(path[:-1], path[1:]):
    flows = subjectData.groupby([parent, child])['volume'].sum().reset_index()
    for _, row in flows.iterrows():
        sources.append(get_node(parent, row[parent]))
        targets.append(get_node(child,  row[child]))
        values.append(row['volume'])

fig = go.Figure(data = [go.Sankey(
    arrangement = "snap",
    node = dict(
        pad = 10,
        thickness = 15,
        line = dict(color = "black", width = 0.5),
        label = labels,
        color = "steelblue"
    ),
    link = dict(
        source = sources,
        target = targets,
        value = values
    )
)])

fig.update_layout(
    title_text = f"MRICloud volumes for subject {id}",
    font_size = 9,
    height = 1400
)

st.plotly_chart(fig)
