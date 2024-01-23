import streamlit as st
from utils.utility_functions import set_header, check_session_state

check_session_state(st)
set_header('Home', st)