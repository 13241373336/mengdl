from flask import Flask,request,jsonify,session
from models import *
import requests
import json
from code import *
import time
import random
import memcache
import os
from wtforms import Form,FileField,StringField
from werkzeug.utils import secure_filename
from flask_wtf.file import  FileAllowed,FileRequired
from werkzeug.datastructures import CombinedMultiDict
from mem import *
app=Flask(__name__)

class uploadForm(Form):  
    avatar=FileField(validators=[FileRequired(),FileAllowed(['jpg'])])

@app.route('/first_login',methods=['POST','GET'])
def first_login():

    code=request.form.get('code')
    url='https://api.weixin.qq.com/sns/jscode2session?appid=APPID&secret=SECRET&js_code=JSCODE&grant_type=authorization_code'
    params={
        'appid':"小程序的appid",
        'secret':"小程序的appSecret",
        'js_code':code,
        'grant_type':'authorization_code'
    }
    res=requests.get(url,params=params)
    data=json.loads(res.text)
    openid=data.get('openid')
    session_key=data.get('session_key')
    add_session_key(openid,session_key)
    error_code=data.get('error_code')
    location=data.get('location')
    bind=user_exist(openid)
    if not bind:
        add_user(openid,location)
    return jsonify({
        'bind':bind,
        'error_code':error_code,
        'session':session_key
    })
@app.route('/join',methods=['GET','POST'])
def register():
    if check(session) == False:
        return jsonify({
            'flag':'error',
            'reason':'time_out'
        })
    session=request.headers.get('session')
    openid=get_openid_from_session_key(session)
    activity_id=request.form.get('activity_id')
    res=register_activity(activity_id,openid)
    if res=='success':
        return jsonify({
            'flag':'success',
            'reason':'success'
        })
    else :
        return jsonify({
            'flag':"error",
            'reason':res
        })

@app.route('/cancel_register',methods=['GET','POST'])
def cancel_register():
    if check(session) == False:
        return jsonify({
            'flag':'time_out'
        })
    session=request.headers.get('session')
    activity_id=request.form.get('activity_id')
    openid=get_openid_from_session_key(session)
    user=get_user_from_openid(openid)
    if activity_exist(activity_id)==False:
        return jsonify({
            'flag':'not_found'
        })
    activity=get_activity_from_activity_id(activity_id)
    if whether_joined == None :
        return jsonify({
            'flag':'not_join'
        })
    user.activity_joined.remove(activity)
    return jsonify({
        'flag':'success'
    })

@app.route('/delete_activity',methods=['POST','GET'])
def delete_activity():
    if check(session) == False:
        return jsonify({
            'flag':'time_out'
        })
    session=request.headers.get('session')
    activity_id=request.form.get('activity_id')
    openid=get_openid_from_session_key(session)
    if activity_exist(activity_id)==False:
        return jsonify({
            'flag':'not_found'
        })
    activity=get_activity_from_activity_id(activity_id)
    host=activity.host
    if host.openid != openid:
        return jsonify({
            'flag':'not_host'
        })
    session.delete(activity)
    return jsonify({
            'flag':'success'
        })

@app.route('/stop_enter',methods=['POST','GET'])
def stop_enter():
    if check(session) == False:
        return jsonify({
            'flag':'time_out'
        })
    session=request.headers.get('session')
    openid=get_openid_from_session_key(session)
    activity_id=request.form.get('activity_id')
    if not activity_exist(activity_id):
        return jsonify({
            'flag':'not_found'
        })
    activity=get_activity_from_activity_id(activity_id)
    if activity.host.openid!=openid:
        return jsonify({
            'flag':'not_host'
        })
    if activity.status!='on_register':
        return jsonify({
            'flag':'stop_register'
        })
    activity.status='end_register'
    return {
        jsonify({
            'flag':'success'
        })
    }

@app.route('/start_enter',methods=['POST','GET'])
def start_enter():
    if check(session) == False:
        return jsonify({
            'flag':'time_out'
        })
    session=request.headers.get('session')
    openid=get_openid_from_session_key(session)
    activity_id=request.form.get('activity_id')
    if not activity_exist(activity_id):
        return jsonify({
            'flag':'not_found'
        })
    activity=get_activity_from_activity_id(activity_id)
    if activity.host.openid!=openid:
        return jsonify({
            'flag':'not_host'
        })
    if activity.status == 'on_register':
        return jsonify({
            'flag':'on_register'
        })
    if datetime.now>activity.ddl_time:
        return jsonify({
            'flag':'time_out'
        })
    if datetime.now>activity.end_time:
        return jsonify({
            'flag':'end'
        })
    activity.status='on_register'
    return {
        jsonify({
            'flag':'success'
        })
    }

@app.route('/get_user_info',methods=['POST','GET'])
def get_user_info():
    if check(session) == False:
        return jsonify({
            'flag':'time_out'
        })
    session=request.headers.get('session')
    openid=get_openid_from_session_key(session)
    if not user_exist(openid):
        return jsonify({
            'flag':'not_found'
        })
    user=get_user_from_openid(openid)
    activities_issue=user.activity_issue
    res_issue=[]
    for activity in activities_issue:
        res_issue.append(activity.activity_id)
    issue_num=len(res_issue)
    activities_joined=user.activity_joined
    res_joined=[]
    for activity in activities_joined:
        res_joined.append(activity.activity_id)
    joined_num=len(res_joined)
    location=user.location
    return jsonify({
        'flag':'success',
        'location':location,
        'num_joined':joined_num,
        'activity_joined':res_joined,
        'num_issue':issue_num,
        'activity_issue':res_issue
    })

@app.route('/get_activity',methods=['POST','GET'])
def get_activity():
    if check(session) == False:
        return jsonify({
            'flag':'time_out'
        })
    session=request.headers.get('session')
    openid=get_openid_from_session_key(session)
    activity_id=request.form.get('activity_id')
    if not activity_exist(activity_id):
        return jsonify({
            'flag':"not_found"
        })
    activity=get_activity_from_activity_id(activity_id)
    status=activity.status
    present_number=activity.present_number
    score=activity.score
    title=activity.title
    subtitle=activity.subtitle
    description=activity.description
    location=activity.location
    location_detail=activity.location_detail
    poster=activity.poster
    max_member=activity.max_member
    ddl_time=activity.ddl_time
    if whether_joined(activity_id,openid):
        code=random.randrange(1000000000,999999999)
        create_codes(code)
        barcode_url='barcode/'+str(code)+'.jpg'  
        qrcode_url='barcode/'+str(code)+'.jpg'  
        add_code(activity_id,openid,code)
        return jsonify({
            'flag':"success",
            "status":status,
            'present_number':present_number,
            "score":score,
            "title":title,
            "subtitle":subtitle,
            "description":description,
            "location":location,
            "location_detail":location_detail,
            "poster":poster,
            "max_member":max_member,
            "ddl_time":ddl_time,
            'barcode_url':barcode_url,
            'qrcode_url':qrcode_url
         })
    
@app.route('/scan_code',methods=['GET','POST'])
def scan_code():
    if check(session) == False:
        return jsonify({
            'flag':'error',
            'reason':'time_out'
        })
    session=request.headers.get('session')
    openid=get_openid_from_session_key(session)
    code=request.form.get('code')
    member=session.query(Member).filter(and_(Member.code==code,Member.activity_id==activity_id,Member.openid==openid)).all()
    if member != None:
        session.delete(member)
        session.commit()
        os.remove('qrcode/'+str(code)+'.jpg')
        os.remove('barcode/'+str(code)+'.jpg')
        return jsonify({
            'flag':'success'
        })
    else:
        return jsonify({
            'flag':'error'
        })

@app.route('/issue_activity',methods=['GET','POST'])
def issue_activity():
    session=request.headers.get('session')
    openid=get_openid_from_session_key(session)
    form=uploadForm(CombinedMultiDict([request.form,request.files]))
    location=request.form.get('location')
    location_detail=request.form.get('detail_location')
    activity_id=location_detail+str(random.randrange(100,999))
    max_member=request.form.get('num_max')
    ddl_time=request.form.get('ddl_time')
    title=request.form.get('title')
    subtitle=request.form.get('subtitle')
    description=request.form.get('description')
    if form.validate():    
        desc=request.form.get('desc')
        avatar=request.files.get('avatar')
        filename=secure_filename(avatar.filename)
        poster='/poster'+activity_id+'.jpg'
        avatar.save(poster)
        add_activity(openid,location,location_detail,max_member,ddl_time,poster,title,subtitle,description)
        return jsonify({
            'flag':'success'
        }) 
    else:
        return jsonify({
            'flag':'file_error'
        })

@app.route('/get_activities')
def get_activities():
    location=request.form.get('location')
    order_by=request.form.get('order_by')
    if location != None:
        if order_by == 'score':
            activities=session.query(Activity).filter(Activity.location==location).order_by(Activity.score).all()
        if order_by=='score_reversed':
            activities=session.query(Activity).filter(Activity.location==location).order_by(Activity.score.desc()).all()
        if order_by=='date':
            activities=session.query(Activity).filter(Activity.location==location).order_by(Activity.issue_date).all()               
        res=[]
        for activity in activities:
            res.append(activity.activity_id)
        num=len(res)
        if len(res)==0:
            return jsonify({
                'flag':'not_found',
                'num':0,
                'detail':[]
            })
        else:
            return jsonify({
                'flag':'success',
                'num':num,
                'detail':res
            })
    else:
        if order_by == 'score':
            activities=session.query(Activity).order_by(Activity.score).all()
        if order_by=='score_reversed':
            activities=session.query(Activity).order_by(Activity.score.desc()).all()
        if order_by=='date':
            activities=session.query(Activity).order_by(Activity.issue_date).all()               
        res=[]
        for activity in activities:
            res.append(activity.activity_id)
        num=len(res)
        if len(res)==0:
            return jsonify({
                'flag':'not_found',
                'num':0,
                'detail':[]
            })
        else:
            return jsonify({
                'flag':'success',
                'num':num,
                'detail':res
            })

@app.route('/check_session')           
def check_session():
    session=request.headers.get('session')
    check(session)
    if check(session):
        return jsonify({
            'flag':'success',
        })
    else:
        return jsonify({
            'flag':'time_out'
        })

if __name__=='__main__':
    app.run(host='0.0.0.0',port=5000)