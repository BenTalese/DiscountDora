from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from p2pnetwork.node import Node


class P2PApp(App):
    def build(self):
        self.node = Node('localhost', 5556, None, 'MyP2PApp')
        self.node.start()

        layout = BoxLayout(orientation='vertical', padding=10)

        self.ip_input = TextInput(hint_text="Enter peer's IP Address", multiline=False)
        layout.add_widget(self.ip_input)

        connect_button = Button(text='Connect', on_press=self.connect_to_peer)
        layout.add_widget(connect_button)

        self.message_input = TextInput(hint_text='Type your message', multiline=False)
        layout.add_widget(self.message_input)

        send_button = Button(text='Send', on_press=self.send_message)
        layout.add_widget(send_button)

        self.chat_label = Label(text='Chat:\n')
        layout.add_widget(self.chat_label)

        return layout

    def connect_to_peer(self, instance):
        peer_ip = self.ip_input.text
        if peer_ip:
            self.node.connect_to_node(peer_ip, 5555, 'MyP2PApp')

    def send_message(self, instance):
        message = self.message_input.text
        if message:
            self.node.send_to_all(message)
            self.update_chat(f'Sent: {message}')

    def update_chat(self, message):
        self.chat_label.text += message + '\n'

    def on_message(self, node, message):
        self.update_chat(f'Received from {node}: {message}')

    def on_stop(self):
        self.node.stop()


if __name__ == '__main__':
    P2PApp().run()




# # main.py
# import time
# from kivy.app import App
# from kivy.uix.boxlayout import BoxLayout
# from kivy.uix.button import Button
# from kivy.uix.textinput import TextInput
# from kivy.uix.label import Label
# from p2pnetwork.node import Node


# class P2PApp(App):
#     def node_callback(self, event, node, connected_node, data):
#         try:
#             if event == 'outbound_node_connected':
#                 print('SUCCESSFULLY CONNECTED TO PEER!')

#             if event != 'node_request_to_stop': # node_request_to_stop does not have any connected_node, while it is the main_node that is stopping!
#                 print('Event: {} from main node {}: connected node {}: {}'.format(event, node.id, connected_node.id, data))

#             self.on_message(node, data)

#         except Exception as e:
#             print(e)

#     def build(self):
#         self.node = Node('127.0.0.1', 60000, None, callback=self.node_callback)
#         self.node.start()
#         time.sleep(1)
#         # self.node.node_message(self.on_message)

#         layout = BoxLayout(orientation='vertical', padding=10)

#         self.ip_input = TextInput(hint_text="Enter peer's IP Address", multiline=False)
#         layout.add_widget(self.ip_input)

#         connect_button = Button(text='Connect', on_press=self.connect_to_peer)
#         layout.add_widget(connect_button)

#         self.message_input = TextInput(hint_text='Type your message', multiline=False)
#         layout.add_widget(self.message_input)

#         send_button = Button(text='Send', on_press=self.send_message)
#         layout.add_widget(send_button)

#         self.chat_label = Label(text='Chat:\n')
#         layout.add_widget(self.chat_label)

#         return layout

#     def connect_to_peer(self, instance):
#         peer_ip = self.ip_input.text
#         if peer_ip:
#             print("CONNECTING TO PEER")
#             self.node.connect_with_node(peer_ip, 60000)
#             time.sleep(1)

#     def send_message(self, instance):
#         message = self.message_input.text
#         if message:
#             print("SENDING MESSAGE")
#             self.node.send_to_nodes(message)
#             self.update_chat(f'Sent: {message}')

#     def update_chat(self, message):
#         self.chat_label.text += message + '\n'

#     def on_message(self, node, message):
#         self.update_chat(f'Received from {node}: {message}')

#     def on_stop(self):
#         self.node.stop()


# if __name__ == '__main__':
#     P2PApp().run()
