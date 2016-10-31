#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Alex Wang'

import os, re, time, base64, hashlib, logging

import markdown2

from transwarp.web import get, post, ctx, view, interceptor, seeother, notfound

from apis import api, Page, APIError, APIValueError, APIPermissionError, APIResourceNotFoundError
from models import User, Movie, Review
from config import configs

_COOKIE_NAME = 'imdbsession'
_COOKIE_KEY = configs.session.secret

_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_MD5 = re.compile(r'^[0-9a-f]{32}$')

def _get_page_index():
    page_index = 1
    try:
        page_index = int(ctx.request.get('page', '1'))
    except ValueError:
        pass
    return page_index

def _get_movies_by_page():
    total = Movie.count_all()
    page = Page(total, _get_page_index())
    movies = Movie.find_by('order by created_at desc limit ?,?', page.offset, page.limit)
    return movies, page

def make_signed_cookie(id, password, max_age):
    # build cookie string by: id-expires-md5
    expires = str(int(time.time() + (max_age or 86400)))
    L = [id, expires, hashlib.md5('%s-%s-%s-%s' % (id, password, expires, _COOKIE_KEY)).hexdigest()]
    return '-'.join(L)

def parse_signed_cookie(cookie_str):
    try:
        L = cookie_str.split('-')
        if len(L) != 3:
            return None
        id, expires, md5 = L
        if int(expires) < time.time():
            return None
        user = User.get(id)
        if user is None:
            return None
        if md5 != hashlib.md5('%s-%s-%s-%s' % (id, user.password, expires, _COOKIE_KEY)).hexdigest():
            return None
        return user
    except:
        return None

def check_admin():
    user = ctx.request.user
    if user and user.admin:
        return
    raise APIPermissionError('No permission.')

@interceptor('/')
def user_interceptor(next):
    logging.info('try to bind user from session cookie...')
    user = None
    cookie = ctx.request.cookies.get(_COOKIE_NAME)
    if cookie:
        logging.info('parse session cookie...')
        user = parse_signed_cookie(cookie)
        if user:
            logging.info('bind user <%s> to session...' % user.email)
    ctx.request.user = user
    return next()

@interceptor('/manage/')
def manage_interceptor(next):
    user = ctx.request.user
    if user and user.admin:
        return next()
    raise seeother('/signin')

@view('index.html')
@get('/')
def index():
    movies, page = _get_movies_by_page()
    for movie in movies:
        movie.year = movie.date[0:4]
        movie.directors = movie.director.split(' ')
        movie.writers = movie.writer.split(' ')
        movie.stars = movie.star.split(' ')
        movie.styles = movie.style.split(' ')
        movie.summarys = movie.summary.split("\r")
        movie.num_directors = len(movie.directors)
        movie.num_writers = len(movie.writers)
        movie.num_stars = len(movie.stars)
        movie.num_styles = len(movie.styles)
    return dict(page=page, movies=movies, user=ctx.request.user)

@view('register.html')
@get('/register')
def register():
    return dict()

@view('signin.html')
@get('/signin')
def signin():
    return dict()

@get('/signout')
def signout():
    ctx.response.delete_cookie(_COOKIE_NAME)
    raise seeother('/')

@get('/manage/')
def manage_index():
    raise seeother('/manage/reviews')

@view('manage_review_list.html')
@get('/manage/reviews')
def manage_reviews():
    return dict(page_index=_get_page_index(), user=ctx.request.user)

@api
@post('/api/users')
def register_user():
    i = ctx.request.input(name='', email='', password='')
    name = i.name.strip()
    email = i.email.strip().lower()
    password = i.password
    if not name:
        raise APIValueError('name')
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')
    if not password or not _RE_MD5.match(password):
        raise APIValueError('password')
    user = User.find_first('where name=?', name)
    if user:
        raise APIError('register:failed', 'name', 'Name is already in use.')
    user = User.find_first('where email=?', email)
    if user:
        raise APIError('register:failed', 'email', 'Email is already in use.')
    user = User(name=name, email=email, password=password, image='http://www.gravatar.com/avatar/%s?d=mm&s=120' % hashlib.md5(email).hexdigest())
    user.insert()
    # make session cookie:
    cookie = make_signed_cookie(user.id, user.password, None)
    ctx.response.set_cookie(_COOKIE_NAME, cookie)
    return user

@api
@post('/api/name_authenticate')
def name_authenticate():
    i = ctx.request.input(name='')
    name = i.name.strip()
    if not name:
        raise APIValueError('name')
    user = User.find_first('where name=?', name)
    if user:
        raise APIError('register:failed', 'name', 'Name is already in use.')
    return dict()

@api
@post('/api/email_authenticate')
def email_authenticate():
    i = ctx.request.input(email='')
    email = i.email.strip().lower()
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')
    user = User.find_first('where email=?', email)
    if user:
        raise APIError('register:failed', 'email', 'Email is already in use.')
    return dict()

@api
@post('/api/authenticate')
def authenticate():
    i = ctx.request.input(remember='')
    email = i.email.strip().lower()
    password = i.password
    remember = i.remember
    user = User.find_first('where email=?', email)
    if user is None:
        raise APIError('auth:failed', 'email', 'Invalid email.')
    elif user.password != password:
        raise APIError('auth:failed', 'password', 'Invalid password.')
    # make session cookie:
    max_age = 604800 if remember=='true' else None
    cookie = make_signed_cookie(user.id, user.password, max_age)
    ctx.response.set_cookie(_COOKIE_NAME, cookie, max_age=max_age)
    user.password = '******'
    return user
