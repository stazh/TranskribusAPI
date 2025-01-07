import sys
import os
import glob
from bs4 import BeautifulSoup
from PIL import Image
"""Diese Klasse extrahiert sämtliche Bilder der Textregionen, welche einen Namen haben, aus einem lokalen Transkribus-Dokument.
Starten: python extract_TR_images.py [Pfad zu Transkribus-Dokument]"""
class ExtractImagesLocal():

	def extractRegionsImage(self, xmldoc,page_img):
			#get the data that contains the images
		page_img = Image.open(page_img)
		images = []
		region_names = []
		openxmldoc = open(xmldoc,'r')
		soup = BeautifulSoup(openxmldoc, "xml")

		for region in soup.findAll("TextRegion"):
			region_text = region['custom']
			iregion = region_text.rfind("type:")

			#Falls Textregion nicht benannt.
			if iregion != -1:
				region_text = region_text[iregion+5:-2]
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

				images.append(page_img.crop((minX, minY, maxX,maxY)))
				region_names.append(region_text)

		return images,region_names

if __name__ == "__main__":
	eil = ExtractImagesLocal()
	pfad = sys.argv[1]
	pfadneu = pfad.replace("\\","/") + '_images'
	if not os.path.exists(pfadneu):
  		os.makedirs(pfadneu)
	for xmlpfad in glob.glob(pfad + "\page/*.xml"):
		print('extract from '+ xmlpfad)
		imgpfad = xmlpfad.replace(".xml",".jpg")
		imgpfad = imgpfad.replace("page","")
		images, images_names = eil.extractRegionsImage(xmlpfad,imgpfad)
		for i in range(0,len(images)):
			iSuperPfad = pfad.rfind("/")
			iStartXml = xmlpfad[:-2].rfind("\\")
			images[i].save(pfadneu + xmlpfad[iStartXml:].replace('.xml','').replace("\\","/") +'_' + images_names[i] + '.jpg')