import streamlit as st
from streamlit_option_menu import option_menu
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
                #save_credentials(email, password, credentialPath)

                #check if login was successfull
                if st.session_state.sessionId == None:
                    st.warning("Fehler! Login war nicht erfolgreich! \n Bitte erneut versuchen.", icon="⚠️")
                else:
                    st.warning("Login erfolgreich...", icon="✅")
                    switch_page("home")
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
    """
    Creates a Streamlit session with the provided authentication session, email, and password.

    Parameters:
    - auth_session: The authentication session.
    - email: The email associated with the session.
    - password: The password associated with the session.
    """
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

def save_credentials(email, password, credentials_path):
    """
    Save the provided email and password to the credentials file.

    Args:
        email (str): The email to be saved.
        password (str): The password to be saved.
        credentials_path (str): The path to the credentials file.

    Returns:
        None
    """
    # Path to the credentials.py file
    credentials_path = credentials_path + st.session_state.sessionId + '.py'

    # If the file doesn't exist, create it
    if not Path(credentials_path).is_file():
        create_credentials_file(credentials_path)
        return

    # Read the existing content
    with open(credentials_path, 'r') as file:
        content = file.readlines()

    # Modify the content
    for i, line in enumerate(content):
        if 'login' in line:
            content[i] = f'login    = "{email}"\n'
        elif 'password' in line:
            content[i] = f'password = "{password}"\n'

    # Write the modified content back
    with open(credentials_path, 'w') as file:
        file.writelines(content)

def create_credentials_file(file_name, login='', password=''):
    """
    Create a credentials file with the provided login and password.

    Args:
        file_name (str): The name of the file to create.
        login (str, optional): The login to be included in the credentials file. Defaults to an empty string.
        password (str, optional): The password to be included in the credentials file. Defaults to an empty string.
    """

    content = f"""# -*- coding: utf-8 -*-
    login    = "{login}"
    password = "{password}"
    """

    with open(file_name, 'w', encoding='utf-8') as file:
        file.write(content)


if __name__ == "__main__":
    app()