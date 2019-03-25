from sqlalchemy import  create_engine,Column,Integer,String,Float,Text,Enum,DateTime,PickleType,JSON,Table,ForeignKey,and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker,relationship
from datetime import datetime,timedelta
from time import sleep
import memcache
mc=memcache.Client(['127.0.0.1:11211'],debug=True)

HOST = '127.0.0.1'
PORT = '3306'
DATABASE = 'test'
USERNAME = 'root'
PASSWORD = 'root'
db_uri="mysql+pymysql://{username}:{password}@{host}:{port}/{db}?charset=utf8".format(username=USERNAME,password=PASSWORD,host=HOST,port=PORT,db=DATABASE)

engine=create_engine(db_uri)
Base=declarative_base(engine)
session=sessionmaker(engine)()


user_activity=Table(
    'user_activity',
    Base.metadata,
    Column('user_openid',Integer,ForeignKey('user.id'),primary_key=True),
    Column('activity_id',Integer,ForeignKey('activity.id'),primary_key=True)
)

host_activity=Table(
    'host_activity',
    Base.metadata,
    Column('user_openid',Integer,ForeignKey('user.id'),primary_key=True),
    Column('activity_id',Integer,ForeignKey('activity.id'),primary_key=True)
)

class Activity(Base):
    __tablename__='activity'
    id=Column(Integer,primary_key=True,autoincrement=True)
    status=Column(Enum("on_register","end_register","suspend_register","will_register","end"),default='on_register')
    key=Column(String(30))
    present_number=Column(Integer,default=0)
    score=Column(Float,default=0)
    title=Column(String(20))
    subtitle=Column(String(50))
    description=Column(Text)
    location=Column(String(20))
    location_detail=Column(Text)
    poster=Column(Text)
    max_member=Column(Integer,default=0)
    ddl_time=Column(DateTime)
    end_time=Column(DateTime)
    activity_id=Column(String(50))
    issue_date=Column(DateTime)
    

class Member(Base):
    __tablename__='member'
    id=Column(Integer,primary_key=True,autoincrement=True)
    activity_id=Column(String(50))
    openid=Column(String(50))
    code=Column(String(50))

class User(Base):
    __tablename__='user'
    id=Column(Integer,primary_key=True,autoincrement=True)
    username=Column(String(20))
    password=Column(String(20))
    activity_issue=relationship('Activity',backref='host',secondary=host_activity)
    activity_joined=relationship('Activity',backref='members',secondary=user_activity)
    location=Column(String(50))
    openid=Column(String(50))
    session_key=Column(Text)

Base.metadata.drop_all()
Base.metadata.create_all()

def user_exist(openid):
    users=session.query(User).filter(User.openid==openid).all()
    res=[]
    for user in users:
        res.append(user.openid)
    if len(res) == 0:
        return False
    else:
        return True

def activity_exist(activity_id):
    activities=session.query(Activity).filter(Activity.activity_id==activity_id).all()
    res=[]
    for activity in activities:
        res.append(activity.activity_id)  
    if len(res)==0:
        return False
    else:
        return True
def whether_joined(activity_id,openid):
    activity=get_activity_from_activity_id(activity_id)
    members=activity.members
    for member in members:
        if member.openid==openid:
            return True
        else:
            return False

def add_user(openid,location):
    user=User(username=openid,location=location)
    session.add(user)
    session.commit()

def add_session_key(openid,session_key):
    mc.set(session_key,openid,time=3600)

# def check_session(openid,session_key):
#     res=mc.get(session_key)
#     if res is not None:
#         mc.delete(session_key)
#         add_session_key(session_key,openid)
#         return True
#     else:
#         return False

def add_code(activity_id,openid,code):
    member=Member(activity_id=activity_id,openid=openid,code=code)
    session.add(member)
    session.commit()

def get_user_from_openid(openid):
    user=session.query(User).filter(User.openid==openid).first()
    return user
def get_activity_from_activity_id(activity_id):
    activity=session.query(Activity).filter(Activity.activity_id==activity_id).first()
    return activity
def get_openid_from_session_key(session_key):
    openid=mc.get(session_key)
    return openid
def register_activity(activity_id,openid):
    user=get_user_from_openid(openid)
    activity=get_activity_from_activity_id(activity_id)
    if activity==None:
        return 'not_found'
    elif (datetime.now()>activity.ddl_time) or (activity.status !='on_register') :
        return 'time_out'
    elif whether_joined(activity.activity_id,user.openid):
        return 'joined'
    elif activity.present_number>=activity.max_member:
        return 'full'
    else:
        user.activity_joined.append(activity)
        activity.present_number+=1
    return 'success'

def add_activity(openid,location,detail_location,num_max,ddl_time,poster,title,subtitle,description): 
    activity=Activity(title=title,subtitle=subtitle,description=description,location=location,location_detail=detail_location,max_member=num_max,ddl_time=ddl_time,issue_time=datetime.now)
    host=get_user_from_openid(openid)
    activity.host.append(host)
    session.add(activity)
    session.commit()

# def check_code(activity_id,openid,code)
#     member=session.query(Member).filter(and_(Member.code==code,Member.activity_id==activity_id,Member.openid==openid)).all()
#     if member != None:
#         session.delete(member)
#         session.commit()
#         return True
#     else:
#         return False
# def cancel_register(activity_id,openid):
# #     user=get_user_from_openid(openid)
# #     activity=get_activity_from_activity_id(activity_id)
# #     user.activity_joined.remove(activity)

# activity=Activity(activity_id='activity1',ddl_time=datetime.now(),present_number=10,max_member=100)
# user1=User(openid='user1')
# user4=User(openid='user4')
# activity.members.append(user4)
# activity.host.append(user1)
# session.add(activity)
# session.commit()
# # # # print(activity_exist('activity2'))

# # activity.host.append(user4)
# # session.add(activity)
# # session.commit()

# # # # user2=User(openid='user2')
# # activity.members.append(user3)
# # session.add(activity)
# # session.commit()
# # print(whether_joined('activity1','user3'))
# # cancel_register('activity1','user3')
# # print(whether_joined('activity1','user3'))

# # # activity.members.append(user2)
# # session.add(activity)
# # session.add(user3)
# # session.commit()
# # # # sleep(1)
# # # # print(get_activity_from_activity_id('activity1').members)
# # # # print(whether_joined('activity1','user1'))
# # # # print(get_activity_from_activity_id('qwe'))
# # # # print(register_activity('activity1','user1'))
# # # print(register_activity('activity1','user3'))
# # # print(activity.present_number)

# def delete_activity(activity_id,openid):
#     if activity_exist(activity_id)==False:
#         return ({
#             'flag':'not_found'
#         })
#     activity=get_activity_from_activity_id(activity_id)
#     host=activity.host[0]
#     if host.openid != openid:
#         return ({
#             'flag':'not_host'
#         })
#     session.delete(activity)
#     return ({
#             'flag':'success'
#         })

# print(activity_exist('activity1'))
# print(delete_activity('activity1','user1'))
# print(activity_exist('activity1'))