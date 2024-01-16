import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
import os
import streamlit.components.v1 as components
from streamlit_extras.app_logo import add_logo
from streamlit_extras.switch_page_button import switch_page
from streamlit.source_util import (
    page_icon_and_name, 
    calc_md5,
    get_pages,
    _on_pages_changed
)
from bs4 import BeautifulSoup
import requests

def app():
    if st.session_state.get("sessionId") is None:
        switch_page("Start")

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

    st.header("Import-Modul")
    st.markdown("---")

    text_entry_col_id = st.text_input("Collection id:")
    checkbox_tr = st.checkbox("Import Textregionen (unangewählt = Linien)")

    uploaded_file = st.file_uploader("Upload a file", type=["csv", "txt", "xlsx"])

    if st.button('Starten'):
        st.write("Starten")
        start_import(text_entry_col_id, checkbox_tr, uploaded_file)


def start_import(colid, isTR, uploaded_file):
    if isTR:
        import_tr(colid, uploaded_file)
    else:
        import_lines(colid, uploaded_file)


def import_lines(colid, uploaded_file):
    try:
        # To read first 12 characters to determine the delimiter
        first_chars = uploaded_file.read(12)
        delimiter = chr(first_chars[11])

        # Seek to the start of the file
        uploaded_file.seek(0)

        # Load the file using pandas
        df = pd.read_csv(uploaded_file, delimiter=delimiter, dtype=str, encoding='unicode_escape')

        customs = [df[u'Tag'][0]]
        ids = [df[u'Textregion Id'][0]]
        linetexts = [df[u'Text'][0]]
        docid = df[u'Dokument Id'][0]
        pageNo = df[u'SeitenNr'][0]

        for i in range(1, df.shape[0]):
            if int(df[u'SeitenNr'][i - 1]) == int(df[u'SeitenNr'][i]):
                customs.append(df[u'Tag'][i])
                ids.append(df[u'Textregion Id'][i])
                linetexts.append(df[u'Text'][i])
                docid = int(df[u'Dokument Id'][i])
                pageNo = int(df[u'SeitenNr'][i])
                if i == (df.shape[0] - 1):
                    import_in_page(colid, docid, pageNo, ids, linetexts, customs)
            else:
                import_in_page(colid, docid, pageNo, ids, linetexts, customs)
                customs = [df[u'Tag'][i]]
                ids = [df[u'Textregion Id'][i]]
                linetexts = [df[u'Text'][i]]
                docid = df[u'Dokument Id'][i]
                pageNo = df[u'SeitenNr'][i]

        st.success("Ende erreicht! Daten aus csv importiert!")

    except Exception as e:
        st.error('Fehler! Mit dem Import-File scheint etwas nicht zu stimmen. Es müsste ein csv mit den Feldern Dokument Id, SeitenNr, Textregion Id, Text, Tag sein. Error: {}'.format(e))

    return

def import_tr(colid, uploaded_file):
    try:
        # Read first 12 characters to determine the delimiter
        first_chars = uploaded_file.read(12)
        delimiter = chr(first_chars[11])

        # Reset file pointer to the start
        uploaded_file.seek(0)

        # Read file into DataFrame
        df = pd.read_csv(uploaded_file, delimiter=delimiter, dtype=str, encoding='unicode_escape')

        # Initialize progress bar and text
        progress = st.progress(0)
        progress_text = st.empty()

        # Process DataFrame
        customs = []
        ids = []
        docid = pageNo = None

        for i in range(df.shape[0]):
            if i == 0 or int(df['SeitenNr'][i-1]) != int(df['SeitenNr'][i]):
                if ids:
                    import_tr_in_page(colid, docid, pageNo, ids, customs)
                    customs = []
                    ids = []
            
            customs.append(df['Tag'][i])
            ids.append(df['Textregion Id'][i])
            docid = int(df['Dokument Id'][i])
            pageNo = int(df['SeitenNr'][i])

            if i == df.shape[0] - 1:
                import_tr_in_page(colid, docid, pageNo, ids, customs)

            # Update progress bar
            progress_value = int(100 * ((i + 1) / df.shape[0]))
            progress.progress(progress_value)
            progress_text.text(f"Job progress {progress_value}%")

        st.success("Data import complete!")

    except Exception as e:
        st.error(f'Error: {str(e)}')

def import_tr_in_page(colid, docid, pageNo, ids, customs):
    xml = get_page(colid, docid, pageNo)
    soup = BeautifulSoup(xml, "xml")

    try:
        for j in range(len(ids)):
            for region in soup.findAll("TextRegion"):
                if ids[j] == region['id']:
                    region['custom'] = customs[j]

        # Assuming post_page performs some posting or updating task
        post_page(colid, docid, pageNo, soup)

    except Exception as e:
        st.error(f'Fehler beim Import in {docid}, Seite {pageNo}. Abbruch. Error: {str(e)}')

    return True

def import_in_page(colid, docid, pageNo, ids, linetexts, customs):
    xml = get_page(colid, docid, pageNo)
    soup = BeautifulSoup(xml, "xml")

    try:
        for j in range(len(ids)):
            for line in soup.findAll("TextLine"):
                if ids[j] == line['id']:
                    line['custom'] = customs[j]
                    for t in line.findAll("Unicode"):
                        t.string = linetexts[j]

        # Assuming post_page performs some posting or updating task
        post_page(colid, docid, pageNo, soup)

    except Exception as e:
        st.error(f'Fehler beim Import in {docid}, Seite {pageNo}. Abbruch. Error: {str(e)}')

    return True

def get_page(colid, docid, pageNo):
    if st.session_state.proxy is not None and st.session_state.proxy["https"] == 'http://:@:':
        r = requests.get("https://transkribus.eu/TrpServer/rest/collections/{}/{}/{}/text?JSESSIONID={}".format(colid, docid, pageNo, st.session_state.sessionId))
    else:
        r = requests.get("https://transkribus.eu/TrpServer/rest/collections/{}/{}/{}/text?JSESSIONID={}".format(colid, docid, pageNo, st.session_state.sessionId), proxies = st.session_state.proxy)
    if r.status_code == requests.codes.ok:
        return r.text
    else:
        print(r)
        st.error('Fehler!','Fehler bei der Abfrage einer Seite. Doc-ID ' + str(docid) + ' invalid oder Seitenzahl ' + str(pageNo) + ' ausserhalb des Bereichs.')
        return None
    
def post_page(colid, docid, pageNo, xml):
    if st.session_state.proxy is not None and st.session_state.proxy["https"] == 'http://:@:':
        r = requests.post("https://transkribus.eu/TrpServer/rest/collections/{}/{}/{}/text?JSESSIONID={}".format(colid, docid, pageNo, st.session_state.sessionId), data=xml.encode("utf8"), params={ "note":"DC" })
    else:
        r = requests.post("https://transkribus.eu/TrpServer/rest/collections/{}/{}/{}/text?JSESSIONID={}".format(colid, docid, pageNo, st.session_state.sessionId), data=xml.encode("utf8"), params={ "note":"DC" }, proxies = st.session_state.proxy)
    if r.status_code == requests.codes.ok:
        return True
    else:
        print(r)
        st.error("Fehler!","Fehler beim posten einer Seite. Doc-ID " + str(docid) + " invalid oder Seitenzahl " + str(pageNo) + " ausserhalb des Bereichs?")
        return False

if __name__ == "__main__":
    app()