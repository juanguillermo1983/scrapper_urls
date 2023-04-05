#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
presentacion
"""
import sys
from urllib.parse import urlparse
import warnings
import requests
from bs4 import BeautifulSoup as Soup
from email_scraper import scrape_emails

warnings.filterwarnings("ignore")

urls_crawler = []
urls_sitemap = []


def check_robot(url):
    """
    Funcion check_robot, extrae urls desde el archivo robots.txt
    retorna una lista"""
    lt_urls=[]
    res = requests.get(url + '/robots.txt', timeout=5)
    if res.ok is True:
        lt_text = res.text.split('\n')
        for texto in lt_text:
            texto = texto.replace('Disallow:', '').replace(' ', '').replace('Allow:', '')
            texto = texto.replace('*', '').replace('Sitemap:', '')
            if len(texto) > 1:
                if texto.startswith('/'):
                    target = str(url+texto)
                elif texto.startswith('http'):
                    target = str(texto)
                else:
                    target = False

                if (target not in lt_urls) and target is not False:
                    res = requests.get(target, timeout=3)
                    if res.status_code >= 200 and res.status_code < 300:
                        lt_urls.append(target)
    return lt_urls


def check_sitemap(url):
    """
    Funcion sitemap, extrae las url desde el archivo sitemap.xml
    buscando de manera recursiva
    retorna una lista
    """
    if not url.endswith('.xml'):
        url= url+'/sitemap.xml'

    resp = requests.get(url)
    if 200 == resp.status_code:
        soup = Soup(resp.content,features='xml')
        urls = soup.findAll('loc')
        for url_loc in urls:
            sitio = str(url_loc).replace('<loc>','').replace('</loc>','')
            if sitio.endswith('.xml'):
                check_sitemap(sitio)
            else:
                if sitio not in urls_sitemap:
                    urls_sitemap.append(sitio)
    return urls_sitemap

def crawler(url,url_base):
    """
    Funcion crawler, extrae las url encontradas en la url target
     y sigue buscando recursivamente
    """
    resp = requests.get(url)
    soup = Soup(resp.content,'html.parser')
    for lnk_href in soup.find_all("a",href=True):
        sitio = lnk_href['href']
        if sitio.startswith(url_base):
            if sitio.endswith('.jpg') or sitio.endswith('.png') or sitio.endswith('.gif')\
                 or sitio.endswith('.pdf'):
                pass
            else:
                if sitio not in urls_crawler:
                    urls_crawler.append(sitio)
                    print(sitio)
                    crawler(sitio,url_base)

def scraper(url):
    """
    Funcion que recibe una url objetivo
    retorna lista de correos electronicos encontrados
    """
    emails =[]
    try:
        resp = requests.get(url,timeout=2)
        if 200 == resp.status_code:
            emails = list(scrape_emails(resp.content.decode()))
            return emails
    except requests.exceptions.Timeout:
        return emails

    return emails

def export_data(file_name, data):
    """ Funcion para exportar datos a archivos
    recibe file_name nombre del archivo
    data, corresponde a una lista de informacion
    la informacion es almacena con salto de linea"""
    with open(file_name,'a',encoding = 'utf-8') as file_data:
        for linea in data:
            file_data.write(str(linea)+'\n')
    file_data.close()

def main():
    """ funcion principal """
    url = str(input("Ingresa la url: "))
    #url='https://www.wom.cl'
    valida = urlparse(url)
    if valida.scheme and valida.netloc:

        #Llama a la funcion check_robot, la cual retornara una lista de urls
        lista_robot = check_robot(url)

        #Crea el archivo robots.txt
        export_data('robots.txt',lista_robot)
        print("="*30)
        print("Fin proceso robots")
        print("="*30)
        #Recorre la lista por cada url encontrada
        for url_rob in lista_robot:
            crawler(url_rob,url)
        export_data('urls.txt',urls_crawler)
        print('largo urls_crawler',len(urls_crawler))

        print("="*30)
        print("crawler robot almacenado")
        print("="*30)

        lt_fuzz=['/sitemap.xml','/new-sitemap.xml','/wp-sitemap.xml',\
        '/site/sitemap_pags.xml','/media/sitemap.xml']

        targ = url
        for fuz in lt_fuzz:
            resp = requests.get(url+fuz)
            if 200 == resp.status_code:
                targ = url+fuz
                break

        print(targ)
        print('Sitemap encontrado','='*30)
        #Llama a la funcion check_sitemap
        lista_sitemap = check_sitemap(targ)
        export_data('sitemap.txt',lista_sitemap)

        #Recorre la lista por cada path encontrado
        for url_site in lista_sitemap:
            crawler(url_site,url)
        export_data('urls.txt',urls_crawler)
        print('largo urls_crawler',len(urls_crawler))

        print("="*30)
        print("crawler sitemap almacenado")
        print("="*30)

        lista_scraper = []
        with open('urls.txt', 'r',encoding = 'utf-8') as file_craw:
            tex = file_craw.read()
            file_craw.close()
        texto = [x for x in tex.split('\n') if x != '']
        for url in texto:
            lt_tmp = scraper(url)
            if len(lt_tmp) > 0:
                print(lt_tmp)
                lista_scraper.extend(lt_tmp)

        lista_scraper = list(set(lista_scraper))
        export_data('emails.txt',lista_scraper)
        print("="*30)
        print("scraper email almacenado")
        print("="*30)

    else:
        print('Ingrese URL Valida')
        main()

    print("="*60)
    print('Proceso terminado terminado')

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt():
        sys.exit()
