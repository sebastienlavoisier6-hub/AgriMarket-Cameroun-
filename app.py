import streamlit as st
import pandas as pd
import os
import uuid # NÉCESSAIRE POUR LES COMMENTAIRES
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="AgriMarket Cameroun", page_icon="🐟", layout="wide")

# --- 2. FICHIERS ---
FICHIER_DB = "journal_data.csv"
FICHIER_VENTES = "marche.csv"
FICHIER_USERS = "utilisateurs.csv"
FICHIER_DIAGNOSTIC = "diagnostic.csv"
# NOUVEAUX FICHIERS POUR LE SOCIAL
FICHIER_COMMENTS = "commentaires.csv"
FICHIER_NOTES = "notes.csv"
FICHIER_FAVORIS = "favoris.csv"

# --- 3. SESSION ---
if 'connecte' not in st.session_state:
    st.session_state['connecte'] = False
if 'role' not in st.session_state:
    st.session_state['role'] = None
if 'email' not in st.session_state:
    st.session_state['email'] = None

# --- 4. FONCTIONS INTELLIGENTES & UTILITAIRES ---

def charger_csv_social(fichier, colonnes):
    """Charge les fichiers sociaux sans casser le reste"""
    if not os.path.exists(fichier):
        df = pd.DataFrame(columns=colonnes)
        df.to_csv(fichier, index=False)
        return df
    try:
        return pd.read_csv(fichier, dtype=str)
    except:
        return pd.DataFrame(columns=colonnes)

def charger_users():
    if not os.path.exists(FICHIER_USERS):
        df = pd.DataFrame(columns=["Email", "Password", "Role", "Statut"])
        admin_default = pd.DataFrame({
            "Email": ["admin@agrimarket.cm"], 
            "Password": ["admin123"], 
            "Role": ["Administrateur"], 
            "Statut": ["Validé"]
        })
        df = pd.concat([df, admin_default], ignore_index=True)
        df.to_csv(FICHIER_USERS, index=False)
    
    try:
        df = pd.read_csv(FICHIER_USERS, dtype=str)
        df['Email'] = df['Email'].str.strip()
        df['Password'] = df['Password'].str.strip()
        return df
    except:
        return pd.DataFrame(columns=["Email", "Password", "Role", "Statut"])

def charger_donnees_journal():
    if not os.path.exists(FICHIER_DB):
        df = pd.DataFrame(columns=[
            "Date", "Heure", "Email_Eleveur", "pH", "Temperature", 
            "Ammoniac", "Oxygene", "Aliment_kg", 
            "Mortalite", "Alerte_Auto"
        ])
        df.to_csv(FICHIER_DB, index=False)
    return pd.read_csv(FICHIER_DB)

# --- ALGORITHME DE CERTIFICATION (VOTRE CODE) ---
def obtenir_badge_qualite(email_vendeur):
    df = charger_donnees_journal()
    df_vendeur = df[df['Email_Eleveur'] == email_vendeur]
    if df_vendeur.empty: return ""
    dernieres_mesures = df_vendeur.tail(3)
    problemes = dernieres_mesures['Alerte_Auto'].str.contains("DANGER|Attention", case=False, na=False)
    if problemes.any(): return ""
    else: return "🏅 Éleveur Certifié AgriMarket"

# --- ALGORITHME DE NOTATION (NOUVEAU) ---
def calculer_moyenne_etoiles(id_offre):
    df_notes = charger_csv_social(FICHIER_NOTES, ["ID_Offre", "Note"])
    notes_offre = pd.to_numeric(df_notes[df_notes['ID_Offre'] == id_offre]['Note'], errors='coerce')
    if notes_offre.empty: return 0, 0
    return round(notes_offre.mean(), 1), len(notes_offre)

def analyser_normes(ph, amm, oxy):
    alertes = []
    if ph < 6.0: alertes.append("🔴 DANGER : pH trop ACIDE (< 6.0)")
    elif ph > 9.0: alertes.append("🔴 DANGER : pH trop BASIQUE (> 9.0)")
    elif 6.0 <= ph < 6.5: alertes.append("🟠 Attention : pH un peu bas")
    elif 8.5 < ph <= 9.0: alertes.append("🟠 Attention : pH un peu élevé")
        
    if amm > 0.05: alertes.append("🔴 DANGER : Ammoniac (> 0.05)")
    elif 0.02 <= amm <= 0.05: alertes.append("🟠 Attention : Ammoniac en hausse")
        
    if oxy < 3: alertes.append("🔴 DANGER : Manque d'Oxygène (< 3mg/L)")
    elif 3 <= oxy < 5: alertes.append("🟠 Attention : Oxygène faible")
        
    if not alertes: return "✅ RAS (Paramètres Optimaux)"
    else: return " | ".join(alertes)

# --- 5. PAGE LOGIN ---
def login_page():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.title("🔐 AgriMarket Cameroun")
        tab1, tab2 = st.tabs(["Se Connecter", "S'inscrire"])
        
        with tab2:
            with st.form("inscription"):
                new_email = st.text_input("Votre Email")
                new_pass = st.text_input("Votre Mot de passe", type="password")
                new_role = st.selectbox("Vous êtes ?", ["Éleveur (Vendeur)", "Client (Acheteur)"])
                if st.form_submit_button("Envoyer demande"):
                    df_users = charger_users()
                    if new_email.strip() in df_users['Email'].values:
                        st.error("Email déjà pris.")
                    else:
                        new_user = pd.DataFrame({
                            "Email": [new_email.strip()], 
                            "Password": [new_pass.strip()], 
                            "Role": [new_role],
                            "Statut": ["En attente"]
                        })
                        new_user.to_csv(FICHIER_USERS, mode='a', header=False, index=False)
                        st.success("✅ Inscrit ! Attente validation.")

        with tab1:
            email_input = st.text_input("Email")
            pass_input = st.text_input("Mot de passe", type="password")
            if st.button("Se connecter", type="primary"):
                df = charger_users()
                user = df[(df['Email'] == email_input.strip()) & (df['Password'] == pass_input.strip())]
                if not user.empty:
                    if user.iloc[0]['Statut'] == "Validé":
                        st.session_state['connecte'] = True
                        st.session_state['email'] = email_input.strip()
                        st.session_state['role'] = user.iloc[0]['Role']
                        st.rerun()
                    else:
                        st.warning("⏳ Compte en attente.")
                else:
                    st.error("❌ Erreur connexion.")

# --- 6. ADMIN ---
def admin_interface():
    st.header("🛡️ Administration")
    df_users = charger_users()
    attente = df_users[df_users['Statut'] == "En attente"]
    if not attente.empty:
        st.warning(f"{len(attente)} demande(s)")
        with st.form("valid"):
            target = st.selectbox("Qui valider ?", attente['Email'].unique())
            if st.form_submit_button("Valider"):
                df_users.loc[df_users['Email'] == target, 'Statut'] = "Validé"
                df_users.to_csv(FICHIER_USERS, index=False)
                st.rerun()
    st.dataframe(df_users)

# --- 7. APP PRINCIPALE ---
def main_app():
    role = st.session_state['role']
    email_user = st.session_state['email']
    
    st.sidebar.title("🌿 AgriMarket")
    st.sidebar.caption(f"Connecté: {email_user}")
    
    # CALCUL DU BADGE PERSONNEL
    mon_badge = obtenir_badge_qualite(email_user)
    if mon_badge:
        st.sidebar.success(f"{mon_badge}")
    
    options = ["🚪 Déconnexion"]
    if role == "Administrateur":
        options.insert(0, "🛡️ Administration")
    elif role == "Client (Acheteur)":
        # AJOUT MENU FAVORIS
        options = ["💰 Marché (Achat)", "❤️ Mes Favoris"] + options
    else:
        # AJOUT MENU FAVORIS POUR ÉLEVEUR AUSSI
        options = ["📝 Mon Journal", "📊 Analyse", "🏥 Diagnostic", "📢 Ma Boutique", "💰 Marché (Achat)", "❤️ Mes Favoris"] + options
        
    menu = st.sidebar.radio("Menu", options)
    
    if menu == "🚪 Déconnexion":
        st.session_state['connecte'] = False
        st.rerun()
    elif menu == "🛡️ Administration":
        admin_interface()

    # --- JOURNAL ---
    elif menu == "📝 Mon Journal":
        st.header("📝 Saisie Journalière")
        st.info("Des mesures régulières et saines vous donneront le Badge 'Certifié' sur le marché !")
        
        with st.form("journal"):
            c1, c2 = st.columns(2)
            with c1:
                date = st.date_input("Date")
                heure = st.time_input("Heure")
                ph = st.number_input("pH", 0.0, 14.0, 7.0)
                temp = st.number_input("Temp °C", 10.0, 40.0, 26.0)
            with c2:
                amm = st.number_input("Ammoniac", 0.00, 5.00, 0.00)
                oxy = st.number_input("Oxygène", 0.0, 20.0, 6.0)
                alim = st.number_input("Aliment (kg)", 0.0, 500.0, 0.0)
                morts = st.number_input("Morts", 0, 1000, 0)
            
            if st.form_submit_button("Enregistrer"):
                diag = analyser_normes(ph, amm, oxy)
                if "DANGER" in diag: st.error(diag)
                elif "Attention" in diag: st.warning(diag)
                else: st.success(diag)
                
                new_row = pd.DataFrame({
                    "Date": [date], "Heure": [heure], 
                    "Email_Eleveur": [email_user],
                    "pH": [ph], "Temperature": [temp], "Ammoniac": [amm], 
                    "Oxygene": [oxy], "Aliment_kg": [alim], 
                    "Mortalite": [morts], "Alerte_Auto": [diag]
                })
                df_old = charger_donnees_journal()
                pd.concat([df_old, new_row], ignore_index=True).to_csv(FICHIER_DB, index=False)
                st.rerun()

    # --- ANALYSE ---
    elif menu == "📊 Analyse":
        st.header("📊 Historique")
        df = charger_donnees_journal()
        mes_donnees = df[df['Email_Eleveur'] == email_user]
        
        if not mes_donnees.empty:
            st.dataframe(mes_donnees.tail(10))
            st.line_chart(mes_donnees, x="Date", y="pH")
        else:
            st.info("Aucune donnée saisie.")

    # --- DIAGNOSTIC ---
    elif menu == "🏥 Diagnostic":
        st.header("🏥 Docteur Poisson")
        if os.path.exists(FICHIER_DIAGNOSTIC):
            try:
                df = pd.read_csv(FICHIER_DIAGNOSTIC)
                c = st.selectbox("Catégorie", df['Categorie'].unique())
                s = st.selectbox("Symptôme", df[df['Categorie']==c]['Symptome'].unique())
                res = df[df['Symptome']==s].iloc[0]
                st.error(f"Cause : {res['Cause']}")
                st.success(f"Solution : {res['Solution']}")
            except: st.error("Erreur fichier diagnostic")

    # --- BOUTIQUE (VOS COLONNES EXACTES + ID CACHÉ) ---
    elif menu == "📢 Ma Boutique":
        st.header("📢 Vendre sur le Marché")
        if mon_badge:
            st.success(f"✨ Excellente nouvelle ! Vos annonces afficheront le badge : **{mon_badge}**")
        else:
            st.warning("Conseil : Remplissez votre journal régulièrement sans alertes pour obtenir le Badge Certifié.")
            
        with st.form("form_boutique"):
            colA, colB = st.columns(2)
            with colA:
                date_dispo = st.date_input("📅 Date Disponibilité")
                ville = st.text_input("📍 Ville / Quartier")
                espece = st.selectbox("🐟 Espèce", ["Silure (Clarias)", "Tilapia", "Carpe", "Autre"])
                calibrage = st.text_input("⚖️ Calibrage", placeholder="Ex: 500g")
            with colB:
                qte = st.number_input("📦 Quantité (kg)", 1, 10000, 100)
                prix = st.number_input("💰 Prix / KG", 100, 10000, 2500)
                livraison = st.radio("🚚 Livraison ?", ["Oui", "Non"], horizontal=True)
                contact = st.text_input("📞 Tél", placeholder="699...")
            
            if st.form_submit_button("📢 Mettre en vente"):
                # GÉNÉRATION ID UNIQUE POUR COMMENTAIRES
                offre_id = str(uuid.uuid4())
                
                new_offer = pd.DataFrame({
                    "ID": [offre_id], # Colonne technique ajoutée
                    "Date_Dispo": [date_dispo], "Ville_Quartier": [ville],
                    "Espece": [espece], "Poids_Moyen": [calibrage],
                    "Quantite_Totale": [qte], "Prix_KG": [prix],
                    "Livraison": [livraison], "Contact": [contact],
                    "Vendeur_Email": [email_user]
                })
                header_mode = not os.path.exists(FICHIER_VENTES)
                new_offer.to_csv(FICHIER_VENTES, mode='a', header=header_mode, index=False)
                st.success("✅ Offre publiée !")

    # --- MARCHÉ (VOS COLONNES + FONCTIONS SOCIALES) ---
    elif menu == "💰 Marché (Achat)":
        st.header("🛒 Le Marché Certifié")
        
        # On vérifie si le fichier existe ET s'il a une colonne ID
        if os.path.exists(FICHIER_VENTES):
            df = pd.read_csv(FICHIER_VENTES)
            if df.empty:
                st.info("Aucune offre.")
            elif "ID" not in df.columns:
                st.error("⚠️ Ancien format détecté. Veuillez supprimer 'marche.csv' et recréer une annonce.")
            else:
                for index, row in df.iterrows():
                    vendeur = row['Vendeur_Email']
                    badge = obtenir_badge_qualite(vendeur)
                    offre_id = row['ID']
                    moyenne, nb_votes = calculer_moyenne_etoiles(offre_id)
                    
                    with st.container():
                        # TITRE AVEC BADGE
                        if badge:
                            st.markdown(f"### 🐟 {row['Espece']} {badge}")
                        else:
                            st.markdown(f"### 🐟 {row['Espece']}")
                            
                        st.markdown(f"**Prix : {row['Prix_KG']} FCFA / kg**")
                        
                        # VOS COLONNES
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            st.write(f"📅 Dispo: {row['Date_Dispo']}")
                            st.write(f"📍 Lieu: {row['Ville_Quartier']}")
                        with c2:
                            st.write(f"📦 Stock: {row['Quantite_Totale']} kg")
                            st.write(f"⚖️ Calibrage: {row['Poids_Moyen']}")
                        with c3:
                            st.write(f"📞 **{row['Contact']}**")
                            st.write(f"⭐ Avis: {moyenne} ({nb_votes})")
                        
                        # --- FONCTIONNALITÉS SOCIALES ---
                        with st.expander("💬 Commenter / ❤️ Sauvegarder"):
                            col_actions = st.columns([1, 2])
                            
                            # 1. FAVORIS
                            with col_actions[0]:
                                if st.button("❤️ Favoris", key=f"fav_{offre_id}"):
                                    df_fav = charger_csv_social(FICHIER_FAVORIS, ["Client", "ID_Offre"])
                                    if not ((df_fav['Client'] == email_user) & (df_fav['ID_Offre'] == offre_id)).any():
                                        new_fav = pd.DataFrame([[email_user, offre_id]], columns=["Client", "ID_Offre"])
                                        pd.concat([df_fav, new_fav], ignore_index=True).to_csv(FICHIER_FAVORIS, index=False)
                                        st.toast("Ajouté aux favoris !", icon="❤️")
                                    else:
                                        st.toast("Déjà en favori.")

                            # 2. NOTES ET COMMENTAIRES
                            with col_actions[1]:
                                with st.form(f"rate_{offre_id}"):
                                    note = st.slider("Note", 1, 5, 5)
                                    avis = st.text_input("Commentaire")
                                    if st.form_submit_button("Envoyer avis"):
                                        # Note
                                        df_notes = charger_csv_social(FICHIER_NOTES, ["ID_Offre", "Client", "Note"])
                                        new_note = pd.DataFrame([[offre_id, email_user, note]], columns=["ID_Offre", "Client", "Note"])
                                        pd.concat([df_notes, new_note], ignore_index=True).to_csv(FICHIER_NOTES, index=False)
                                        # Commentaire
                                        if avis:
                                            df_com = charger_csv_social(FICHIER_COMMENTS, ["ID_Offre", "Client", "Texte", "Date"])
                                            new_com = pd.DataFrame([[offre_id, email_user, avis, datetime.now()]], columns=df_com.columns)
                                            pd.concat([df_com, new_com], ignore_index=True).to_csv(FICHIER_COMMENTS, index=False)
                                        st.success("Merci !")
                                        st.rerun()

                        # Lecture des commentaires
                        df_all_comments = charger_csv_social(FICHIER_COMMENTS, ["ID_Offre", "Client", "Texte", "Date"])
                        com_offre = df_all_comments[df_all_comments['ID_Offre'] == offre_id]
                        if not com_offre.empty:
                            st.caption("Derniers avis :")
                            for _, com in com_offre.tail(2).iterrows():
                                st.text(f"👤 {com['Client']}: {com['Texte']}")

                        st.divider()
        else:
            st.info("Marché vide.")

    # --- NOUVEAU MENU : MES FAVORIS ---
    elif menu == "❤️ Mes Favoris":
        st.header("❤️ Mes Offres Sauvegardées")
        df_fav = charger_csv_social(FICHIER_FAVORIS, ["Client", "ID_Offre"])
        mes_fav_ids = df_fav[df_fav['Client'] == email_user]['ID_Offre'].tolist()
        
        if not mes_fav_ids:
            st.info("Aucun favori pour l'instant.")
        else:
            if os.path.exists(FICHIER_VENTES):
                df_ventes = pd.read_csv(FICHIER_VENTES)
                # On filtre les offres qui sont dans mes favoris
                mes_offres = df_ventes[df_ventes['ID'].isin(mes_fav_ids)]
                
                if mes_offres.empty:
                    st.warning("Vos offres favorites ne sont plus disponibles.")
                else:
                    st.dataframe(mes_offres[['Espece', 'Prix_KG', 'Ville_Quartier', 'Contact']])

# --- 8. LANCEMENT ---
if st.session_state['connecte']:
    main_app()
else:
    login_page()