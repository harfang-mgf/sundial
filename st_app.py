import streamlit as st

st.set_page_config("Sundial", ":material/sunny:")

pg = st.navigation([
    st.Page('st_pages/welcome.py'),
    st.Page('st_pages/sundial.py'),
    st.Page('st_pages/sunposition.py'),
    ], position='hidden')
pg.run()
