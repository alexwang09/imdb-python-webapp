#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Alex Wang'

from models import User, Movie, Review, History

from transwarp import db

import time, uuid
if __name__ == '__main__':
    #print Movie().__sql__()
    db.create_engine('root', 'wxy6772102', 'imdb')

    db.update('drop table if exists histories')
    db.update(History().__sql__())
    '''
    id = '0014781867782440246055d8b314bb1be953e2843a5af0a000'
    m = Movie.get(id)

    m.score = 0
    m.num_review = 0
    m.update()
    user_name = 'alex'
    content = 'hello'

    r = Review(user_name=user_name, content=content)
    r.insert()

    #id = '0014778151211044fbebfc019244892b8714a9ce9553d3e000'
    name = '大圣归来'
    summary = '五百年前，由石猴变化而成的齐天大圣孙悟空（张磊 配音）大闹天宫，最终被如来佛祖镇在了五行山下。此去经年，长安城内突然遭到山妖洗劫，童男童女哭声连连，命悬一线。危机时刻，自幼被行脚僧法明（吴文伦 配音）抚养长大的江流儿（林子杰 配音）救下了一个小女孩，结果反遭山妖追杀。经过一番追逐，江流儿无意中解除了孙悟空的封印，齐天大圣自然好好地将山妖教训了一番。因为封印未解开，悟空不得不护送江流儿和小女孩回长安，一路上又遭遇了猪八戒（刘九容 配音）和白龙马。'
    duration = 89
    style = '喜剧 动作 动画 奇幻'
    date = '20150710'
    director = '田晓鹏'
    writer = '田晓鹏 刘虎 米粒 金冉 金成'
    star = '张磊 林子杰 吴文伦 童自荣 刘九容 吴迪 刘北辰 赵乾景 周帅'

    m = Movie(name=name, summary=summary, duration=duration, style=style, date=date, director=director, writer=writer, star=star)
    m.insert()

    db.update('drop table if exists users')
    db.update('drop table if exists movies')
    db.update('drop table if exists reviews')
    db.update(User().__sql__())
    db.update(Movie().__sql__())
    db.update(Review().__sql__())
    u = User(name='Test', email='test@example.com', password='1234567890')
    u.insert()

    u = User(name='Test', email='test@example.com', password='1234567890', image='about:blank')

    u.insert()

    print 'new user id:', u.id

    u1 = User.find_first('where email=?', 'test@example.com')
    print 'find user\'s name:', u1.name

    u1.delete()

    u2 = User.find_first('where email=?', 'test@example.com')
    print 'find user:', u2
    '''
