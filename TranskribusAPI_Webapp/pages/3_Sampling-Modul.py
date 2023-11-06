import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
from PIL import Image
import streamlit.components.v1 as components
from streamlit_extras.app_logo import add_logo
from streamlit_extras.switch_page_button import switch_page
st.set_page_config(
    page_title="StAZH Transkribus API",
)

hide_decoration_bar_style = '''
    <style>
        header {visibility: hidden;}
    </style>
'''
st.markdown(hide_decoration_bar_style, unsafe_allow_html=True)

add_logo("data/loewe.png", height=150)


st.header("Sampling-Modul")
st.write("##")
st.markdown("---")

st.markdown("Hier kommt das Sampling-Modul hin")