# main.py
import os

os.chdir('framework/kivy_app/')

import socket
import sqlite3
import threading

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
import sqlite3
import os
from queue import Queue

class P2PSyncApp(App):
    def build(self):
        self.peer_address = ('localhost', 12346)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(self.peer_address)
        self.server_socket.listen(1)

        root = BoxLayout(orientation='vertical')

        self.status_label = Label(text='P2P Sync: Waiting for peers...')
        root.add_widget(self.status_label)

        self.input_text = TextInput(hint_text='Enter data to sync...')
        root.add_widget(self.input_text)

        self.sync_button = Button(text='Sync Data', on_press=self.sync_data)
        root.add_widget(self.sync_button)

        threading.Thread(target=self.start_server).start()

        # Initialize a connection pool
        self.connection_pool = Queue(maxsize=5)
        for _ in range(5):
            self.connection_pool.put(self.create_connection())

        # Create the table before any data insertion
        connection = self.connection_pool.get()
        cursor = connection.cursor()
        self.create_table(connection, cursor)
        connection.commit()
        self.connection_pool.put(connection)
        return root

    def create_connection(self):
        return sqlite3.connect("mydatabase2.db")
        # script_dir = os.path.dirname(os.path.abspath(__file__))
        # database_path = os.path.join(script_dir, "framework/kivy_app/mydatabase1.db")
        # return sqlite3.connect(database_path)

    def create_table(self, connection, cursor):
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS mytable (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT
            )
            """
        )
        connection.commit()
        print("Table 'mytable' created successfully.")

    def start_server(self):
        while True:
            client_socket, client_address = self.server_socket.accept()
            threading.Thread(target=self.sync_with_peer, args=(client_socket,)).start()

    def sync_with_peer(self, peer_socket):
        try:
            connection = self.connection_pool.get()
            cursor = connection.cursor()
            self.create_table(connection, cursor)

            while True:
                data = peer_socket.recv(1024)
                if not data:
                    break
                query = data.decode('utf-8')
                self.handle_database_change(connection, cursor, query)
        except Exception as e:
            print(f"Error syncing with peer: {e}")
        finally:
            peer_socket.close()
            self.connection_pool.put(connection)

    def handle_database_change(self, connection, cursor, query):
        try:
            cursor.execute(query)
            connection.commit()
            self.status_label.text = f'P2P Sync: Database updated with "{query}"'
        except Exception as e:
            print(e)

    def propagate_change(self, query):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect(self.peer_address)
            client_socket.sendall(query.encode('utf-8'))

    def sync_data(self, instance):
        data_to_sync = self.input_text.text
        query = f"INSERT INTO mytable (data) VALUES ('{data_to_sync}')"
        connection = self.connection_pool.get()
        cursor = connection.cursor()
        self.handle_database_change(connection, cursor, query)
        self.connection_pool.put(connection)

        # Propagate the change to other peers
        threading.Thread(target=self.propagate_change, args=(query,)).start()
if __name__ == '__main__':
    P2PSyncApp().run()
