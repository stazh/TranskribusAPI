import shutil
import requests
from PIL import Image
from streamlit_extras.app_logo import add_logo
from streamlit_extras.switch_page_button import switch_page
from streamlit.source_util import (
    page_icon_and_name, 
    calc_md5,
    get_pages,
    _on_pages_changed
)


def get_document_r(colid, docid, st):
    """
    Retrieves the full document from Transkribus API.

    Args:
        colid (str): The collection ID.
        docid (str): The document ID.
        st: The session state object.

    Returns:
        dict or None: The JSON response containing the full document if the request is successful, 
        otherwise None.

    Raises:
        None

    """
    if st.session_state.proxy is not None and st.session_state.proxy["https"] == 'http://:@:':
        r = requests.get("https://transkribus.eu/TrpServer/rest/collections/{}/{}/fulldoc?JSESSIONID={}".format(colid, docid, st.session_state.sessionId))
    else:
        r = requests.get("https://transkribus.eu/TrpServer/rest/collections/{}/{}/fulldoc?JSESSIONID={}".format(colid, docid, st.session_state.sessionId), proxies = st.session_state.proxy)

    if r.status_code == requests.codes.OK:
        return r.json()
    else:
        st.error(f'Fehler bei der Abfrage eines Dokumentes. Doc-ID {docid} invalid?')
        return None


def get_doc_name_from_id(colId, docId, st):
    """
    Retrieves the document name from the given collection ID, document ID, and server token.

    Parameters:
    colId (str): The ID of the collection.
    docId (str): The ID of the document.
    st (str): The server token.

    Returns:
    str: The document name.
    """
    doc = get_document_r(colId, docId, st)
    return doc['md']['title']


def extract_transcription_raw(colId, docId, text_entry_start_page, text_entry_end_page, toolName, st):
    """
    Extracts raw transcriptions from a document in Transkribus.

    Args:
        colId (str): The collection ID.
        docId (str): The document ID.
        text_entry_start_page (int or str): The starting page number or '-' to indicate the first page.
        text_entry_end_page (int or str): The ending page number or '-' to indicate the last page.
        toolName (str): The name of the transcription tool.
        st: The session state object.

    Returns:
        list: A list of raw transcriptions for each page.

    Raises:
        Exception: If there is an error retrieving the transcription.

    """
def extract_transcription_raw(colId, docId, text_entry_start_page, text_entry_end_page, toolName, st):
    #get document
    doc = get_document_r(colId, docId, st)['pageList']['pages']

    #setup the startpage
    if isinstance(text_entry_start_page, int):
        startPage = text_entry_start_page
    else:
        startPage = int(text_entry_start_page)
    
    #define the end_pages
    if text_entry_end_page == "-" or text_entry_end_page == '-':
        end_page = len(doc)
    elif isinstance(text_entry_end_page, int):
        end_page = text_entry_end_page
    else:
        end_page = int(text_entry_end_page)
    
    #define the pages
    pages = range(startPage-1, end_page)
    
    page_text = []
    
    #go through all pages
    for page in pages:
        if toolName == 'LAST':
                url = doc[page]['tsList']['transcripts'][0]['url']
        else:
            for ts in doc[page]['tsList']['transcripts']:
                if toolName == 'GT':
                    if ts['status'] == 'GT':
                        url = ts['url']
                        break
                else:
                    try:
                        if toolName in ts['toolName']:
                            url = ts['url']
                            break
                    except:
                        pass
        try:
            if st.session_state.proxy is not None and st.session_state.proxy["https"] == 'http://:@:':
                req = requests.get(url)
            else:
                req = requests.get(url, proxies = st.session_state.proxy)
            
            page_text.append(req.text)
            
        except Exception as e:
            st.write(e)
            return
    return page_text


def get_image_from_url(url, st):
    """
    Retrieves an image from a given URL and returns it as a PIL Image object.

    Parameters:
    url (str): The URL of the image.
    st (object): The session state object.

    Returns:
    PIL.Image.Image: The image retrieved from the URL.
    """
    if st.session_state.proxy is not None and st.session_state.proxy["https"] == 'http://:@:':
        r = requests.get(url, stream=True)
    else:
        r = requests.get(url, stream=True, proxies=st.session_state.proxy)
    img = Image.open(r.raw)
    return img


def set_header(header_name, st):
    """
    Sets the header for the web application page.

    Parameters:
    - header_name (str): The name of the header.
    - st (Streamlit): The Streamlit object.

    Returns:
    None
    """
    st.set_page_config(
        page_title="StAZH Transkribus API",
    )

    current_pages = get_pages("Start")
    for key, value in current_pages.items():
        if value['page_name'] == "Start":
            del current_pages[key]
            break
        else:
            pass

    hide_decoration_bar_style = '''
        <style>
            header {visibility: hidden;}
        </style>
    '''
    st.markdown(hide_decoration_bar_style, unsafe_allow_html=True)

    add_logo("data/loewe.png", height=150)

    st.header(header_name)
    st.markdown("---")

def check_session_state(st):
    """
    Check the session state for the presence of a sessionId.

    Parameters:
        st (SessionState): The session state object.

    Returns:
        None
    """
    if st.session_state.get("sessionId") is None:
        switch_page("Start")


def remove_file(file_path):
    """
    Removes a file or directory at the given file path.

    Args:
        file_path (str): The path to the file or directory to be removed.

    Returns:
        None
    """
    try:
        shutil.rmtree(file_path)
    except:
        pass