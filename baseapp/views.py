from django.shortcuts import render, redirect, HttpResponseRedirect
from django.http import HttpResponse, JsonResponse
from django.db.models import Q  # This allows the use of |, &&
from .models import Room, Topic, Message, Profile, LikeDislike
from .forms import RoomForm, UserProfileForm, ProfileForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm

from openai import ChatCompletion
import openai
from .secrets import api_key
# Chatbot starts


def chatbot_view(request):
    conversation = request.session.get('conversation', [])

    if request.method == 'POST':
        user_input = request.POST.get('user_input')

        # Define your chatbot's predefined prompts
        prompts = []

        # Append user input to the conversation
        if user_input:
            conversation.append({"role": "user", "content": user_input})

        # Append conversation messages to prompts
        prompts.extend(conversation)

        # Set up and invoke the ChatGPT model
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=prompts,
            api_key=api_key
        )
        print(response)
        # Extract chatbot replies from the response

        chatbot_replies = [message['message']['content']
                           for message in response['choices'] if message['message']['role'] == 'assistant']
        print(len(chatbot_replies))
        # Append chatbot replies to the conversation
        for reply in chatbot_replies:
            conversation.append({"role": "assistant", "content": reply})

        # Update the conversation in the session
        request.session['conversation'] = conversation
        context = {'user_input': user_input,
                   'chatbot_replies': chatbot_replies, 'conversation': conversation}
        return render(request, 'baseapp/chatbox.html', context)
    else:
        # request.session.clear()
        return render(request, 'baseapp/chatbox.html', {'conversation': conversation})
# CHATBOT ENDS

# LOGIN PAGE


def loginPage(request):
    page = 'login'  # This variable confirms in the login/register to know what content to render
    # This prevents logged in users from going to the login page again
    if request.user.is_authenticated:
        return redirect('home')

    already_printed = False
    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)

        except:
            messages.error(request, f'User {username} is not registered ')
            already_printed = True

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            if already_printed:
                pass
            else:
                messages.error(request, 'Incorrect password entered')

    context = {'page': page, }
    return render(request, 'baseapp/login_register.html', context)

# LOGOUT


def logoutPage(request):
    logout(request)
    return redirect('home')

# REGISTER PAGE


def registerPage(request):
    '''
    Page for users to register
    '''
    form = UserProfileForm()

    if request.method == 'POST':
        form = UserProfileForm(request.POST)
        if form.is_valid():
            # this accesses the created user and not save it directly
            user = form.save(commit=False)
            # This ensures only lowercase usernames are stored in the database
            user.username = user.username.lower()
            user.save()

            Profile.objects.create(
                user=user,
                first_name=user.first_name,
                last_name=user.last_name,
                bio="",

            )
            messages.success(
                request, "Congratulation, registration successful")
            login(request, user)
            return redirect('home')
        else:
            for error in list(form.errors.values()):
                messages.error(request, error)

    context = {
        'form': form,
    }
    return render(request, 'baseapp/login_register.html', context)

# PROFILE VIEW


def edit_profile(request):
    profile = request.user.profile
    form = ProfileForm(instance=profile)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            request.user.first_name = request.POST.get('first_name')
            request.user.last_name = request.POST.get('last_name')
            profile.save()
            request.user.save()
            form.save()
            return redirect('user-profile', pk=request.user.id)

    context = {'form': form}
    return render(request, 'baseapp/update_profile.html', context)

# HOME PAGE


def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    rooms = Room.objects.filter(
        # contains returns any topic whose first characters match q. Since all all topics start with an empty string, '' returns all topics. i there makes the search non-case sensitive
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
    )

    topics = Topic.objects.all()
    room_count = rooms.count()
    recent_messages = Message.objects.filter(
        Q(room__topic__name__icontains=q)).order_by('-updated')

    context = {
        'rooms': rooms,
        'topics': topics,
        'room_count': room_count,
        'recent_messages': recent_messages
    }
    return render(request, 'baseapp/home.html', context)

# DISPLAY ROOM


def room(request, pk):
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all().order_by('-updated')
    partcipants = room.participants.all()

    if request.user in partcipants:
        join_or_leave = 'leave'
    else:
        join_or_leave = 'join'

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
        message = Message.objects.create(
            user=request.user,
            room=room,
            body=request.POST.get('body'),
            image=request.FILES.get('image')
        )

        room.participants.add(request.user)
        return redirect('room', pk=room.id)

    context = {
        'rooms': room,
        'room_messages': room_messages,
        'participants': partcipants,
        'join_or_leave': join_or_leave,
    }
    return render(request, 'baseapp/room.html', context)

# CREATE ROOM


@login_required(login_url='login')
def create_room(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room = Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
        )

        # Add the host to the room participants
        room.participants.add(request.user)

        return redirect('home')

    context = {
        'form': form,
        'topics': topics,
    }
    return render(request, 'baseapp/create_room.html', context)

# UPDATE ROOM


# Decorator ensures only logged in users are able to update rooms
@login_required(login_url='login')
def update_room(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()

    # Two lines below ensures only hosts of a room are able to edit room
    if request.user != room.host:
        return HttpResponse('Only room admins can edit room')

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)

        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()

        return redirect('room', pk=room.id)

    context = {
        'form': form,
        'topics': topics,
        'room': room,
    }

    return render(request, 'baseapp/update_room.html', context)

# JOIN ROOM


@login_required(login_url='login')
def join_room(request, pk):
    room = Room.objects.get(id=pk)
    room.participants.add(request.user)

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


@login_required(login_url='login')
def leave_room(request, pk):
    room = Room.objects.get(id=pk)
    room.participants.remove(request.user)
    room.save()

    return redirect('home')


# DELETE ROOM
@login_required(login_url='login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)

    # Two lines below ensures only hosts of a room are able to edit room
    if request.user != room.host:
        return HttpResponse('Only room admins can edit room')

    if request.method == 'POST':
        room.delete()
        return redirect('home')
    context = {'obj': room}
    return render(request, 'baseapp/delete.html', context)


# DELETE MESSAGE
@login_required(login_url='login')
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)

    # Two lines below ensures only hosts of a room are able to edit room
    if request.user != message.user:
        return HttpResponse('Only message owner can delete message')

    if request.method == 'POST':
        message.delete()
        return redirect('room', pk=message.room.id)
    context = {'obj': message}
    return render(request, 'baseapp/delete.html', context)

# USER PROFILE


def userProfile(request, pk):
    all_rooms = Room.objects.all()
    user = User.objects.get(id=pk)
    topics = Topic.objects.all()
    recent_messages = user.message_set.all()
    rooms = user.room_set.all()
    user_rooms_count = Room.objects.filter(host=user).count

    user_rooms_joined_count = 0
    # user_rooms_joined_count = Room.objects.filter(participants.filter(username=user.username)).count
    # user_rooms_joined_count = user.message_set.all().count
    for room in all_rooms:
        if room.participants.filter(username=user.username).count() == 1:
            user_rooms_joined_count += 1

    context = {
        'user': user,
        'topics': topics,
        'recent_messages': recent_messages,
        'rooms': rooms,
        'user_rooms_count': user_rooms_count,
        'user_rooms_joined_count': user_rooms_joined_count,
    }

    return render(request, 'baseapp/profile.html', context)


@login_required(login_url='login')
def save(request, pk):
    bookmarks = request.user.profile.bookmarks
    message = Message.objects.get(id=pk)
    bookmarks.add(message)

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


@login_required(login_url='login')
def bookmarks(request, pk):
    bookmarks = request.user.profile.bookmarks.all().order_by('-updated')
    context = {
        'bookmarks': bookmarks,
    }

    return render(request, 'baseapp/bookmarks.html', context)


@login_required(login_url='login')
def likes(request, pk):
    message = Message.objects.get(id=pk)
    objectt = message

    try:
        preference = LikeDislike.objects.get(user=request.user, post=message)

        if preference.value == 0:
            message.likes += 1
            preference.value = 1

        else:
            if preference.value == 1:
                message.likes -= 1
                preference.value = 0

            else:
                message.dislikes -= 1
                message.likes += 1
                preference.value = 1

        message.save()
        preference.save()

    except LikeDislike.DoesNotExist:
        new_preference = LikeDislike()
        new_preference.user = request.user
        new_preference.post = message
        new_preference.value = 1
        message.likes += 1

        new_preference.save()
        message.save()

    dislike_count = message.dislikes
    like_count = message.likes
    det = like_count - dislike_count
    context = {
        'dislike_count': dislike_count,
        'like_count': like_count,
        'det': det,
    }
    return JsonResponse(context)
    # return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


@login_required(login_url='login')
def dislike(request, pk):
    message = Message.objects.get(id=pk)

    try:
        preference = LikeDislike.objects.get(user=request.user, post=message)

        if preference.value == 0:
            message.dislikes += 1
            preference.value = 2

        else:
            if preference.value == 2:
                message.dislikes -= 1
                preference.value = 0

            else:
                message.likes -= 1
                message.dislikes += 1
                preference.value = 2

        message.save()
        preference.save()

    except LikeDislike.DoesNotExist:
        new_preference = LikeDislike()
        new_preference.user = request.user
        new_preference.post = message
        new_preference.value = 2
        message.dislikes += 1

        new_preference.save()
        message.save()

    dislike_count = message.dislikes
    like_count = message.likes
    context = {
        'dislike_count': dislike_count,
        'like_count': like_count,
    }
    return JsonResponse(context)
