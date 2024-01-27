# main.py
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
import socket
import threading

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
        host = '0.0.0.0'  # Listen on all available network interfaces
        port = 12345
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))

        # Join the multicast group
        group = '224.0.0.1'
        self.server_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton(group) + socket.inet_aton(host))

        while True:
            data, addr = self.server_socket.recvfrom(1024)
            message = data.decode('utf-8')
            self.label.text += f'\nReceived: {message}'

    def sync_database(self, instance):
        message = self.text_input.text
        self.label.text += f'\nSent: {message}'

        # Use UDP multicast to send the message
        try:
            multicast_group = ('224.0.0.1', 12345)
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client_socket.sendto(message.encode('utf-8'), multicast_group)
            client_socket.close()
        except Exception as e:
            print(f"Error syncing database: {e}")

if __name__ == '__main__':
    P2PSyncApp().run()
