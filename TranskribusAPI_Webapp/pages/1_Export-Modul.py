from io import BytesIO
import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
from PIL import Image
import streamlit.components.v1 as components
from streamlit_extras.app_logo import add_logo
from streamlit_extras.switch_page_button import switch_page
from pathlib import Path
from streamlit.source_util import (
    page_icon_and_name, 
    calc_md5, 
    get_pages,
    _on_pages_changed
)
import xlsxwriter
import os
from PIL import Image  # Assuming images are handled with PIL
import shutil
from bs4 import BeautifulSoup
import requests
import numpy as np

'''
TODO:
- Add image insertion into Excel
- The file right now gets created inside the file-py running folder. Make it downloadable
- Add progression bar
- Style it so it looks more appealing
'''

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

    st.markdown("Bitte die Parameter definieren:")

    textentryColId = st.text_input("Collection id:")
    textentryDocId = st.text_input("Doc id:")
    textentryExportTR = st.text_input("zu exportierende Textregion (leer = alle):")
    #checkboxBilder = st.checkbox('ohne Bilder exportieren')
    checkboxLinie = st.checkbox('Zeilen der Textregion separiert exportieren')

    checkboxBilder = True

    # Input for starting page
    text_entry_start_page = st.text_input('Start Seite:', key='start_page')

    # Input for ending page
    text_entry_end_page = st.text_input('End Seite:', key='end_page')

    # Assuming you have a function 'startExtraction' defined elsewhere in your code
    # Create the button to start extraction
    if st.button('Start Extraction'):
        start_extraction(textentryColId, textentryDocId, text_entry_start_page, text_entry_end_page, textentryExportTR, checkboxLinie, checkboxBilder)
    
    # Browse button (the functionality will depend on how you want to implement browsing in Streamlit)
    download_button = st.button('Download extracted data')


def check_session():
    if dict.get(st.session_state["sessionId"]) == None:
        return False
    else:
        return True


def start_extraction(col_id, doc_id, start_page, end_page, region_name, export_line, no_export_images):

    doc_name = get_doc_name_from_id(col_id, doc_id)
    doc_name = doc_name.replace("(", "").replace(")", "").replace(" ", "_").replace("/", "_")

    if export_line:
        result = extract_regions_lines_text_and_image(col_id, doc_id, start_page, end_page, 'LAST', region_name)
        text, nr_on_page, region_name, ids, customs, imgs, page_nr = result
        workbook_name = f"{doc_name}_RegionExtraction_{region_name}_lines.xlsx"
    else:
        result = extract_regions_text_and_image(col_id, doc_id, start_page, end_page, 'LAST', region_name)
        text, nr_on_page, region_name, ids, customs, imgs, page_nr = result
        workbook_name = f"{doc_name}_RegionExtraction_{region_name}_regions.xlsx"

    wb = xlsxwriter.Workbook(workbook_name)
    sht1 = wb.add_worksheet()

    st.write(nr_on_page[0])

    # Initialize the column names
    columns = ['Dokument Id', 'Dokument Name', 'Region Name', 'Seitennr', 'Nummer auf Seite', 'Text', 'Textregion Id', 'Customs']
    if not no_export_images:
        columns.append('Bild')

    # Write the columns header
    for i, col in enumerate(columns):
        sht1.write(0, i, col)

    wrap = wb.add_format({'text_wrap': True})

    sht1.set_column(5, 5, 50)
    sht1.set_column(6, 6, 50)
    sht1.set_column(4, 4, 50)
    sht1.set_column(7, 7, 70)

    row = 1
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
                    image = imgs[page][c]
                    image_buffer = BytesIO()
                    image.save(image_buffer, format='jpg')
                    sht1.insert_image(row, 8, None, {'image_data': image_buffer, 'x_scale': 0.3, 'y_scale': 0.3})
                    #img_path = f'tempImgs/tempImg{page}_{c}.jpg'
                    #imgs[page][c].save(img_path)  # Assuming imgs is a list of PIL Image objects
                row += 1
    else:
        for c in range(len(text)):
            sht1.set_row(row, 150)
            sht1.write(row, 0 , str(doc_id))
            sht1.write(row, 1, str(doc_name))
            sht1.write(row, 2, region_name[c])
            sht1.write(row, 3, page_nr[c])
            sht1.write(row, 4, nr_on_page[c])
            sht1.write(row, 5, '\n'.join(text[c]), wrap)
            sht1.write(row, 6, ids[c])
            sht1.write(row, 7, customs[c])
            if not no_export_images:
                #img_path = f'tempImgs/tempImg{c}_{nr_on_page[c]}.jpg'
                #imgs[c].save(img_path)
                #sht1.insert_image(row, 8, img_path, {'x_scale': 0.3, 'y_scale': 0.3})
                image = imgs[page][c]
                image_buffer = BytesIO()
                image.save(image_buffer, format='jpg')
                sht1.insert_image(row, 8, None, {'image_data': image_buffer, 'x_scale': 0.3, 'y_scale': 0.3})
            row += 1

    wb.close()

    st.success(f"Textregion {region_name} aus Doc {doc_id} extrahiert.")


def extract_regions_lines_text_and_image(col_id, doc_id, start_page, end_page, tool_name, region_name):
    try:
        # Assuming extractTranscriptionRaw and getDocumentR are defined elsewhere
        doc = extract_transcription_raw(col_id, doc_id, start_page, end_page, tool_name)
        doc_config = get_document_r(col_id, doc_id)['pageList']['pages']
        

        # Determine start and end pages
        start_page = int(start_page)

        end_page = len(doc) if end_page == '-' else int(end_page) if isinstance(end_page, int) else int(end_page)

        full_text = []
        ids = []
        region_names = []
        customs = []
        nr_on_page = []
        page_nrs = []
        imgs = []
        nr_on_page_counter = 0

        for c, page in enumerate(doc):
            soup = BeautifulSoup(page, "xml")
            page_txt = []
            region_name_txt = []
            nr_on_page_txt = []
            line_txt = []
            custom_txt = []
            page_imgs = []
            page_nr_array = []

            page_img_url = doc_config[start_page + c - 1]['url']
            page_nr = doc_config[start_page + c - 1]['pageNr']

            nr_on_page_counter = 0
            # Fetch and process image
            #response = requests.get(page_img_url)
            #page_img = Image.open(BytesIO(response.content))

            page_img = get_image_from_url(page_img_url)

            for region in soup.find_all("TextRegion"):
                try:
                    if region_name in region['custom'] or region_name == "":
                        nr_on_page_counter += 1
                        region_name_text = region['custom'][region['custom'].find('structure {type:')+16:-2]

                        for line in region.find_all("TextLine"):
                            lineid_text = line['id']
                            custom_text = line['custom']
                            region_text = ""
                            for t in line.findAll("Unicode"):
                                region_text = t.text
                            cords = line.find('Coords')['points']
                            points = [c.split(",") for c in cords.split(" ")]

                            maxX = -1000
                            minX = 100000
                            maxY = -1000
                            minY = 100000

                            for p in points:
                                maxX = max(int(p[0]), maxX)
                                minX = min(int(p[0]), minX)
                                maxY = max(int(p[1]), maxY)
                                minY = min(int(p[1]), minY)

                            nr_on_page_txt.append(str(nr_on_page_counter))
                            page_imgs.append(page_img.crop((minX, minY, maxX, maxY)))
                            page_txt.append(region_text)
                            line_txt.append(lineid_text)
                            region_name_txt.append(region_name_text)
                            custom_txt.append(custom_text)
                            page_nr_array.append(page_nr)
                except:
                    # Add error handling
                    pass

            full_text.append(page_txt)
            nr_on_page.append(nr_on_page_txt)
            ids.append(line_txt)
            region_names.append(region_name_txt)
            customs.append(custom_txt)
            imgs.append(page_imgs)
            page_nrs.append(page_nr_array)

        return full_text, nr_on_page, region_names, ids, customs, imgs, page_nrs

    except Exception as e:
        st.error(f'Ein Fehler ist aufgetreten bei: {e}')

def extract_regions_text_and_image(col_id, doc_id, start_page, end_page, tool_name, region_name):
    try:
        # Assuming extract_transcription_raw and get_document_r are defined elsewhere
        doc = extract_transcription_raw(col_id, doc_id, start_page, end_page, tool_name)

        # Determine start and end pages
        start_page = int(start_page) if isinstance(start_page, int) else int(start_page)
        end_page = len(doc) if end_page == '-' else int(end_page) if isinstance(end_page, int) else int(end_page)

        doc_config = get_document_r(col_id, doc_id)['pageList']['pages']
        page_txt, region_name_txt, page_nr_txt, nr_on_page_txt, trid_txt, custom_txt, page_imgs = ([] for _ in range(7))
        nr_on_page_counter = 0

        for c, page in enumerate(doc[start_page-1:end_page]):
            soup = BeautifulSoup(page, "xml")
            page_img_url = doc_config[start_page + c - 1]['url']
            page_nr = doc_config[start_page + c - 1]['pageNr']

            # Fetch and process image
            response = requests.get(page_img_url)
            page_img = Image.open(BytesIO(response.content))

            for region in soup.find_all("TextRegion"):
                try:
                    if region_name in region['custom'] or region_name == "":
                        nr_on_page_counter += 1
                        trid_text = region['id']
                        region_name_text = region['custom'][region['custom'].find('structure {type:')+16:-2]
                        custom_text = region['custom']
                        region_text = []

                        for line in region.find_all("TextLine"):
                            last_line = ''.join(t.text for t in line.find_all("Unicode"))
                            region_text.append(last_line)

                        cords = region.find('Coords')['points']
                        points = [list(map(int, c.split(","))) for c in cords.split(" ")]

                        minX, minY = min(points)[0], min(points)[1]
                        maxX, maxY = max(points)[0], max(points)[1]

                        page_imgs.append(page_img.crop((minX, minY, maxX, maxY)))
                        page_txt.append(region_text)
                        trid_txt.append(trid_text)
                        region_name_txt.append(region_name_text)
                        custom_txt.append(custom_text)
                        page_nr_txt.append(page_nr)
                except:
                    pass

        return page_txt, nr_on_page_txt, region_name_txt, trid_txt, custom_txt, page_imgs, page_nr_txt

    except Exception as e:
        st.error(f'Fehler bei der Extraktion der Regionen: {e}')

def get_doc_name_from_id(colId, docId):
    doc = get_document_r(colId, docId)
    return doc['md']['title']

## Returns the raw text transcription of a loaded document pulled from the API
def extract_transcription_raw(colId, docId, text_entry_start_page, text_entry_end_page, toolName):
        #get document
        doc = get_document_r(colId, docId)['pageList']['pages']

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
                #self.popupmsg("Keine Transkription für {} auf Seite {} vorhanden! Vorgang wird abgebrochen...".format(toolName, page))
                return
        return page_text


def get_document_r(colid, docid):
    if st.session_state.proxy is not None and st.session_state.proxy["https"] == 'http://:@:':
        r = requests.get("https://transkribus.eu/TrpServer/rest/collections/{}/{}/fulldoc?JSESSIONID={}".format(colid, docid, st.session_state.sessionId))
    else:
        r = requests.get("https://transkribus.eu/TrpServer/rest/collections/{}/{}/fulldoc?JSESSIONID={}".format(colid, docid, st.session_state.sessionId), proxies = st.session_state.proxy)

    if r.status_code == requests.codes.OK:
        return r.json()
    else:
        print(r)
        st.error(f'Fehler bei der Abfrage eines Dokumentes. Doc-ID {docid} invalid?')
        return None
    
def get_image_from_url(url):
        if st.session_state.proxy is not None and st.session_state.proxy["https"] == 'http://:@:':
            r = requests.get(url, stream=True)
        else:
            r = requests.get(url, stream=True, proxies = st.session_state.proxy)
        img = Image.open(r.raw)
        return img


if __name__ == "__main__":
    app()