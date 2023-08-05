from channels.generic.websocket import AsyncWebsocketConsumer
from channels.generic.websocket import WebsocketConsumer
import json
from asgiref.sync import sync_to_async, async_to_sync
from django.contrib.auth.models import User
from . models import Room, Message
from django.shortcuts import get_object_or_404


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.room_id = self.scope["url_route"]['kwargs']['room_id']
        self.room_group_name = 'room_%s' % self.room_id
        print(self.room_group_name)

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.channel_layer,
            self.room_group_name
        )

    def receive(self, text_data):
        data = json.loads(text_data)
        print(data)

        message = data['message']
        username = data['username']
        room = data['room']
        self.save_message(username, room, message)

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username,
                'room': room,
            }
        )

    def chat_message(self, event):
        message = event['message']
        username = event['username']
        room = event['room']
        user = User.objects.get(username=username)

        self.send(text_data=json.dumps({
            'message': message,
            'message_id': self.message_id,
            'username': username,
            'room': room,
            'user_id': user.id,
            'avatar': user.profile.avatar.url
        }))

    # @sync_to_async
    def save_message(self, username, room, message):
        user = User.objects.get(username=username)
        room = Room.objects.get(id=room)
        message = Message.objects.create(user=user, room=room, body=message)
        self.message_id = message.id
        print("Message saved successfully")

    # things to send to the frontend:
    # avatar, username, user_id, message.updated, message_body, message_id
