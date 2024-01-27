# main.py
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
import socket
import threading
import sqlite3

class P2PSyncApp(App):
    def build(self):
        self.title = 'P2P Sync App'

        self.layout = BoxLayout(orientation='vertical')
        self.label = Label(text='Messages:')
        self.text_input = TextInput(multiline=True)
        self.sync_button = Button(text='Sync Database', on_press=self.sync_database)

        self.layout.add_widget(self.label)
        self.layout.add_widget(self.text_input)
        self.layout.add_widget(self.sync_button)

        self.server_thread = threading.Thread(target=self.start_server)
        self.server_thread.start()

        return self.layout

    def start_server(self):
        host = 'localhost'
        port = 12346
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(1)

        while True:
            client_socket, addr = self.server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        try:
            data = client_socket.recv(1024)
            message = data.decode('utf-8')
            self.label.text += f'\nReceived: {message}'

            # Here, you would update your SQLite database with the received data
            # For simplicity, let's just display the message for now
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client_socket.close()

    def sync_database(self, instance):
        message = self.text_input.text
        self.label.text += f'\nSent: {message}'

        # Here, you would send the message to the other instance of the app
        # For simplicity, let's just use localhost for testing
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(('localhost', 12346))
            client_socket.send(message.encode('utf-8'))
            client_socket.close()
        except Exception as e:
            print(f"Error syncing database: {e}")

if __name__ == '__main__':
    P2PSyncApp().run()
