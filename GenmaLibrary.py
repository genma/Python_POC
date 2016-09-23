#!/usr/bin/python
# -*-coding:Utf-8 -*
import configparser
import urllib2
import sys
import smtplib
import os.path
import fnmatch
from twython import Twython
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
"""
Ensemble des fonctions qui ont été validées via des POC
"""

def SMSFreemobile(texte_du_sms):
    """SMSFreemobile(texte_du_sms) : envoi d'un SMS sur un smartphone Freemobile
    Le codes user et password sont lus dans le fichier de configuration Config.ini
    Retour : renvoit un bloc de texte. OK si sms envoyé, Motif de l'erreur sinon.
    """

    # Initialisation des variables locales
    userFreemobile = None
    passFreemobile = None
    resultatFonction = None

    # Lecture du fichier de param pour les codes
    try :
        config = configparser.ConfigParser()
        config.read('Config.ini')
        configFreemobile = config['CodeFreemobile']
        userFreemobile = configFreemobile['UserFreemobile']
        passFreemobile = configFreemobile['PassFreemobile']
    except IOError, e:
        resultatFonction = e

    # URL par defaut de Freemobile
    url = 'https://smsapi.free-mobile.fr/sendmsg?&user='+userFreemobile+'&pass='+passFreemobile+'&msg='+texte_du_sms
    # Appel de l'URL
    req = urllib2.Request(url)
    try:
      reponse = urllib2.urlopen(req)
    except IOError, e:
        if hasattr(e,'code'):
            if e.code == 400:
                resultatFonction = 'Un des paramètres obligatoires est manquant.'
            if e.code == 402:
                resultatFonction =  'Trop de SMS ont été envoyés en trop peu de temps.'
            if e.code == 403:
                resultatFonction =  'Le service n’est pas activé sur l’espace abonné, ou login / clé incorrect.'
            if e.code == 500:
                resultatFonction =  'Erreur côté serveur. Veuillez réessayez ultérieurement.'
    resultatFonction =  'OK. Le SMS a été envoyé sur votre mobile.'
    return resultatFonction
#Fin de la fonction SMSFreemobile

def EnvoiTwitt(messageDuTwitt):
    '''
    EnvoiTwitt(messageDuTwitt) prend un bloc de texte en paramètre
    et gènere un twitt automatiquement, en coupant au mot précédent
    si le message fait plus de 140 caractères....

    TODO : faire que la suite des messages soit des reply au 1er message envoyé

    '''
    resultatFonction = None
    try :
        config = configparser.ConfigParser()
        config.read('Config.ini')
        # Bloc lié à Twitter
        configTwitter = config['Twitter']
        CONSUMER_KEY = configTwitter['CONSUMER_KEY']
        CONSUMER_SECRET = configTwitter['CONSUMER_SECRET']
        ACCESS_KEY = configTwitter['ACCESS_KEY']
        ACCESS_SECRET = configTwitter['ACCESS_SECRET']
        # Si le message fait plus de 140 caractères,
        # On coupe au mot précédent et on ajoute le 1/n
        debutChaineCourante = 0
        finChaineCourante = 140

        # On regarde en combien de morceaux de 140 caractères le message doit être splitté
        multiple = len(messageDuTwitt)/140 +1
        #print ("multiple : " +  str(multiple))
        for i in range(0, multiple):

            # Deux cas : soit on a - de 140 caractères et on ne boucle pas

            print ("boucle "+str(i))
            #Si on n'est pas encore à la fin du message complet
            #print ("finChaineCourante " + str(finChaineCourante))
            #print("Longueur du messageDuTwitt " + str(len(messageDuTwitt)))

            # Si >140 caractère, on passe dans le if
            # et on va découper le message
            if finChaineCourante < len(messageDuTwitt):
                # Pour pouvoir ajouter un x/n à la fin du twitt, on se garde 3 caractères de marge
                finChaineCourante = finChaineCourante -3
                ajoutdeXsurN = True
                #Cas où finChaineCourante tombe dans un mot,
                # on repart en arrière jusqu'à l'espace précédent
                keepGoing = True
                #print("Ici " + messageDuTwitt[finChaineCourante -1:finChaineCourante])
                while keepGoing:
                    if messageDuTwitt[finChaineCourante -1].isspace() is False:
                        #print("ce n'est pas un espace")
                        #print(messageDuTwitt[finChaineCourante -1:finChaineCourante])
                        finChaineCourante=finChaineCourante -1
                    else:
                        #print("c'est un espace")
                        keepGoing = False
            # Fin du if
            if ajoutdeXsurN:
                messageSplitte = messageDuTwitt[debutChaineCourante:finChaineCourante]+ str(i+1)+"/"+str(multiple)
            else:
                messageSplitte = messageDuTwitt[debutChaineCourante:finChaineCourante]
            print("Partie + " + str(i) + " : "+ messageSplitte)
            #---------------------------------------"
            # Appel de l'API python pour avoir un twitt
            #---------------------------------------"
            api = Twython(CONSUMER_KEY,CONSUMER_SECRET,ACCESS_KEY,ACCESS_SECRET)
            api.update_status(status=messageSplitte)

            #---------------------------------------"
            # Intialisation des variables pour la boucle suivante
            #---------------------------------------"
            debutChaineCourante = finChaineCourante
            if finChaineCourante + 140 < len(messageDuTwitt):
                finChaineCourante = finChaineCourante + 140
            else:
                finChaineCourante = len(messageDuTwitt)
    except IOError, e:
        resultatFonction = e
    return resultatFonction

def RaccourcirURL(urlToShortened):
    '''
    Appel de l'API du raccourcisseur d'URL huit.re de Framasoft
    Pour une URL plus petite
    '''
    urlShortened = None
    url = "https://huit.re/a"
    #params = {"lsturl" : "http://genma.free.fr", "lsturl-custom" : "testJ1" , "format" : "json"}
    params = {"lsturl" : urlToShortened,  "format" : "json"}
    myResponse = requests.post(url, params=params)
    data = json.loads(myResponse.text)
    if data['success']:
    	urlShortened=data['short']
    return urlShortened

class BilletBlog(object):
    '''
    BilletBlog : classe qui definit un billet de blog
    par son titre et son URL
    utilisée dans la méthode DernierBilletDsRSSBlog
    '''
    titre = None
    url = None

def DernierBilletDsRSSBlog():
    ''' Recuperation du RSS, on parse pour ne récuper
        que le dernier article (titre et url)
    '''
    config = configparser.ConfigParser()
    config.read('Config.ini')
    # Bloc lié au blog / RSS
    configBlog = config['Blog']
    blog_rss = configBlog['filRSS']
    feeds = feedparser.parse(blog_rss)
    syndication_number = 1
    urlToShorten = None
    articleTitle= None
    for i in range(0, syndication_number):
    	urlToShorten = feeds.entries[i]['link']
    	articleTitle = feeds.entries[i]['title']
    # Creation d'un objet qui contient le titre et l'URL
    billetBlog = BilletBlog()
    billetBlog.titre = articleTitle
    billetBlog.url = urlToShorten
    return billetBlog

def CreationTwittDernierBilletDsRSSBlog():
    ''' Methode qui fait appel à DernierBilletDsRSSBlog
        Recuperation du RSS, on parse pour ne récuper
        que le dernier article (titre et url)
        On cree un bloc de texte qui sera le message du twitt
        Et on appelle l'API de twitter via la méthode EnvoiTwitt
    '''
    billetBlog = DernierBilletDsRSSBlog()
    titreBilletBlog = billetBlog.titre
    urlBilletBlog = billetBlog.url
    messageDuTwitt = "A lire sur le blog \"" + titreBilletBlog + "\" " + urlBilletBlog
    EnvoiTwitt(messageDuTwitt)
    return "Twitt géneré pr le dernier billet de blog"

def EnvoitMail(From, To, Subject, Message, ServeurSMTP, LoginSMTP, PasswordSMTP):
    '''Methode pour envoyer un mail
    Ca peut servir ;)
    Message = "Ceci est le message de mon mail que j'envoie via Python. \nGenma"
    Appel de la méthode :
    EnvoitMail('genma@free.fr', 'genma@free.fr', "Test de mail depuis python", Message,
                                        'smtp.free.fr', 'genma@free.fr',  'Password_A_Changer'))
    '''
    msg = MIMEMultipart()
    msg['From'] = From
    msg['To'] = To
    msg['Subject'] = Subject
    msg.attach(MIMEText(Message))
    mailserver = smtplib.SMTP(ServeurSMTP, 587)
    mailserver.ehlo()
    mailserver.starttls()
    mailserver.ehlo()
    mailserver.login(LoginSMTP, PasswordSMTP)
    mailserver.sendmail(From, To, msg.as_string())
    mailserver.quit()
    return "Mail envoyé"
	
# Liste des fichiers de façon récursive
def listdirectory(path, extension):  
    fichier=[]  
    for root, dirs, files in os.walk(path):  
        for file in files:
			if fnmatch.fnmatch(file,extension):
				fichier.append(os.path.join(root, file))
    return fichier

# Pour l'affichage ligne à ligne
def printTableau(table):
	for case in table:
		print (case)	