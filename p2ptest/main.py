# main.py
import socket
import threading

from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput


class P2PApp(App):
    def build(self):
        from kivy.utils import platform
        if platform == "android":
            from android.permissions import (Permission, check_permission,
                                             request_permissions)
            request_permissions([Permission.INTERNET, Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
            print(check_permission('android.permission.INTERNET'))
            print(check_permission('android.permission.WRITE_EXTERNAL_STORAGE'))

        self.layout = BoxLayout(orientation='vertical', spacing=10)
        self.input_ip = TextInput(text='127.0.0.1', multiline=False)
        self.message_input = TextInput(multiline=False, hint_text='Type your message')
        self.btn_connect = Button(text='Connect', on_press=self.connect_to_peer)
        self.btn_start_server = Button(text='Start Server', on_press=self.start_server)
        self.btn_send = Button(text='Send', on_press=self.send_message)

        # Box to display received messages
        self.messages_box = ScrollView()
        self.messages_layout = BoxLayout(orientation='vertical', spacing=5)
        self.messages_box.add_widget(self.messages_layout)

        self.layout.add_widget(self.input_ip)
        self.layout.add_widget(self.btn_connect)
        self.layout.add_widget(self.btn_start_server)
        self.layout.add_widget(self.messages_box)
        self.layout.add_widget(self.message_input)
        self.layout.add_widget(self.btn_send)

        self.server_socket = None
        self.client_socket = None

        self.receive_data_clock_event = None  # Store the clock event for later cancellation

        return self.layout

    @mainthread
    def show_connection_status(self, status):
        content = BoxLayout(orientation='vertical', spacing=10)
        content.add_widget(Label(text=status))
        popup = Popup(title='Connection Status', content=content, size_hint=(None, None), size=(300, 200))
        popup.open()
        Clock.schedule_once(popup.dismiss, 5)  # Close the popup after 5 seconds

    def connect_to_peer(self, instance):
        peer_ip = self.input_ip.text
        threading.Thread(target=self.connect_to_server, args=(peer_ip,)).start()

    def start_server(self, instance):
        threading.Thread(target=self.initiate_server).start()

    def initiate_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('0.0.0.0', 12345))
        self.server_socket.listen(1)
        try:
            self.client_socket, addr = self.server_socket.accept()
            self.start_receive_data_clock()  # Start periodic checking for new data
            self.show_connection_status('Connection successful!')
        except socket.timeout:
            self.show_connection_status('Connection timed out')
        except socket.error:
            self.show_connection_status('Connection failed')

    def connect_to_server(self, peer_ip):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Set a connection timeout of 5 seconds
            self.client_socket.settimeout(5)
            self.client_socket.connect((peer_ip, 12345))
            self.start_receive_data_clock()  # Start periodic checking for new data
            self.show_connection_status('Connection successful!')
        except socket.timeout:
            self.show_connection_status('Connection timed out')
        except socket.error:
            self.show_connection_status('Connection failed')

    def start_receive_data_clock(self):
        if not self.receive_data_clock_event:
            self.receive_data_clock_event = Clock.schedule_interval(self.receive_data, 0.1)

    def stop_receive_data_clock(self):
        if self.receive_data_clock_event:
            self.receive_data_clock_event.cancel()
            self.receive_data_clock_event = None

    def send_data(self, message):
        try:
            self.client_socket.send(message.encode())
        except socket.error:
            print("Failed to send data")

    def send_message(self, instance):
        message = self.message_input.text
        if message:
            self.send_data(message)
            self.message_input.text = ''  # Clear the input field after sending

    def receive_data(self, dt):
        try:
            data = self.client_socket.recv(1024).decode()
            if data:
                # Display received message in the box
                received_message_label = Label(text=data, size_hint_y=None, height=30)
                self.messages_layout.add_widget(received_message_label)
                # Scroll to the latest message
                self.messages_box.scroll_y = 0
        except socket.error:
            self.stop_receive_data_clock()  # Stop periodic checking for new data

    def on_stop(self):
        if self.server_socket:
            self.server_socket.close()
        if self.client_socket:
            self.client_socket.close()

if __name__ == '__main__':
    P2PApp().run()
