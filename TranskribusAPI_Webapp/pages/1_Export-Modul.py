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
checkboxBilder = st.checkbox('ohne Bilder exportieren')
checkboxLinie = st.checkbox('Zeilen der Textregion separiert exportieren')
#Funktioniert nicht download-Button!
with st.file_input() as input:
  if input == None:
    st.warning('No file selected.')
  else:
    TARGET_DIR = input.read()
"""       
        checkboxLinie = Checkbutton(self.window, bg='white',font=self.inputFont, text="Zeilen der Textregion separiert exportieren", variable=exportLinien).grid(row=6, column=1,sticky=W)
        #Target directory
        Label(self.window, text='Zielordner:', bg='white', font=self.inputFont).grid(row=9, column=0,sticky=W)
        
        TARGET_DIR = StringVar(value = '')
 

        #starting page
        Label(self.window, text='Start Seite:', bg='white', font=self.inputFont).grid(row=7, column=0,sticky=W)
        textentryStartPage = Entry(self.window, bg='white',width=40, font = self.inputFont)

        #ending page
        Label(self.window, text='End Seite:', bg='white', font=self.inputFont).grid(row=7, column=1,sticky=W)
        textentryEndPage = Entry(self.window, bg='white',width=40, font = self.inputFont)

        browseButton = Button(text="Browse", command=lambda: self.browse_button(self.TARGET_DIR))
        browseButton.grid(row=10, column=0, sticky=E)
        
        #create the button
        startExtraction(textentryColId.get(), textentryDocId.get(),textentryStartPage,textentryEndPage, textentryExportTR.get(), exportLinien, noExportImages))



    def startExtraction(self, colId, docId, textentryStartPage,textentryEndPage,regionName,exportLine,noExportImages):

        if TARGET_DIR == "":
            tkinter.messagebox.showinfo('Fehler!','Bitte wählen sie einen Zielpfad aus!')

        docName = self.getDocNameFromId(colId, docId)
        docName1 = str(docName)
        docName2 = docName1.replace("(","")
        docName3 = docName2.replace(")","")
        docName4 = docName3.replace(" ","_")
        docName5 = docName4.replace("/","_")

        if exportLine.get() == 1:
            text, nrOnPage, region_Name,ids, customs, imgs, pageNr = self.extractRegionsLinesTextandImage(colId, docId, textentryStartPage, textentryEndPage, 'LAST', regionName)
            wb = xlsxwriter.Workbook(self.TARGET_DIR.get() + '/' + docName5 + '_RegionExtraction'+'_'+ regionName +'_lines.xlsx')
        else:
            text, nrOnPage, region_Name,ids, customs, imgs, pageNr = self.extractRegionsTextandImage(colId, docId,textentryStartPage, textentryEndPage, 'LAST', regionName)
            wb = xlsxwriter.Workbook(self.TARGET_DIR.get() + '/' + docName5 + '_RegionExtraction'+'_'+ regionName +'_regions.xlsx')

        sht1 = wb.add_worksheet()
        
        #init the column names
        if noExportImages.get() == 1:
            columns = ['Dokument Id', 'Dokument Name', 'Region Name','Seitennr', 'Nummer auf Seite', 'Text', 'Textregion Id','Customs']
        else:
            columns = ['Dokument Id', 'Dokument Name', 'Region Name','Seitennr', 'Nummer auf Seite', 'Text', 'Textregion Id','Customs','Bild']
        
        #write the first entry together with the columns header
        for i, col in enumerate(columns):
            sht1.write(0, i, col)
        
        row = 1
        
        #this format is needed, such that we can write on multiple lines
        wrap = wb.add_format({'text_wrap': True})
        
        #folder for temp imgs:
        if not os.path.exists('tempImgs/'):
            os.makedirs("tempImgs")
        #set Image and Text column width
        sht1.set_column(5, 5, 50)
        sht1.set_column(6, 6, 50)
        sht1.set_column(4, 4, 50)
        sht1.set_column(7, 7, 70)
        if exportLine.get() == 1:
            for page in range(len(text)):
                for c in range(len(text[page])):
                    sht1.set_row(row, 50)
                    sht1.write(row, 0, str(docId))
                    sht1.write(row, 1, str(docName))
                    sht1.write(row, 2, region_Name[page][c])
                    sht1.write(row, 3, pageNr[page][c])
                    sht1.write(row, 4, nrOnPage[page][c])
                    sht1.write(row, 5, text[page][c])
                    sht1.write(row, 6, ids[page][c])
                    sht1.write(row, 7, customs[page][c])
                    #sht1.write(row, 6, xmls[page][c])
                    if noExportImages.get() != 1:
                        imgs[page][c].save('tempImgs/tempImg{}_{}.jpg'.format(page, c))
                    # Maybe we could add a scale variable to change the scale of the images in the excel file (Keep x_scale and y_scale equal to get the same ratio)
                        sht1.insert_image(row, 8,'tempImgs/tempImg{}_{}.jpg'.format(page, c),{'x_scale': 0.3, 'y_scale': 0.3})
                    row += 1
        else:
        #write the results into the excel file
            for c in range(len(text)):
                sht1.set_row(row, 150)
                sht1.write(row, 0 , str(docId))
                sht1.write(row, 1, str(docName))
                sht1.write(row, 2, region_Name[c])
                sht1.write(row, 3, pageNr[c])
                sht1.write(row, 4, nrOnPage[c])
                sht1.write(row, 5, '\n'.join(text[c]),wrap)
                sht1.write(row, 6, ids[c])
                sht1.write(row, 7, customs[c])
                    #sht1.write(row, 6, xmls[page][c])
                if noExportImages.get() != 1:
                    imgs[c].save('tempImgs/tempImg{}_{}.jpg'.format(c,nrOnPage[c]))
                    # Maybe we could add a scale variable to change the scale of the images in the excel file (Keep x_scale and y_scale equal to get the same ratio)
                    sht1.insert_image(row, 8,'tempImgs/tempImg{}_{}.jpg'.format(c,nrOnPage[c]),{'x_scale': 0.3, 'y_scale': 0.3})
                row += 1
        wb.close()
        #delete the temporary folder for the images
        shutil.rmtree('tempImgs')
        tkinter.messagebox.showinfo("Ende erreicht!","Textregion " + regionName + " aus Doc " + docId + " extrahiert.")
        return

    def extractRegionsTextandImage(self, colId, docId, textentryStartPage, textentryEndPage, toolName, regionName):
        try:
            #start a progressbar
            progress = Progressbar(self.window,orient=HORIZONTAL,length=100,mode='determinate')
            progress.grid(row=0,column=1, rowspan = 1, columnspan = 2, padx=(100, 10))

            #set title to progressbar
            progressText = Label(self.window, text="job progress 0%:",font=self.titleFont, bg='white')
            progressText.grid(row=0, column=1,sticky=W)
            progressText.config(bg="white")

            self.window.update()
            doc = self.extractTranscriptionRaw(colId, docId, textentryStartPage, textentryEndPage, toolName)

            if isinstance(textentryStartPage, int):
                startPage = textentryStartPage
            else:
                startPage = int(textentryStartPage.get())

            #define the endPages
            if textentryEndPage == '-' or textentryEndPage.get() == '-':
                endPage = len(doc)
            elif isinstance(textentryEndPage, int):
                endPage = textentryEndPage
            else:
                endPage = int(textentryEndPage.get())
            #get document

            #get the data that contains the images
            docConfig = self.getDocumentR(colId, docId)['pageList']['pages']
            page_txt = []
            region_name_txt = []
            page_nr_txt = []
            nrOnPage_txt = []
            trid_txt = []
            custom_txt = []
            page_imgs = []
            nrOnPageCounter = 0
            for c, page in enumerate(doc):
                
                soup = BeautifulSoup(page, "xml")
                page_img = self.getImageFromUrl(docConfig[startPage+c-1]['url'])
                page_nr = docConfig[startPage + c-1]['pageNr']
                nrOnPageCounter = 0
                for region in soup.findAll("TextRegion"):
                    try:
                        if regionName in region['custom'] or regionName == "":
                            nrOnPageCounter = nrOnPageCounter + 1
                            trid_text = region['id']
                            region_name_text = region['custom'][region['custom'].find('structure {type:')+16:-2]
                            custom_text = region['custom']
                            region_text = []
                            last_line = ""
                            for line in region.findAll("TextLine"):
                                for t in line.findAll("Unicode"):
                                    last_line = t.text
                                region_text.append(last_line)
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
                            nrOnPage_txt.append(str(nrOnPageCounter))
                            page_imgs.append(page_img.crop((minX, minY, maxX,maxY)))
                            page_txt.append(region_text)
                            trid_txt.append(trid_text)
                            region_name_txt.append(region_name_text)
                            custom_txt.append(custom_text)
                            page_nr_txt.append(page_nr)
                    except:
                        pass
                #update progressbar
                progress['value'] = 100*((c + 1)/len(doc))
                progressText['text'] = "job progress {}%:".format(np.round(100*((c + 1)/len(doc)),1))
                self.window.update()

            return page_txt, nrOnPage_txt, region_name_txt, trid_txt, custom_txt, page_imgs, page_nr_txt
        except:
            tkinter.messagebox.showinfo('Fehler!','Ein Fehler is aufgetreten bei der Extraktion der Regionen! Vorgang wird abgebrochen...')

    def extractRegionsLinesTextandImage(self, colId, docId, textentryStartPage, textentryEndPage, toolName, regionName):
        try:
            #start a progressbar
            progress = Progressbar(self.window,orient=HORIZONTAL,length=100,mode='determinate')
            progress.grid(row=0,column=1, rowspan = 1, columnspan = 2, padx=(100, 10))

            #set title to progressbar
            progressText = Label(self.window, text="job progress 0%:",font=self.titleFont, bg='white')
            progressText.grid(row=0, column=1,sticky=W)
            progressText.config(bg="white")

            self.window.update()
            doc = self.extractTranscriptionRaw(colId, docId, textentryStartPage, textentryEndPage, toolName)

            if isinstance(textentryStartPage, int):
                startPage = textentryStartPage
            else:
                startPage = int(textentryStartPage.get())

            #define the endPages
            if textentryEndPage == '-' or textentryEndPage.get() == '-':
                endPage = len(doc)
            elif isinstance(textentryEndPage, int):
                endPage = textentryEndPage
            else:
                endPage = int(textentryEndPage.get())
            #get document

            #get the data that contains the images
            docConfig = self.getDocumentR(colId, docId)['pageList']['pages']

            full_text = []
            ids = []
            region_names = []
            customs = []
            nrOnPage = []
            page_Nrs = []
            imgs = []
            nrOnPageCounter = 0
            for c, page in enumerate(doc):
                soup = BeautifulSoup(page, "xml")
                page_txt = []
                region_name_txt = []
                nrOnPage_txt = []
                line_txt = []
                custom_txt = []
                page_imgs = []
                page_Nr_array = []
                page_img = self.getImageFromUrl(docConfig[startPage+c-1]['url'])
                page_Nr = docConfig[startPage + c-1]['pageNr']
                nrOnPageCounter = 0
                for region in soup.findAll("TextRegion"):
                    try:
                        if regionName in region['custom'] or regionName == "":
                            nrOnPageCounter = nrOnPageCounter + 1
                            region_name_text = region['custom'][region['custom'].find('structure {type:')+16:-2]
                            for line in region.findAll("TextLine"):
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
                                nrOnPage_txt.append(str(nrOnPageCounter))
                                page_imgs.append(page_img.crop((minX, minY, maxX,maxY)))
                                page_txt.append(region_text)
                                line_txt.append(lineid_text)
                                region_name_txt.append(region_name_text)
                                custom_txt.append(custom_text)
                                page_Nr_array.append(page_Nr)
                            #crop out the image
                    except:
                        pass
                full_text.append(page_txt)
                nrOnPage.append(nrOnPage_txt)
                ids.append(line_txt)
                region_names.append(region_name_txt)
                customs.append(custom_txt)
                imgs.append(page_imgs)
                page_Nrs.append(page_Nr_array)
                #update progressbar
                progress['value'] = 100*((c + 1)/len(doc))
                progressText['text'] = "job progress {}%:".format(np.round(100*((c + 1)/len(doc)),1))
                self.window.update()
            return full_text, nrOnPage, region_names, ids, customs, imgs, page_Nrs
        except:
            tkinter.messagebox.showinfo('Fehler!','Ein Fehler is aufgetreten bei')"""