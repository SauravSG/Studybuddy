from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
# from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, render

from .forms import RoomForm, UserForm, MyUserCreationForm
from .models import Room, Topic, Message, User


# roomDetails = [
#     {
#         'id': 1,
#         'name': 'Room1'
#     },
#     {
#         'id': 2,
#         'name': 'Room2'
#     },
#     {
#         'id': 3,
#         'name': 'Room3'
#     },
# ]

def loginPage(request):
  page = 'login'
  if request.user.is_authenticated:
      return redirect('home')

  if request.method == 'POST':
      email = request.POST.get('email').lower()
      password = request.POST.get('password')

      try:
          user = User.objects.get(email=email)
      except:
          messages.error(request, 'User does not exist')
          return redirect('login')

      user = authenticate(request, username=user.username, password=password)

      if user is not None:
          login(request, user)
          return redirect('home')
      else:
          messages.error(request, 'Username OR password does not exist')

  context = {'page': page}
  return render(request, 'home/login_register.html', context)

def logoutUser(request):
  logout(request)
  return redirect('home')

def registerPage(request):
  form = MyUserCreationForm(request.POST)
  if request.method == 'POST':
    form = MyUserCreationForm(request.POST)
    if form.is_valid():
      user = form.save(commit = False)
      user.username = user.username.lower()
      user.save()
      login(request, user)
      return redirect('home')
    else:
      messages.error(request, 'An error occurred during registration')
      
  return render(request, 'home/login_register.html', {'form':form})

def home(request):

  q = request.GET.get('q') if request.GET.get('q') != None else ''

  roomDetails = Room.objects.filter(
      Q(topic__name__icontains=q) | Q(name__icontains=q) | Q(description__icontains=q)
  )

  topics = Topic.objects.all()[0:5]

  room_count = roomDetails.count()

  room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))

  context = {'roomDetails': roomDetails, 'topics': topics, 'room_count': room_count, 'room_messages': room_messages}

  return render(request, 'home/home.html', context)

  #the http request that we need to pass into


"""render: This is a shortcut function in Django that loads a template, renders it with a context, and returns an HttpResponse object with the rendered content.
request: This is the HTTP request object that Django receives from the user's browser. It contains information about the request, such as the user's browser, the URL being accessed, and any data sent with the request."""


def room(request, pk):
  #pk: primary key
  # room = None
  # for i in Room.objects.all():
  #     if i.id == int(pk):
  #         room = i
  room = Room.objects.get(id=pk)
  # give us the set of messages in the room
  room_messages = room.message_set.all()
  participants = room.participants.all()
  
  if request.method == "POST":
    message = Message.objects.create(
      user=request.user, 
      room=room, 
      body=request.POST.get('body')
    )
    room.participants.add(request.user)
    
    return redirect('room', pk=room.id) 
                                     
  context = {'room': room, 'room_messages':room_messages, 'participants':participants}

  return render(request, 'home/room.html', context)

@login_required(login_url = 'login')

def userProfile(request, pk):
  user = User.objects.get(id=pk)
  roomDetails = user.room_set.all()
  room_messages = user.message_set.all()
  topics = Topic.objects.all()
  context = {'user': user, 'roomDetails': roomDetails, 'room_messages': room_messages, 'topics': topics}
  return render(request, 'home/profile.html', context)

def createRoom(request):
  form = RoomForm()
  topics = Topic.objects.all()
  if request.method == 'POST':
    topic_name = request.POST.get('topic')
    topic, created = Topic.objects.get_or_create(name=topic_name)
    Room.objects.create(
      host = request.user,
      topic = topic,
      name = request.POST.get('name'),
      description = request.POST.get('description'),
    )
    return redirect('home')

  context = {'form': form, 'topics': topics}
  return render(request, 'home/room_form.html', context)

@login_required(login_url = 'login')
def updateRoom(request, pk):
  room = Room.objects.get(id=pk)
  form = RoomForm(instance=room)
  topics = Topic.objects.all()
  if request.user != room.host:
    return HttpResponse(b'You are not allowed here!')
  
  if request.method == 'POST':
    topic_name = request.POST.get('topic')
    topic, created = Topic.objects.get_or_create(name=topic_name)
    room.name = request.POST.get('name')
    room.topic = topic
    room.name = request.POST.get('description')
    room.save()
    return redirect('home')

  context = {'form': form, 'topics': topics, 'room':room}
  return render(request, 'home/room_form.html', context)

@login_required(login_url = 'login')
def deleteRoom(request, pk):
  room = Room.objects.get(id=pk)

  if request.user != room.host:
    return HttpResponse(b'You are not allowed here!')
    
  if request.method == 'POST':
    room.delete()
    return redirect('home')
  return render(request, 'home/delete.html', {'obj': room})


@login_required(login_url = 'login')
def deleteMessage(request, pk):
  message = Message.objects.get(id=pk)

  if request.user != message.user:
    return HttpResponse(b'You are not allowed here!')

  if request.method == 'POST':
    message.delete()
    return redirect('home')
  return render(request, 'home/delete.html', {'obj': message})

@login_required(login_url="login")
def updateUser(request):
  user = request.user
  form = UserForm(instance = user)
  if request.method == 'POST':
    form = UserForm(request.POST, request.FILES, instance=user)
    if form.is_valid():
      form.save()
      return redirect('user-profile', pk=user.id)
  context={'form':form}
  return render(request, 'home/update-user.html', context)

def topicsPage(request):
  q = request.GET.get('q') if request.GET.get('q') != None else ''
  topics = Topic.objects.filter(name__icontains=q)
  context = {'topics': topics}
  return render(request, 'home/topics.html', context)

def activityPage(request):
  room_messages = Message.objects.all()
  context = {'room_messages': room_messages}
  return render(request, 'home/activity.html', context)