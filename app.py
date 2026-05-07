import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, Membre, President, Club, Evenement

app = Flask(__name__)
app.secret_key = "super_secret_key_pour_les_sessions"

# ============================================================
# CONFIGURATION DE LA BASE DE DONNÉES (RAILWAY + LOCAL)
# ============================================================
# Récupère l'URL de la base de données de Railway
database_url = os.getenv("DATABASE_URL")

# Correction obligatoire pour SQLAlchemy (Postgres -> PostgreSQL)
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# Si on est sur Railway, on utilise Postgres. Sinon, on utilise SQLite en local.
app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'clubconnect.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialisation de la base de données
db.init_app(app)

# ============================================================
# INITIALISATION DES DONNÉES DE DÉMONSTRATION
# ============================================================
def init_db():
    with app.app_context():
        db.create_all()
        if not President.query.first():
            print("Initialisation de la base de données...")
            pres1 = President(nom="Dupont", prenom="Jean", email="jean.dupont@email.com", password="pass123", filiere="Informatique", telephone="0601020304")
            pres2 = President(nom="Martin", prenom="Sophie", email="sophie.martin@email.com", password="pass456", filiere="Marketing", telephone="0605060708")
            db.session.add(pres1)
            db.session.add(pres2)
            db.session.commit()

            club_info = Club(nom="Club Informatique", description="Passionnés de code.", categorie="Tech", date_creation="2023-09-01", president=pres1)
            club_bde = Club(nom="BDE", description="Bureau des étudiants.", categorie="Vie associative", date_creation="2020-09-01", president=pres2)
            db.session.add(club_info)
            db.session.add(club_bde)
            db.session.commit()

init_db()

# ============================================================
# ROUTES (TON BACKEND)
# ============================================================

@app.route('/')
def index():
    user = session.get('user_email')
    clubs = Club.query.all()
    return render_template('index.html', clubs=clubs, user=user)

@app.route('/club/<int:club_id>')
def voir_club(club_id):
    club = db.session.get(Club, club_id)
    if not club:
        return "Club non trouvé", 404
    return render_template('club.html', club=club)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = Membre.query.filter_by(email=email, password=password).first()
        if user:
            session['user_email'] = user.email
            session['user_nom'] = f"{user.prenom} {user.nom}"
            session['user_id'] = user.id
            flash("Connexion réussie !", "success")
            return redirect(url_for('index'))
        else:
            flash("Email ou mot de passe incorrect.", "danger")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nom = request.form.get('nom')
        prenom = request.form.get('prenom')
        email = request.form.get('email')
        password = request.form.get('password')
        filiere = request.form.get('filiere')
        telephone = request.form.get('telephone')
        
        if Membre.query.filter_by(email=email).first():
            flash("Cet email est déjà utilisé.", "danger")
            return redirect(url_for('register'))
        
        nouveau_membre = Membre(nom=nom, prenom=prenom, email=email, password=password, filiere=filiere, telephone=telephone)
        db.session.add(nouveau_membre)
        db.session.commit()
        flash("Compte créé avec succès !", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/club/<int:club_id>/join', methods=['POST'])
def join_club(club_id):
    if 'user_id' not in session:
        flash("Connectez-vous pour rejoindre un club.", "danger")
        return redirect(url_for('login'))
    club = db.session.get(Club, club_id)
    user = db.session.get(Membre, session['user_id'])
    if club and user and user not in club.membres:
        club.membres.append(user)
        db.session.commit()
        flash(f"Vous avez rejoint {club.nom} !", "success")
    return redirect(url_for('voir_club', club_id=club_id))

@app.route('/logout')
def logout():
    session.clear()
    flash("Vous êtes déconnecté.", "info")
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Sur Railway, le port est dynamique
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
