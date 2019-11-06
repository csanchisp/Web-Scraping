#import the necessary packages
import argparse
from bs4 import BeautifulSoup
import builtwith
import csv
import os
import re
import requests
import unidecode
import urllib.request
import whois

print(whois.whois('https://www.normacomics.com'))
builtwith.parse('https://www.normacomics.com')

#Creació del nom del directori "pictures_comics"
base_dir = os.getcwd()
dir_name = "pictures_comics"
dir_path = os.path.join(base_dir, dir_name)

#Create the directory if already not there
if not os.path.exists(dir_path):
    os.mkdir(dir_path)
    
# Descarrega de la url
def download (url, user_agent="wswp", num_retries=2):
    print ("Downloading:", url)
    headers = {"User-agent": user_agent}
    page    = requests.get(url)

    return page

# Tractament d'imatges
def trt_imatge_comic(soup):

    # Tractament per obtindre la url d'on esta la imatge
    image     = soup.find_all('img', id= "loadImage")
    image_src = re.findall('src="(.*?jpg)"',str(image))
    
    if not image_src:
        # Si no es jpg busquem per png
        image_src = re.findall('src="(.*?png)"',str(image))
        
    text_src  = re.sub("']",'',str(image_src))
    text_src  = text_src[2:]
    
    # Títol de la imatge
    name = str(text_src.split('/')[-1])
    
    # Guardem la imatge en el directori pictures_comics
    urllib.request.urlretrieve(text_src,os.path.join(dir_path, name))

    return name

# Lectura d'un item
def item(url):
    dl   = download(url)
    soup = BeautifulSoup(dl.content)

    # titulo, considerem algunes excepcions referents a caracters extranys
    titulo= soup.h1.get_text()
    if not titulo.istitle():
        titulo= unidecode.unidecode(titulo)
    
    # precio, el capturem com a float
    precio = soup.find_all('span', class_ = 'price')
    precio = float(re.findall('>(.*?)\xa0', str(precio[1]))[0].replace(',','.'))
    
    # com que la seguent part de la pagina pot no ser consistent considerem algunes excepcions
    comic_containers = soup.find_all('div', class_ = 'grid_10 no-both-margin pad005')
    comic_csup       = soup.find_all('strong', class_='grid_2 no-both-margin')
    
    autores          = ""
    colecciones      = ""
    editoriales      = ""
    series           = ""
    
    # recorrem comic_containes per tal d'obtenir les variables autores, colecciones, editoriales, series
    for i in range(len(comic_containers)):
        if (comic_csup[i].get_text() == 'Autores: '):
            autores = comic_containers[i].get_text().strip()
            if 'Y' in autores:
                autores= unidecode.unidecode(autores)
        elif (comic_csup[i].get_text() == 'Colecciones: '):
            colecciones = comic_containers[i].get_text().strip()
        elif (comic_csup[i].get_text() == 'Editoriales: '):
            editoriales = comic_containers[i].get_text().strip()
        elif (comic_csup[i].get_text() == 'Series: '):
            series = comic_containers[i].get_text().strip()
            if not series.istitle():
                series= unidecode.unidecode(series)
            
    # com que la seguent part de la pagina pot no ser consistent considerem algunes excepcions
    caracteristicas = soup.find_all('td')
    carsup          = soup.find_all('th')
    
    isbn            = ""
    fecha_venta     = ""
    formato         = ""
    paginas         = ""

    # recorrem caracteristiques per tal d'obtenir les variables isbn, fecha de venta, formato, Num páginas
    for i in range(len(caracteristicas)):
        if (carsup[i].get_text() == 'ISBN'):
            isbn = caracteristicas[i].get_text()
        elif (carsup[i].get_text() == 'Fecha de venta'):
            fecha_venta = caracteristicas[i].get_text()
        elif (carsup[i].get_text() == 'Formato'):
            formato = caracteristicas[i].get_text()
        elif (carsup[i].get_text() == 'Num páginas'):
            paginas = int(str(caracteristicas[i].get_text()))
 
    # tractament per a les imatges del comics
    imagen = trt_imatge_comic(soup)
    
    # creem el registre
    comic_element  =[isbn,titulo,precio,autores,colecciones,editoriales,series,fecha_venta,formato,paginas,imagen]
    
    return(comic_element)


# Llegim enllaços dels items de la pagina seguent. Funció recursiva amb retorn
def pagmes(url):
    dl    = download(url)
    soup  = BeautifulSoup(dl.content)
    
    # agafem enllaços dels items
    titulos = soup.find_all('div', class_="product-content")    
    links   = re.findall('<a href="(.*?comic.*?.html)" ', str(titulos))
    
    # busquem la pagina seguent (problemes amb la lectura de &)
    paginas = soup.find_all('a', class_="next i-next")
    papre   = re.findall('href="(.*?)amp;', str(paginas))
    papos   = re.findall('amp;(.*?)"', str(paginas))    
    paginas = [papre[i] + papos[i] for i in range(len(papre))]
    
    # si hi ha pagina següent
    if paginas:
        links += pagmes(paginas[0])
    
    #retornem llista de links
    return(links)

# Tractament per cada pagina
def pagina(url):
    dl   = download(url)
    soup = BeautifulSoup(dl.content)
    
    # agafem enllaços dels items
    titulos = soup.find_all('div', class_="product-content")
    links   = re.findall('<a href="(.*?comic.*?.html)" ', str(titulos))
    
    # busquem la pagina seguent (lectura especial de &)
    paginas = soup.find_all('a', class_="next i-next")
    papre   = re.findall('href="(.*?)amp;', str(paginas))
    papos   = re.findall('amp;(.*?)"', str(paginas))    
    paginas = [papre[i] + papos[i] for i in range(len(papre))]
    
    # si hi ha pagina següent
    if paginas:
        links += pagmes(paginas[0])
        
    print(len(links))
  
    # generem el dataset escrivint en el fitxer csv "novedades_comics.csv"
    headerList =["ISBN","Título","Precio","Autores","Colecciones","Editoriales","Series","Fecha de venta","Formato","Páginas","Nombre Imagen"]
    with open("novedades_comics.csv", 'w', newline='') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerow(headerList)
        for link in links:
            writer.writerow(item(link)) 
            
# maxim d'items per pagina 
def maxnum(url):
    dl    = download(url)
    items = re.findall('href="(.*?)" class="show_icon ">', str(dl.content))
    pagina(items[-1])

# Examen del sitemap
def crawl(url):
    # download the sitemap file
    sitemap= download(url)
    # extract the sitemap links
    links= re.findall('<loc>(.*?)</loc>', str(sitemap.content))
    # escollim links que ens interessen
    for link in links:
        # agafem directament novedades-comics.html
        if re.match('.*novedades-comics.html',link):
            maxnum(link)

crawl("https://www.normacomics.com/sitemap/sitemap.xml")

