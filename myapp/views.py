from __future__ import unicode_literals
from django.shortcuts import render, redirect
from forms import SignUpForm, LoginForm, PostForm, LikeForm, CommentForm
from models import UserModel, SessionToken, PostModel, LikeModel, CommentModel
from django.contrib.auth.hashers import make_password, check_password
from Instaclone.settings import BASE_DIR
from imgurpython import ImgurClient
from datetime import timedelta, datetime
from django.utils import timezone
import requests


def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            # saving data to DB
            empty = len(username) == 0 and len(password) == 0
            if len(username) >= 4 and len(password) >= 3:
                user = UserModel(name=name, password=make_password(password), email=email, username=username)
                user.save()
                return render(request, 'success.html')
            text = {}
            text = "Username or password is not long enough"
            # return redirect('login/')
        else:
            form = SignUpForm()
    elif request.method == "GET":
        form = SignUpForm()
        today = datetime.now()
    return render(request, 'index.html', {'today': today, 'form': form})


def login_view(request):
    response_data = {}
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = UserModel.objects.filter(username=username).first()

            if user:
                if check_password(password, user.password):
                    token = SessionToken(user=user)
                    token.create_token()
                    token.save()
                    response = redirect('feed/')
                    response.set_cookie(key='session_token', value=token.session_token)
                    return response
                else:
                    response_data['message'] = 'Incorrect Password! Please try again!'

    elif request.method == 'GET':
        form = LoginForm()

    response_data['form'] = form
    return render(request, 'login.html', response_data)


def like_view(request):
    user = check_validation(request)
    if user and request.method == 'POST':
        form = LikeForm(request.POST)
        if form.is_valid():
            post_id = form.cleaned_data.get('post').id
            posts = PostModel.objects.all().order_by('-created_on')
            for post in posts:

                existing_like = LikeModel.objects.filter(post_id=post_id, user=user).first()
                if existing_like:
                    post.has_liked = True

                if not existing_like:
                    LikeModel.objects.create(post_id=post_id, user=user)
                else:
                    existing_like.delete()

                return redirect('/feed/')


        else:
            return redirect('/feed/')


    else:
        return redirect('/login/')


def feed_view(request):
    user = check_validation(request)
    if user:
        posts = PostModel.objects.all().order_by('created_on')
        return render(request, 'feed.html', {'posts': posts})
    else:
        return redirect('/login/')


def post_view(request):
    user = check_validation(request)

    if user:
        if request.method == 'POST':
            form = PostForm(request.POST, request.FILES)
            if form.is_valid():
                image = form.cleaned_data.get('image')
                caption = form.cleaned_data.get('caption')
                post = PostModel(user=user, image=image, caption=caption)
                post.save()

                path = str(BASE_DIR + "\\" + post.image.url)

                client = ImgurClient('16510a88c098088', '94a0461aa512dc7a622781c8d8f8f81b91b30699')
                post.image_url = client.upload_from_path(path,anon=True)['link']
                post.save()

                return redirect('/feed/')

        else:
            form = PostForm()
        return render(request, 'post.html', {'form' : form})
    else:
        return redirect('/login/')


def arr_of_dict(args):
    pass


def send_response(comment_text):
    pass


def comment_view(request):
    user = check_validation(request)
    if user and request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            post_id = form.cleaned_data.get('post').id
            print post_id
            comment_text = form.cleaned_data.get('comment_text')
            comment = CommentModel.objects.create(user=user, post_id=post_id, comment_text=comment_text)
            comment.save()

            apikey = 'UXqiW0EEfpWD1oB8AgJXAveneCAQxkIQSGXZwbAioS0'
            request_url =('https://apis.paralleldots.com/sentiment?sentence1=%s&apikey=%s') % (comment_text, apikey)
            print 'POST request url : %s' % (request_url)
            sentiment = requests.get(request_url, verify=False).json()
            sentiment_value = sentiment['sentiment']
            print sentiment_value
            if sentiment_value < 0.5:
                print 'Negative Comment'
            else:
                print 'Positive Comment'

            print 'commented'
            return redirect('/feed/')
        else:
            return redirect('/feed/')
    else:
        return redirect('/login')

def check_validation(request):
    if request.COOKIES.get('session_token'):
        session = SessionToken.objects.filter(session_token=request.COOKIES.get('session_token')).first()
        if session:
            time_to_live = session.created_on + timedelta(days=1)
            if time_to_live > timezone.now():
                return session.user
    else:
        return None

def logout_view(request):

        user = check_validation(request)

        if user is not None:
            latest_sessn = SessionToken.objects.filter(user=user).last()
            if latest_sessn:
                latest_sessn.delete()
                return redirect("/login/")


# method to create upvote for comments
def upvote_view(request):
    user = check_validation(request)
    comment = None

    print ("upvote view")
    if user and request.method == 'POST':

        form = UpvoteForm(request.POST)
        if form.is_valid():

            comment_id = int(form.cleaned_data.get('id'))

            comment = CommentModel.objects.filter(id=comment_id).first()
            print ("upvoted not yet")

            if comment is not None:
                # print ' unliking post'
                print ("upvoted")
                comment.upvote_num += 1
                comment.save()
                print (comment.upvote_num)
            else:
                print ('stupid mistake')
                #liked_msg = 'Unliked!'

        return redirect('/feed/')
    else:
        return redirect('/feed/')

def query_based_search_view(request):

    user = check_validation(request)
    if user:
        if request.method == "POST":
            searchForm = SearchForm(request.POST)
            if searchForm.is_valid():
                print 'valid'
                username_query = searchForm.cleaned_data.get('searchquery')
                user_with_query = UserModel.objects.filter(username=username_query).first();
                posts = PostModel.objects.filter(user=user_with_query)
                return render(request, 'feed.html',{'posts':posts})
            else:
                return redirect('/feed/')
    else:
        return redirect('/login/')