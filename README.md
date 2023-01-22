# Scrapy Meal - Webscapping & Data Processing 

ESILV 2022–2023

<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/6/60/Logo_ESILV.svg/2560px-Logo_ESILV.svg.png" alt="alt text" width="300" height="whatever" align="right">


## Sommaire

1. [Introduction](#introduction)
2. [Démonstration](#démonstration)
3. [Installation](#installation)
4. [Auteurs](#auteurs)

---

## Introduction

<img src=https://aistoucuisine.com/wp-content/uploads/2022/05/mousseul3.jpg alt="alt text" width="250" height="whatever" align="right">

De nombreux sites proposant des recettes de cuisine 🍽 en ligne ont été popularisés ces dernières années. Cependant il n'est pas forcément facile pour les utilisateurs de s'y retrouver dans la liste des ingrédients 🥭 à acheter pour réaliser les recettes. Et après ? Dans quel magasin devrait-il se diriger afin d'être optimisé en termes de temps ⏲ et de prix 💰.


Notre solution "Scrapy Meal" est un interface en ligne permettant de rechercher une recette et obtenir automatiquement la liste des ingrédients et les étapes de celle-ci. Ensuite, notre algorithme se charge de comparer les prix des ingrédients dans 2 chaînes de magasins belges célèbres, et enfin de lui trouver le magasin plus proche tout en calculant le prix du trajet.

&nbsp;&nbsp;



![image](https://user-images.githubusercontent.com/84092005/213861323-6d29fc12-feb6-43c3-b2dd-c41e6127315c.png)

[Retour au sommaire](#sommaire)

---

## Démonstration

<iframe  title="demo video" width="480" height="390" src="https://www.youtube.com/watch?v=lUN19aL4wJc" frameborder="0" allowfullscreen></iframe>

[Retour au sommaire](#sommaire)

---


## Installation
<img src=https://upload.wikimedia.org/wikipedia/commons/d/d5/Selenium_Logo.png alt="alt text" width="125" height="whatever" align="right">

&nbsp;&nbsp;

<strong>Afin de pouvoir utiliser l'application, merci d'exécuter le code suivant :</strong>


* [Scrapy_Meal/app.py](https://github.com/NicolasCarval/Scrapy_Meal/blob/master/app.py )

<strong>Puis se rendre ensuite sur un navigateur à l'adresse suivante :</strong>
* [http://localhost:8989 ](http://localhost:8989 )

| ⚠️ WARNING: Le code peut parfois être long à s'exécuter en fonction du réseau et du nombre d'ingrédients ! |
| --- |

<img src=https://play-lh.googleusercontent.com/keVVojxW-b11NTKWZg8GulfLlhqBpATvqGFViblYsI0fxW_8a0sIPgyRlB94Gu1AQMY alt="alt text" width="150" height="whatever" align="right">

<strong>Librairies nécessaires : </strong>
* [Scrapy_Meal/requirements.txt](https://github.com/NicolasCarval/Scrapy_Meal/blob/master/requirements.txt)

```
- Flask==2.2.2
- geopy==2.3.0
- jellyfish==0.9.0
- pandas==1.3.5
- plotly==5.11.0
- requests==2.28.1
- selenium==3.141.0
```

>utiliser la commande suivante pour installer des librairies
```
   pip install "library name"
```




[Retour au sommaire](#sommaire)

---


## Auteurs

* PINCET Bruno 
    * [Github - @GitBrunoCode](https://github.com/GitBrunoCode)
    * [Linkedin - PINCET Bruno](https://www.linkedin.com/in/bruno-pincet/)
* CARVAL Nicolas 
    * [Github - @NicolasCarval](https://github.com/NicolasCarval)
    * [Linkedin - CARVAL Nicolas](https://www.linkedin.com/in/nicolas-carval-0a8860214/)


[Retour au sommaire](#sommaire)

