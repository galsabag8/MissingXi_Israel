import psycopg2
import json

def export_to_json():
    conn = psycopg2.connect(
        dbname="Top10Game",
        user="postgres",
        password="Sabigo11!!",
        host="localhost",
        port=5432
    )
    cur = conn.cursor()

    # Example: export players table
    cur.execute("SELECT * FROM teams;")
    cols = [desc[0] for desc in cur.description]
    data = [dict(zip(cols, row)) for row in cur.fetchall()]

    cur.close()
    conn.close()

    # Save to JSON file
    with open("teams.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("✅ Exported players.json")

if __name__ == "__main__":
    export_to_json()
