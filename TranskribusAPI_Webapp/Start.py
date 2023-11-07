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
    initial_sidebar_state="collapsed",
)

hide_decoration_bar_style = '''
    <style>
        header {visibility: hidden;}
        [data-testid="collapsedControl"] {
            display: none;
        }
    </style>
'''
st.markdown(hide_decoration_bar_style, unsafe_allow_html=True)

add_logo("data/loewe.png", height=150)

st.subheader("StAZH TranskribusAPI")

st.markdown("Bitte Logindaten eingeben:")

email = st.text_input('Transkribus Email')
password = st.text_input('Transkribus Passwort', type="password")

if st.button('Login'):
    if email and password:
        r = requests.post("https://transkribus.eu/TrpServer/rest/auth/login",
                                data ={"user":email, "pw":password})

        if r.status_code == requests.codes.ok:
            session = r.text
            session = et.fromstring(session)
            userId = session.find("userId").text
            sessionId = session.find("sessionId").text
            #check if login was successfull
            if sessionId == None:
                st.warning("Fehler! Login war nicht erfolgreich! \n Bitte erneut versuchen.", icon="⚠️")
            else:
                st.warning("Login erfolgreich...", icon="✅")
                switch_page("Home")
        else:
            st.warning('Login war nicht erfolgreich', icon="⚠️")

    else:
        st.warning('Bitte Logindaten eingeben.', icon="⚠️")

## Todo add streamlit session handling

def authentification(request):
    session = {
        "userId": et.fromstring(request.text).find("userId").text,
        "sessionId": et.fromstring(request.text).find("sessionId").text,
    }
    return session

def createStreamlitSession(auth_session):
    if 'sessionId' not in st.session_state:
        st.session_state.sessionId = auth_session['sessionId']

    if 'username' not in st.session_state:
        st.session_state.username = auth_session['userId']

    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = True
