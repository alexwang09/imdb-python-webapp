#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Alex Wang'

'''
Models for user, blog, comment.
'''

import time, uuid

from transwarp.db import next_id
from transwarp.orm import Model, StringField, BooleanField, FloatField, TextField, IntegerField

def next_id():
    return '%015d%s000' % (int(time.time() * 1000), uuid.uuid4().hex)

class User(Model):
    __table__ = 'users'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    email = StringField(updatable=False, ddl='varchar(50)')
    password = StringField(ddl='varchar(50)')
    admin = BooleanField()
    name = StringField(ddl='varchar(50)')
    created_at = FloatField(updatable=False, default=time.time)

class Movie(Model):
    __table__ = 'movies'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    name = StringField(ddl='varchar(50)')
    summary = TextField()
    score = FloatField()
    num_review = IntegerField()
    duration = IntegerField()
    style = StringField(ddl='varchar(50)')
    date = StringField(ddl='varchar(50)')
    director = StringField(ddl='varchar(50)')
    writer = StringField(ddl='varchar(50)')
    star = StringField(ddl='varchar(500)')
    created_at = FloatField(updatable=False, default=time.time)

class Review(Model):
    __table__ = 'reviews'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    movie_id = StringField(updatable=False, ddl='varchar(50)')
    user_id = StringField(updatable=False, ddl='varchar(50)')
    user_name = StringField(ddl='varchar(50)')
    score = IntegerField()
    content = TextField()
    created_at = FloatField(updatable=False, default=time.time)
