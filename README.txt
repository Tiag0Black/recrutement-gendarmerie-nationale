PORTAIL DE RECRUTEMENT — GENDARMERIE RP
=======================================

Cette version utilise un vrai serveur Flask et une base SQLite.
Les candidatures sont partagées entre les visiteurs du site et l'équipe recrutement
lorsque le projet est installé sur un hébergement commun.

LANCEMENT EN LOCAL (Windows)
----------------------------
1. Installe Python 3.11 ou plus récent depuis https://www.python.org/downloads/
   Pendant l'installation, coche "Add Python to PATH".
2. Décompressez le ZIP dans un dossier.
3. Ouvrez un terminal dans ce dossier.
4. Installez les dépendances :
      py -m pip install -r requirements.txt
5. Définissez les variables d'environnement (PowerShell) :
      $env:SECRET_KEY = "remplacez-par-une-longue-cle-aleatoire"
      $env:ADMIN_USERNAME = "votre_identifiant"
      $env:ADMIN_PASSWORD = "choisissez-un-mot-de-passe-long-et-unique"
6. Lancez :
      py app.py
7. Ouvrez http://127.0.0.1:5000
   Connexion staff : http://127.0.0.1:5000/recrutement/connexion

IMPORTANT
---------
- Ne partagez jamais le mot de passe administrateur.
- Ne mettez pas de vrais renseignements personnels dans les candidatures RP.
- Pour rendre le site accessible à tout le serveur, il faut le déployer sur un
  hébergeur compatible Python/Flask avec stockage persistant.
- Configurez SECRET_KEY, ADMIN_USERNAME et ADMIN_PASSWORD dans les variables
  d'environnement de l'hébergeur, jamais dans le code.
- Activez HTTPS et définissez COOKIE_SECURE=1 en production.
- Conservez des sauvegardes régulières de applications.sqlite3.
- Cette application est un outil de roleplay, sans affiliation avec la
  Gendarmerie nationale.
- Ce ZIP n'est pas déjà publié sur Internet : il faut effectuer le déploiement.


DÉPLOIEMENT SUR RENDER
----------------------
- Root Directory : gendarmerie_rp_portal (si le dépôt contient le dossier parent)
- Build Command : pip install -r requirements.txt
- Start Command : gunicorn app:app
- Variables d'environnement à créer dans Render :
    SECRET_KEY = une longue clé aléatoire
    ADMIN_USERNAME = votre identifiant administrateur
    ADMIN_PASSWORD = un mot de passe long et unique
    COOKIE_SECURE = 1

Attention : SQLite stocke les candidatures dans applications.sqlite3.
Sur Render, configurez un disque persistant et adaptez DB_PATH pour le placer
dans le dossier de ce disque si vous souhaitez conserver les candidatures
après les redéploiements et redémarrages.
