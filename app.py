# -*- coding: utf-8 -*-
"""
@author: Nicolas Carval & Bruno Pincet 
"""
#%% Libraries 

#Main lib
from flask import Flask, request, render_template
import pandas as pd
import json
import re
from geopy.geocoders import Nominatim
import requests
import copy
import jellyfish

#Plot lib
import plotly
import plotly.graph_objects as go

#Scrapping lib
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

#Driver Parameters
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

wd = webdriver.Chrome("chromedriver.exe",options=chrome_options)


#%% STATIC PAGES

#APPLICATION
app = Flask(__name__)

#Home page
@app.route('/')
def home():
    return render_template('index.html')

#List of recipe page
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

#Recipe not found page
@app.route('/Not_found',methods=['GET'])
def Not_found():
    return render_template('Not_found.html')



#%% POST routes
    
#Post the recipe choice of the user
@app.route('/Choose_recipe',methods=['POST'])
def scrap_recipe():
    '''
    Récupération de la recette écrite par l'utilisateur
    Recherche de la barre de recherche sur 750g.com
    Ecriture du titre de la recette dans la barre puis entrer
    Si aucun résultat sur 750g demande à l'utilisateur d'entrer une autre recette
    Sinon affiche les résultats
    '''
    recipe_to_scrap =  [str(x) for x in request.form.values()]
    
    #scrap recipe
    wd.get("https://www.750g.com/")
    wd.find_element(By.XPATH,'/html/body/header/div/div[2]/label').click()
    wd.implicitly_wait(3)
     
    #variable declaration
    recette=recipe_to_scrap[0]
    nom_recette=[]
    lien_recette=[]
    pic=[]
    
    #localisation de la barre de recherche du site
    rech = wd.find_element(By.XPATH,'/html/body/header/div/div[2]/div/div/form/div/div/input')
    rech.send_keys(recette);
    rech.send_keys(Keys.ENTER);
    
    #Si plusieurs recettes en résultats alors affichage    
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
            pic=[]
            for i in range(0,lenOfPage,600):
                wd.execute_script(f"window.scrollTo(0, {i})") 
                wd.implicitly_wait(2)
            p=wd.find_elements(By.CLASS_NAME, "to-lazy.media-round.lazyed")
            for i in p:
                pic.append(i.get_attribute("src"))
        
    #Sinon redemande une autre recette   
    else :
        print("Aucune recette trouvée")
        #recette=input("veuillez entrer une nouvelle recette : ")
        wd.back();
    print("success")
    print(pic)
    #S'il existe une recette nous renvoyons la liste
    if(len(nom_recette)>=1):
        df = list(zip(nom_recette, lien_recette,pic))
        return render_template('Choose_recipe.html',recipee = recipe_to_scrap[0], tables=df)
    #Sinon nous affichons une page d'erreur
    else :
        df = [" no recipe found "]
        return render_template('Not_found.html',recipee = recipe_to_scrap[0], tables=df)
    #df["picture_link"]=pic
    

#Post the ingredients of the recipe
@app.route('/Recipe',methods=['POST'])
def scrap_ingredients():
    """
    récupération de la liste des ingrédients
    récupération des étapes de la recette
    sur le lien de la recette
    """
    recipe_to_scrap =  request.form.getlist("ids")[0]
    print(request)
    print(recipe_to_scrap)
    
    lien_recette=recipe_to_scrap
    wd.get(lien_recette)
    ingr = wd.find_elements(By.CLASS_NAME, "recipe-ingredients-item-label")
    #recette=wd.find_elements(By.CLASS_NAME, "recipe-steps-text")
    
    #save ingredients
    liste_ingr=[]
    for i in ingr:
        liste_ingr.append(i.text)
    print(liste_ingr)
    result = get_clean_ingr(liste_ingr)
    
    #check price of fuel
    dfoil=pd.read_html('https://carbu.com/france/prixmoyens')[0]
    dfoil["Aujourd'hui"]=dfoil["Aujourd'hui"].str.extract(r'(\d,\d+)')
    dfoil["Aujourd'hui"]=dfoil["Aujourd'hui"].str.replace(',','.')
    dfoil["Aujourd'hui"] = dfoil["Aujourd'hui"].astype('float64')
    dfoil=dfoil.iloc[:,:2]
    dfoil.columns=["type de carburant","prix €/L"]
    
    #format ingredients
    result["complete"] = result["Produit"]+" - "+result["Quantité"].astype(str)+" - "+result["Unité"]
    return render_template('Recipe.html',recipee = "yooo", tables=result.complete.tolist(), fuel=list(zip(dfoil["type de carburant"].tolist(),  dfoil["prix €/L"].tolist())))

#Post the best market for selected ingredients
@app.route('/Best_market',methods=['POST'])
def scrap_market():
    '''
    Pour tous les ingrédients dans la liste:
        Recherche sur Aldi
        Recherche sur SuperMarcheMatch
    Comparaison des résultats
    '''
    #list of ingredients selected
    ing_to_scrap =  request.form.getlist("ids")
    list_ingredient = [el.split(" - ")[0] for el in ing_to_scrap]
    print(list_ingredient)
    
    location_to_scrap = request.form.getlist("location")[0]
    print(location_to_scrap)
    #scrap ingredients
    # sur match
    match_list = get_liste_achat_match(list_ingredient)
    # sur aldi
    aldi_list=get_liste_achat_aldi(list_ingredient)
    print("\n\nhere\n")
    print(match_list)
    print(aldi_list)
    
    ingredient_index = []
    for key,val in match_list.items():
        if val is not None and key in aldi_list:
            if aldi_list[key] is not None:
                ingredient_index.append(key)
    # calcul de la différence
    diff,low,total_a,total_b,prix_a,prix_b,available_a,available_b = compar_brand(aldi_list,match_list,"Aldi","Match & Smatch")    
    
    result = pd.DataFrame({"Prix Aldi ":prix_a, "Prix Match & Smatch ":prix_b},index=ingredient_index)
    show = [str(diff)+" %",available_a, available_b]
    
    #Barchart creation
    colors = ['lightslategray',] * 2
    colors[0] = 'Green'
    if total_a >total_b:
        colors[0] = 'lightslategray'
        colors[1] = 'Green'
    fig = go.Figure(data=[go.Bar(x=['Aldi', 'Match & Smatch'],
                                 y=[float(total_a), float(total_b)],marker_color=colors)])
    fig.update_layout(title_text='Prix total le moins cher')
    #Saving graph to json object
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    ###### Nouveau bloc à entrer dans une nouvelle page #####
    
    #Obtenir l'adresse de l'utilisateur
    locator = Nominatim(user_agent="myGeocoder")
    location = locator.geocode(location_to_scrap)
    if location is None:
        print("couldn't find location, using default instead")
        location = locator.geocode("Courbevoie")
        
    #Rechercher les magasins les plus proche
    aldi_nom,aldi_d,aldi_km=get_nearest_mag("Aldi",location)
    match_nom,match_d,match_km=get_nearest_mag("Match",location)
    #return nom du magasin, durée en min et distance en km 
    print(aldi_nom,match_nom)
    #type de carburant de la voiture de l'utilisateur
    #faire cocher à l'utilisateur dans ce df
    
    eurol=float(request.form.getlist("fuel")[0])
    
    #et Lui demander sa consommation au 100km
    #Calcul du prix du trajet dans chaque mag
    conso=float(request.form.getlist("conso")[0])
    print(conso)

    prix_trajet_aldi=((conso/100)*aldi_km)*eurol
    prix_trajet_match=((conso/100)*match_km)*eurol
    
    print(prix_trajet_aldi,prix_trajet_match)
    df_distance = pd.DataFrame({"Nom du magasin":[aldi_nom, match_nom],
                                "Distance km":[aldi_km,match_km],
                                "Prix Trajet":[prix_trajet_aldi,prix_trajet_match]},index=["Aldi","Match"]).sort_values(by="Prix Trajet")
    return render_template('Best_market.html', graphJSON=graphJSON,show=show, tables=[result.to_html(classes='data'), df_distance.to_html(classes="data")], titles=result.columns.values)



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
        val["prix_u"] = val.apply(lambda x: x["prix_total"] if x["prix_u"] is None else  x["prix_u"] , axis=1)
        val['prix_u'] = val['prix_u'].str.replace(',','.')
        val['prix_u'] = val['prix_u'].astype('float32')
        val["leven"] = val["nom_produit"].apply(lambda x:jellyfish.damerau_levenshtein_distance(i, x))
        val=val.sort_values(by=['leven','prix_u'])
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
    try:
        wd.find_element(By.XPATH,'/html/body/div[1]/div[1]/div[1]/div[3]/div/div[2]/div/div/ul/li[2]/button').click()
    except:
        pass
    lenOfPage = wd.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
    wd.execute_script("document.body.style.zoom='50%'")
    for i in range(0,lenOfPage,600):
                wd.execute_script(f"window.scrollTo(0, {i})") 
                wd.implicitly_wait(2)
    wd.implicitly_wait(1)
    wd.implicitly_wait(2)
    nom_produit=[]
    prix_u=[]
    prix_total=[]
    
    #Nom Produit
    n=wd.find_elements(By.CLASS_NAME,"mod-article-tile__title")
    for i in n:
        try:
            nom_produit.append(i.get_attribute('innerHTML'))
        except:
            nom_produit.append(None)
            
    if(len(nom_produit)>5):
        nom_produit=nom_produit[:5]
    
    #Prix
    p=wd.find_elements(By.CLASS_NAME,"price__wrapper")
    for i in p:
        try:
            prix_total.append(i.get_attribute('innerHTML').split("<")[0])
        except:
            prix_total.append(None)
            
    if(len(prix_total)>5):
        prix_total=prix_total[:5]

    #Prix Unité
    pu=wd.find_elements(By.CLASS_NAME,"price__base")
    for i in pu:
        try:
            prix_u.append(re.search('([0-9]{0,2}(?:[.][0-9]{1,2})?)/', i.get_attribute('innerHTML')).group(1))
        except:
            prix_u.append(None)
            
    if(len(prix_u)>5):
        prix_u=prix_u[:5]
    
    print(len(n),len(p),len(pu))
    df_produit_ingr = pd.DataFrame(list(zip(nom_produit,prix_u,prix_total)),
                  columns =['nom_produit','prix_u','prix_total'])
     
    return df_produit_ingr
  except:
      return None

def get_liste_achat_aldi(list_ingred):
  liste_achat_match={}
  for i in list_ingred:
    val=get_produit_aldi(i)
    print(val)
    if val is not None and val.empty==False:
      print("2: ",val)
      val["prix_u"] = val.apply(lambda x: x["prix_total"] if x["prix_u"] is None else  x["prix_u"] , axis=1)
      val['prix_u'] = val['prix_u'].astype('float32')
      val["leven"] = val["nom_produit"].apply(lambda x:jellyfish.damerau_levenshtein_distance(i, x))
      val=val.sort_values(by=['leven','prix_u'])
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
    for i in lista.keys():
            if lista[i] is not None and listb[i] is not None:
                if(lista[i][2] is not None and listb[i][2] is not None):
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
    try:
        diff=abs(total_a-total_b)/((total_a+total_b)/2)*100
    except:
        diff = None
    if total_a<total_b:
        low=namea
    else:
        low=nameb
        
    return round(diff,2),low,total_a,total_b,prix_a,prix_b,available_a,available_b

#%% Recherche du magasin le plus proche

def get_nearest_mag(nom_mag,location):
  #Obtenir la liste des adresses
  if nom_mag=="Aldi":
    mag_add=pd.read_csv("https://raw.githubusercontent.com/NicolasCarval/Scrapy_Meal/master/data_adresse/Aldi_address.csv",index_col=0)
  else:
    mag_add=pd.read_csv("https://raw.githubusercontent.com/NicolasCarval/Scrapy_Meal/master/data_adresse/Match_address.csv",index_col=0)
  mag_add["addresse"]=mag_add["addresse"].apply(lambda x : x.replace("\n"," "))
  
  min_duree=999999999999
  min_distance=99999999999
  nom_mag=""

  for index, row in mag_add.iterrows():
    r = requests.get(f"http://router.project-osrm.org/route/v1/car/{location.longitude},{location.latitude};{row['long']},{row['lat']}?overview=false""")
    routes = json.loads(r.content)
    duree = routes.get("routes")[0]["duration"]
    distance = routes.get("routes")[0]["distance"]

    if distance<min_distance:
      min_duree=duree
      min_distance=distance
      nom_mag=row["nom_mag"]

  return(nom_mag,round(min_duree/60,0),round(min_distance/1000,1))

#%% MAIN
if __name__ == "__main__":
    app.run(host='localhost', port=8989)