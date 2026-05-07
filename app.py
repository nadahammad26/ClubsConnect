import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, Membre, President, Club, Evenement

app = Flask(__name__)
app.secret_key = "super_secret_key_pour_les_sessions"

# Configuration de la base de données SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'clubconnect.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialisation de la base de données avec l'application Flask
db.init_app(app)

# ============================================================
# INITIALISATION DES DONNÉES DE DÉMONSTRATION (Si DB vide)
# ============================================================
def init_db():
    with app.app_context():
        db.create_all()
        # On vérifie si la base est vide
        if not President.query.first():
            print("Initialisation de la base de données avec les données de démo...")
            
            # Création de présidents
            pres1 = President(nom="Dupont", prenom="Jean", email="jean.dupont@email.com", password="pass123", filiere="Informatique", telephone="0601020304")
            pres2 = President(nom="Martin", prenom="Sophie", email="sophie.martin@email.com", password="pass456", filiere="Marketing", telephone="0605060708")
            
            db.session.add(pres1)
            db.session.add(pres2)
            db.session.commit() # Commit pour avoir les IDs générés

            # Création de clubs
            club_info = Club(nom="Club Informatique", description="Le club pour les passionnés de code.", categorie="Tech", date_creation="2023-09-01", president=pres1)
            club_bde = Club(nom="BDE", description="Bureau des étudiants.", categorie="Vie associative", date_creation="2020-09-01", president=pres2)
            
            # Le président est automatiquement membre de son club
            club_info.membres.append(pres1)
            club_bde.membres.append(pres2)
            
            db.session.add(club_info)
            db.session.add(club_bde)

            # Création d'événements
            event1 = Evenement(titre="Hackathon 2024", date="2024-05-15", description="Un hackathon de 48h.", adhesion="Gratuit", club=club_info)
            db.session.add(event1)

            # Création de membres standards
            membre1 = Membre(nom="Bernard", prenom="Luc", email="luc.bernard@email.com", password="mdp1", filiere="Informatique", telephone="0701020304")
            membre2 = Membre(nom="Dubois", prenom="Marie", email="marie.dubois@email.com", password="mdp2", filiere="Design", telephone="0705060708")
            
            db.session.add(membre1)
            db.session.add(membre2)
            
            # Ajout des membres au club info
            club_info.membres.append(membre1)
            club_info.membres.append(membre2)
            
            db.session.commit()
            print("Données de démo injectées avec succès !")

# Appel manuel pour créer les tables au premier lancement
init_db()

# ============================================================
# ROUTES (PAGES WEB)
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
        
        # Requête dans la base de données
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
        
        # Vérifier si l'email existe déjà
        if Membre.query.filter_by(email=email).first():
            flash("Cet email est déjà utilisé.", "danger")
            return redirect(url_for('register'))
        
        nouveau_membre = Membre(nom=nom, prenom=prenom, email=email, password=password, filiere=filiere, telephone=telephone)
        db.session.add(nouveau_membre)
        db.session.commit()
        
        flash("Compte créé avec succès ! Vous pouvez maintenant vous connecter.", "success")
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/club/<int:club_id>/join', methods=['POST'])
def join_club(club_id):
    if 'user_id' not in session:
        flash("Vous devez être connecté pour rejoindre un club.", "danger")
        return redirect(url_for('login'))
        
    club = db.session.get(Club, club_id)
    user = db.session.get(Membre, session['user_id'])
    
    if club and user:
        if user not in club.membres:
            club.membres.append(user)
            db.session.commit()
            flash(f"Vous avez rejoint le {club.nom} !", "success")
        else:
            flash("Vous êtes déjà membre de ce club.", "info")
            
    return redirect(url_for('voir_club', club_id=club_id))

@app.route('/club/<int:club_id>/add_event', methods=['POST'])
def add_event(club_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    club = db.session.get(Club, club_id)
    # Vérification que l'utilisateur est bien le président du club
    if club and club.president_id == session['user_id']:
        titre = request.form.get('titre')
        date = request.form.get('date')
        description = request.form.get('description')
        adhesion = request.form.get('adhesion')
        
        nouvel_evenement = Evenement(titre=titre, date=date, description=description, adhesion=adhesion, club=club)
        db.session.add(nouvel_evenement)
        db.session.commit()
        
        flash("Événement ajouté avec succès.", "success")
    else:
        flash("Action non autorisée.", "danger")
        
    return redirect(url_for('voir_club', club_id=club_id))

@app.route('/club/<int:club_id>/remove_member/<int:membre_id>', methods=['POST'])
def remove_member(club_id, membre_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    club = db.session.get(Club, club_id)
    if club and club.president_id == session['user_id']:
        membre_a_supprimer = db.session.get(Membre, membre_id)
        if membre_a_supprimer and membre_a_supprimer in club.membres:
            club.membres.remove(membre_a_supprimer)
            db.session.commit()
            flash(f"Le membre {membre_a_supprimer.prenom} a été retiré.", "success")
    
    return redirect(url_for('voir_club', club_id=club_id))

@app.route('/logout')
def logout():
    session.clear()
    flash("Vous êtes déconnecté.", "info")
    return redirect(url_for('index'))

if __name__ == "__main__":
    # Railway donne un port dynamique, on doit le récupérer ici
    port = int(os.environ.get("PORT", 5000))
    # On dit à Flask d'écouter sur l'hôte 0.0.0.0 pour être accessible en ligne
    app.run(host="0.0.0.0", port=port)
