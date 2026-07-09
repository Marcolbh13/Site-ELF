# Mise en ligne du site sur OVH

Le site est 100 % statique (HTML, CSS, JavaScript). Aucune base de données, aucun langage serveur : il fonctionne tel quel sur un hébergement mutualisé OVH.

## 1. Fichiers à téléverser

Tout le contenu du dépôt sauf les dossiers et fichiers techniques :

- `index.html`, `materiel.html`, `services.html`, `groupe.html`, `contact.html`, `mentions-legales.html`, `404.html`
- `robots.txt`, `sitemap.xml`, `.htaccess`
- le dossier `assets/` complet (css, js, fonts, img)

Ne pas téléverser : `.github/`, `DEPLOIEMENT-OVH.md`, `.git/`.

## 2. Téléversement

1. Dans l'espace client OVH, section Hébergements, récupérer les identifiants FTP ou SFTP.
2. Avec FileZilla (ou équivalent), se connecter et déposer les fichiers dans le dossier `www/`.
3. Vérifier que `index.html` est bien à la racine de `www/`.

## 3. Domaine et HTTPS

1. Associer le domaine (multisite) au dossier `www/` dans l'espace client.
2. Activer le certificat SSL Let's Encrypt (gratuit, inclus chez OVH).
3. Le fichier `.htaccess` redirige déjà automatiquement vers HTTPS et vers le domaine avec www.

Si le domaine définitif n'est pas `www.elf-environnement.fr`, remplacer cette adresse dans :
- les balises `canonical`, `og:url` et `og:image` de chaque page HTML,
- `sitemap.xml` et `robots.txt`,
- la règle de redirection www du fichier `.htaccess`.

## 4. Adresse email de contact

Le formulaire de contact ouvre le logiciel de messagerie du visiteur vers `contact@elf-environnement.fr` (attribut `data-dest` dans `contact.html`). Créer cette adresse dans l'espace client OVH (section Emails) ou remplacer par l'adresse souhaitée dans `contact.html` (deux occurrences) et dans les pieds de page.

## 5. Référencement

1. Déclarer le site dans la Google Search Console et soumettre `sitemap.xml`.
2. Créer la fiche Google Business Profile (adresse : 5031 chemin de Phalempin, 59273 Fretin) et pointer vers le site.
3. Pistes d'évolution SEO : créer des pages d'atterrissage dédiées par famille de matériel (location foreuse dirigée, location mini pelle électrique, location matériel TP Lille) pour viser les requêtes les plus recherchées.

## 6. Évolutions prévues côté images

Les visuels du matériel proviennent des médias officiels des constructeurs (pages produit publiques). Pour un rendu encore plus personnel, remplacer progressivement par des photos de vos propres machines et chantiers : mêmes noms de fichiers dans `assets/img/machines/`, aucune modification de code nécessaire.
