import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import psycopg


HOST = "0.0.0.0"
PORT = 5000

MESSAGE = os.getenv("MESSAGE", "Hello from Docker!")

DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "dockerlab")
DB_USER = os.getenv("DB_USER", "dockeruser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "dockerpassword")


def get_connection():
    return psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def initialize_database():
    for attempt in range(10):
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS lab_data (
                            id SERIAL PRIMARY KEY,
                            message TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                conn.commit()

            print("Connected to PostgreSQL.")
            return

        except Exception as error:
            print(f"Database connection failed: {error}")
            print(f"Retrying... ({attempt + 1}/10)")
            time.sleep(2)

    raise RuntimeError("Could not connect to PostgreSQL.")


class APIHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        # Liveness health check
        if self.path == "/health":

            body = '{"status": "healthy"}'

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body.encode())))
            self.end_headers()

            self.wfile.write(body.encode())

        # Home endpoint
        elif self.path == "/":

            body = MESSAGE

            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body.encode())))
            self.end_headers()

            self.wfile.write(body.encode())

        # Database endpoint
        elif self.path == "/db":

            try:
                with get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT id, message, created_at
                            FROM lab_data
                            ORDER BY id
                        """)

                        rows = cur.fetchall()

                body = "\n".join(
                    f"id={row[0]} | message={row[1]} | created_at={row[2]}"
                    for row in rows
                )

                if not body:
                    body = "Database connected, but lab_data is empty."

                self.send_response(200)

            except Exception as error:

                body = f"Database error: {error}"

                self.send_response(500)

            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body.encode())))
            self.end_headers()

            self.wfile.write(body.encode())

        # Unknown endpoint
        else:

            body = "Not Found"

            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body.encode())))
            self.end_headers()

            self.wfile.write(body.encode())

    def log_message(self, format, *args):
        print(f"{self.address_string()} - {format % args}")


initialize_database()

server = HTTPServer((HOST, PORT), APIHandler)

print(f"API listening on {HOST}:{PORT}")
print(f"Database host: {DB_HOST}:{DB_PORT}")

server.serve_forever()
