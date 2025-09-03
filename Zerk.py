import berserk
import os
import time

# Lichess API-Token aus Umgebungsvariablen
API_TOKEN = os.getenv("LICHESS_API_TOKEN")

# Initialisiere den Lichess-Client
session = berserk.TokenSession(API_TOKEN)
client = berserk.Client(session=session)

# Hauptlogik des Skripts
def main():
    print("Monitoring for new games...")
    
    # Stream eingehende Ereignisse
    for event in client.board.stream_incoming_events():
        if event["type"] == "gameStart":
            game_id = event["game"]["id"]
            print(f"Game started: {game_id}")

            # Stream den Spielstatus
            for state in client.board.stream_game_state(game_id):
                if state.get("status") != "started":
                    print(f"Game {game_id} ended.")
                    break

                # Überprüfe, ob der Gegner berserkt hat
                is_opponent_berserk = (
                    state.get("wtime") == state.get("btime")  # Zeit ist gleich, wenn berserkt
                    and state.get("wtime") is not None
                    and state.get("moves") == ""  # Nur zu Spielbeginn prüfen
                )

                if is_opponent_berserk:
                    try:
                        client.board.go_berserk(game_id)
                        print(f"Berserk activated for game {game_id} because opponent berserked!")
                    except Exception as e:
                        print(f"Failed to berserk in game {game_id}: {e}")

                # Warte kurz, um die API nicht zu überlasten
                time.sleep(0.5)

if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)  # Warte 10 Sekunden vor Neustart
