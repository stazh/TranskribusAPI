import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import requests
import utils.utility_functions as uf

def app():
    # Check and set up the session state, ensuring it's properly initialized for the Streamlit app.
    uf.check_session_state(st)

    # Set the header of the Streamlit application to 'Import-Modul'.
    uf.set_header('Import-Modul', st)
    
    # Create a text input field for the user to enter a collection ID.
    text_entry_col_id = st.text_input("Collection id:")

    # Create a checkbox for the user to select whether to import text regions. 
    # Unchecked means the user intends to import lines.
    checkbox_tr = st.checkbox("Import Textregionen (unangewählt = Linien)")

    # Create a file uploader allowing the user to upload a file in CSV, TXT, or XLSX format.
    uploaded_file = st.file_uploader("Upload a file", type=["csv", "txt", "xlsx"])

    # Create a button named 'Starten'. When clicked, it initiates the import process.
    if st.button('Starten'):
        # Call the function to start the import process with the provided parameters.
        with st.spinner("Import läuft..."):
            start_import(text_entry_col_id, checkbox_tr, uploaded_file)



def start_import(colid, isTR, uploaded_file):
    """
    Initiates the import process based on whether text regions or lines are to be imported.

    Parameters:
    - colid: The identifier for the collection where the data is to be imported.
    - isTR: A boolean flag indicating the type of import. If True, text regions will be imported; if False, lines will be imported.
    - uploaded_file: The file uploaded by the user, containing the data to be imported.

    """

    # Check if the import is for text regions (TextRegion).
    if isTR:
        # If isTR is True, initiate the import process for text regions.
        import_tr(colid, uploaded_file)
    else:
        # If isTR is False (meaning lines are to be imported), initiate the import process for lines.
        import_lines(colid, uploaded_file)


def import_lines(colid, uploaded_file):
    """
    Imports line data from an uploaded file into a specified collection.

    Parameters:
    - colid: The identifier for the collection where the data is to be imported.
    - uploaded_file: The file uploaded by the user, containing line data to be imported.
    """

    try:
        # Read the first 12 characters of the file to determine the delimiter used.
        first_chars = uploaded_file.read(12)
        delimiter = chr(first_chars[11])

        # Reset the file read pointer to the beginning of the file.
        uploaded_file.seek(0)

        # Load the file into a pandas DataFrame, using the detected delimiter and specified data types.
        df = pd.read_csv(uploaded_file, delimiter=delimiter, dtype=str, encoding='unicode_escape')

        # Initialize lists to store data from the first row of the DataFrame.
        customs = [df[u'Tag'][0]]
        ids = [df[u'Textregion Id'][0]]
        linetexts = [df[u'Text'][0]]
        docid = df[u'Dokument Id'][0]
        pageNo = df[u'SeitenNr'][0]

        # Loop through each row in the DataFrame and organize data for import.
        for i in range(1, df.shape[0]):
            # If the page number is the same as the previous row, append data to lists.
            if int(df[u'SeitenNr'][i - 1]) == int(df[u'SeitenNr'][i]):
                customs.append(df[u'Tag'][i])
                ids.append(df[u'Textregion Id'][i])
                linetexts.append(df[u'Text'][i])
                docid = int(df[u'Dokument Id'][i])
                pageNo = int(df[u'SeitenNr'][i])
                # If it's the last row, import the accumulated data for the current page.
                if i == (df.shape[0] - 1):
                    import_in_page(colid, docid, pageNo, ids, linetexts, customs)
            else:
                # If the page number changes, import the data for the completed page.
                import_in_page(colid, docid, pageNo, ids, linetexts, customs)
                # Reinitialize the lists with data from the current row for the next page.
                customs = [df[u'Tag'][i]]
                ids = [df[u'Textregion Id'][i]]
                linetexts = [df[u'Text'][i]]
                docid = df[u'Dokument Id'][i]
                pageNo = df[u'SeitenNr'][i]

        # Display a success message upon completion.
        st.success("Ende erreicht! Daten aus csv importiert!")

    except Exception as e:
        # Display an error message if there's an issue with the import process.
        st.error('Fehler! Mit dem Import-File scheint etwas nicht zu stimmen. Es müsste ein csv mit den Feldern Dokument Id, SeitenNr, Textregion Id, Text, Tag sein. Error: {}'.format(e))

    # End of function without a return value.
    return


def import_tr(colid, uploaded_file):
    """
    Imports text region data from an uploaded file into a specified collection.

    Parameters:
    - colid: The identifier for the collection where the data is to be imported.
    - uploaded_file: The file uploaded by the user, containing text region data to be imported.
    """

    try:
        # Read the first 12 characters of the file to determine the delimiter used.
        first_chars = uploaded_file.read(12)
        delimiter = chr(first_chars[11])

        # Reset the file read pointer to the start of the file.
        uploaded_file.seek(0)

        # Load the file into a pandas DataFrame using the detected delimiter and specified data types.
        df = pd.read_csv(uploaded_file, delimiter=delimiter, dtype=str, encoding='unicode_escape')

        # Initialize a progress bar and text element for the Streamlit UI.
        progress = st.progress(0)
        progress_text = st.empty()

        # Initialize lists to store data from the DataFrame.
        customs = []
        ids = []
        docid = pageNo = None

        # Loop through each row in the DataFrame and organize data for import.
        for i in range(df.shape[0]):
            # Check if it's a new page or the first row.
            if i == 0 or int(df['SeitenNr'][i-1]) != int(df['SeitenNr'][i]):
                # If not the first row and a new page is detected, import the accumulated data for the previous page.
                if ids:
                    import_tr_in_page(colid, docid, pageNo, ids, customs)
                    # Reinitialize the lists for the new page.
                    customs = []
                    ids = []
            
            # Append data from the current row to the lists.
            customs.append(df['Tag'][i])
            ids.append(df['Textregion Id'][i])
            docid = int(df['Dokument Id'][i])
            pageNo = int(df['SeitenNr'][i])

            # If it's the last row, import the accumulated data for the current page.
            if i == df.shape[0] - 1:
                import_tr_in_page(colid, docid, pageNo, ids, customs)

            # Update the progress bar and text element in the UI.
            progress_value = int(100 * ((i + 1) / df.shape[0]))
            progress.progress(progress_value)
            progress_text.text(f"Job progress {progress_value}%")

        # Display a success message upon completion.
        st.success("Data import complete!")

    except Exception as e:
        # Display an error message if there's an issue with the import process.
        st.error(f'Error: {str(e)}')


def import_tr_in_page(colid, docid, pageNo, ids, customs):
    """
    Updates the text regions for a specific page in a document.

    Parameters:
    - colid: The identifier for the collection.
    - docid: The identifier for the document.
    - pageNo: The page number in the document to be updated.
    - ids: A list of text region identifiers.
    - customs: A list of custom attributes corresponding to each text region.

    Returns:
    - True: Indicates successful completion of the function.
    """

    # Retrieve the XML data for the specified page.
    xml = get_page(colid, docid, pageNo)
    soup = BeautifulSoup(xml, "xml")

    try:
        # Iterate over each id and custom attribute pair.
        for j in range(len(ids)):
            # Find all 'TextRegion' elements in the XML.
            for region in soup.findAll("TextRegion"):
                # Check if the current region's id matches the provided id.
                if ids[j] == region['id']:
                    # Update the 'custom' attribute of the region.
                    region['custom'] = customs[j]

        # Post the updated page back to the server via API.
        post_page(colid, docid, pageNo, soup)

    except Exception as e:
        # Log an error message indicating a problem during the import process.
        st.error(f'Fehler beim Import in {docid}, Seite {pageNo}. Abbruch. Error: {str(e)}')

    # Return True to indicate that the function completed successfully.
    return True


def import_in_page(colid, docid, pageNo, ids, linetexts, customs):
    """
    Updates the text lines for a specific page in a document.

    Parameters:
    - colid: The identifier for the collection.
    - docid: The identifier for the document.
    - pageNo: The page number in the document to be updated.
    - ids: A list of text line identifiers.
    - linetexts: A list of text content for each line.
    - customs: A list of custom attributes corresponding to each text line.

    Returns:
    - True: Indicates successful completion of the function.
    """

    # Retrieve the XML data for the specified page.
    xml = get_page(colid, docid, pageNo)
    soup = BeautifulSoup(xml, "xml")

    try:
        # Iterate over each provided text line id.
        for j in range(len(ids)):
            # Find all 'TextLine' elements in the XML.
            for line in soup.findAll("TextLine"):
                # Check if the current line's id matches the provided id.
                if ids[j] == line['id']:
                    # Update the 'custom' attribute and text content ('Unicode' element) of the line.
                    line['custom'] = customs[j]
                    for t in line.findAll("Unicode"):
                        t.string = linetexts[j]

        # Post the updated page back to the server via API.
        post_page(colid, docid, pageNo, soup)

    except Exception as e:
        # Log an error message indicating a problem during the import process.
        st.error(f'Fehler beim Import in {docid}, Seite {pageNo}. Abbruch. Error: {str(e)}')

    # Return True to indicate that the function completed successfully.
    return True


def get_page(colid, docid, pageNo):
    """
    Retrieves the XML content of a specific page from a Transkribus collection.

    Parameters:
    - colid: The identifier for the collection.
    - docid: The identifier for the document within the collection.
    - pageNo: The page number to retrieve.

    Returns:
    - The XML content of the page if successful, None otherwise.
    """

    # Check if a proxy is set in the session state and if it's configured to a specific value.
    if st.session_state.proxy is not None and st.session_state.proxy["https"] == 'http://:@:':
        # Perform a GET request without a proxy if the proxy setting matches the specific value.
        r = requests.get(f"https://transkribus.eu/TrpServer/rest/collections/{colid}/{docid}/{pageNo}/text?JSESSIONID={st.session_state.sessionId}")
    else:
        # Perform a GET request with the proxy settings from the session state.
        r = requests.get(f"https://transkribus.eu/TrpServer/rest/collections/{colid}/{docid}/{pageNo}/text?JSESSIONID={st.session_state.sessionId}", proxies=st.session_state.proxy)

    # Check if the request was successful.
    if r.status_code == requests.codes.ok:
        # Return the text (XML content) of the response.
        return r.text
    else:
        st.error('Fehler!','Fehler bei der Abfrage einer Seite. Doc-ID ' + str(docid) + ' invalid oder Seitenzahl ' + str(pageNo) + ' ausserhalb des Bereichs.')
        # Return None to indicate an unsuccessful request.
        return None

    
def post_page(colid, docid, pageNo, xml):
    """
    Submits the updated XML content of a specific page to the Transkribus collection.

    Parameters:
    - colid: The identifier for the collection.
    - docid: The identifier for the document within the collection.
    - pageNo: The page number to update.
    - xml: The updated XML content to be submitted.

    Returns:
    - True if the submission is successful, False otherwise.
    """

    # Check if a proxy is set in the session state and if it's configured to a specific value.
    if st.session_state.proxy is not None and st.session_state.proxy["https"] == 'http://:@:':
        # Perform a POST request without a proxy if the proxy setting matches the specific value.
        r = requests.post(f"https://transkribus.eu/TrpServer/rest/collections/{colid}/{docid}/{pageNo}/text?JSESSIONID={st.session_state.sessionId}", 
                          data=xml.encode("utf8"), params={"note": "DC"})
    else:
        # Perform a POST request with the proxy settings from the session state.
        r = requests.post(f"https://transkribus.eu/TrpServer/rest/collections/{colid}/{docid}/{pageNo}/text?JSESSIONID={st.session_state.sessionId}", 
                          data=xml.encode("utf8"), params={"note": "DC"}, proxies=st.session_state.proxy)

    # Check if the request was successful.
    if r.status_code == requests.codes.ok:
        # Return True to indicate a successful submission.
        return True
    else:
        # Log an error message if the request was unsuccessful.
        print(r)
        st.error("Fehler!","Fehler beim posten einer Seite. Doc-ID " + str(docid) + " invalid oder Seitenzahl " + str(pageNo) + " ausserhalb des Bereichs?")
        # Return False to indicate an unsuccessful submission.
        return False


if __name__ == "__main__":
    app()