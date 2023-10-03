from moviepy.editor import VideoFileClip
import os
from datetime import timedelta
from datetime import datetime as dt
import mysql.connector
import sqlite3
import configparser
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import sys

class ConsoleRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        self.text_widget.insert(tk.END, message)

def redirect_console_to_text_widget(text_widget):
    console_redirector = ConsoleRedirector(text_widget)
    sys.stdout = console_redirector
    sys.stderr = console_redirector

def display_current_time(label):
    current_time = dt.now().strftime("%Y-%m-%d %H:%M:%S")
    label.config(text=f"Dátum és idő: {current_time}")
    label.after(1000, lambda: display_current_time(label))  # Update every second

def update_timer():
    global remaining_time

    remaining_time -= 1
    if remaining_time <= 0:
        remaining_time = 100  # 5 perc újraindítása
        label.config(text="Visszaszámláló: 5:00")
        #Ha letelt az ido elinditja a folyamatot
        start_tasks()
    else:
        minutes = remaining_time // 60
        seconds = remaining_time % 60
        label.config(text="Visszaszámláló: {:02d}:{:02d}".format(minutes, seconds))

    root.after(1000, update_timer)

def start_tasks():
    # MySQL adatbázis beállítások
    host = config['database']['host']
    user = config['database']['user']
    password = config['database']['password']
    database = config['database']['databasename']
    tvid = config['database']['tvid']

    # Kapcsolódás az SQLite adatbázishoz (ha nem létezik, létrehozza)
    connDB3 = sqlite3.connect('C:/ES5Lite/PlaylistDB2.db3')

    # Cursor létrehozása
    cursorDB3 = connDB3.cursor()

    directory_path = config['clips']['directory_path']
    file_names = get_file_names_in_directory(directory_path)

    for f_name in file_names:
        print(f_name)

        video_file_path = config['clips']['video_file_path'] + f_name
        frame_count = get_video_frame_count(video_file_path)
        file_size_bytes = get_video_file_size(video_file_path)
        formatted_duration = get_video_duration_formatted(video_file_path)
        file_names = get_file_names_in_directory(directory_path)

        # Lekérdezés az érték ellenőrzésére
        query = "SELECT * FROM clips WHERE clip = %s"
        value_to_check = f_name  # Az ellenőrizendő érték

        # Kapcsolódás a MySQL adatbázishoz
        connection = connect_to_mysql(host, user, password, database)

        if connection:
            # Ellenőrzés, hogy az érték létezik-e
            value_exists = check_if_value_exists(connection, query, value_to_check)

            # Kapcsolat bezárása
            connection.close()

            if value_exists:
                print(f"Az érték már létezik a táblában.")
                print("============================")
            else:
                print(f"Az érték még nem létezik a táblában...")

                if isinstance(frame_count, int):
                    print(f"A videó frame-ek száma: {frame_count}")
                else:
                    print(f"Hiba történt a frame-ek számának meghatározása során: {frame_count}")

                if isinstance(file_size_bytes, int):
                    print(f"A videó fájl mérete: {file_size_bytes} B")
                else:
                    print(f"Hiba történt a fájlméret meghatározása során: {file_size_bytes}")

                if isinstance(formatted_duration, str):
                    print(f"A videó hossza: {formatted_duration}")
                else:
                    print(f"Hiba történt a videó hosszának meghatározása során: {formatted_duration}")

                video_file_path_for_DB3 = config['clips']['video_file_path_for_DB3'] + f_name

                # Adatok beszúrása
                cursorDB3.execute('INSERT INTO Files (path, filename, filesize, duration, inpoint, outpoint, type, ch, frrate, follow, promo) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (video_file_path_for_DB3, f_name, file_size_bytes, frame_count, '0', frame_count, 'File', '1', '25', '0', '0'))

                print(
                    "ES5Lite adatbázisába beszúrva.")

                # Tranzakció mentése
                connDB3.commit()

                # Cursor és kapcsolat lezárása
                cursorDB3.close()
                connDB3.close()

                # Lekérdezés
                query = f"INSERT IGNORE INTO `{tvid}` (`id`, `clip`, `frame`, `size`, `duration`) VALUES (NULL, %s, %s, %s, %s);"
                values = (f_name, frame_count, file_size_bytes, formatted_duration)  # A változók helyére kerülő értékek

                # Kapcsolódás a MySQL adatbázishoz
                connection = connect_to_mysql(host, user, password, database)

                if connection:
                    # Adatok beszúrása
                    insert_data_with_variables(connection, query, values)

                    # Kapcsolat bezárása
                    connection.close()

                print("============================")

def get_video_frame_count(video_file):
    try:
        clip = VideoFileClip(video_file)
        frame_count = clip.fps * clip.duration  # Frame-ek száma: fps * időtartam
        return int(frame_count)
    except Exception as e:
        return str(e)


def get_video_file_size(video_file):
    try:
        file_size_bytes = os.path.getsize(video_file)
        return file_size_bytes
    except Exception as e:
        return str(e)


def format_duration(duration):
    # A timedelta objektumot átalakítjuk idő formátumra (óra:perc:másodperc)
    return str(timedelta(seconds=duration))


def get_video_duration_formatted(video_file):
    try:
        clip = VideoFileClip(video_file)
        duration = clip.duration
        formatted_duration = format_duration(duration)
        return formatted_duration
    except Exception as e:
        return str(e)

def get_file_names_in_directory(directory_path):
    try:
        if not os.path.isdir(directory_path):
            raise ValueError("A megadott elérési út nem egy mappa.")

        file_names = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
        return file_names
    except Exception as e:
        return str(e)

def connect_to_mysql(host, user, password, database):
    try:
        # Kapcsolat létrehozása a MySQL szerverrel
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )

        if connection.is_connected():
            return connection

    except mysql.connector.Error as err:
        print(f"Hiba a MySQL kapcsolódás során: {err}")
        return None


def insert_data_with_variables(connection, query, values):
    try:
        cursor = connection.cursor()

        # Lekérdezés végrehajtása
        cursor.execute(query, values)

        # Tranzakció mentése
        connection.commit()

        print("Adat sikeresen beszúrva!")

    except mysql.connector.Error as err:
        connection.rollback()  # Visszagörgetjük a tranzakciót hiba esetén
        print(f"Hiba az adat beszúrása során: {err}")

    finally:
        # Cursor lezárása
        if cursor:
            cursor.close()

def check_if_value_exists(connection, query, value):
    try:
        cursor = connection.cursor()

        # Lekérdezés végrehajtása
        cursor.execute(query, (value,))

        # Eredmények lekérése
        result = cursor.fetchall()

        return len(result) > 0

    except mysql.connector.Error as err:
        print(f"Hiba a lekérdezés végrehajtása során: {err}")
        return False

    finally:
        # Cursor lezárása
        if cursor:
            cursor.close()

def create_table_if_not_exits():
        # MySQL adatbázis beállítások
        host = config['database']['host']
        user = config['database']['user']
        password = config['database']['password']
        database = config['database']['databasename']
        tvid = config['database']['tvid']

        # Kapcsolódás az adatbázishoz
        conn1 = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )

        # Adatbázis kurzor létrehozása
        cursor1 = conn1.cursor()

        # SQL lekérdezés a tábla létrehozásához
        ct_query = f"""CREATE TABLE IF NOT EXISTS `{database}`.`{tvid}` ( `id` int(11) NOT NULL, `clip` text NOT NULL, `frame` int(11) NOT NULL, `size` bigint(20) NOT NULL, `duration` text NOT NULL ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_hungarian_ci; ALTER TABLE `{database}`.`{tvid}` ADD PRIMARY KEY (`id`); ALTER TABLE `{database}`.`{tvid}` MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=55 ;)"""

        # Tábla létrehozása
        cursor1.execute(ct_query)

        # Kapcsolat bezárása
        cursor1.close()
        conn1.close()


# ======== MAIN ===========================================================

root = tk.Tk()
root.title(
    " S4U - Database Updater")
root.iconbitmap(
    "rec.ico")

config = configparser.ConfigParser()
config.read(
    'C:/data.ini')

create_table_if_not_exits()

# Create a scrolled text widget to display console messages
scrolled_text = ScrolledText(
    root,
    wrap=tk.WORD,
    width=80,
    height=30)
scrolled_text.pack(
    expand=True,
    fill=tk.BOTH)

# Redirect console messages to the text widget
redirect_console_to_text_widget(
    scrolled_text)

# Create a label to display the current time
time_label = tk.Label(
    root, text="")
time_label.pack()

# Display the current time
display_current_time(
    time_label)

remaining_time = 300  # 5 perc = 300 másodperc

label = tk.Label(root, text="", font=("Arial", 18))
label.pack(padx=10, pady=10)

update_timer()

# Create a button to start the tasks
start_button = tk.Button(
    root,
    text="Manuális indítás",
    command=start_tasks)
start_button.pack(padx=10, pady=10)

# Run the main event loop
root.mainloop()


















