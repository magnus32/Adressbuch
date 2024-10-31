from flask import Flask, request, render_template, redirect, url_for, flash
from markupsafe import Markup
import pymysql
import re
from config import Config
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

# Datenbankverbindung herstellen
def get_db_connection():
    connection = pymysql.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB'],
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection

app.secret_key = 'dein_geheimer_schlüssel'  # Für Flash-Nachrichten (Meldungen nach Aktionen)

# Highlight-Funktion definieren und als Jinja2-Filter hinzufügen
def highlight_search(text, search_query):
    if not search_query:
        return text

    highlighted_text = re.sub(
        f"({re.escape(search_query)})",
        r"<mark>\1</mark>",
        text,
        flags=re.IGNORECASE
    )
    return Markup(highlighted_text)

# Funktion zum Formatieren des Datums
def format_date(value):
    if isinstance(value, datetime):
        return value.strftime('%d.%m.%Y')
    return value

# Funktion zum Formatieren des Datums für datetime-local Eingabefeld
def format_datetime_local(value):
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%dT%H:%M')
    return value

# Filter registrieren
app.jinja_env.filters['format_date'] = format_date
app.jinja_env.filters['format_datetime_local'] = format_datetime_local

@app.route('/add_contact', methods=['GET', 'POST'])
def add_contact():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        address = request.form['address']
        
        connection = get_db_connection()
        with connection.cursor() as cur:
            cur.execute(
                "INSERT INTO contacts (name, phone, email, address) VALUES (%s, %s, %s, %s)",
                (name, phone, email, address)
            )
            connection.commit()
        connection.close()
        flash("Kontakt erfolgreich hinzugefügt.")
        return redirect(url_for('get_contacts', sort_by=request.args.get('sort_by'), sort_order=request.args.get('sort_order'), search=request.args.get('search')))
    return render_template('add_contact.html', title='Neuen Kontakt hinzufügen')


@app.route('/edit_contact/<int:id>', methods=['GET', 'POST'])
def edit_contact(id):
    connection = get_db_connection()
    
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        address = request.form['address']

        with connection.cursor() as cur:
            cur.execute(
                "UPDATE contacts SET name=%s, phone=%s, email=%s, address=%s WHERE id=%s",
                (name, phone, email, address, id)
            )
            connection.commit()
        connection.close()
        flash("Kontakt erfolgreich aktualisiert.")
        return redirect(url_for('get_contacts', sort_by=request.args.get('sort_by'), sort_order=request.args.get('sort_order'), search=request.args.get('search')))
    
    with connection.cursor() as cur:
        cur.execute("SELECT * FROM contacts WHERE id=%s", (id,))
        contact = cur.fetchone()
    connection.close()
    return render_template('edit_contact.html', contact=contact, title='Kontakt bearbeiten', sort_by=request.args.get('sort_by'), sort_order=request.args.get('sort_order'), search=request.args.get('search'))

@app.route('/delete_contact/<int:id>', methods=['POST'])
def delete_contact(id):
    connection = get_db_connection()
    with connection.cursor() as cur:
        cur.execute("DELETE FROM contacts WHERE id=%s", (id,))
        connection.commit()
    connection.close()
    flash("Kontakt erfolgreich gelöscht.")
    return redirect(url_for('get_contacts', sort_by=request.args.get('sort_by'), sort_order=request.args.get('sort_order'), search=request.args.get('search')))

@app.route('/')
def get_contacts():
    # Paginierungs- und Suchparameter werden abgerufen
    page = request.args.get('page', 1, type=int)
    per_page = 5
    offset = (page - 1) * per_page
    search_query = request.args.get('search', '').strip()
    sort_by = request.args.get('sort_by', 'id')
    sort_order = request.args.get('sort_order', 'asc')
    
    # Überprüfen, ob die Sortierparameter gültig sind
    if sort_by not in ['id', 'name', 'email', 'phone', 'address', 'date']:
        sort_by = 'id'
    if sort_order not in ['asc', 'desc']:
        sort_order = 'asc'
    
    connection = get_db_connection()
    with connection.cursor() as cur:
        base_query = "SELECT * FROM contacts"
        count_query = "SELECT COUNT(*) as count FROM contacts"
        
        if search_query:
            search_condition = " WHERE name LIKE %s OR phone LIKE %s OR email LIKE %s OR address LIKE %s"
            search_term = f"%{search_query}%"
            base_query += search_condition
            count_query += search_condition
            query_params = (search_term, search_term, search_term, search_term)
        else:
            query_params = ()
        
        cur.execute(count_query, query_params)
        total_contacts = cur.fetchone()['count']
        
        base_query += f" ORDER BY {sort_by} {sort_order} LIMIT %s OFFSET %s"
        cur.execute(base_query, query_params + (per_page, offset))
        contacts = cur.fetchall()
    
    connection.close()
    total_pages = (total_contacts + per_page - 1) // per_page
    start_page = max(1, page - 5)
    end_page = min(start_page + 9, total_pages)
    
    return render_template(
        'contacts.html',
        contacts=contacts,
        page=page,
        total_pages=total_pages,
        start_page=start_page,
        end_page=end_page,
        search_query=search_query,
        highlight_search=highlight_search,
        sort_by=sort_by,
        sort_order=sort_order,
        total_contacts=total_contacts
    )

if __name__ == '__main__':
    app.run(debug=True)
