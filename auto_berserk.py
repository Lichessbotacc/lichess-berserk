import berserk
import os
import time
import logging
from datetime import datetime

# Logging für GitHub Actions
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Lade API-Token aus Umgebungsvariablen
API_TOKEN = os.getenv("LICHESS_API_TOKEN")
if not API_TOKEN:
    logging.error("LICHESS_API_TOKEN nicht gesetzt! Bitte in GitHub Secrets konfigurieren.")
    raise ValueError("LICHESS_API_TOKEN nicht gesetzt!")

# Initialisiere Lichess-Client
session = berserk.TokenSession(API_TOKEN)
client = berserk.Client(session=session)

def main():
    logging.info("Starte Auto-Berserk-Script...")
    logging.warning("Automatisierte Aktionen auf Hauptaccounts können zu Lichess-Bans führen!")
    
    try:
        # Stream eingehende Ereignisse
        for event in client.board.stream_incoming_events():
            if event["type"] == "gameStart":
                game_id = event["game"]["id"]
                logging.info(f"Neue Partie gestartet: {game_id}")
                
                # Stream Spielstatus
                for state in client.board.stream_game_state(game_id):
                    if state["type"] == "gameFull":
                        # Ermittle deine Farbe und Gegner
                        my_username = client.account.get()["username"]
                        white_player = state["white"]["id"]
                        my_color = "white" if my_username == white_player else "black"
                        opponent_color = "black" if my_color == "white" else "white"
                        
                        # Prüfe, ob Gegner berserkt hat
                        opponent = state[opponent_color]
                        if opponent.get("berserk") and not opponent.get("spectator", True):
                            logging.info(f"Gegner hat in Partie {game_id} berserkt! Versuche zurückzuberserken...")
                            try:
                                client.board.go_berserk(game_id)
                                logging.info(f"Berserk aktiviert für Partie {game_id}")
                            except Exception as e:
                                logging.error(f"Fehler beim Berserk in Partie {game_id}: {e}")
                            break  # Beende Game-Stream nach Berserk
                    
                    elif state["type"] == "gameState":
                        # Prüfe, ob Spiel beendet
                        if state.get("status") != "started":
                            logging.info(f"Partie {game_id} beendet mit Status {state.get('status')}.")
                            break
                    
                    time.sleep(0.1)  # Vermeide API-Überlastung
    
    except Exception as e:
        logging.error(f"Fehler im Hauptprozess: {e}")
        raise  # Wirf Fehler, damit Workflow neu startet

if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            logging.error(f"Script-Absturz: {e}. Neustart in 10 Sekunden...")
            time.sleep(10)
