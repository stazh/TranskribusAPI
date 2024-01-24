from io import BytesIO
import random
import shutil
import streamlit as st
from PIL import Image
import xlsxwriter
from PIL import Image
from bs4 import BeautifulSoup
import utils.utility_functions as uf
import requests
import os


def app():
    """
    This is the starting point of the application, thus it runs first.

    Parameters:
        None

    Returns:
        None
    """

    # Check if the user is logged in and set the header accordingly via utility_functions.py
    uf.check_session_state(st)
    uf.set_header('Export-Modul', st)

    # Prompt the user to define parameters with markdown text.
    st.markdown("Bitte die Parameter definieren:")

    # Collect various user inputs for collection id, document id, and text region export.
    textentryColId = st.text_input("Collection id:")
    textentryDocId = st.text_input("Doc id:")
    textentryExportTR = st.text_input("zu exportierende Textregion (leer = alle):")
    checkboxBilder = st.checkbox('ohne Bilder exportieren')
    checkboxLinie = st.checkbox('Zeilen der Textregion separiert exportieren')

    # Input fields for specifying the start and end page for extraction.
    text_entry_start_page = st.text_input('Start Seite:', key='start_page')
    text_entry_end_page = st.text_input('End Seite:', key='end_page')

    # Button to initiate the extraction process. Calls 'start_extraction' when clicked.
    if st.button('Start Extraction'):
        with st.spinner('Extrahiere Textregion. Dies kann einige Zeit dauern...'):
            file_download, user_file_name = start_extraction(textentryColId, textentryDocId, text_entry_start_page, text_entry_end_page, textentryExportTR, checkboxLinie, checkboxBilder)
    
    # Attempt to provide a download button for the file, if available.
    try:
        with open(file_download, 'rb') as file:
            st.download_button(
                label='Download Export',
                data=file,
                file_name=user_file_name,
                mime='application/vnd.ms-excel',
                on_click=remove_file(file_download)
            )
            
    except Exception as e:
        # Silently pass if there is any exception (like file not found).
        # This code causes an exception but it still works somehow. It says the used variables are not defined, but they are. May be worth looking into it at a later time
        pass

# Function to remove the temporary file after download.
# Gets called as a callback when the download button is clicked.
def remove_file(file_path):
    def remove_action():
        new_path = os.path.dirname(file_path)
        shutil.rmtree(new_path)
    return remove_action

def start_extraction(col_id, doc_id, start_page, end_page, region_name, export_line, no_export_images):
    """
    Extracts text and images from Transkribus API for a given document and region.

    Parameters:
    col_id (int): The collection ID.
    doc_id (int): The document ID.
    start_page (int): The starting page number.
    end_page (int): The ending page number.
    region_name (str): The name of the region to extract.
    export_line (bool): Flag indicating whether to extract lines of text or not.
    no_export_images (bool): Flag indicating whether to export images or not.

    Returns:
    tuple: A tuple containing the workbook name and file name of the extracted data.
    """

    # Retrieve and format the document name based on the collection and document IDs.
    doc_name = uf.get_doc_name_from_id(col_id, doc_id, st)
    doc_name = doc_name.replace("(", "").replace(")", "").replace(" ", "_").replace("/", "_")

    # Define output paths for the extracted data and temporary images.
    output_path = 'data/export/download/' + st.session_state.sessionId + '/'
    image_folder = 'data/export/tempImgs/' + st.session_state.sessionId + '/'

    # Create a folder for personal excel download if it doesn't exist.
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # generate a random number between 1 and 1000 to avoid overwriting of files
    random_number = str(random.randint(1, 1000))
    
    # Extract text and images based on whether lines or entire regions are to be exported.
    if export_line:
        result = extract_regions_lines_text_and_image(col_id, doc_id, start_page, end_page, 'LAST', region_name)
        text, nr_on_page, region_name, ids, customs, imgs, page_nr = result
        workbook_name = f"{output_path}{random_number}.xlsx"
        file_name = f"{doc_name}_RegionExtraction_lines.xlsx"
    else:
        result = extract_regions_text_and_image(col_id, doc_id, start_page, end_page, 'LAST', region_name)
        text, nr_on_page, region_name, ids, customs, imgs, page_nr = result
        workbook_name = f"{output_path}{random_number}.xlsx"
        file_name = f"{doc_name}_RegionExtraction_regions.xlsx"

    # Create and configure an Excel workbook and worksheet.
    wb = xlsxwriter.Workbook(workbook_name)
    sht1 = wb.add_worksheet()

    # Initialize column names based on whether images will be exported.
    if not no_export_images:
        columns = ['Dokument Id', 'Dokument Name', 'Region Name','Seitennr', 'Nummer auf Seite', 'Text', 'Textregion Id','Customs']
    else:
        columns = ['Dokument Id', 'Dokument Name', 'Region Name','Seitennr', 'Nummer auf Seite', 'Text', 'Textregion Id','Customs','Bild']

    # Write the column headers into the Excel sheet.
    for i, col in enumerate(columns):
        sht1.write(0, i, col)

    # Define a text wrap format for cells.
    wrap = wb.add_format({'text_wrap': True})

    # Create a folder for temporary images if it doesn't exist.
    if not os.path.exists(image_folder):
        os.makedirs(image_folder)
 
    # Set the column widths for better readability.
    sht1.set_column(5, 5, 50)
    sht1.set_column(6, 6, 50)
    sht1.set_column(4, 4, 50)
    sht1.set_column(7, 7, 70)

    # Iterate over the extracted data and populate the worksheet.
    # The logic differs if exporting lines or entire regions.
    # In both cases, images are saved and inserted into the worksheet if required.
    row = 1
    # Insertion logic for lines
    if export_line:
        for page in range(len(text)):
            for c in range(len(text[page])):
                sht1.set_row(row, 50)
                sht1.write(row, 0, str(doc_id))
                sht1.write(row, 1, str(doc_name))
                sht1.write(row, 2, region_name[page][c])
                sht1.write(row, 3, page_nr[page][c])
                sht1.write(row, 4, nr_on_page[page][c])
                sht1.write(row, 5, text[page][c])
                sht1.write(row, 6, ids[page][c])
                sht1.write(row, 7, customs[page][c])
                if not no_export_images:
                    imgs[page][c].save(image_folder + '/tempImg{}_{}.jpg'.format(page, c))
                    sht1.insert_image(row, 8, image_folder + '/tempImg{}_{}.jpg'.format(page, c),{'x_scale': 0.3, 'y_scale': 0.3})
                row += 1
    else:
        for c in range(len(text)):
            sht1.set_row(row, 150)
            sht1.write(row, 0, str(doc_id))
            sht1.write(row, 1, str(doc_name))
            sht1.write(row, 2, region_name[c])
            sht1.write(row, 3, page_nr[c])
            sht1.write(row, 4, nr_on_page[c])
            sht1.write(row, 5, '\n'.join(text[c]), wrap)
            sht1.write(row, 6, ids[c])
            sht1.write(row, 7, customs[c])
            if not no_export_images:
                imgs[c].save(image_folder + '/tempImg{}_{}.jpg'.format(c,nr_on_page[c]))
                sht1.insert_image(row, 8, image_folder + '/tempImg{}_{}.jpg'.format(c,nr_on_page[c]),{'x_scale': 0.3, 'y_scale': 0.3})
            row += 1
    
    # Close the workbook and remove the temporary image folder.
    wb.close()
    shutil.rmtree(image_folder)

    # Notify the user of successful extraction.
    st.success(f"Textregionen aus Doc {doc_id} extrahiert.")

    # Return the workbook and file names for further use.
    return workbook_name, file_name

"""
The following two functions are used to extract text and images from a document.
They are based on the functions from the TranskribusPyClient library, but modified
to work with Streamlit and to return the extracted data instead of writing it to a file.
"""
def extract_regions_lines_text_and_image(col_id, doc_id, start_page, end_page, tool_name, region_name):
    try:
        # Extract transcription and document configuration data from Transkribus API.
        doc = uf.extract_transcription_raw(col_id, doc_id, start_page, end_page, tool_name, st)
        doc_config = uf.get_document_r(col_id, doc_id, st)['pageList']['pages']
        
        # Determine the actual start and end page numbers for processing.
        start_page = int(start_page)
        end_page = len(doc) if end_page == '-' else int(end_page) if isinstance(end_page, int) else int(end_page)

        # Initialize lists to store extracted data.
        full_text = []
        ids = []
        region_names = []
        customs = []
        nr_on_page = []
        page_nrs = []
        imgs = []
        nr_on_page_counter = 0

        # Process each page in the document.
        for c, page in enumerate(doc):
            soup = BeautifulSoup(page, "xml")

            # Initialize lists for storing data specific to the current page.
            page_txt = []
            region_name_txt = []
            nr_on_page_txt = []
            line_txt = []
            custom_txt = []
            page_imgs = []
            page_nr_array = []

            # Fetch page image URL and number from document configuration.
            page_img_url = doc_config[start_page + c - 1]['url']
            page_nr = doc_config[start_page + c - 1]['pageNr']

            nr_on_page_counter = 0

            # Retrieve the page image.
            response = requests.get(page_img_url)
            page_img = Image.open(BytesIO(response.content))

            # Process each TextRegion in the page.
            for region in soup.find_all("TextRegion"):
                try:
                    # Check if the region matches the specified name or if the name is empty.
                    if region_name in region['custom'] or region_name == "":
                        nr_on_page_counter += 1

                        # Extract region name and other details.
                        region_name_text = region['custom'][region['custom'].find('structure {type:')+16:-2]

                        # Process each TextLine within the region.
                        for line in region.find_all("TextLine"):
                            lineid_text = line['id']
                            custom_text = line['custom']
                            region_text = ""
                            for t in line.findAll("Unicode"):
                                region_text = t.text
                            cords = line.find('Coords')['points']
                            points = [c.split(",") for c in cords.split(" ")]

                            # Determine the bounding box for the line text.
                            maxX, minX = -1000, 100000
                            maxY, minY = -1000, 100000
                            for p in points:
                                maxX = max(int(p[0]), maxX)
                                minX = min(int(p[0]), minX)
                                maxY = max(int(p[1]), maxY)
                                minY = min(int(p[1]), minY)

                            # Append extracted data to corresponding lists.
                            nr_on_page_txt.append(str(nr_on_page_counter))
                            page_imgs.append(page_img.crop((minX, minY, maxX, maxY)))
                            page_txt.append(region_text)
                            line_txt.append(lineid_text)
                            region_name_txt.append(region_name_text)
                            custom_txt.append(custom_text)
                            page_nr_array.append(page_nr)
                except:
                    # Add appropriate error handling.
                    pass

            # Add extracted data from the current page to the full dataset.
            full_text.append(page_txt)
            nr_on_page.append(nr_on_page_txt)
            ids.append(line_txt)
            region_names.append(region_name_txt)
            customs.append(custom_txt)
            imgs.append(page_imgs)
            page_nrs.append(page_nr_array)

        # Return the compiled data from all pages.
        return full_text, nr_on_page, region_names, ids, customs, imgs, page_nrs

    except Exception as e:
        # Handle any exceptions that occur during the process.
        st.error(f'Ein Fehler ist aufgetreten bei: {e}')


def extract_regions_text_and_image(col_id, doc_id, start_page, end_page, tool_name, region_name):
    """
    Extracts the text and image of specified regions from a document.

    Parameters:
    - col_id (str): The collection ID.
    - doc_id (str): The document ID.
    - start_page (int or str): The starting page number or '-' to start from the first page.
    - end_page (int or str): The ending page number or '-' to extract until the last page.
    - tool_name (str): The name of the tool used for extraction.
    - region_name (str): The name of the region to extract. Leave empty to extract all regions.

    Returns:
    - page_txt (list): A list of lists containing the extracted text for each region on each page.
    - nr_on_page_txt (list): A list of integers representing the number of regions on each page.
    - region_name_txt (list): A list of strings representing the names of the extracted regions.
    - trid_txt (list): A list of strings representing the TRID (Text Region ID) of each extracted region.
    - custom_txt (list): A list of strings representing the custom attributes of each extracted region.
    - page_imgs (list): A list of PIL.Image objects representing the cropped images of each extracted region.
    - page_nr_txt (list): A list of integers representing the page numbers of each extracted region.
    """
    try:
        # Extract transcription and document configuration data from Transkribus API.
        doc = uf.extract_transcription_raw(col_id, doc_id, start_page, end_page, tool_name, st)

        # Determine the actual start and end page numbers for processing.
        start_page = int(start_page) if isinstance(start_page, int) else int(start_page)
        end_page = len(doc) if end_page == '-' else int(end_page) if isinstance(end_page, int) else int(end_page)

        # Get document configuration, which includes page URLs and numbers.
        doc_config = uf.get_document_r(col_id, doc_id, st)['pageList']['pages']

        # Initialize lists to store extracted data.
        page_txt, region_name_txt, page_nr_txt, nr_on_page_txt, trid_txt, custom_txt, page_imgs = ([] for _ in range(7))

        # Process each page in the document.
        for c, page in enumerate(doc):
            soup = BeautifulSoup(page, "xml")
            # Fetch page image URL and number from document configuration.
            page_img_url = doc_config[start_page + c - 1]['url']
            page_nr = doc_config[start_page + c - 1]['pageNr']
            nr_on_page_counter = 0

            # Retrieve the page image.
            response = requests.get(page_img_url)
            page_img = Image.open(BytesIO(response.content))

            # Process each TextRegion in the page.
            for region in soup.find_all("TextRegion"):
                try:
                    # Check if the region matches the specified name or if the name is empty.
                    if region_name in region['custom'] or region_name == "":
                        nr_on_page_counter += 1

                        # Extract text region ID, name, and other details.
                        trid_text = region['id']
                        region_name_text = region['custom'][region['custom'].find('structure {type:')+16:-2]
                        custom_text = region['custom']
                        region_text = []
                        last_line = ""

                        # Process each TextLine within the region, extracting text.
                        for line in region.findAll("TextLine"):
                            for t in line.findAll("Unicode"):
                                last_line = t.text
                            region_text.append(last_line)

                        # Determine the bounding box for the text region.
                        cords = region.find('Coords')['points']
                        points = [c.split(",") for c in cords.split(" ")]
                        maxX, minX = -1000, 100000
                        maxY, minY = -1000, 100000
                        for p in points:
                            maxX = max(int(p[0]), maxX)
                            minX = min(int(p[0]), minX)
                            maxY = max(int(p[1]), maxY)
                            minY = min(int(p[1]), minY)

                        # Append extracted data to corresponding lists.
                        page_imgs.append(page_img.crop((minX, minY, maxX, maxY)))
                        page_txt.append(region_text)
                        trid_txt.append(trid_text)
                        region_name_txt.append(region_name_text)
                        custom_txt.append(custom_text)
                        page_nr_txt.append(page_nr)
                        nr_on_page_txt.append(nr_on_page_counter)
                except:
                    # Error handling for individual region processing.
                    pass

        # Return the compiled data from all pages.
        return page_txt, nr_on_page_txt, region_name_txt, trid_txt, custom_txt, page_imgs, page_nr_txt

    except Exception as e:
        # Handle any exceptions that occur during the overall process.
        st.error(f'Fehler bei der Extraktion der Regionen: {e}')


if __name__ == "__main__":
    app()