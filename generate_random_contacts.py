import pymysql
from faker import Faker
from config import Config

fake = Faker()

# Verbindung zur Datenbank herstellen
def get_db_connection():
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

# 100 zufällige Einträge generieren und einfügen
def generate_random_contacts(num_entries=100):
    connection = get_db_connection()
    with connection.cursor() as cursor:
        for _ in range(num_entries):
            name = fake.name()
            phone = fake.phone_number()[:15]  # Beschränke die Länge auf maximal 15 Zeichen
            email = fake.email()
            address = fake.address().replace("\n", ", ")  # Ersetze Zeilenumbrüche durch Kommas

            # SQL-Befehl zum Einfügen
            cursor.execute(
                "INSERT INTO contacts (name, phone, email, address) VALUES (%s, %s, %s, %s)",
                (name, phone, email, address)
            )

        connection.commit()
    connection.close()
    print(f"{num_entries} zufällige Kontakte wurden erfolgreich in die Datenbank eingefügt.")

# Skript ausführen
if __name__ == "__main__":
    generate_random_contacts()
