from flask_sqlalchemy import SQLAlchemy
from typing import List

# On initialise l'objet db, qui sera lié à notre application Flask dans app.py
db = SQLAlchemy()

# ============================================================
# TABLES D'ASSOCIATION (Relations Many-to-Many)
# ============================================================

# Table pour lier les Membres et les Clubs (qui est membre de quel club)
club_membres = db.Table('club_membres',
    db.Column('membre_id', db.Integer, db.ForeignKey('membre.id'), primary_key=True),
    db.Column('club_id', db.Integer, db.ForeignKey('club.id'), primary_key=True)
)

# Table pour lier les Membres et les Événements (qui participe à quel événement)
event_membres = db.Table('event_membres',
    db.Column('membre_id', db.Integer, db.ForeignKey('membre.id'), primary_key=True),
    db.Column('evenement_id', db.Integer, db.ForeignKey('evenement.id'), primary_key=True)
)

# ============================================================
# CLASSE MEMBRE (ET PRESIDENT via Héritage)
# ============================================================

class Membre(db.Model):
    __tablename__ = 'membre'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Colonne pour l'héritage polymorphique (différencier un membre normal d'un président)
    type_membre = db.Column(db.String(50))
    
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    filiere = db.Column(db.String(100))
    telephone = db.Column(db.String(20))
    
    # Relations: un membre a plusieurs clubs (rejoints) et plusieurs événements (inscrits)
    clubs_rejoints = db.relationship('Club', secondary=club_membres, backref=db.backref('membres', lazy=True))
    evenements_inscrits = db.relationship('Evenement', secondary=event_membres, backref=db.backref('membres_inscrits', lazy=True))

    __mapper_args__ = {
        'polymorphic_identity': 'membre',
        'polymorphic_on': type_membre
    }

    def rejoindre_club(self, club: "Club"):
        if club not in self.clubs_rejoints:
            self.clubs_rejoints.append(club)

class President(Membre):
    __mapper_args__ = {
        'polymorphic_identity': 'president'
    }
    
    # Un président gère plusieurs clubs (relation One-to-Many)
    clubs_geres = db.relationship('Club', backref='president', lazy=True)

    def ajouter_evenement(self, club: "Club", evenement: "Evenement"):
        if club.president == self:
            club.evenements.append(evenement)

    def supprimer_membre(self, club: "Club", membre: Membre):
        if club.president == self and membre in club.membres:
            club.membres.remove(membre)

# ============================================================
# CLASSE CLUB
# ============================================================

class Club(db.Model):
    __tablename__ = 'club'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    categorie = db.Column(db.String(50))
    date_creation = db.Column(db.String(20))
    
    # Clé étrangère vers le président qui gère ce club
    president_id = db.Column(db.Integer, db.ForeignKey('membre.id'))
    
    # Un club a plusieurs événements
    evenements = db.relationship('Evenement', backref='club', cascade="all, delete-orphan", lazy=True)

    # Note: 'membres' est généré automatiquement par le backref dans la classe Membre.

# ============================================================
# CLASSE EVENEMENT
# ============================================================

class Evenement(db.Model):
    __tablename__ = 'evenement'
    
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(20))
    description = db.Column(db.Text)
    adhesion = db.Column(db.String(20))  # Gratuit / Payant
    termine = db.Column(db.Boolean, default=False)
    
    # Clé étrangère vers le club auquel l'événement appartient
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'))
    
    # Note: 'membres_inscrits' est généré automatiquement par le backref dans la classe Membre.

    def statut(self):
        return "Terminé" if self.termine else "En cours"
