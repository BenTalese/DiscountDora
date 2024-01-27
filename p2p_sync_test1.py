# main.py
import socket
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
import sqlite3

class ThreadLocalData:
    def __init__(self):
        self.connection = None
        self.cursor = None

thread_local_data = threading.local()

def get_connection_and_cursor():
    if not hasattr(thread_local_data, 'connection') or not thread_local_data.connection:
        thread_local_data.connection = sqlite3.connect("mydatabase1.db")
        thread_local_data.cursor = thread_local_data.connection.cursor()
    return thread_local_data.connection, thread_local_data.cursor

class P2PSyncApp(App):
    def build(self):
        self.peer_address = ('localhost', 12345)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(self.peer_address)
        self.server_socket.listen(5)

        root = BoxLayout(orientation='vertical')

        self.status_label = Label(text='P2P Sync: Waiting for peers...')
        root.add_widget(self.status_label)

        self.input_text = TextInput(hint_text='Enter data to sync...')
        root.add_widget(self.input_text)

        self.sync_button = Button(text='Sync Data', on_press=self.sync_data)
        root.add_widget(self.sync_button)

        threading.Thread(target=self.start_server).start()

        # Initialize SQLite connection and cursor for the main thread
        self.create_table()

        return root

    def create_table(self):
        connection, cursor = get_connection_and_cursor()
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
        print("RECEIVED FROM PEER 2")
        try:
            connection, cursor = get_connection_and_cursor()

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

    def handle_database_change(self, connection, cursor, query):
        print("HANDLING CHANGE" + query)
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
        connection, cursor = get_connection_and_cursor()
        self.handle_database_change(connection, cursor, query)
        self.propagate_change(query)

if __name__ == '__main__':
    P2PSyncApp().run()
