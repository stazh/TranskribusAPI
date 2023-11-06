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

st.markdown("Bitte Logindaten eingeben:")


email = st.text_input('Transkribus Email')
password = st.text_input('Transkribus Passwort', type="password")


if st.button('Login'):
    if email == '' or password == '':
        st.warning('Bitte Logindaten eingeben.', icon="⚠️")

    r = requests.post("https://transkribus.eu/TrpServer/rest/auth/login",
                              data ={"user":email, "pw":password})

    if r.status_code == requests.codes.ok:
        session = r.text
    else:
        session = ""
        st.warning('Login war nicht erfolgreich', icon="⚠️")

    session = et.fromstring(session)
    userId = session.find("userId").text
    sessionId = session.find("sessionId").text
        #check if login was successfull
    if sessionId == None:
        st.warning("Fehler! Login war nicht erfolgreich! \n Bitte erneut versuchen.", icon="⚠️")
    else:
        st.warning("Login erfolgreich...", icon="✅")    




    
      


