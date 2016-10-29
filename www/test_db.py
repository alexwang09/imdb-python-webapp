#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Alex Wang'

from models import User, Movie, Review

from transwarp import db

if __name__ == '__main__':
    print Movie().__sql__()
    db.create_engine('root', 'wxy6772102', 'imdb')
    db.update('drop table if exists users')
    db.update('drop table if exists movies')
    db.update('drop table if exists reviews')
    db.update(User().__sql__())
    db.update(Movie().__sql__())
    db.update(Review().__sql__())
    u = User(name='Test', email='test@example.com', password='1234567890')
    u.insert()
    '''
    u = User(name='Test', email='test@example.com', password='1234567890', image='about:blank')

    u.insert()

    print 'new user id:', u.id

    u1 = User.find_first('where email=?', 'test@example.com')
    print 'find user\'s name:', u1.name

    u1.delete()

    u2 = User.find_first('where email=?', 'test@example.com')
    print 'find user:', u2
    '''
