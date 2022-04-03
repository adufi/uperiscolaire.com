# uperiscolaire.com

Hello,
Bienvenue sur le site de la périscolaire de Saint-Joseph. C'est le premier site que j'ai développé pour l'UPEM. La première version a permis aux parents de pouvoir inscrire leur enfant mais également aux employés de récupérer leurs paiements en espèce et en chèque. Et la deuxième version a permis le paiement CB ainsi que le paiement en ligne.

## Installation

Pour l'installation vous aurez besoin de virtualenv ou venv.

```bash
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```
NOTE: Sur MacOS j'ai eu des soucis avec cairo, pillow et psycopg2. Psycopg2 peut s'installer avec pip de nouveau. Cairo et pillow avec brew.

Une fois l'installation du virtualenv terminé, il faut préparer le script pour les variables d'environnements.

Le site tourne initialement sur du PostgreSQL, mais devrait fonctionner également sur du SQLite.

```bash
touch scripts/.var.env.sh
```

TRES IMPORTANT: les fichiers finissants en '.env.sh' ne seront pas synchronisés pour des questions de sécurité.

Pour la [secret key...](https://djecrety.ir/).

```bash
#!/bin/bash

source venv/bin/activate

export DEBUG="1"

export SECRET_KEY=""

export DB_NAME_DEV="name_dev"
export DB_NAME_TEST="name_test"

export DB_USER=""
export DB_PASSWORD=""
export DB_PORT=""
export DB_HOST="127.0.0.1"

export EMAIL_USER=""
export EMAIL_PASSWORD=""
export EMAIL_HOST=""
export EMAIL_PORT=""
export EMAIL_USE_TLS="1"

export ROOT_URLCONF="project.urls"
export DJANGO_SETTINGS_MODULE="project.settings.dev"

export DJANGO_ALLOWED_HOSTS="localhost 127.0.0.1 192.168.1.XXX"
```

## Usage

Veillez à être dans l'environnement, puis à compiler les varibles.

```bash
python project/manage.py migrate
python project/manage.py createsuperuser
python project/manage.py runserver 0.0.0.0:8000
```
