# streamlit 'sundial' page
#
# Demonstration of 'ombre.py', using sidebar controls for the (numerous)
# arguments.
#
import streamlit as st
from src.ombre_svg import draw_sundial, __version__ as version

def lat_lon(ll: float, pm: str) -> str:
    l,d,m = pm[int(ll<0)], int(abs(ll)), int(abs(ll)*60)%60
    return f"{l} {d}°{m:02}'"

with st.sidebar:
    st.page_link("st_pages/welcome.py", label="(back)", icon=":material/home:")
    doit = st.checkbox('Draw sundial')

    lat = st.slider('latitude', -90.0, 90.0, 24.0, 1.0, "%+.2f°" )
    lon = st.slider('longitude', -180.0, 180.0, -32.0, 1.0, "%+.2f°" )
    st.write(f"{lat_lon(lat,'NS')} ; {lat_lon(lon,'EW')}")
    ori = st.slider('orientation (0° = South)', -135, 135, 0, 1, '%+d°')
    slo = st.slider('slope of the wall', 0, 135, 0, 1, '%d°')

    noc = st.checkbox('virtual nocturnal lines', False)

    totx = st.slider('width of the sundial', 0.0, 10.0, 3.0, 0.1)
    toty = st.slider('height of the sundial', 0.0, 10.0, 2.0, 0.1)
    addx = st.slider('horizontal shift', -5.0, 5.0, 0.0, 0.1)
    addy = st.slider('vertical shift', -5.0, 5.0, 0.0, 0.1)
    styl = st.slider('lenght of the style', 0.1, 5.0, 1.0, 0.1)
    hsty = st.slider('height of the gnomon (*)', 0.0, 5.0, 1.0, 0.1)
    scale = st.slider('scale (pixel per unit)', 10, 1000, 200, 10)

    txt = st.checkbox('add info box', True)
    std = st.checkbox('standard dial', True)
    ext = st.checkbox('extreme shadows', True)
    hyp = st.checkbox('shadow traces', True)
    teq = st.checkbox('equation of time', False)
    sha = st.checkbox('special: octahedron', False)



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
    st.image('src/sundial.svg', f"{lat_lon(lat,'NS')} ; {lat_lon(lon,'EW')}")
else:
    st.image('src/image.svg', "somewhere in Geneva")

with st.sidebar:
    st.write('----')
    st.write(f"• powered by **ombre.py* {version} • (°v°)")
