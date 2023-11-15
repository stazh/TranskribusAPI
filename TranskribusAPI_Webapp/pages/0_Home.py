import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
from PIL import Image
from streamlit.components.v1 import html
from streamlit_extras.app_logo import add_logo
from streamlit_extras.switch_page_button import switch_page
from pathlib import Path
import requests
import xml.etree.ElementTree as et
from streamlit.source_util import (
    page_icon_and_name, 
    calc_md5, 
    get_pages,
    _on_pages_changed
)

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

st.subheader("StAZH TranskribusAPI")

def select_destination_directory():
    st.sidebar.header("Select Destination Directory")
    selected_directory = st.sidebar.selectbox(
        "Choose a destination directory:",
        options=["/path/to/directory1", "/path/to/directory2", "/path/to/directory3"]
    )
    return selected_directory

# Example usage
selected_directory = select_destination_directory()
if selected_directory:
    st.write(f"Selected directory: {selected_directory}")
else:
    st.write("No directory selected.")
