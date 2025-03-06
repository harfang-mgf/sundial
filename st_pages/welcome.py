import streamlit as st

with st.sidebar:
    st.page_link('st_pages/sundial.py', label="sundial calculator")
    st.page_link('st_pages/sunposition.py', label="sun's position")

st.title("Welcome to the sundial project")
st.markdown(\
"""
### Introduction

The *sundial project* aims to collect and develop tools for the understanding
and creation of sundials. This requires to:
 *  understand the relative positions of the Earth and the Sun over time;
 *  compute the asimuth and declination of the Sun as seen from a given
    geographic location on Earth, at a given time;
 *  translate these into the the perspective of a given sundial;
 *  draw the *precision sundial*, with time and season reading and
    legal time correction.

This streamlit application showcases some of the tools that I have developped
for the course given by Antonio Pisanello at *nomades advanced technologies*
towards the certifications
*python programming language* (PPL) /
*pathon software engineer* (PSE).

The tools – with acompanying documents, sources, and archives – will be made
available on a public GitHup repository.
""")

