# config-sample.py — Exemple de configuration pour gtgDroid
# ─────────────────────────────────────────────────────────────
# Copier ce fichier en config.py et remplir vos informations.
# Ne jamais committer config.py — il contient vos credentials.
#
# cp config-sample.py config.py

# URL de votre serveur CalDAV
# Nextcloud : https://votre-instance.example.com/remote.php/dav
# Format attendu : avec le /remote.php/dav/ final
URL = 'https://votre-nextcloud.example.com/remote.php/dav/'

# Nom d'utilisateur Nextcloud
USERNAME = 'votre_utilisateur'

# Mot de passe Nextcloud (ou mot de passe d'application recommandé)
# Générer un mot de passe d'application dans :
# Nextcloud → Paramètres → Sécurité → Appareils et sessions
PASSWORD = 'votre_mot_de_passe'

# Nom du calendrier CalDAV utilisé par GTG (ne pas modifier sauf cas particulier)
# GTG crée automatiquement un calendrier nommé 'gtg' lors de la première synchro
CALENDAR_NAME = 'gtg'
