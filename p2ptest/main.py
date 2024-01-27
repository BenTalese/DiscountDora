# main.py
import platform
import select
import socket
import threading

from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle


class P2PApp(App):
    def build(self):
        from kivy.utils import platform
        if platform == "android":
            from android.permissions import request_permissions, Permission, check_permission
            request_permissions([Permission.INTERNET, Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
            print(check_permission('android.permission.INTERNET'))
            print(check_permission('android.permission.WRITE_EXTERNAL_STORAGE'))

        self.layout = BoxLayout(orientation='vertical', spacing=10)

        # Status bar at the top
        self.status_bar = BoxLayout(orientation='horizontal', size_hint=(1, None), height=30, spacing=10)
        self.connection_status_label = Label(text='', color=(1, 1, 1, 1))
        self.ip_address_label = Label(text='', color=(1, 1, 1, 1))
        self.peers_label = Label(text='', color=(1, 1, 1, 1))
        self.status_bar.add_widget(self.connection_status_label)
        self.status_bar.add_widget(self.ip_address_label)
        self.status_bar.add_widget(self.peers_label)

        # Draw a line as a visual separator
        with self.layout.canvas.before:
            Color(1, 1, 1, 1)
            Rectangle(pos=(0, self.layout.height), size=(self.layout.width, 2))

        # Box to display received messages
        self.messages_box = ScrollView()
        self.messages_layout = BoxLayout(orientation='vertical', spacing=5)
        self.messages_box.add_widget(self.messages_layout)

        self.input_ip = TextInput(text='127.0.0.1', multiline=False)
        self.message_input = TextInput(multiline=False, hint_text='Type your message')
        self.btn_connect = Button(text='Connect', on_press=self.connect_to_peer)
        self.btn_start_server = Button(text='Start Server', on_press=self.start_server, disabled=False)
        self.btn_send = Button(text='Send', on_press=self.send_message)

        self.layout.add_widget(self.status_bar)
        self.layout.add_widget(self.messages_box)
        self.layout.add_widget(self.input_ip)
        self.layout.add_widget(self.btn_connect)
        self.layout.add_widget(self.btn_start_server)
        self.layout.add_widget(self.message_input)
        self.layout.add_widget(self.btn_send)

        self.server_socket = None
        self.client_socket = None
        self.server_running = False

        self.peers = []

        self.receive_data_clock_event = None  # Store the clock event for later cancellation

        return self.layout

    @mainthread
    def update_connection_status(self, status, color):
        self.connection_status_label.text = status
        self.connection_status_label.color = color

    @mainthread
    def update_ip_address(self, ip_address):
        self.ip_address_label.text = f'IP: {ip_address}'

    @mainthread
    def update_peers(self, peers):
        self.peers_label.text = f'Peers: {", ".join(peers)}'

    def connect_to_peer(self, instance):
        peer_ip = self.input_ip.text
        threading.Thread(target=self.connect_to_server, args=(peer_ip,)).start()

    def start_server(self, instance):
        if not self.server_running:
            threading.Thread(target=self.initiate_server).start()
            self.btn_start_server.disabled = True

    def initiate_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('0.0.0.0', 12345))
        self.server_socket.listen(1)
        try:
            self.client_socket, addr = self.server_socket.accept()                      # FIXME! It gets to here and waits, then upon connect request resumes and makes the connection successful, bypassing all the other code
            self.start_receive_data_clock()  # Start periodic checking for new data
            self.server_running = True
            self.update_connection_status('Connection successful!', (0, 1, 0, 1))  # Green color
            self.update_peer_list()  # Update the list of peer addresses
        except socket.timeout:
            self.update_connection_status('Connection timed out', (1, 1, 0, 1))  # Yellow color
            self.btn_start_server.disabled = False
        except socket.error:
            self.update_connection_status('Connection failed', (1, 0, 0, 1))  # Red color
            self.btn_start_server.disabled = False

    def connect_to_server(self, peer_ip):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Set a connection timeout of 5 seconds
            # self.client_socket.settimeout(5)
            self.client_socket.connect((peer_ip, 12345))
            self.start_receive_data_clock()  # Start periodic checking for new data

            # Send a connection request to the target device
            device_info = f"{platform.system()} {platform.release()} - {platform.machine()}"
            self.send_data(f"CONNECTION_REQUEST:{device_info}")

            response = self.wait_for_connection_response()

            if response == "ACCEPT":
                # Continue with connection setup logic here
                self.update_connection_status('Connection successful!', (0, 1, 0, 1))  # Green color
                self.update_peer_list()  # Update the list of peer addresses
                #self.send_device_info()  # Send device info to the connected peer
            elif response == "DECLINE":
                self.update_connection_status('Connection declined', (1, 0, 0, 1))  # Red color
            else:
                self.update_connection_status('Connection timed out', (1, 1, 0, 1))  # Yellow color

        except socket.timeout:
            self.update_connection_status('Connection timed out', (1, 1, 0, 1))  # Yellow color
        except socket.error:
            self.update_connection_status('Connection failed', (1, 0, 0, 1))  # Red color

    def wait_for_connection_response(self):
        # Function to wait for the user's response to the connection request
        # For simplicity, you can use a simple variable to store the response

        # Reset the response variable before waiting for a new response
        self.connect_request_response = None

        # Show a popup with accept and decline buttons
        # self.show_connection_request_popup()

        # Wait for the user's response
        while True:
            if self.connect_request_response:
                response = self.connect_request_response
                self.connect_request_response = None
                return response

    def dismiss_popup(self):
        self.connect_request_popup.dismiss()

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
            ready_to_read, _, _ = select.select([self.client_socket], [], [], 0)
            for sock in ready_to_read:
                data = sock.recv(1024).decode()
                if data:
                    # Check if the received data is a connection request
                    if data.startswith("CONNECTION_REQUEST:"):
                        _, device_info = data.split(":", 1)
                        self.handle_connection_request(device_info)
                    elif data.startswith("CONNECTION_RESPONSE:"):
                        _, response = data.split(":", 1)
                        self.connect_request_response = response
                    else:
                        # Display received message in the box
                        received_message_label = Label(text=data, size_hint_y=None, height=30)
                        self.messages_layout.add_widget(received_message_label)
                        # Scroll to the latest message
                        self.messages_box.scroll_y = 0
        except socket.error:
            self.stop_receive_data_clock()  # Stop periodic checking for new data

    # TODO: THIS IS THE NEW POPUP
    @mainthread
    def handle_connection_request(self, device_info):
        content = BoxLayout(orientation='vertical', spacing=10, size_hint=(None, None), size=(300, 200))
        content.add_widget(Label(text="Connection request received", size_hint_y=None, height=50))

        # Accept button callback
        def accept_connection(instance):
            self.connect_request_response = "ACCEPT"
            self.dismiss_popup()

        # Decline button callback
        def decline_connection(instance):
            self.connect_request_response = "DECLINE"
            self.dismiss_popup()

        accept_button = Button(text='Accept', on_press=accept_connection, size_hint_y=None, height=50)
        decline_button = Button(text='Decline', on_press=decline_connection, size_hint_y=None, height=50)

        content.add_widget(accept_button)
        content.add_widget(decline_button)

        self.connect_request_popup = Popup(title='Connection Request', content=content, size_hint=(None, None), size=(300, 200))
        self.connect_request_popup.open()

    # TODO: THIS IS THE OLD POPUP
    # @mainthread
    # def handle_connection_request(self, device_info):
    #     # Function to handle the incoming connection request and show the popup
    #     peer_ip = self.client_socket.getpeername()[0]
    #     content = BoxLayout(orientation='vertical', spacing=10)
    #     content.add_widget(Label(text=f"Connection request from {peer_ip}:\n{device_info}"))

    #     # Accept button callback
    #     def accept_connection(instance):
    #         self.dismiss_popup()
    #         self.send_data("CONNECTION_RESPONSE:ACCEPT")

    #         # Continue with the connection setup logic here

    #     # Decline button callback
    #     def decline_connection(instance):
    #         self.dismiss_popup()
    #         self.send_data("CONNECTION_RESPONSE:DECLINE")

    #     accept_button = Button(text='Accept', on_press=accept_connection)
    #     decline_button = Button(text='Decline', on_press=decline_connection)

    #     content.add_widget(accept_button)
    #     content.add_widget(decline_button)

    #     self.connect_request_popup = Popup(title='Connection Request', content=content, size_hint=(None, None), size=(300, 200))
    #     self.connect_request_popup.open()

    def get_ip_address(self):
        try:
            # Use a dummy socket to get the local IP address
            dummy_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            dummy_socket.connect(('8.8.8.8', 80))
            local_ip_address = dummy_socket.getsockname()[0]
            dummy_socket.close()
            print(local_ip_address)
            return local_ip_address
        except socket.error:
            return 'Unknown'

    def update_peer_list(self):
        # Update the list of peer addresses
        if self.server_running:
            peers = [self.get_ip_address()]
            if self.client_socket:
                peers.append(self.client_socket.getpeername()[0])
            self.peers = peers
            self.update_peers(peers)

    def on_stop(self):
        if self.server_socket:
            self.server_socket.close()
        if self.client_socket:
            self.client_socket.close()

if __name__ == '__main__':
    P2PApp().run()



# def send_device_info(self):
#         device_info = f"{platform.system()} {platform.release()} - {platform.machine()}"
#         self.send_data(f"DEVICE_INFO:{device_info}")

# encryption example:
# $ pip install pynacl
# from nacl.public import PrivateKey, PublicKey, Box

# def generate_key_pair():
#     # Generate a key pair for public-key cryptography
#     private_key = PrivateKey.generate()
#     public_key = private_key.public_key
#     return private_key, public_key

# def encrypt_message(message, sender_private_key, recipient_public_key):
#     # Create a Box for secure communication between sender and recipient
#     box = Box(sender_private_key, recipient_public_key)
#     # Encrypt the message
#     encrypted_message = box.encrypt(message.encode())
#     return encrypted_message

# def decrypt_message(encrypted_message, sender_public_key, recipient_private_key):
#     # Create a Box for secure communication between sender and recipient
#     box = Box(recipient_private_key, sender_public_key)
#     # Decrypt the message
#     decrypted_message = box.decrypt(encrypted_message)
#     return decrypted_message.decode()

# # Example usage
# alice_private_key, alice_public_key = generate_key_pair()
# bob_private_key, bob_public_key = generate_key_pair()

# # Alice sends an encrypted message to Bob
# message_to_bob = "Hello Bob, this is Alice!"
# encrypted_message = encrypt_message(message_to_bob, alice_private_key, bob_public_key)

# # Bob decrypts the message
# decrypted_message = decrypt_message(encrypted_message, alice_public_key, bob_private_key)
# print(f"Bob received: {decrypted_message}")
