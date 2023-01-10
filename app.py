# -*- coding: utf-8 -*-
"""
@author: Nicolas Carval & Bruno Pincet 
"""
#%% Libraries and MongoDB connection

import numpy as np
from flask import Flask, request, jsonify, render_template
import pandas as pd
import json
import time
import re

import copy
import plotly
import plotly.express as px

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd
import time

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

wd = webdriver.Chrome("chromedriver.exe",options=chrome_options)


#%% STATIC PAGES

# method to send query to collection


#APPLICATION
app = Flask(__name__)

#Home page
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/Choose_recipe',methods=['GET'])
def Choose_recipe():
    return render_template('Choose_recipe.html')

#List of ingredients page
@app.route('/Recipe',methods=['GET'])
def Recipe():
    return render_template('Recipe.html')

#Comparison page
@app.route('/Best_market',methods=['GET'])
def Best_market():
    return render_template('Best_market.html')

#Comparison page
@app.route('/Not_found',methods=['GET'])
def Not_found():
    return render_template('Not_found.html')



#%% QUERIES
@app.route('/Choose_recipe',methods=['POST'])
def scrap_recipe():
    recipe_to_scrap =  [str(x) for x in request.form.values()]
    
    #scrap recip
    wd.get("https://www.750g.com/")
    wd.find_element(By.XPATH,'/html/body/header/div/div[2]/label').click()
    wd.implicitly_wait(3)
    # 
    
    #recette=input("recette : ")
    recette=recipe_to_scrap[0]
    nom_recette=[]
    lien_recette=[]
    pic=[]
    
    rech = wd.find_element(By.XPATH,'/html/body/header/div/div[2]/div/div/form/div/div/input')
    rech.send_keys(recette);
    rech.send_keys(Keys.ENTER);
    
    #WebDriverWait(wd, 30).until(EC.presence_of_element_located((By.CLASS_NAME, "card-media")))
    
    if len(wd.find_elements(By.CLASS_NAME, "card-title")) > 0:
        print("len recipe ok")
        n=wd.find_elements(By.CLASS_NAME, "card-title")
        l=wd.find_elements(By.CLASS_NAME, "card-link")
        p=wd.find_elements(By.CLASS_NAME, "card-media")
    
        for i in range(len(n)):
            
            nom_recette.append(n[i].text)
            lien_recette.append(l[i].get_attribute('href'))
    
        lenOfPage = wd.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
        
        
        while(len(pic)!=len(lien_recette)):
            print("boucle while")
            pic=[]
            for i in range(0,lenOfPage,600):
                wd.execute_script(f"window.scrollTo(0, {i})") 
                wd.implicitly_wait(2)
            p=wd.find_elements(By.CLASS_NAME, "to-lazy.media-round.lazyed")
            for i in p:
                pic.append(i.get_attribute("src"))    
            print(len(pic))
        
        
    else :
        print("Aucune recette trouvée")
        recette=input("veuillez entrer une nouvelle recette : ")
        wd.back();
    print("success")
    if(len(nom_recette)>=1):
        df = list(zip(nom_recette, lien_recette))
        return render_template('Choose_recipe.html',recipee = recipe_to_scrap[0], tables=df)
    else :
        df = [" no recipe found "]
        return render_template('Not_found.html',recipee = recipe_to_scrap[0], tables=df)
    #df["picture_link"]=pic
    

@app.route('/Recipe',methods=['POST'])
def scrap_ingredients():
    recipe_to_scrap =  request.form.getlist("ids")[0]
    print(request)
    print(recipe_to_scrap)
    
    
    lien_recette=recipe_to_scrap
    wd.get(lien_recette)
    ingr = wd.find_elements(By.CLASS_NAME, "recipe-ingredients-item-label")
    #recette=wd.find_elements(By.CLASS_NAME, "recipe-steps-text")
    
    liste_ingr=[]
    for i in ingr:
        liste_ingr.append(i.text)
    print(liste_ingr)
    result = get_clean_ingr(liste_ingr)
    
    
    result["complete"] = result["Produit"]+" - "+result["Quantité"].astype(str)+" - "+result["Unité"]
    return render_template('Recipe.html',recipee = "yooo", tables=result.complete.tolist())

@app.route('/Best_market',methods=['POST'])
def scrap_market():
    ing_to_scrap =  request.form.getlist("ids")
    list_ingredient = [el.split(" - ")[0] for el in ing_to_scrap]
    print(list_ingredient)
    

    #scrap ing
    match_list = get_liste_achat_match(list_ingredient)
    aldi_list=get_liste_achat_aldi(list_ingredient)
    print(match_list)
    print(aldi_list)
    
    print(compar_brand(aldi_list,match_list,"Aldi","Match & Smatch"))     

    
    
    result = pd.DataFrame({"Market":["Carrefour","Auchan", "Lidl"], "Total":["10€", "14€", "20€"]})
    
    return render_template('Best_market.html', tables=[result.to_html(classes='data')], titles=result.columns.values)



#%% Regex pour traiter liste des ingrédients 

def get_clean_ingr(liste_ingr):
  df_course = pd.DataFrame(columns = ["Ingredient_brut", "Quantité", "Unité","Produit"])
  for ingredient in liste_ingr:
    match = re.search(r"(.*) ou (.*)", ingredient)
    if match: ingredient= match.group(1)
    brute=True
    # c à s / c à c
    match = re.search(r"(\d+)\sc\.\sà\s[s|c]\.\s(de|d')( |)(.*)", ingredient)
    if match:
      quantity = match.group(1)
      unit = "c. à s./c."
      name = match.group(4)
      df1 = pd.DataFrame({
      "Ingredient_brut": [ingredient],
      "Quantité": [quantity],
      "Unité":[unit],
      "Produit":[name]})
      df_course = df_course.append(df1)
      brute=False


    # sachet / paquets
    match = re.search(r"(\d+) (?:paquet+s?|sachet+s?) (de|d')( |)(.*)", ingredient)
    if match:
      quantity = match.group(1)
      unit = "sachets"
      name = match.group(4)
      df1 = pd.DataFrame({
      "Ingredient_brut": [ingredient],
      "Quantité": [quantity],
      "Unité":[unit],
      "Produit":[name]})
      df_course = df_course.append(df1)
      brute=False

    # g de
    match = re.search(r"(\d+)( |)+g\s(de|d')( |)+(.*)", ingredient)
    if match:
      quantity = match.group(1)
      unit = "g"
      name = match.group(5)
      df1 = pd.DataFrame({
      "Ingredient_brut": [ingredient],
      "Quantité": [quantity],
      "Unité":[unit],
      "Produit":[name]})
      df_course = df_course.append(df1)
      brute=False

    # cl de
    match = re.search(r"(\d+)( |)+cl\s(de|d')( |)+(.*)", ingredient)
    if match:
      quantity = match.group(1)
      unit = "cl"
      name = match.group(5)
      df1 = pd.DataFrame({
      "Ingredient_brut": [ingredient],
      "Quantité": [quantity],
      "Unité":[unit],
      "Produit":[name]})
      df_course = df_course.append(df1)
      brute=False

    # dl de
    match = re.search(r"(\d+)( |)+dl\s(de|d')( |)+(.*)", ingredient)
    if match:
      quantity = match.group(5)
      unit = "dl"
      name = match.group(4)
      df1 = pd.DataFrame({
      "Ingredient_brut": [ingredient],
      "Quantité": [quantity],
      "Unité":[unit],
      "Produit":[name]})
      df_course = df_course.append(df1)
      brute=False

    # l de
    match = re.search(r"(\d+)( |)+l\s(de|d')( |)+(.*)", ingredient)
    if match:
      quantity = match.group(1)
      unit = "l"
      name = match.group(5)
      df1 = pd.DataFrame({
      "Ingredient_brut": [ingredient],
      "Quantité": [quantity],
      "Unité":[unit],
      "Produit":[name]})
      df_course = df_course.append(df1)
      brute=False


    # kg de
    match = re.search(r"(\d+)( |)+kg\s(de|d')( |)+(.*)", ingredient)
    if match:
      quantity = match.group(1)
      unit = "kg"
      name = match.group(5)
      df1 = pd.DataFrame({
      "Ingredient_brut": [ingredient],
      "Quantité": [quantity],
      "Unité":[unit],
      "Produit":[name]})
      df_course = df_course.append(df1)
      brute=False

    # pincée de
    match = re.search(r"(\d+)\s+pincée+s?\s(de|d')( |)+(.*)", ingredient)
    if match:
      quantity = match.group(1)
      unit = "pincée"
      name = match.group(4)
      df1 = pd.DataFrame({
      "Ingredient_brut": [ingredient],
      "Quantité": [quantity],
      "Unité":[unit],
      "Produit":[name]})
      df_course = df_course.append(df1)
      brute=False

    # verre de
    match = re.search(r"(\d+)\s+verre+s?\s(de|d')( |)+(.*)", ingredient)
    if match:
      quantity = match.group(1)
      unit = "verre"
      name = match.group(4)
      df1 = pd.DataFrame({
      "Ingredient_brut": [ingredient],
      "Quantité": [quantity],
      "Unité":[unit],
      "Produit":[name]})
      df_course = df_course.append(df1)
      brute=False

      # bol de
    match = re.search(r"bol+s? (de|d')( |)+(.*)", ingredient)
    if match:
      quantity = "No info"
      unit = "No info"
      name = match.group(3)
      df1 = pd.DataFrame({
      "Ingredient_brut": [ingredient],
      "Quantité": [quantity],
      "Unité":[unit],
      "Produit":[name]})
      df_course = df_course.append(df1)
      brute=False
      #rouleau de 
    match = re.search(r"(\d+) (?:rouleau+x?) (de|d')( |)(.*)", ingredient)
    if match:
      quantity = match.group(1)
      unit = "rouleaux"
      name = match.group(4)
      df1 = pd.DataFrame({
      "Ingredient_brut": [ingredient],
      "Quantité": [quantity],
      "Unité":[unit],
      "Produit":[name]})
      df_course = df_course.append(df1)
      brute=False

      
    if brute==True:

      match = re.search(r"(\d+)\s(.*)", ingredient)
      if match:
        quantity = match.group(1)
        unit = "unités"
        name = match.group(2)
        df1 = pd.DataFrame({
        "Ingredient_brut": [ingredient],
        "Quantité": [quantity],
        "Unité":[unit],
        "Produit":[name]})
        df_course = df_course.append(df1)
      else:
        quantity='No info'
        unit="No info"
        name = ingredient
        df1 = pd.DataFrame({
        "Ingredient_brut": [ingredient],
        "Quantité": [quantity],
        "Unité":[unit],
        "Produit":[name]})
        df_course = df_course.append(df1)
      

  df_course=df_course.drop_duplicates()
  return df_course

#%% Scrapping des Courses "Match & Smatch"

def get_liste_achat_match(list_ingred):
  liste_achat_match={}
  for i in list_ingred:
    val=get_produit_match(i)
    
    if val is not None and val.empty != True:
        val['prix_u'] = val['prix_u'].str.replace(',','.')
        val['prix_u'] = val['prix_u'].astype('float32')
        val=val.sort_values(by=['prix_u'])
        liste_achat_match[i]=[val.head(1)["nom_produit"].tolist()[0],val.head(1)["prix_u"].tolist()[0],val.head(1)["prix_total"].tolist()[0]]
    else:
      liste_achat_match[i]=None
  return liste_achat_match

def get_produit_match(produit):
  wd.get(f"https://www.supermarchesmatch.fr/fr/recherche?recherche={produit}")
  wd.implicitly_wait(4)
  wd2= copy.copy(wd)
  lenOfPage = wd.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
  wd.execute_script(f"window.scrollTo(0, {lenOfPage})") 

  for i in range(0,lenOfPage,600):
            wd.execute_script(f"window.scrollTo(0, {i})") 
            wd.implicitly_wait(1)
  name=[]
  cond=[]
  prixu=[]
  unite=[]
  prix_produit=[]
  wd.implicitly_wait(1)
  wd.execute_script("window.scrollTo(0, 100000)") 
  wd.implicitly_wait(2)

  def check_exists_by_xpath(xpath):
      try:
          wd2.find_element(By.XPATH,xpath)
      except :
          return False
      return True
  print("before if")
  if check_exists_by_xpath('//*[@id="pageSearchContainer"]/div/div[2]/span/div[3]/span')==False:
    WebDriverWait(wd, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "label")))
    l=wd.find_elements(By.CLASS_NAME, "label")
    if len(l)>5:
      l=l[0:5]
    for i in l:
      WebDriverWait(wd, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "part1")))
      WebDriverWait(wd, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME,"a")))
      WebDriverWait(wd, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "conditionnement")))
      try:
        name.append(i.find_element(By.CLASS_NAME,"part1").text+" "+i.find_element(By.TAG_NAME,"a").text)
        cond.append(wd.find_element(By.CLASS_NAME, "conditionnement").text)
      except:
        name.append(None)
        cond.append(None)

    prix=wd.find_elements(By.CLASS_NAME, "prix")
    prix=prix[:len(l)]
    for i in prix:
      try:
        entier=i.find_element(By.CLASS_NAME, "entier").text
        deci=i.find_element(By.CLASS_NAME, "decimal").text
        dev=i.find_element(By.CLASS_NAME, "devise").text
        prixu.append(entier+deci)
        unite.append(i.find_element(By.CLASS_NAME, "parUnite").text)
      except:
        prixu.append(None)
        unite.append(None)

    realprix=wd.find_elements(By.CLASS_NAME, "prix.prix-unitaire")
    realprix=realprix[:len(l)]

    for i in realprix:
      prix_produit.append(i.find_element(By.CLASS_NAME, "entier").text+i.find_element(By.CLASS_NAME, "decimal").text)

    df_produit_ingr = pd.DataFrame(list(zip(name,cond,prixu,unite,prix_produit)),
               columns =['nom_produit',"cond",'prix_u', 'unite','prix_total'])
    
    
    return df_produit_ingr

#%% Scrapping des Courses "Aldi"

def get_produit_aldi(produit):
  try:
    wd.get(f"https://www.aldi.be/fr/resultats-de-recherche.html?query={produit}")
    wd.implicitly_wait(1)
    wd.execute_script("window.scrollTo(0, 10000)") 
    index=1
    wd.implicitly_wait(2)
    l=wd.find_elements(By.TAG_NAME, "section")
    txt_l=[]
    for i in l:
      txt_l+=i.text.split("Résultats de recherche dans")

    txt_l=list(filter(lambda x: x.startswith(" Assortiment"), txt_l))
    txt_l=txt_l[0].replace(' Assortiment',"").split("AJOUTER À LA LISTE DE COURSES")
    for i in range(len(txt_l)):
      if i==0:
        txt_l[i]=txt_l[i].split('\n')[1:-1]
      else:
        txt_l[i]=txt_l[i].split('\n')[2:-1]

    if len(txt_l)>5:
      txt_l=txt_l[:5]
    elif len(txt_l)>2:
      txt_l=txt_l[:-1]


    nom_produit=[]
    prix_u=[]
    prix_total=[]

    for i in txt_l:
      if len(i)==2:
        nom_produit.append(i[1])
        prix_u.append(None)
        prix_total.append(None)
      else:
        nom_produit.append(i[len(i)-2]+" "+i[len(i)-1])
        prix_u.append(re.search('([0-9]{0,2}(?:[.][0-9]{1,2})?)/', i[len(i)-3]).group(1))
        prix_total.append(i[0])


    df_produit_ingr = pd.DataFrame(list(zip(nom_produit,prix_u,prix_total)),
                  columns =['nom_produit','prix_u','prix_total'])
    return df_produit_ingr
  except:
      return None

def get_liste_achat_aldi(list_ingred):
  liste_achat_match={}
  for i in list_ingred:
    val=get_produit_aldi(i)
    if val is not None:
      val['prix_u'] = val['prix_u'].astype('float32')
      val=val.sort_values(by=['prix_u'])
      liste_achat_match[i]=[val.head(1)["nom_produit"].tolist()[0],val.head(1)["prix_u"].tolist()[0],val.head(1)["prix_total"].tolist()[0]]
    else:
      liste_achat_match[i]=None
  return liste_achat_match
#%% Comparaison

def compar_brand(lista,listb,namea,nameb):
    prix_a=[]
    available_a=0
    prix_b=[]
    available_b=0
    name=[]
    for i in lista.keys():
            if lista[i] is not None and listb[i] is not None:
                name=[]
                prix_a.append(float(lista[i][2]))
                prix_b.append(float(listb[i][2].replace(",",".")))
                available_b+=1
                available_a+=1
            elif lista[i] is None:
                available_b+=1
            else:
                available_a+=1
    total_a=sum(prix_a)
    total_b=sum(prix_b)
    diff=abs(total_a-total_b)/((total_a+total_b)/2)*100
    if total_a<total_b:
        low=namea
    else:
        low=nameb
        
    return(diff,low,total_a,total_b,prix_a,prix_b,available_a,available_b)

#%% MAIN
if __name__ == "__main__":
    app.run(host='localhost', port=8989)