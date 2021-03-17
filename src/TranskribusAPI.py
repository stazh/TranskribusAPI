from tkinter import *
from tkinter import _setit
from tkinter.ttk import Progressbar
import tkinter.font as font
import sys
import os
import xml.etree.ElementTree as et
import requests
import numpy as np
import time
import json
import pandas as pd
import xlwings as xw
from itertools import chain

import xlsxwriter
import shutil
from bs4 import BeautifulSoup
from PIL import Image
import urllib
from tkinter import filedialog

class TextSegmentation():
    """
        This class defines a program which enables the authentication on Transkribus and allows to execute 
        some functions in Transkribus in batch, f.e. line detection of individual text regions in order 
        to prevent lines crossing multiple text regions.
        
        The implementation makes usage of the TranskribusClient: https://github.com/Transkribus/TranskribusPyClient
    	and is developed by Luca Ferrazzini and Rebekka Plüs
    """
    
    def __init__(self):

        """
            This function initializes all important variables
        """
        #intitialize the window
        self.window = Tk()
        self.sessionId = None
        
        #define where to store and save credentials (They are also used for the TranskribusPyClient)
        self.credentialPath = '../lib/TranskribusPyClient/src/Transkribus_credential.py'
        self.ressourcePath = '../res/'

        #define fonts
        self.titleFont = font.Font(family='Helvetica', size=20, weight='bold')
        self.buttonFont = font.Font(family='Helvetica', size=16)
        self.inputFont = font.Font(family='Helvetica', size=12)
        
        #read in image
        self.titleImg = PhotoImage(file = self.ressourcePath + 'staatsarchiv_kt_zh.png')
        
        #define the credentials
        self.email = None
        self.password = None
        self.proxy = None
        
        #list of available models for sample ealuation
        self.modelList = []
        
        #start the program
        self.startup()

        return
    
    ###----------------------------------------start up section------------------------------------------------###
    
    def startup(self):
        """
            This function sets up the initial login window in order for the API
            to start a session with Transkribus and saves the corresponding necessary variables.
        """
        #init window
        if self.window == None:
            self.window = Tk()
        
        self.window.title('Login Transkribus')
        self.window.configure(bg='white')
        self.window.geometry('890x380')
        #select a title image
        img = Label(self.window, image = self.titleImg)
        img.grid(row=0, column=0,sticky=W)
        img.config(bg="white")

        #Set the instruction title
        titleText = Label(self.window, text="Bitte Logindaten eingeben:",font=self.titleFont, bg='white')
        titleText.grid(row=1, column=0,sticky=W)
        titleText.config(bg="white")

        #create the input fields
        Label(self.window, text='E-mail:', bg='white', font=self.inputFont).grid(row=2, column=0,sticky=W) 
        textentryEmail = Entry(self.window, bg='white', width=40, font = self.inputFont)
        textentryEmail.grid(row=3, column=0,sticky=W)
        
        Label(self.window, text='Passwort:', bg='white', font=self.inputFont).grid(row=2, column=1,sticky=W)
        textentryPassword = Entry(self.window, bg='white',width=40, font = self.inputFont)
        textentryPassword.config(show="*")
        textentryPassword.grid(row=3, column=1,sticky=W)
        
        Label(self.window, text='Proxy-Host:', bg='white', font=self.inputFont).grid(row=4, column=0,sticky=W)
        proxyHost = Entry(self.window, bg='white', width=40, font = self.inputFont)
        proxyHost.grid(row=5, column=0,sticky=W)
        proxyHost.insert(END, '')
        
        Label(self.window, text='Proxy-Port:', bg='white', font=self.inputFont).grid(row=4, column=1,sticky=W)
        proxyPort = Entry(self.window, bg='white',width=40, font = self.inputFont)
        proxyPort.grid(row=5, column=1,sticky=W)
        proxyPort.insert(END, '')
        
        #read last login
        email, password = self.getLastLogin()
        textentryEmail.insert(END, email)
        textentryPassword.insert(END, password)
        
        #create the button
        self.loginButton = Button(self.window,text='Login', font = self.buttonFont, height = 2, width = 20,
                                  command = lambda: self.login(textentryEmail, textentryPassword, proxyHost, proxyPort))
        
        self.window.grid_rowconfigure(6, minsize=25)

        self.loginButton.grid(row=7, rowspan = 2, columnspan = 2)

        self.window.mainloop()

        return
    
    ###----------------------------------------------Login functions-----------------------------------------------###
    
    def getLastLogin(self):
        """
            If there was a previous login it is saved into the credentials file and loaded on start.
        """
        file = open(self.credentialPath, "rt") 
        text = file.read()

        try:
            email = text.split('"')[1]
            password = text.split('"')[3]
        except:
            email = ""
            password = ""

        return email, password
    
    def saveLogin(self, email, password):
        """
            If desired this function saves the email and password in a file.
            NOTE: This is not save against reads from others.
        """
        file = open(self.credentialPath, "wt") 
        lines = ['# -*- coding: utf-8 -*-\n', 'login    = "{}"\n'.format(email),'password = "{}"'.format(password)]
        file.writelines(lines)
        file.close()
        return
    
    #start login process
    def login(self, textentryEmail, textentryPassword, proxyHost, proxyPort):
        """
            Establish a connection with the api and start a session.
        """
        self.email = textentryEmail.get()
        self.password = textentryPassword.get()
        self.proxyHost = proxyHost.get()
        self.proxyPort = proxyPort.get()
        
        if proxyHost.get() == '' or proxyPort.get() == '':
            self.proxy = {"https" : 'http://:@:',
                         "http" : 'http://:@:'}
        else:
            self.proxy = {"https" : 'http://' + self.email.split('@')[0] + ':' + self.password + '@' + proxyHost.get() + ':' + proxyPort.get() + '/',
                             "http" : 'http://' + self.email.split('@')[0] + ':' + self.password + '@' + proxyHost.get() + ':' + proxyPort.get() + '/'}
        

        if self.email == '' or self.password == '':
            self.popupmsg("Login war nicht erfolgreich! \n Bitte erneut versuchen.")
            return
        
        self.saveLogin(self.email, self.password)
        session = self.getLoginData()
        session = et.fromstring(session)
        self.userId = session.find("userId").text
        self.sessionId = session.find("sessionId").text
        #check if login was successfull
        if self.sessionId == None:
            popupmsg("Login war nicht erfolgreich! \n Bitte erneut versuchen.")
        else:
            self.startConfigurationWindow()
            
        return
    
    def getLoginData(self):
        if self.proxy["https"] == 'http://:@:':
            r = requests.post("https://transkribus.eu/TrpServer/rest/auth/login",
                              data ={"user":self.email, "pw":self.password})
        else:
            print("trying login with proxy")
            r = requests.post("https://transkribus.eu/TrpServer/rest/auth/login",
                              data ={"user":self.email, "pw":self.password}, proxies = self.proxy)

        if r.status_code == requests.codes.ok:
            return r.text
        else:
            self.popupmsg("Login war nicht erfolgreich! \n Bitte erneut versuchen.")
            return
        
    ###-------------------------------------------Line detection functions------------------------------------------###
        
    def startConfigurationWindow(self):

        """
            This window starts the line detection module and prepares all variables and functions which are necessary.
        """

        self.window.destroy()
        
        #start the configuration window
        self.window = Tk()
        self.window.title('Transkribus Linienerkennung')
        self.window.configure(bg='white')
        
        #create the default Header
        self.createDefaultHeader()
        self.window.geometry('890x400')
        #Set the instruction title
        titleText = Label(self.window, text="Bitte die Parameter für den Job definieren:",font=self.titleFont, bg='white')
        titleText.grid(row=2, column=0,sticky=W)
        titleText.config(bg="white")

        #create the input fields
        
        #collection id
        Label(self.window, text='Collection id:', bg='white', font=self.inputFont).grid(row=3, column=0,sticky=W)   
        textentryColId = Entry(self.window, bg='white', width=40, font = self.inputFont)
        textentryColId.grid(row=4, column=0,sticky=W)
        textentryColId.insert(END, '')


        #document id
        Label(self.window, text='Document id:', bg='white', font=self.inputFont).grid(row=3, column=1,sticky=W)
        textentryDocId = Entry(self.window, bg='white',width=40, font = self.inputFont)
        textentryDocId.grid(row=4, column=1,sticky=W)
        textentryDocId.insert(END, '')

        
        #starting page
        Label(self.window, text='Start Seite:', bg='white', font=self.inputFont).grid(row=5, column=0,sticky=W)
        textentryStartPage = Entry(self.window, bg='white',width=40, font = self.inputFont)
        textentryStartPage.grid(row=6, column=0,sticky=W)
        textentryStartPage.insert(END, '1')
        
        #ending page
        Label(self.window, text='End Seite:', bg='white', font=self.inputFont).grid(row=5, column=1,sticky=W)
        textentryEndPage = Entry(self.window, bg='white',width=40, font = self.inputFont)
        textentryEndPage.grid(row=6, column=1,sticky=W)
        textentryEndPage.insert(END, '-')
        
        #TexRegions
        Label(self.window, text='Textregionen (Komma separiert):', bg='white', font=self.inputFont).grid(row=7, column=0,sticky=W)
        textentryTextReg = Entry(self.window, bg='white',width=40, font = self.inputFont)
        textentryTextReg.grid(row=8, column=0,sticky=W)

        textentryTextReg.insert(END, 'page-number,paragraph,header')
        
        #create the button
        self.submitJobButton = Button(self.window,text='Starten', font = self.buttonFont, height = 2, width = 20,
                                      command = lambda: self.submitJobLineSeg(textentryColId, textentryDocId,
                                                                      textentryStartPage, textentryEndPage, textentryTextReg))
        self.window.grid_rowconfigure(9, minsize=25)

        self.submitJobButton.grid(row=10, rowspan = 2, columnspan = 2)

        self.window.mainloop()
        

        return
    
    def submitJobLineSeg(self, textentryColId, textentryDolId, textentryStartPage, textentryEndPage, textentryTextReg):
        """
            This function submits a job to transkribus for the line segmentation of the specified text regions.
        """
        colId = textentryColId.get()
        docId = textentryDolId.get()

        startPage = int(textentryStartPage.get())
        endPage = textentryEndPage.get() 
        regions_string = textentryTextReg.get()
        
        #get document defined by colid, docid and sessionid
        fullDoc = self.getDocumentR(colId, docId)
        
        if endPage == '-':
            endPage = fullDoc['md']['nrOfPages']
        else:
            endPage = int(endPage)
        pages = range(startPage, endPage + 1)
        
        #define all target regions
        target_regions = regions_string.replace(' ','').split(',')
        #self.popupmsg("Job wird ausgeführt!")
        
        #start progress bar
        progress = Progressbar(self.window,orient=HORIZONTAL,length=100,mode='determinate')
        progress.grid(row=0,column=1, rowspan = 1, columnspan = 2, padx=(100, 10))
        
        #set title to progressbar
        progressText = Label(self.window, text="job progress 0%:".format(len(target_regions)*len(pages)),font=self.titleFont, bg='white')
        progressText.grid(row=0, column=1,sticky=W)
        progressText.config(bg="white")

        self.window.update()
        try:
            for region_nr,target_region in enumerate(target_regions):

                while(self.checkRunningJobs(colId, docId)):
                    time.sleep(1)
                    self.window.update()
                    time.sleep(1)
                    self.window.update()
                    time.sleep(1)
                    self.window.update()
                    time.sleep(1)
                    self.window.update()

                if len(pages) < 5:
                    #we have to wait such that we do not overwrite our last job result with the new one
                    time.sleep(10)

                for page_nr, page in enumerate(pages):

                    progress['value'] = 100*(region_nr*len(pages) + page_nr + 1)/(len(target_regions)*len(pages))
                    progressText['text'] = "job progress {}%:".format(np.round(100*(region_nr*len(pages) + page_nr + 1)/(len(target_regions)*len(pages)),1))

                    self.window.update()

                    #specify the page and transcript id
                    pageId = fullDoc['pageList']['pages'][page - 1]['pageId']
                    tsId = fullDoc['pageList']['pages'][page - 1]['tsList']['transcripts'][0]['tsId']

                    #extract the url of the transcript
                    url = fullDoc['pageList']['pages'][page - 1]['tsList']['transcripts'][0]['url']

                    #get the xml of the transcript

                    if self.proxy["https"] != 'http://:@:':
                        xml = requests.get(url, proxies = self.proxy).text
                    else:
                        xml = requests.get(url).text

                    xml = et.fromstring(xml)

                    #initialize the region id string
                    region_ids = ''
                    self.window.update()
                    #run the line analyzer for every region
                    for c, region in enumerate(xml[1].findall('{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}TextRegion')):
                        if target_region in region.attrib['custom']:
                            if region_ids == '': region_ids += region.attrib['id']
                            else: region_ids += ',' + region.attrib['id']

                    self.window.update()

                    if not region_ids == '':
                        if self.proxy["https"] == 'http://:@:':
                            os.system('python ../lib/TranskribusPyClient/src/TranskribusCommands/do_analyzeLayout.py {} {}/{} --doLineSeg --region={}'
                                .format(colId, docId, page, region_ids))
                        else:
                            os.system('python ../lib/TranskribusPyClient/src/TranskribusCommands/do_analyzeLayout.py {} {}/{} --doLineSeg --region={} --https_proxy={}'
                                .format(colId, docId, page, region_ids, self.proxy["https"]))
            self.popupmsg("Alle Jobs sind in Auftrag")
        except:
            self.popupmsg("Ein Fehler bei den Jobs ist aufgetreten! Bitte erneut versuchen...")
        

            

            
    def checkRunningJobs(self, colId, docId):
        #retrieve the job list from transkribus
        if self.proxy["https"] == 'http://:@:':
            jobList = json.loads(requests.get("https://transkribus.eu/TrpServer/rest/jobs/list?JSESSIONID={}".format(self.sessionId)).text)
        else:
            jobList = json.loads(requests.get("https://transkribus.eu/TrpServer/rest/jobs/list?JSESSIONID={}".format(self.sessionId), proxies = self.proxy).text)

        for job in jobList:
            #check if there is a running job
            if int(job['colId']) == int(colId) and int(job['docId']) == int(docId):
                if not (job['state'] == "FINISHED" or job['state'] == "CANCELED" or job['state'] == "FAILED"):
                    return True
        return False
        
###--------------------------------------------search and replace functions--------------------------------------### 
    
    def startSearchAndReplaceWindow(self):

        
        self.window.destroy()
        
        #start the configuration window
        self.window = Tk()

        self.window.title('Transkribus suchen/ersetzen')

        self.window.configure(bg='white')
        
        #create the default Header
        self.createDefaultHeader()
        self.window.geometry('890x490')
        #Set the instruction title
        titleText = Label(self.window, text="Bitte die Parameter definieren:",font=self.titleFont, bg='white')
        titleText.grid(row=2, column=0,sticky=W)
        titleText.config(bg="white")

        #create the input fields
        #collection id
        Label(self.window, text='Collection id:', bg='white', font=self.inputFont).grid(row=3, column=0,sticky=W)   
        textentryColId = Entry(self.window, bg='white', width=40, font = self.inputFont)
        textentryColId.grid(row=4, column=0,sticky=W)
        textentryColId.insert(END, '')


        #document id
        Label(self.window, text='Document id:', bg='white', font=self.inputFont).grid(row=3, column=1,sticky=W)
        textentryDocId = Entry(self.window, bg='white',width=40, font = self.inputFont)
        textentryDocId.grid(row=4, column=1,sticky=W)
        
        #TR to be searched
        Label(self.window, text='Textregion suchen:', bg='white', font=self.inputFont).grid(row=5, column=0,sticky=W)
        textentryTrSearch = Entry(self.window, bg='white',width=40, font = self.inputFont)
        textentryTrSearch.grid(row=6, column=0,sticky=W)

        textentryTrSearch.insert(END, '')

        
        #TR to be replaced
        Label(self.window, text='Textregion ersetzen mit:', bg='white', font=self.inputFont).grid(row=5, column=1,sticky=W)
        textentryTrReplace = Entry(self.window, bg='white',width=40, font = self.inputFont)
        textentryTrReplace.grid(row=6, column=1,sticky=W)

        textentryTrReplace.insert(END, '')
        
         #create the button
        self.replaceTrButton = Button(self.window,text='TR ersetzen starten', font = self.buttonFont, height = 2, width = 20,
                                      command = lambda: self.searchReplacePagexml(textentryColId.get(), textentryDocId.get(), "structure {type:" + textentryTrSearch.get() + ";}","structure {type:" + textentryTrReplace.get() + ";}"))

        
        self.window.grid_rowconfigure(9, minsize=25)

        self.replaceTrButton.grid(row=10, rowspan = 2, columnspan = 2)

        
        #Text to be searched
        Label(self.window, text='Diese Funktion ist vorsichtig zu verwenden:', bg='white', font=self.inputFont).grid(row=12, column=0,sticky=W)
        Label(self.window, text='Text in pagexml suchen:', bg='white', font=self.inputFont).grid(row=13, column=0,sticky=W)
        textentrySearch = Entry(self.window, bg='white',width=40, font = self.inputFont)
        textentrySearch.grid(row=14, column=0,sticky=W)
        textentrySearch.insert(END, '')
        
        #Text to be replaced
        Label(self.window, text='Text in pagexml ersetzen mit:', bg='white', font=self.inputFont).grid(row=13, column=1,sticky=W)
        textentryReplace = Entry(self.window, bg='white',width=40, font = self.inputFont)
        textentryReplace.grid(row=14, column=1,sticky=W)
        textentryReplace.insert(END, '')
        
         #create the button
        self.searchReplaceButton = Button(self.window,text='Text ersetzen starten', font = self.buttonFont, height = 2, width = 20,
                                      command = lambda: self.searchReplacePagexml(textentryColId.get(), textentryDocId.get(), textentrySearch.get(), textentryReplace.get()))
        self.searchReplaceButton.place(x=330,y=430)
        #self.window.grid_rowconfigure(12, minsize=25)

        #self.searchReplaceButton.grid(row=25, rowspan = 2, columnspan = 2)

        self.window.mainloop()
    
    def searchReplacePagexml(self, colid, docid, sString, rString):
        doc = self.getDocumentR(colid, docid)['pageList']['pages']
        startPage = 1
        endPage = len(doc)
        #start progress bar

        progress = Progressbar(self.window,orient=HORIZONTAL,length=100,mode='determinate')
        progress.grid(row=0,column=1, rowspan = 1, columnspan = 2, padx=(100, 10))
        
        #set title to progressbar
        progressText = Label(self.window, text="job progress 0%:".format(startPage * endPage),font=self.titleFont, bg='white')
        progressText.grid(row=0, column=1,sticky=W)
        progressText.config(bg="white")
        self.window.update()
        for x in range(startPage,endPage):

            self.searchReplaceInPage(colid,docid,x, sString, rString)

            print("page " + str(x) + " done.")
            progress['value'] = 100*x/endPage
            progressText['text'] = "job progress {}%:".format(np.round(100*x/endPage,1))
            self.window.update()
        progress['value'] = 100*endPage/endPage
        progressText['text'] = "job progress {}%:".format(np.round(100*endPage/endPage,1))

        self.window.update()
        print("Doc with id " + docid + " done.")
    
    def searchReplaceInPage(self, colid, docid, pageNo, sString, rString):
        xml = self.getPage(colid,docid,pageNo)
        xml = xml.replace(sString,rString)
        self.postPage(colid, docid, pageNo, xml)
        return True
    
    ###--------------------------------------------Sampling functions--------------------------------------###        
    
    def startSamplesWindow(self):

        """
            This function prepares the tab which lets us submit transcription jobs for certain trained models and
            evaluate those models.
        """

        self.window.destroy()
        
        #start the configuration window
        self.window = Tk()
        self.window.title('Transkribus Sampling')
        self.window.configure(bg='white')

        #create the default Header
        self.createDefaultHeader() 
        self.window.geometry('890x410')
        #Set the instruction title
        titleText = Label(self.window, text="Bitte die Parameter für das Sampling definieren:",font=self.titleFont, bg='white')
        titleText.grid(row=2, column=0,sticky=W)
        titleText.config(bg="white")

        #create the input fields
        #collection id
        Label(self.window, text='Collection id:', bg='white', font=self.inputFont).grid(row=3, column=0,sticky=W)   
        textentryColId = Entry(self.window, bg='white', width=40, font = self.inputFont)
        textentryColId.grid(row=4, column=0,sticky=W)
        textentryColId.insert(END, '')

        #document id
        Label(self.window, text='Document id:', bg='white', font=self.inputFont).grid(row=3, column=1,sticky=W)
        textentryDocId = Entry(self.window, bg='white',width=40, font = self.inputFont)
        textentryDocId.grid(row=4, column=1,sticky=W)
        textentryDocId.insert(END, '')
        #starting page
        """Label(self.window, text='Start Seite:', bg='white', font=self.inputFont).grid(row=5, column=0,sticky=W)
        textentryStartPage = Entry(self.window, bg='white',width=40, font = self.inputFont)
        textentryStartPage.grid(row=6, column=0,sticky=W)
        textentryStartPage.insert(END, '0')
        
        #ending page
        Label(self.window, text='End Seite:', bg='white', font=self.inputFont).grid(row=5, column=1,sticky=W)
        textentryEndPage = Entry(self.window, bg='white',width=40, font = self.inputFont)
        textentryEndPage.grid(row=6, column=1,sticky=W)
        textentryEndPage.insert(END, '-')"""
                
        #Models      
        Label(self.window, text='Modelle:', bg='white', font=self.inputFont).grid(row=7, column=0,sticky=W)
        
        self.modelList = ["GT"]
        
        self.selectedModel = StringVar(value="Wählen Sie ein Modell")  
        self.optionModels = OptionMenu(self.window, self.selectedModel, *self.modelList)
        self.optionModels.grid(row=8, rowspan = 1, column=0,sticky=W)
        
        #Model load button
        self.loadModels = Button(self.window, text='Modelle abrufen', font = self.buttonFont, height = 1, width = 20,
                                      command = lambda: self.loadModelNames(textentryColId))
        self.loadModels.grid(row=8, column = 1)
        
        #Target directory
        Label(self.window, text='Zielordner:', bg='white', font=self.inputFont).grid(row=9, column=0,sticky=W)
        
        self.TARGET_DIR = StringVar(value = '')
        targetDisplay = Label(self.window, textvariable=self.TARGET_DIR, width=50)
        targetDisplay.grid(row=10, column=0, sticky=W)

        browseButton = Button(text="Browse", command=lambda: self.browse_button(self.TARGET_DIR))
        browseButton.grid(row=10, column=0, sticky=E)

        #create the button
        self.submitJobButton = Button(self.window,text='Starten', font = self.buttonFont, height = 2, width = 20,
                                      command = lambda: self.evaluateSelectedModels(textentryColId, textentryDocId, 0, "-"))
        self.window.grid_rowconfigure(11, minsize=25)


        self.submitJobButton.grid(row=12, rowspan = 2, columnspan = 2)

        self.window.mainloop()
        return
    
    def getModelsList(self, colId):
        """
            This function returns a list of all available models in transkribus
        """
        if self.proxy["https"] == 'http://:@:':
            r = requests.get('https://transkribus.eu/TrpServer/rest/recognition/{}/list?JSESSIONID={}'.format(colId, self.sessionId))
        else:
            r = requests.get('https://transkribus.eu/TrpServer/rest/recognition/{}/list?JSESSIONID={}'.format(colId, self.sessionId), proxies = self.proxy)
        self.modelsRaw = r.text
        modelsId = r.text.split('htrId>')[1::2]
        models = r.text.split('name>')[1::2]

        modelsProvider = r.text.split('provider>')[1::2]
        for i in range(len(models)):
            models[i] = models[i].replace('</', '')
            modelsId[i] = modelsId[i].replace('</', '')
            modelsProvider[i] = modelsId[i].replace('</', '')
        modelsIdMap = dict(zip(models,modelsId))
        modelsProviderMap = dict(zip(models, modelsProvider))
        models.sort()
        return models, modelsIdMap, modelsProviderMap
    
    def loadModelNames(self, textentryColId):
        """
            This function loads the names of all available models into the option menu.
        """
        try:
            colId = textentryColId.get()

            self.modelList, self.modelsIdMap, self.modelProvMap = self.getModelsList(colId)
            self.modelList = list(set(self.modelList))
            self.optionModels['menu'].delete(0, 'end')

            # Insert list of new options (tk._setit hooks them up to var)
            for model in self.modelList:
                self.optionModels['menu'].add_command(label=model, command=_setit(self.selectedModel, model))
        except:
            self.popupmsg("Ein Fehler beim laden der Modellnamen ist aufgetreten!")
    
    def evaluateSelectedModels(self,textentryColId, textentryDocId, textentryStartPage, textentryEndPage):
        """
            This function starts the evaluation process by using the selected model for transcription,
            if no transcription is available. Note: If textentryDocId is == "" then the process is applied to all
            documents inside the defined collection.
        """
        
        if textentryDocId.get() == "":
            #start progress bar
            progress = Progressbar(self.window,orient=HORIZONTAL,length=100,mode='determinate')
            progress.grid(row=0,column=1, rowspan = 1, columnspan = 2, padx=(100, 10))

            #set title to progressbar
            progressText = Label(self.window, text="job progress 0%:",font=self.titleFont, bg='white')
            progressText.grid(row=0, column=1,sticky=W)
            progressText.config(bg="white")
            self.window.update()
            docIds = self.getDocIdsList(self.sessionId, textentryColId.get())

            for c, docId in enumerate(docIds):
                self.evaluateModels(textentryColId, docId, textentryStartPage, textentryEndPage)
                progress['value'] = 100*(c/len(docIds))
                progressText['text'] = "job progress {}%:".format(np.round(100*(c/len(docIds))))
                self.window.update()
        else:
            self.evaluateModels(textentryColId, textentryDocId, textentryStartPage, textentryEndPage)
        
        return
    
    def evaluateModels(self, textentryColId, textentryDocId, textentryStartPage, textentryEndPage):
        """
            This function evaluates a specific model on a specified document. 
            Defined through self.selectedModel.get() resp. textentryDocId.
        """
        if isinstance(textentryDocId, int):
            currentDocId = textentryDocId
        else:
            currentDocId = textentryDocId.get()
        if isinstance(textentryColId, int):
            currentColId = textentryColId
        else:
            currentColId = textentryColId.get()
            
        #get the keys of the transcriptions of the Ground Truth
        keys_GT = self.getDocTranscriptKeys(textentryColId.get(), currentDocId, textentryStartPage, textentryEndPage, 'GT')
        #get the keys of the transcriptions of the selected model
        keys = self.getDocTranscriptKeys(textentryColId.get(), currentDocId, textentryStartPage, textentryEndPage, self.selectedModel.get())
        transcripts_GT = self.getDocTranscript(textentryColId.get(), currentDocId, textentryStartPage, textentryEndPage, 'GT')
        transcripts_M = self.getDocTranscript(textentryColId.get(), currentDocId, textentryStartPage, textentryEndPage, self.selectedModel.get())
        charAmount_List = []
        try:
            if len(transcripts_GT) == len(transcripts_M):
                for i in range(len(transcripts_GT)):
                    amount = (len(transcripts_GT[i]) + len(transcripts_M[i]))/2
                    charAmount_List.append(len(transcripts_GT[i]))
            wer_list = []
            cer_list = []
            if not os.path.exists(self.TARGET_DIR.get() + '/Images_best_cer_' + self.selectedModel.get() + '/'):
                os.makedirs(self.TARGET_DIR.get() + '/Images_best_cer_' + self.selectedModel.get() + '/')
            if not os.path.exists(self.TARGET_DIR.get() + '/Images_worst_cer_' + self.selectedModel.get() + '/'):
                os.makedirs(self.TARGET_DIR.get() + '/Images_worst_cer_' + self.selectedModel.get() + '/')
        #calculate wer and cer for every transcription a model produced
            if not (keys == None or keys_GT == None):
                for k in range(len(keys)):
                    wer, cer = self.getErrorRate(keys[k], keys_GT[k])
                    wer_list.append(wer)
                    cer_list.append(cer)
                cer_list_gew = []
                wer_list_gew = []
                for j in range(len(cer_list)):
                    cer_list_gew.append(cer_list[j]*charAmount_List[j]/np.sum(charAmount_List))
                    wer_list_gew.append(wer_list[j]*charAmount_List[j]/np.sum(charAmount_List))
                pages = self.extractTranscriptionRaw(currentColId, currentDocId, textentryStartPage, textentryEndPage, self.selectedModel.get())
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
            #save best and worst cer as image and variable
                image_worst_temp = self.getImageFromUrl(self.getDocumentR(currentColId, currentDocId)['pageList']['pages'][cer_worst[1]]['url'])
                image_best_temp = self.getImageFromUrl(self.getDocumentR(currentColId, currentDocId)['pageList']['pages'][cer_best[1]]['url'])
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
                best_url = self.TARGET_DIR.get() + '/Images_best_cer_' + self.selectedModel.get() + '/'+ str(currentDocId) +'_CER_' + str(best_cer) + '_Page_'+str(cer_best[1]+1) +'.jpg'
                worst_url = self.TARGET_DIR.get() + '/Images_worst_cer_' + self.selectedModel.get() + '/'+ str(currentDocId) +'_CER_' + str(worst_cer) + '_Page_'+str(cer_worst[1]+1) +'.jpg'
                image_best.save(best_url)
                image_worst.save(worst_url)

            #check if excel file already exists
                if not os.path.exists(self.TARGET_DIR.get() + '/ModelEvaluation.xlsx'):
                #create the excel file
                    pd.DataFrame().to_excel(self.TARGET_DIR.get() + '/ModelEvaluation.xlsx')
                #wb = xlsxwriter.Workbook(self.TARGET_DIR.get() + '/ModelEvaluation.xlsx')
                #open the created excel file
                #sht1 = wb.add_worksheet()
                    wb = xw.Book(self.TARGET_DIR.get() + '/ModelEvaluation.xlsx')
                    sht1 = wb.sheets['Sheet1'] 
                #init the column names
                    columns = ['doc.ID Sample']
                    columns.extend(chain(*[['CER{}'.format(i), 'WER{}'.format(i), 'Model{}'.format(i), 'Best_CER{}'.format(i), 'Best_CER_Imag{}'.format(i), 'Worst_CER{}'.format(i), 'Worst_CER_Imag{}'.format(i)] for i in range(1,10)]))

                    sht1.range('A1').value = columns
                    sht1.range('A2').value = currentDocId
                    sht1.range('B2').value = np.sum(cer_list_gew)
                    sht1.range('C2').value = np.sum(wer_list_gew)
                    sht1.range('D2').value = self.selectedModel.get()
                    sht1.range('E2').value = best_cer
                    sht1.range('G2').value = worst_cer
                    sht1.range('F2').value = '=HYPERLINK("' + best_url + '")'
                    sht1.range('H2').value = '=HYPERLINK("' + worst_url + '")'

                else:
                #open the excel sheet if the file already exists
                    wb = xw.Book(self.TARGET_DIR.get() + '/ModelEvaluation.xlsx')
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
                        sht1.range('A{}'.format(currentRow)).value = currentDocId
                        sht1.range('B{}'.format(currentRow)).value = np.sum(cer_list_gew)
                        sht1.range('C{}'.format(currentRow)).value = np.sum(wer_list_gew)
                        sht1.range('D{}'.format(currentRow)).value = self.selectedModel.get()
                        sht1.range('E{}'.format(currentRow)).value = best_cer
                        sht1.range('F{}'.format(currentRow)).value = '=HYPERLINK("' + best_url + '")'
                        sht1.range('G{}'.format(currentRow)).value = worst_cer
                        sht1.range('H{}'.format(currentRow)).value = '=HYPERLINK("' + worst_url + '")'
                    else:
                        values = sht1.range('A{}'.format(currentRow), 'ZZ{}'.format(currentRow)).value
                        values[currentColumn:currentColumn + 6] = [np.sum(cer_list_gew), np.sum(wer_list_gew), self.selectedModel.get(), best_cer, '=HYPERLINK("' + best_url + '")', worst_cer, '=HYPERLINK("' + worst_url + '")']
                        sht1.range('A{}'.format(currentRow), 'ZZ{}'.format(currentRow)).value = values
            else:
                self.popupmsg("Transkriptionen wurden nicht gefunden! Vorgang für Modell {} und Doc {} wird abgebrochen...".format(self.selectedModel.get(), currentDocId))
            wb.save(self.TARGET_DIR.get() + '/ModelEvaluation.xlsx')
        except:
            self.popupmsg("Fehler bei  Modell {} und Doc {} aufgetreten. Vorgang wird abgebrochen.".format(self.selectedModel.get(), currentDocId))
        wb.save(self.TARGET_DIR.get() + '/ModelEvaluation.xlsx')
        return
    
    
    def getErrorRate(self, key, key_ref):
        """
            This gets the wer and cer for a specific model on a specified document
        """
        if self.proxy["https"] == 'http://:@:':
            r = requests.get('https://transkribus.eu/TrpServer/rest/recognition/errorRate?JSESSIONID={}&key={}&ref={}'
                     .format(self.sessionId, key, key_ref))
        else:
            r = requests.get('https://transkribus.eu/TrpServer/rest/recognition/errorRate?JSESSIONID={}&key={}&ref={}'
                     .format(self.sessionId, key, key_ref), proxies = self.proxy)
        #extract wer and cer from the content
        wer = float(et.fromstring(r.content)[0].text)
        cer = float(et.fromstring(r.content)[1].text)
        return wer, cer
    
    def doTranscription(self,toolName, colId, docId):
        """
            This function submits the job such that the model is appied to a certain document.
            Note that a distinction has to be made between PyLaia models and other models.
        """
        if self.modelProvMap[toolName] == 'PyLaia':
            if self.proxy["https"] == 'http://:@:':
                os.system('python ../lib/TranskribusPyClient/src/TranskribusCommands/do_htrRnn.py {} None {} --docid {} --pylaia'.format(self.modelsIdMap[toolName], colId, docId))
            else:
                os.system('python ../lib/TranskribusPyClient/src/TranskribusCommands/do_htrRnn.py {} None {} --docid {} --pylaia --https_proxy={}'.format(self.modelsIdMap[toolName], colId, docId, self.proxy["https"]))
        else:
            if self.proxy["https"] == 'http://:@:':
                os.system('python ../lib/TranskribusPyClient/src/TranskribusCommands/do_htrRnn.py {} None {} --docid {}'.format(self.modelsIdMap[toolName], colId, docId))
            else:
                os.system('python ../lib/TranskribusPyClient/src/TranskribusCommands/do_htrRnn.py {} None {} --docid {} --https_proxy={}'.format(self.modelsIdMap[toolName], colId, docId, self.proxy["https"]))

                  
        return
    
    def getDocTranscript(self, colId, docId, textentryStartPage, textentryEndPage, toolName):
        """
            This function returns the transcription of a certain document.
        """
        pxList = self.extractTranscriptionRaw(colId, docId, textentryStartPage, textentryEndPage, toolName)
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
    
    def getDocTranscriptKeys(self, colId, docId, textentryStartPage, textentryEndPage, toolName):
        """
            Get the keys for the transcriptions of a certain document. Those are needed in order to extract the wer and cer.
        """
        #get document
        doc = self.getDocumentR(colId, docId)['pageList']['pages']
        
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
                        if ts['toolName'][-len(toolName):] == toolName:
                            keys.append(ts['key'])
                            break
                    except:
                        pass
        if len(keys) == len(pages):
            return keys
        elif toolName == "GT":
            self.popupmsg("Fehler! Nicht für alle Pages in Sample mit Docid " + str(docId) + " GT vorhanden.")
            return None
        else:
            #self.popupmsg("HTR müssen noch ausgeführt werden. Dies kann einige Zeit dauern...")
            print("HTR für " + str(docId) + " gestartet.")
            self.doTranscription(toolName, colId, docId)
            time.sleep(5)
            while(self.checkRunningJobs(colId, docId)):
                time.sleep(1)
                self.window.update()
                time.sleep(1)
                self.window.update()
                time.sleep(1)
                self.window.update()
                time.sleep(1)
                self.window.update()
            keys = self.getDocTranscriptKeys(colId, docId, textentryStartPage, textentryEndPage, toolName)
            return keys
            
        return keys

###--------------------------------------------TR export functions--------------------------------------### 
    
    def startExportTrWindow(self):
        
        self.window.destroy()
        #start the configuration window
        self.window = Tk()
        self.window.title('Transkribus Export TR-Text')
        self.window.configure(bg='white')
        
        #create the default Header
        self.createDefaultHeader()
        self.window.geometry('890x400')
        
        #Set the instruction title
        titleText = Label(self.window, text="Bitte die Parameter definieren:",font=self.titleFont, bg='white')
        titleText.grid(row=2, column=0,sticky=W)
        titleText.config(bg="white")   
        
        #collection id
        Label(self.window, text='Collection id:', bg='white', font=self.inputFont).grid(row=3, column=0,sticky=W)   
        textentryColId = Entry(self.window, bg='white', width=40, font = self.inputFont)
        textentryColId.grid(row=4, column=0,sticky=W)
        textentryColId.insert(END, '')

        #document id
        Label(self.window, text='Document id:', bg='white', font=self.inputFont).grid(row=3, column=1,sticky=W)
        textentryDocId = Entry(self.window, bg='white',width=40, font = self.inputFont)
        textentryDocId.grid(row=4, column=1,sticky=W)
        
        #TR to be searched
        Label(self.window, text='zu exportierende Textregion:', bg='white', font=self.inputFont).grid(row=5, column=0,sticky=W)
        textentryExportTR = Entry(self.window, bg='white',width=40, font = self.inputFont)
        textentryExportTR.grid(row=6, column=0,sticky=W)
        textentryExportTR.insert(END, 'header')
        
        #Target directory
        Label(self.window, text='Zielordner:', bg='white', font=self.inputFont).grid(row=7, column=0,sticky=W)
        
        self.TARGET_DIR = StringVar(value = '')
        targetDisplay = Label(self.window, textvariable=self.TARGET_DIR, width=50)
        targetDisplay.grid(row=8, column=0, sticky=W)

        browseButton = Button(text="Browse", command=lambda: self.browse_button(self.TARGET_DIR))
        browseButton.grid(row=8, column=0, sticky=E)
        
        #create the button
        self.replaceTrButton = Button(self.window,text='Starten', font = self.buttonFont, height = 2, width = 20,
                                      command = lambda: self.startExtraction(textentryColId.get(), textentryDocId.get()
                                                                             , textentryExportTR.get()))
        
        self.window.grid_rowconfigure(9, minsize=25)

        self.replaceTrButton.grid(row=10, rowspan = 2, columnspan = 2) 

    def startExtraction(self, colId, docId, regionName):
        
        if self.TARGET_DIR.get() == "":
            self.popupmsg("Bitte wählen sie einen Zielpfad aus!")
            return
        
        docName = self.getDocNameFromId(colId, docId)
        text, lineids, customs, imgs = self.extractRegionsTextandImage(colId, docId, 0, '-', 'LAST', regionName)
        
        #write results in excel
        if os.path.exists(self.TARGET_DIR.get() + '/RegionExtraction.xlsx'):
            os.remove(self.TARGET_DIR.get() + '/RegionExtraction.xlsx')
            
        wb = xlsxwriter.Workbook(self.TARGET_DIR.get() + '/RegionExtraction.xlsx')
        sht1 = wb.add_worksheet()
        
        #init the column names
        columns = ['Dokument Id', 'Dokument Name', 'SeitenNr', 'Nummer auf Seite', 'Text', 'LineIds','Customs','Bild']
        
        #write the first entry together with the columns header
        for i, col in enumerate(columns):
            sht1.write(0, i, col)
        
        row = 1
        
        #set Image and Text column width
        sht1.set_column(5, 5, 80)
        sht1.set_column(4, 4, 60)
        
        #this format is needed, such that we can write on multiple lines
        wrap = wb.add_format({'text_wrap': True})
        
        #folder for temp imgs:
        if not os.path.exists('tempImgs/'):
            os.makedirs("tempImgs")

        #write the results into the excel file
        for page in range(len(text)):             
            for c in range(len(text[page])):
                sht1.set_row(row, 150)
                sht1.write(row, 0 , str(docId))
                sht1.write(row, 1, str(docName))
                sht1.write(row, 2, str(page + 1))
                sht1.write(row, 3, str(c + 1))
                sht1.write(row, 4, '\n'.join(text[page][c]), wrap)
                sht1.write(row, 5, '\n'.join(lineids[page][c]), wrap)
                sht1.write(row, 6, '\n'.join(customs[page][c]), wrap)
                #sht1.write(row, 6, xmls[page][c])
                imgs[page][c].save('tempImgs/tempImg{}_{}.jpg'.format(page, c))

                # Maybe we could add a scale variable to change the scale of the images in the excel file (Keep x_scale and y_scale equal to get the same ratio)
                sht1.insert_image(row, 7,'tempImgs/tempImg{}_{}.jpg'.format(page, c),{'x_scale': 0.3, 'y_scale': 0.3})
                row += 1
        wb.close()
        #delete the temporary folder for the images
        shutil.rmtree('tempImgs')
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

            #get document
            doc = self.extractTranscriptionRaw(colId, docId, textentryStartPage, textentryEndPage, toolName)

            #get the data that contains the images
            docConfig = self.getDocumentR(colId, docId)['pageList']['pages']

            full_text = []
            lineIds = []
            customs = []
            imgs = []

            for c, page in enumerate(doc):
                soup = BeautifulSoup(page, "xml")
                page_txt = []
                line_txt = []
                custom_txt = []
                page_imgs = []
                page_img = self.getImageFromUrl(docConfig[c]['url'])
                for region in soup.findAll("TextRegion"):
                    try:
                        if regionName in region['custom']:
                            region_text = []
                            lineid_text = []
                            custom_text = []
                            for line in region.findAll("TextLine"):
                                lineid_text.append(line['id'])
                                custom_text.append(line['custom'])
                                for t in line.findAll("Unicode"):
                                    region_text.append(t.text)
                            page_txt.append(region_text)
                            line_txt.append(lineid_text)
                            custom_txt.append(custom_text)
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

                            page_imgs.append(page_img.crop((minX, minY, maxX,maxY)))
                    except:
                        pass
                full_text.append(page_txt)
                lineIds.append(line_txt)
                customs.append(custom_txt)
                imgs.append(page_imgs)

                #update progressbar
                progress['value'] = 100*((c + 1)/len(doc))
                progressText['text'] = "job progress {}%:".format(np.round(100*((c + 1)/len(doc)),1))
                self.window.update()
            return full_text, lineIds, customs, imgs
        except:
            self.popupmsg("Ein Fehler is aufgetreten bei der Extraktion der Regionen! Vorgang wird abgebrochen...")
###--------------------------------------------TR import functions--------------------------------------### 
    
    """def startImportTrWindow(self):
        
        self.window.destroy()
        
        #start the configuration window
        self.window = Tk()
        self.window.title('Transkribus Textregionen suchen/ersetzen')
        self.window.configure(bg='white')
        
        #create the default Header
        self.createDefaultHeader()
        
        #Set the instruction title
        titleText = Label(self.window, text="Bitte die Parameter definieren:",font=self.titleFont, bg='white')
        titleText.grid(row=2, column=0,sticky=W)
        titleText.config(bg="white")"""
    
    
###------------------------------------------------general funcitons----------------------------------------------###
    

    def getImageFromUrl(self, url):
        if self.proxy["https"] == 'http://:@:':
            r = requests.get(url, stream=True)
        else:
            r = requests.get(url, stream=True, proxies = self.proxy)
        img = Image.open(r.raw)
        return img
    
    def extractTranscriptionRaw(self, colId, docId, textentryStartPage, textentryEndPage, toolName):
        #get document
        doc = self.getDocumentR(colId, docId)['pageList']['pages']

        #setup the startpage
        if isinstance(textentryStartPage, int):
            startPage = textentryStartPage
        else:
            startPage = int(textentryStartPage.get())
        
        #define the endPages
        if textentryEndPage == "-" or textentryEndPage.get() == '-':
            endPage = len(doc)
        elif isinstance(textentryEndPage, int):
            endPage = int(endPage)
        else:
            endPage = int(textentryEndPage.get())
        
        #define the endPages
        if endPage == "-":
            endPage = len(doc)
        else:
            endPage = int(endPage)
        
        #define the pages
        pages = range(startPage, endPage)
        
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
                            if ts['toolName'][-len(toolName):] == toolName:
                                url = ts['url']
                                break
                        except:
                            pass
            try:
                if self.proxy["https"] == 'http://:@:':
                    req = requests.get(url)
                else:
                    req = requests.get(url, proxies = self.proxy)
                page_text.append(req.text)
                
            except:

                #self.popupmsg("Keine Transkription für {} auf Seite {} vorhanden! Vorgang wird abgebrochen...".format(toolName, page))
                return

        return page_text
    

    def checkRunningJobs(self, colId, docId):
        """
            This function checks, if a job for a specific document in a collection is running.
            It returns False if there is no Job and True if there is a job running.
        """
        #retrieve the job list from transkribus
        if self.proxy["https"] == 'http://:@:':
            jobList = json.loads(requests.get("https://transkribus.eu/TrpServer/rest/jobs/list?JSESSIONID={}".format(self.sessionId)).text)
        else:
            jobList = json.loads(requests.get("https://transkribus.eu/TrpServer/rest/jobs/list?JSESSIONID={}".format(self.sessionId), proxies = self.proxy).text)
        for job in jobList:
            #check if there is a running job
            if int(job['colId']) == int(colId) and int(job['docId']) == int(docId):
                if not (job['state'] == "FINISHED" or job['state'] == "CANCELED" or job['state'] == "FAILED"):
                    return True
        return False
    
    def createDefaultHeader(self):
        """
            This function sets up all the buttons that are present in all tabs.
        """
        #set the title image
        self.titleImg = PhotoImage(file = self.ressourcePath + 'staatsarchiv_kt_zh.png')
        img = Label(self.window, image = self.titleImg)
        img.grid(row=0, column=0,sticky=W)
        img.config(bg="white")
        
        #Set the button for configuration window selection
        self.lineSegButton = Button(self.window,text='Linienerkennung', font = self.buttonFont, height = 1, width = 40,
                                      command = self.startConfigurationWindow)
        #self.lineSegButton.grid(row=1,column = 0, rowspan = 1, columnspan = 1, sticky = W+E)
        self.lineSegButton.place(x=110, y=130, width=185, height=20)
        #Set the button for renaming textregions

        self.replaceTrButton = Button(self.window,text='Suchen/Ersetzen', font = self.buttonFont, height = 1, width = 40,
                                      command = self.startSearchAndReplaceWindow)

        #self.replaceTrButton.grid(row=1,column = 1, rowspan = 1, columnspan = 1, sticky = W+E)
        self.replaceTrButton.place(x=305, y=130, width=185, height=20)
        
        #Set the button for Sampling
        self.modelEvalButton = Button(self.window,text='Sampling', font = self.buttonFont, height = 1, width = 40,
                                      command = self.startSamplesWindow)
        #self.modelEvalButton.grid(row=1, column = 2, rowspan = 1, columnspan = 1, sticky = W+E)
        self.modelEvalButton.place(x=500, y=130, width=185, height=20)
        
        #Set the button for Textregion Export
        self.TrExportButton = Button(self.window,text='Export TR-Text', font = self.buttonFont, height = 1, width = 40,
                                      command = self.startExportTrWindow)
        self.TrExportButton.place(x=695, y=130, width=185, height=20)
        
        #Set the button for Textregion Import
        """self.TrImportButton = Button(self.window,text='Import TR-Text', font = self.buttonFont, height = 1, width = 40,
                                      command = self.startImportTrWindow)
        self.TrImportButton.place(x=730, y=130, width=120, height=20)"""
        
    def getDocumentR(self, colid, docid):

        if self.proxy["https"] == 'http://:@:':
            r = requests.get("https://transkribus.eu/TrpServer/rest/collections/{}/{}/fulldoc?JSESSIONID={}".format(colid, docid, self.sessionId))
        else:
            r = requests.get("https://transkribus.eu/TrpServer/rest/collections/{}/{}/fulldoc?JSESSIONID={}".format(colid, docid, self.sessionId), proxies = self.proxy)

        if r.status_code == requests.codes.ok:
            return r.json()
        else:
            print(r)
            self.popupmsg("Fehler bei der  Abfrage eines Dokumentes. Doc-ID " + str(docid) + " invalid?")
            return None
    
    def getDocuments(self, sid, colid):
        if self.proxy["https"] == 'http://:@:':
            r = requests.get("https://transkribus.eu/TrpServer/rest/collections/{}/list?JSESSIONID={}".format(colid, sid))
        else:
            r = requests.get("https://transkribus.eu/TrpServer/rest/collections/{}/list?JSESSIONID={}".format(colid, sid), proxies = self.proxy)
        if r.status_code == requests.codes.ok:
            return r.json()
        else:
            print(r)
            self.popupmsg("Fehler bei der Abfrage der Dokumentliste. Col-ID " + str(colid) + " invalid?")
            return None

    def getDocNameFromId(self, colId, docId):
        doc = self.getDocumentR(colId, docId)
        return doc['md']['title']

    def getDocIdsList(self, sid, colid):
        docs = self.getDocuments(sid, colid)
        docIds = []
        for d in docs:
            docIds.append(d['docId'])
        return docIds

    def getPage(self, colid, docid, pageNo):
        if self.proxy["https"] == 'http://:@:':
            r = requests.get("https://transkribus.eu/TrpServer/rest/collections/{}/{}/{}/text?JSESSIONID={}".format(colid, docid, pageNo, self.sessionId))
        else:
            r = requests.get("https://transkribus.eu/TrpServer/rest/collections/{}/{}/{}/text?JSESSIONID={}".format(colid, docid, pageNo, self.sessionId), proxies = self.proxy)
        if r.status_code == requests.codes.ok:
            return r.text
        else:
            print(r)
            self.popupmsg("Fehler bei der Abfrage einer Seite. Doc-ID " + str(docid) + " invalid oder Seitenzahl " + str(pageNo) + " ausserhalb des Bereichs?")
            return None

    def postPage(self, colid, docid, pageNo, xml):
        if self.proxy["https"] == 'http://:@:':
            r = requests.post("https://transkribus.eu/TrpServer/rest/collections/{}/{}/{}/text?JSESSIONID={}".format(colid, docid, pageNo, self.sessionId), data=xml.encode("utf8"), params={ "note":"DC" })
        else:
            r = requests.post("https://transkribus.eu/TrpServer/rest/collections/{}/{}/{}/text?JSESSIONID={}".format(colid, docid, pageNo, self.sessionId), data=xml.encode("utf8"), params={ "note":"DC" }, proxies = self.proxy)
        if r.status_code == requests.codes.ok:
            return True
        else:
            print(r)
            self.popupmsg("Fehler beim posten einer Seite. Doc-ID " + str(docid) + " invalid oder Seitenzahl " + str(pageNo) + " ausserhalb des Bereichs?")
            return False

    def browse_button(self, variable):
        # Allow user to select a directory and store it in global var
        # called folder_path
        filename = filedialog.askdirectory()
        variable.set(filename)

    def popupmsg(self, msg):
        popup = Tk()
        popup.wm_title("!")
        label = Label(popup, text=msg, font=self.titleFont)
        label.pack(side="top", fill="x", pady=10)
        B1 = Button(popup, text="    Ok    ", command = popup.destroy)
        B1.pack()
        popup.mainloop()
        
if __name__ == "__main__":
  
    TS = TextSegmentation()



