#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Alex Wang'

import os, re, time, base64, hashlib, logging

import markdown2

from datetime import datetime

from transwarp.web import get, post, ctx, view, interceptor, seeother, notfound

from apis import api, Page, APIError, APIValueError, APIPermissionError, APIResourceNotFoundError
from models import User, Movie, Review, History
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

def _search_movies_by_page(kw):
    sql = "where name like '%%%s%%' "
    sql = sql %(kw)
    total = len(Movie.find_by(sql))
    page = Page(total, _get_page_index())
    sql = "where name like '%%%s%%' order by created_at desc limit %s,%s"
    sql = sql %(kw, page.offset, page.limit)
    movies = Movie.find_by(sql)
    return movies, page

def _get_movie_details(movie):
    movie.year = movie.date[0:4]
    movie.directors = movie.director.split(' ')
    movie.writers = movie.writer.split(' ')
    movie.stars = movie.star.split(' ')
    movie.styles = movie.style.split(' ')
    movie.summarys = movie.summary.split("\n")
    movie.num_directors = len(movie.directors)
    movie.num_writers = len(movie.writers)
    movie.num_stars = len(movie.stars)
    movie.num_styles = len(movie.styles)
    movie.score = int(movie.score)
    return movie

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
        movie = _get_movie_details(movie)
    return dict(page=page, movies=movies, user=ctx.request.user)

@view('index.html')
@get('/search_tag')
def _get_index_by_tags():
    tag = ctx.request.get('tag','')
    sql = "where style like '%%%s%%' "
    sql = sql %(tag)
    movies = Movie.find_by(sql)
    total = len(movies)
    page = Page(total, _get_page_index())
    sql = "where style like '%%%s%%' order by created_at desc limit %s,%s"
    sql = sql %(tag, page.offset, page.limit)
    movies = Movie.find_by(sql)
    for movie in movies:
        movie = _get_movie_details(movie)
    return dict(movies=movies, tag=tag, page=page, user=ctx.request.user)

@view('register.html')
@get('/register')
def register():
    return dict()

@view('signin.html')
@get('/signin')
def signin():
    return dict()

@view('mypath.html')
@get('/mypath')
def mypath():
    return dict(user=ctx.request.user)

@get('/signout')
def signout():
    ctx.response.delete_cookie(_COOKIE_NAME)
    raise seeother('/')

@get('/manage/')
def manage_index():
    raise seeother('/manage/reviews')

@view('manage_user_list.html')
@get('/manage/users')
def manage_users():
    return dict(page_index=_get_page_index(), user=ctx.request.user)

@view('manage_movie_list.html')
@get('/manage/movies')
def manage_movies():
    return dict(page_index=_get_page_index(), user=ctx.request.user)

@view('manage_review_list.html')
@get('/manage/reviews')
def manage_reviews():
    return dict(page_index=_get_page_index(), user=ctx.request.user)

@view('manage_movie_edit.html')
@get('/manage/movies/create')
def manage_movies_create():
    return dict(id=None, action='/api/movies', redirect='/manage/movies', user=ctx.request.user)

@view('manage_movie_edit.html')
@get('/manage/movies/edit/:movie_id')
def manage_movies_edit(movie_id):
    movie = Movie.get(movie_id)
    if movie is None:
        raise notfound()
    return dict(id=movie.id, name=movie.name, duration=movie.duration, style=movie.style, date=movie.date, director=movie.director, writer=movie.writer, star=movie.star, summary=movie.summary, action='/api/movies/%s' % movie_id, redirect='/manage/movies', user=ctx.request.user)

@view('manage_user_list.html')
@get('/manage/users')
def manage_users():
    return dict(page_index=_get_page_index(), user=ctx.request.user)

@view('search_movies.html')
@get('/movies/search')
def search_movies():
    kw = ctx.request.get('kw','').strip()
    if not kw:
        return APIValueError('kw')
    movies, page = _search_movies_by_page(kw)
    for movie in movies:
        movie = _get_movie_details(movie)
    return dict(movies=movies, page=page, kw=kw, user=ctx.request.user)

@view('movie.html')
@get('/movie/:movie_id')
def movie(movie_id):
    user = ctx.request.user
    movie = Movie.get(movie_id)
    movie = _get_movie_details(movie)
    if movie is None:
        raise notfound()
    movie.html_summary = markdown2.markdown(movie.summary)
    if user:
        history = History.find_first('where user_id=? and movie_id=?', user.id, movie_id)
        if not history:
            history = History(user_id=user.id, movie_id=movie_id)
            history.insert()
        else:
            history.created_at = time.time()
            history.update()
    reviews = Review.find_by('where movie_id=? order by created_at desc limit 1000', movie_id)
    user_review = ''
    if user:
        user_review = Review.find_first('where user_id=? and movie_id=?', user.id, movie_id)
    return dict(movie=movie, reviews=reviews, user=user, user_review=user_review)

@api
@get('/api/users')
def api_get_users():
    total = User.count_all()
    page = Page(total, _get_page_index())
    users = User.find_by('order by created_at desc limit ?,?', page.offset, page.limit)
    for u in users:
        u.password = '******'
    return dict(users=users, page=page)

@api
@get('/api/movies')
def api_get_movies():
    format = ctx.request.get('format', '')
    movies, page = _get_movies_by_page()
    for movie in movies:
        movie.directors = movie.director.split(' ')
    if format=='html':
        for movie in movies:
            movie.content = markdown2.markdown(movie.content)
    return dict(movies=movies, page=page)

@api
@get('/api/movies/:movie_id')
def api_get_movie(movie_id):
    movie = Movie.get(movie_id)
    if movie:
        return movie
    raise APIResourceNotFoundError('movie')

@api
@get('/api/reviews')
def api_get_reviews():
    total = Review.count_all()
    page = Page(total, _get_page_index())
    reviews = Review.find_by('order by created_at desc limit ?,?', page.offset, page.limit)
    return dict(reviews=reviews, page=page)

@api
@get('/api/histories/:user_id')
def api_get_histories(user_id):
    if not user_id:
        return APIValueError('users')
    histories = History.find_by('where user_id=? order by created_at desc', user_id)
    movies = []
    if histories:
        for history in histories:
            movie_id = history.movie_id
            movie = Movie.get(movie_id)
            movie = _get_movie_details(movie)
            dt = datetime.fromtimestamp(history.created_at)
            movie.history_day = dt.day
            movie.history_month = dt.month
            movies.append(movie)
        return dict(movies=movies)
    raise APIResourceNotFoundError('histories')

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
@post('/api/movies')
def api_create_movie():
    check_admin()
    i = ctx.request.input(name='', duration='', style='', date='', director='', writer='', star='', summary='')
    name = i.name.strip()
    duration = i.duration.strip()
    style = i.style.strip()
    date = i.date.strip()
    director = i.director.strip()
    writer = i.writer.strip()
    star = i.star.strip()
    summary = i.summary.strip()
    if not name:
        raise APIValueError('name', 'name cannot be empty.')
    if not duration:
        raise APIValueError('duration', 'duration cannot be empty.')
    if not style:
        raise APIValueError('style', 'style cannot be empty.')
    if not date:
        raise APIValueError('date', 'date cannot be empty.')
    if not director:
        raise APIValueError('director', 'director cannot be empty.')
    if not writer:
        raise APIValueError('writer', 'writer cannot be empty.')
    if not star:
        raise APIValueError('star', 'star cannot be empty.')
    if not summary:
        raise APIValueError('summary', 'summary cannot be empty.')
    movie = Movie(name=name, duration=duration, style=style, date=date, director=director, writer=writer, star=star, summary=summary)
    movie.insert()
    return movie

@api
@post('/api/movies/:movie_id')
def api_update_movie(movie_id):
    check_admin()
    i = ctx.request.input(name='', duration='', style='', date='', director='', writer='', star='', summary='')
    name = i.name.strip()
    duration = i.duration.strip()
    style = i.style.strip()
    date = i.date.strip()
    director = i.director.strip()
    writer = i.writer.strip()
    star = i.star.strip()
    summary = i.summary.strip()
    if not name:
        raise APIValueError('name', 'name cannot be empty.')
    if not duration:
        raise APIValueError('duration', 'duration cannot be empty.')
    if not style:
        raise APIValueError('style', 'style cannot be empty.')
    if not date:
        raise APIValueError('date', 'date cannot be empty.')
    if not director:
        raise APIValueError('director', 'director cannot be empty.')
    if not writer:
        raise APIValueError('writer', 'writer cannot be empty.')
    if not star:
        raise APIValueError('star', 'star cannot be empty.')
    if not summary:
        raise APIValueError('summary', 'summary cannot be empty.')
    movie = Movie.get(movie_id)
    if movie is None:
        raise APIResourceNotFoundError('movie')
    movie.name = name
    movie.duration = duration
    movie.style = style
    movie.date = date
    movie.director = director
    movie.writer = writer
    movie.star = star
    movie.summary = summary
    movie.update()
    return movie

@api
@post('/api/movies/:movie_id/reviews')
def api_create_movie_review(movie_id):
    user = ctx.request.user
    if user is None:
        raise APIPermissionError('Need signin.')
    movie = Movie.get(movie_id)
    if movie is None:
        raise APIResourceNotFoundError('Movie')
    i = ctx.request.input(score='', content='')
    score = int(i.score) * 10
    content = i.content.strip()
    if not score:
        raise APIValueError('score')
    if not content:
        content = ''
    review = Review.find_first('where user_id=? and movie_id=?', user.id, movie_id)
    if review:
        movie.score = (movie.score * movie.num_review - review.score + score) / movie.num_review
        movie.update()
        review.score = score
        review.content = content
        review.created_at = time.time()
        review.update()
    else :
        review = Review(movie_id=movie_id, user_id=user.id, user_name=user.name, score=score, content=content)
        review.insert()
        movie.score = (movie.score * movie.num_review + score) / (movie.num_review + 1)
        movie.num_review = movie.num_review + 1
        movie.update()
    return dict(review=review)

@api
@post('/api/movies/:movie_id/delete')
def api_delete_movie(movie_id):
    check_admin()
    movie = Movie.get(movie_id)
    if movie is None:
        raise APIResourceNotFoundError('Movie')
    movie.delete()
    return dict(id=movie_id)

@api
@post('/api/reviews/:review_id/delete')
def api_delete_review(review_id):
    check_admin()
    review = Review.get(review_id)
    if review is None:
        raise APIResourceNotFoundError('Review')
    review.delete()
    return dict(id=review_id)

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
