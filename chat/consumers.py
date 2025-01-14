import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, Chat, Profile


class ChatConsumer(AsyncWebsocketConsumer):
    """
    This consumer has all chat menssages logic

    def connect - If user not in chat-room he is added to chat and the consumer update the chat-room users number,
    the consumer also send a message that a new user has joined to the room.

    def disconnect - This only discard the users from channel layer, in other words he is disconnected.

    def receive - This method receive messages from web-socket and send to the room group, if user exit the chat-room
    the receive remove this user and update the database after this send a message to the chat-room that the user exit.
    Also save the users menssages and send back to the channel layer room group.

    def chat_message - Send back all channel layer room group messages to the frontend, like messages and if a user
    joined to the chat-room or exited from there.
    """
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name
        self.user_name = self.scope['user'].username

        room = await database_sync_to_async(ChatRoom.objects.get)(name=self.room_name)
        num_users = await database_sync_to_async(room.users.all().values)()
        num_users = await database_sync_to_async(list)(num_users)

        ja_esta = False
        for user in num_users:
            if self.scope['user'].id == user['id']:
                ja_esta = True

        room = await database_sync_to_async(ChatRoom.objects.get)(name=self.room_name)
        num_users = await database_sync_to_async(room.users.all().values)()
        num_users = await database_sync_to_async(list)(num_users)

        usuarios = []

        for user in num_users:
            perfil = await database_sync_to_async(Profile.objects.get)(user=user['id'])
            usuarios.append({'id': user['id'], 'username': user['username'], 'image': perfil.image.url})
        print(usuarios)

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        await self.accept()

        if ja_esta:
            print('user já esta')
            pass
        else:
            await database_sync_to_async(room.users.add)(self.scope['user'])
            await database_sync_to_async(room.save)()
            print('user adicionado')
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': '',
                    'user_id': '',
                    'user_name': '',
                    'entrou': f'{self.scope["user"].username} entrou na sala',
                    'num_users': usuarios
                }
            )

    # Leave room group
    async def disconnect(self, close_code):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        room = await database_sync_to_async(ChatRoom.objects.get)(name=self.room_name)

        if 'sair' in text_data_json:
            await database_sync_to_async(room.users.remove)(self.scope['user'])
            print('usuario saiu')

            num_users = await database_sync_to_async(room.users.all().values)()
            num_users = await database_sync_to_async(list)(num_users)
            usuarios = []

            for user in num_users:
                perfil = await database_sync_to_async(Profile.objects.get)(user=user['id'])
                usuarios.append({'id': user['id'], 'username': user['username'], 'image': perfil.image.url})

            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': '',
                    'user_id': '',
                    'user_name': '',
                    'entrou': f'{self.scope["user"].username} saiu da sala',
                    'num_users': usuarios
                }
            )
        else:
            message = text_data_json['message']
            self.user_id = self.scope['user'].id
            self.user_name = self.scope['user'].username
            user_profile = await database_sync_to_async(Profile.objects.get)(user=self.scope['user'])

            chat = Chat(
                content=message,
                user=self.scope['user'],
                room=room,
            )
            await database_sync_to_async(chat.save)()
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'user_id': self.user_id,
                    'user_name': self.user_name,
                    'user_profile': user_profile.image.url,
                }
            )

    # Receive message from room group
    async def chat_message(self, event):
        print(event)
        if event['message']:
            message = event['message']
            user_id = event['user_id']
            user_name = event['user_name']
            user_profile = event['user_profile']
            await self.send(text_data=json.dumps({
                'message': message,
                'user_id': user_id,
                'user_name': user_name,
                'user_profile': user_profile
            }))
        else:
            entrou = event['entrou']
            num_users = event['num_users']
            # Send message to WebSocket
            await self.send(text_data=json.dumps({
                'entrou': entrou,
                'num_users': num_users
            }))


class RoomConsumer(AsyncWebsocketConsumer):
    """
    This consumer update all chat rooms to show rooms users and new created rooms
    """
    async def connect(self):

        salas = await database_sync_to_async(ChatRoom.objects.values)()
        salas = await database_sync_to_async(list)(salas)
        for x in salas:
            room = await database_sync_to_async(ChatRoom.objects.get)(name=x['name'])
            num_users = await database_sync_to_async(room.users.all)()
            num_users = await database_sync_to_async(len)(num_users)
            x['users'] = num_users

        await self.accept()

        self.room_group_name = 'sala'
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'sala_all',
                'salas': salas
            }
        )

    async def disconnect(self, code):
        salas = await database_sync_to_async(ChatRoom.objects.values)()
        salas = await database_sync_to_async(list)(salas)
        for x in salas:
            room = await database_sync_to_async(ChatRoom.objects.get)(name=x['name'])
            num_users = await database_sync_to_async(room.users.all)()
            num_users = await database_sync_to_async(len)(num_users)
            x['users'] = num_users

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'sala_all',
                'salas': salas
            }
        )

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )

    async def sala_all(self, event):
        salas = event['salas']

        await self.send(text_data=json.dumps({
            'salas': salas,
        }))
