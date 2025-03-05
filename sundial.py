import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime
from om import draw_sundial

def lat_lon(ll: float, pm: str) -> str:
    l,d,m = pm[int(ll<0)], int(abs(ll)), int(abs(ll)*60)%60
    return f"{l} {d}°{m:02}'"


doit = st.sidebar.checkbox('Redraw sundial')
lat = st.sidebar.slider('latitude', -90.0, 90.0, 46.0, 1.0, "%+.2f°" )
lon = st.sidebar.slider('longitude', -180.0, 180.0, -6.0, 1.0, "%+.2f°" )
st.sidebar.write(f"{lat_lon(lat,'NS')} ; {lat_lon(lon,'EW')}")
ori = st.sidebar.slider('orientation (0° = South)', -135, 135, 20, 1, '%+d°')
slo = st.sidebar.slider('slope of the wall', 0, 135, 90, 1, '%d°')

noc = st.sidebar.checkbox('virtual nocturnal lines', False)

totx = st.sidebar.slider('width of the sundial', 0.0, 10.0, 0.0, 0.1)
toty = st.sidebar.slider('height of the sundial', 0.0, 10.0, 0.0, 0.1)
addx = st.sidebar.slider('horizontal shift', -5.0, 5.0, 0.0, 0.1)
addy = st.sidebar.slider('vertical shift', -5.0, 5.0, 0.0, 0.1)
styl = st.sidebar.slider('lenght of the style', 0.1, 5.0, 1.0, 0.1)
hsty = st.sidebar.slider('height of the gnomon (*)', 0.0, 5.0, 0.0, 0.1)
scale = st.sidebar.slider('scale (pixel per unit)', 10, 1000, 200, 10)

txt = st.sidebar.checkbox('add info box', True)
std = st.sidebar.checkbox('standard dial', True)
ext = st.sidebar.checkbox('extreme shadows', True)
hyp = st.sidebar.checkbox('shadow traces', True)
teq = st.sidebar.checkbox('equation of time', True)
sha = st.sidebar.checkbox('special shadow: octahedron')



if doit:
    draw_sundial( lat, lon, ori, slo,

        nocturnal = noc,

        wall_width = totx,
        wall_height = toty,
        add_x = addx,
        add_y = addy,
        style_length = styl,
        gnomon_height = hsty,
        scale = scale,

        draw_text = txt,
        draw_standard = std,
        draw_extremes = ext,
        draw_traces = hyp,
        draw_equation = teq,
        draw_special = sha,

        file_name = 'sundial'
    )
    st.image('sundial.svg')
else:
    st.image('image.svg')
