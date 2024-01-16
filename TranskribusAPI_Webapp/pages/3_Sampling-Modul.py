import random
import requests
import streamlit as st
import pandas as pd
import numpy as np
import os
import xlwings as xw
import xml.etree.ElementTree as et
from bs4 import BeautifulSoup
from itertools import chain
from streamlit_option_menu import option_menu
from PIL import Image
import streamlit.components.v1 as components
from streamlit_extras.app_logo import add_logo
from streamlit_extras.switch_page_button import switch_page

def app():
    """
    This function prepares the tab which lets us submit transcription jobs for certain trained models and
    evaluate those models.
    """

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

    # TODO: delete DocumentID

    st.header("Sampling-Modul")
    st.markdown("---")

    # Set the instruction title
    st.markdown("Bitte die Parameter für das Sampling definieren:")

    textentryColId = st.text_input("Collection id:")
    textentryDocId = st.text_input("Doc id:")

    # Models
    st.text('Modelle:')

    # Model load button
    if st.button('Modelle abrufen'):
        models, modelIdMap, modelProvMap = loadModelNames(textentryColId)
        st.session_state['models'] = models  # Store models in session state
        st.session_state['modelsIdMap'] = modelIdMap
        st.session_state['modelProvMap'] = modelProvMap

    # check if models is in session state
    if 'models' in st.session_state and st.session_state['models']:
        st.session_state['model'] = st.selectbox("Wählen Sie ein Modell", st.session_state['models'])

    # Image export checkbox
    imgExport = st.checkbox("Bilder der Linien mit dem besten und schlechtesten CER-Wert exportieren", value=True)

    check_is_collection = st.checkbox("Ist die Collection eine Sample-Collection?")

    # Submit job button
    if st.button('Check Collection'):
        if check_is_collection:
            evaluateSelectedModels(textentryColId, textentryDocId, imgExport, 0, "-")
        else:
            st.write("Bitte zuerst die Checkbox 'Ist die Collection eine Sample-Collection?' aktivieren.")


def loadModelNames(textentryColId):
    """
    This function loads the names of all available models into the select box.
    """

    try:
        colId = str(textentryColId)
        sampleCol = colId

        modelList, modelsIdMap, modelProvMap = get_models_list(colId)

        return modelList, modelsIdMap, modelProvMap

    except Exception as e:
        st.error(f'Fehler: {str(e)}')

def evaluateSelectedModels(colId, docId, imgExport, startPage, endPage):
    """
    This function starts the evaluation process by using the selected model for transcription,
    if no transcription is available. Note: If docId is == "" then the process is applied to all
    documents inside the defined collection.
    """
    try:
        if docId == "":
            docIds = getDocIdsList(st.session_state.sessionId, colId)
            for c, docId in enumerate(docIds):
                evaluateModels(colId, docId, imgExport, startPage, endPage)
        else:
            evaluateModels(colId, docId, imgExport, startPage, endPage)
        st.success("Alle Samples evaluiert.")
    except Exception as e:
        st.warning('Prozess abgebrochen wegen Fehler: ' + str(e), icon="⚠️")


def evaluateModels(textentryColId, textentryDocId, imgExport, textentryStartPage, textentryEndPage):
    """
        This function evaluates a specific model on a specified document. 
        Defined through st.session_state['models'] resp. textentryDocId.
    """

    if isinstance(textentryDocId, int):
        currentDocId = textentryDocId
    else:
        currentDocId = textentryDocId
    if isinstance(textentryColId, int):
        currentColId = textentryColId
    else:
        currentColId = textentryColId
        
    #get the keys of the transcriptions of the Ground Truth
    keys_GT = get_doc_transcript_keys(textentryColId, currentDocId, textentryStartPage, textentryEndPage, 'GT')
    #get the keys of the transcriptions of the selected model
    keys = get_doc_transcript_keys(textentryColId, currentDocId, textentryStartPage, textentryEndPage, st.session_state['model'])
    transcripts_GT = getDocTranscript(textentryColId, currentDocId, textentryStartPage, textentryEndPage, 'GT')
    transcripts_M = getDocTranscript(textentryColId, currentDocId, textentryStartPage, textentryEndPage, st.session_state['model'])
    charAmount_List = []
    target_dir = "D:/00_Work/Zivi/transkribus" + "/" + st.session_state.sessionId
    try:
        if len(transcripts_GT) == len(transcripts_M):
            for i in range(len(transcripts_GT)):
                amount = (len(transcripts_GT[i]) + len(transcripts_M[i]))/2
                charAmount_List.append(len(transcripts_GT[i]))
        wer_list = []
        cer_list = []

        # Replace this with a functioning image processing function
        if imgExport and not os.path.exists(target_dir + '/Images_best_cer_' + str(st.session_state['model']) + '/'):
            os.makedirs(target_dir + '/Images_best_cer_' + str(st.session_state['model']) + '/')

        if imgExport and not os.path.exists(target_dir + '/Images_worst_cer_' + str(st.session_state['model']) + '/'):
            os.makedirs(target_dir + '/Images_worst_cer_' + str(st.session_state['model']) + '/')

        #calculate wer and cer for every transcription a model produced
        if not (keys == None or keys_GT == None):
            for k in range(len(keys)):
                wer, cer = getErrorRate(keys[k], keys_GT[k])
                wer_list.append(wer)
                cer_list.append(cer)
            cer_list_gew = []
            wer_list_gew = []
            for j in range(len(cer_list)):
                cer_list_gew.append(cer_list[j]*charAmount_List[j]/np.sum(charAmount_List))
                wer_list_gew.append(wer_list[j]*charAmount_List[j]/np.sum(charAmount_List))
            pages = extract_transcription_raw(currentColId, currentDocId, textentryStartPage, textentryEndPage, st.session_state['model'])
        #find best and worst cer
            cer_best = [100,0]
            cer_worst = [0,0]
            for h in range(len(cer_list)):
                if cer_list[h] < cer_best[0]:
                    cer_best[0] = cer_list[h]
                    cer_best[1] = h
                if cer_list[h] > cer_worst[0]:
                    cer_worst[0] = cer_list[h]
                    cer_worst[1] = h
            #save best and worst cer as image and variable if checkbox selected ---------
            if imgExport:
                image_worst_temp = get_image_from_url(get_document_r(currentColId, currentDocId)['pageList']['pages'][cer_worst[1]]['url'])
                image_best_temp = get_image_from_url(get_document_r(currentColId, currentDocId)['pageList']['pages'][cer_best[1]]['url'])
                soup_best = BeautifulSoup(pages[cer_best[1]], "xml")
                soup_worst = BeautifulSoup(pages[cer_worst[1]], "xml")
                for region in soup_best.findAll("TextLine"):
                #crop out the image
                    cords = region.find('Coords')['points']
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
                    image_best = image_best_temp.crop((minX, minY, maxX,maxY))
                for region in soup_worst.findAll("TextLine"):
                #crop out the image
                    cords = region.find('Coords')['points']
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
                    image_worst = image_worst_temp.crop((minX, minY, maxX,maxY))
                worst_cer = cer_worst[0]
                best_cer = cer_best[0]
                best_url = target_dir + '/Images_best_cer_' + str(st.session_state['model']) + '/'+ get_doc_name_from_id(currentColId, currentDocId) +'_CER_' + str(best_cer) + '_Page_'+str(cer_best[1]+1) +'.jpg'
                worst_url = target_dir + '/Images_worst_cer_' + str(st.session_state['model']) + '/'+ get_doc_name_from_id(currentColId, currentDocId) +'_CER_' + str(worst_cer) + '_Page_'+str(cer_worst[1]+1) +'.jpg'
                image_best.save(best_url)
                image_worst.save(worst_url)
            #---------------------------------------------------------------------------------------
            #check if excel file already exists
            if not os.path.exists(target_dir + '/ModelEvaluation.xlsx'):
                print("Creating excel file...")
            #create the excel file
                pd.DataFrame().to_excel(target_dir + '/ModelEvaluation.xlsx')
            #wb = xlsxwriter.Workbook(TARGET_DIR.get() + '/ModelEvaluation.xlsx')
            #open the created excel file
            #sht1 = wb.add_worksheet()
                wb = xw.Book(target_dir + '/ModelEvaluation.xlsx')
                sht1 = wb.sheets['Sheet1'] 
            #init the column names
                columns = ['doc Name Sample']
                if imgExport:
                    columns.extend(chain(*[['CER{}'.format(i), 'WER{}'.format(i), 'Model{}'.format(i), 'Best_CER{}'.format(i), 'Best_CER_Imag{}'.format(i), 'Worst_CER{}'.format(i), 'Worst_CER_Imag{}'.format(i)] for i in range(1,10)]))
                else:
                    columns.extend(chain(*[['CER{}'.format(i), 'WER{}'.format(i), 'Model{}'.format(i)] for i in range(1,10)]))
                sht1.range('A1').value = columns
                sht1.range('A2').value = get_doc_name_from_id(currentColId, currentDocId)
                sht1.range('B2').value = np.sum(cer_list_gew)
                sht1.range('C2').value = np.sum(wer_list_gew)
                sht1.range('D2').value = st.session_state['model']
                if imgExport:
                    sht1.range('E2').value = best_cer
                    sht1.range('G2').value = worst_cer
                    sht1.range('F2').value = '=HYPERLINK("' + best_url + '")'
                    sht1.range('H2').value = '=HYPERLINK("' + worst_url + '")'

            else:
                #open the excel sheet if the file already exists
                print("Add to existing excel file")
                wb = xw.Book(target_dir + '/ModelEvaluation.xlsx')
                sht1 = wb.sheets['Sheet1']
            #set the current row to two in order to not overwrite the column names
                currentRow = 2
                for c, docId in enumerate(sht1.range('A1','A10000').value):
                    if docId == None:
                        currentRow = c + 1
                        break
                    try:
                        if int(docId) == int(currentDocId):
                            currentRow = c + 1
                            break
                    except:
                        pass
            
            #find the column where one should write to (in case there is an already evaluated model on this document)
                currentColumn = sum(x is not None for x in sht1.range('A{}'.format(currentRow), 'ZZ{}'.format(currentRow)).value)
            
            #write the evaluation to the excel file
                if currentColumn < 3:
                    sht1.range('A{}'.format(currentRow)).value = get_doc_name_from_id(currentColId, currentDocId)
                    sht1.range('B{}'.format(currentRow)).value = np.sum(cer_list_gew)
                    sht1.range('C{}'.format(currentRow)).value = np.sum(wer_list_gew)
                    sht1.range('D{}'.format(currentRow)).value = st.session_state['model']
                    if imgExport:
                        sht1.range('E{}'.format(currentRow)).value = best_cer
                        sht1.range('F{}'.format(currentRow)).value = '=HYPERLINK("' + best_url + '")'
                        sht1.range('G{}'.format(currentRow)).value = worst_cer
                        sht1.range('H{}'.format(currentRow)).value = '=HYPERLINK("' + worst_url + '")'
                else:
                    values = sht1.range('A{}'.format(currentRow), 'ZZ{}'.format(currentRow)).value
                    if imgExport:
                        values[currentColumn:currentColumn + 6] = [np.sum(cer_list_gew), np.sum(wer_list_gew), st.session_state['model'], best_cer, '=HYPERLINK("' + best_url + '")', worst_cer, '=HYPERLINK("' + worst_url + '")']
                    else:
                        values[currentColumn:currentColumn + 2] = [np.sum(cer_list_gew), np.sum(wer_list_gew), st.session_state['model']]
                    sht1.range('A{}'.format(currentRow), 'ZZ{}'.format(currentRow)).value = values
        else:
            st.info("!","Kein GT in Sample vorhanden! Vorgang für Modell {} und Doc {} wird abgebrochen...".format(st.session_state['models'], currentDocId))
        wb.save(target_dir + '/ModelEvaluation.xlsx')
    except Exception as e:
        print(e)
    return


def get_doc_transcript_keys(colId, docId, textentryStartPage, textentryEndPage, toolName):
    """
        Get the keys for the transcriptions of a certain document. Those are needed in order to extract the wer and cer.
    """
    #get document
    doc = get_document_r(colId, docId)['pageList']['pages']
    
    #setup start page
    if isinstance(textentryStartPage, int):
        startPage = textentryStartPage
    else:
        startPage = int(textentryStartPage.get())
    
    #define the endPages
    if textentryEndPage == "-":
        textentryEndPage = len(doc)

    #setup the endpage
    if isinstance(textentryEndPage, int):
        endPage = textentryEndPage
    else:
        endPage = int(textentryEndPage.get())
    
    
    #define the pages
    pages = range(startPage, endPage)
    
    full_text = []
    
    keys = []
    #go through all pages
    for page in pages:
        for ts in doc[page]['tsList']['transcripts']:
            if toolName == 'GT':
                if ts['status'] == 'GT':
                    keys.append(ts['key'])
                    break
            else:
                try:
                    if toolName in ts['toolName']:
                        keys.append(ts['key'])
                        break
                except:
                    pass
    if len(keys) == len(pages):
        return keys
    elif toolName == "GT":
        st.error("Fehler!", "Nicht für alle Pages in Sample mit Docid " + str(docId) + " GT vorhanden.")
        return None
    else:
        #self.popupmsg("HTR müssen noch ausgeführt werden. Dies kann einige Zeit dauern...")
        print("HTR für " + str(docId) + " gestartet.")
        doTranscription(toolName, colId, docId, st.session_state.modelProvMap, st.session_state.modelsIdMap)

        keys = get_doc_transcript_keys(colId, docId, textentryStartPage, textentryEndPage, toolName)
        return keys
        
    return keys


def getDocTranscript(colId, docId, textentryStartPage, textentryEndPage, toolName):
    """
        This function returns the transcription of a certain document.
    """
    pxList = extract_transcription_raw(colId, docId, textentryStartPage, textentryEndPage, toolName)
    if pxList == None:
        return
    full_text = []
    full_text_List = []
    raw_text = ''
    for px in pxList:
        soup = BeautifulSoup(px, "xml")
        for line in soup.findAll("TextLine"):
            for t in line.findAll("Unicode"):
                full_text.append(t.text)
        for line in full_text:
            raw_text = line + '\n'
        full_text_List.append(raw_text[:-1])
        full_text = []
        raw_text = ''
    return full_text_List


def getDocIdsList(sid, colid):
    docs = get_documents(sid, colid)
    docIds = []
    for d in docs:
        docIds.append(d['docId'])
    return docIds


def getErrorRate(key, key_ref):
    """
        This gets the wer and cer for a specific model on a specified document
    """
    if st.session_state.proxy is not None and st.session_state.proxy["https"] == 'http://:@:':
        r = requests.get('https://transkribus.eu/TrpServer/rest/recognition/errorRate?JSESSIONID={}&key={}&ref={}'
                    .format(st.session_state.sessionId, key, key_ref))
    else:
        r = requests.get('https://transkribus.eu/TrpServer/rest/recognition/errorRate?JSESSIONID={}&key={}&ref={}'
                    .format(st.session_state.sessionId, key, key_ref), proxies = st.session_state.proxy)
    #extract wer and cer from the content
    wer = float(et.fromstring(r.content)[0].text)
    cer = float(et.fromstring(r.content)[1].text)
    return wer, cer


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
    
def get_doc_name_from_id(colId, docId):
    doc = get_document_r(colId, docId)
    return doc['md']['title']


def get_image_from_url(url):
    if st.session_state.proxy is not None and st.session_state.proxy["https"] == 'http://:@:':
        r = requests.get(url, stream=True)
    else:
        r = requests.get(url, stream=True, proxies = st.session_state.proxy)
    img = Image.open(r.raw)
    return img

def get_models_list(colId):
    """
        This function returns a list of all available models in transkribus
    """
    if st.session_state.proxy is not None and st.session_state.proxy["https"] == 'http://:@:':
        r = requests.get('https://transkribus.eu/TrpServer/rest/recognition/{}/list?JSESSIONID={}'.format(colId, st.session_state.sessionId))
    else:
        r = requests.get('https://transkribus.eu/TrpServer/rest/recognition/{}/list?JSESSIONID={}'.format(colId, st.session_state.sessionId), proxies = st.session_state.proxy)

    modelsId = r.text.split('htrId>')[1::2]
    models = r.text.split('name>')[1::2]
    modelsProvider = r.text.split('provider>')[1::2]
    for i in range(len(models)):
        models[i] = models[i].replace('</', '')
        modelsId[i] = modelsId[i].replace('</', '')
        modelsProvider[i] = modelsProvider[i].replace('</', '')
    modelsIdMap = dict(zip(models,modelsId))
    modelsProviderMap = dict(zip(models, modelsProvider))
    models.sort()
    return models, modelsIdMap, modelsProviderMap

def doTranscription(toolName, colId, docId, modelProvMap, modelsIdMap):
    """
        This function submits the job such that the model is applied to a certain document.
        Note that a distinction has to be made between PyLaia models and other models.
    """

    if modelProvMap[toolName] == 'PyLaia':
        if st.session_state.proxy is not None and st.session_state.proxy["https"] == 'http://:@:':
            os.system('python ../../Transkribus/TranskribusAPI/lib/TranskribusPyClient/src/TranskribusCommands/do_htrRnn.py {} None {} --docid {} --pylaia'.format(modelsIdMap[toolName], colId, docId))
        else:
            os.system('python ../../Transkribus/TranskribusAPI/lib/TranskribusPyClient/src/TranskribusCommands/do_htrRnn.py {} None {} --docid {} --pylaia --https_proxy={}'.format(modelsIdMap[toolName], colId, docId, st.session_state.proxy))
    else:
        if st.session_state.proxy is not None and st.session_state.proxy["https"] == 'http://:@:':
            os.system('python ../../Transkribus/TranskribusAPI/lib/TranskribusPyClient/src/TranskribusCommands/do_htrRnn.py {} None {} --docid {}'.format(modelsIdMap[toolName], colId, docId))
        else:
            os.system('python ../../Transkribus/TranskribusAPI/lib/TranskribusPyClient/src/TranskribusCommands/do_htrRnn.py {} None {} --docid {} --https_proxy={}'.format(modelsIdMap[toolName], colId, docId, st.session_state.proxy))

    return


def get_documents(sid, colid):
    if st.session_state.proxy is not None and st.session_state.proxy["https"] == 'http://:@:':
        r = requests.get("https://transkribus.eu/TrpServer/rest/collections/{}/list?JSESSIONID={}".format(colid, sid))
    else:
        r = requests.get("https://transkribus.eu/TrpServer/rest/collections/{}/list?JSESSIONID={}".format(colid, sid), proxies = st.session_state.proxy)
    if r.status_code == requests.codes.ok:
        return r.json()
    else:
        print(r)
        st.error('Fehler!','Fehler bei der Abfrage der Dokumentliste. Col-ID ' + str(colid) + ' invalid?')
        return None
    

if __name__ == "__main__":
    app()