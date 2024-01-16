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

def app():
    """
    This function sets up the StAZH TranskribusAPI web application.
    It handles the login process and displays the login form.
    """
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

    #add_logo("data/loewe.png", height=150)

    st.subheader("StAZH TranskribusAPI")

    st.markdown("Bitte Logindaten eingeben:")

    credentialPath = '../lib/TranskribusPyClient/src/Transkribus_credential.py'

    with st.form(key="login_form"):
        email = st.text_input('Transkribus Email')
        password = st.text_input('Transkribus Passwort', type="password")
        submit_button = st.form_submit_button(label='Login')

    if submit_button:
        if email and password:
            r = requests.post("https://transkribus.eu/TrpServer/rest/auth/login",
                                    data ={"user":email, "pw":password})
            if r.status_code == requests.codes.ok:
                session = r.text
                session = et.fromstring(session)
                createStreamlitSession(session, email, password)
                save_credentials(email, password)

                #check if login was successfull
                if st.session_state.sessionId == None:
                    st.warning("Fehler! Login war nicht erfolgreich! \n Bitte erneut versuchen.", icon="⚠️")
                else:
                    st.warning("Login erfolgreich...", icon="✅")
                    switch_page("Home")
            else:
                st.warning('Login war nicht erfolgreich', icon="⚠️")

        else:
            st.warning('Bitte Logindaten eingeben.', icon="⚠️")

def authentification(request):
    session = {
        "userId": et.fromstring(request.text).find("userId").text,
        "sessionId": et.fromstring(request.text).find("sessionId").text,
    }
    return session

def createStreamlitSession(auth_session, email, password):
    if 'sessionId' not in st.session_state:
        st.session_state.sessionId = auth_session.find("sessionId").text

    if 'username' not in st.session_state:
        st.session_state.username = auth_session.find("userId").text

    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = True

    if 'proxy' not in st.session_state:
        st.session_state.proxy = {"https" : 'http://:@:',
                         "http" : 'http://:@:'}

    st.session_state.email = email
    st.session_state.password = password

def save_credentials(email, password, credentialPath):
    """
            If desired this function saves the email and password in a file.
            NOTE: This is not save against reads from others.
    """
    file = open(credentialPath, "wt") 
    lines = ['# -*- coding: utf-8 -*-\n', 'login = "{}"\n'.format(email),'password = "{}"\n'.format(password),'linien_col  = "{}"\n'.format(linienCol),'linien_doc  = "{}"\n'.format(linienDoc),'linien_TR  = "{}"\n'.format(linienTR),
    'suchenErsetzenCol  = "{}"\n'.format(suchenErsetzenCol),
    'suchenErsetzenDoc  = "{}"\n'.format(suchenErsetzenDoc),
    'exportCol = "{}"\n'.format(exportCol),'exportDoc  = "{}"\n'.format(exportDoc),
    'importCol  = "{}"\n'.format(importCol),
    'sampleCol  = "{}"\n'.format(sampleCol),
    'sampleDoc  = "{}"\n'.format(sampleDoc)]
    file.writelines(lines)
    file.close()
    return

if __name__ == "__main__":
    app()