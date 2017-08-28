from flask import Flask, url_for, redirect, render_template, flash, request, session, jsonify
from subprocess import Popen
import os
import time
from flask_login import (LoginManager, login_required, login_user,
                            logout_user, current_user)
from Form import LoginForm, RegistrationForm
import json
from models import User, Process, START, SCANNED, END
import database
import controller
import signal
import traceback
import logging
from logging import FileHandler
from logging import Formatter
import utils
import pymongo
import redis
import sys
sys.path.append('./pycharm-debug-py3k.egg')
import pydevd

app = Flask(__name__)

app.jinja_env.variable_start_string = '{{ '
app.jinja_env.variable_end_string = ' }}'

appFileHandler = FileHandler(filename=os.path.abspath('flask.log'))
appFileHandler.setLevel(logging.DEBUG)
appFileHandler.setFormatter(Formatter(
    '%(asctime)s %(levelname)s: %(message)s '
    '[in %(pathname)s:%(lineno)d]'
))

app.logger.addHandler(appFileHandler)



database.init_db()
saved_directory = os.path.dirname(os.path.abspath(__file__)) + '/static/user'

def handle_signal(signum, frame):
    print ("信号{0}被捕捉".format(signum))
    os.waitpid(0,0)

signal.signal(signal.SIGCHLD, handle_signal)


# 增加flask验证代码============
app.secret_key = 's3cr3t'
login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.login_view = 'login'
login_manager.init_app(app)


@app.teardown_request
def shutdwon_session(exception=None):
    database.db_session.remove()


@app.errorhandler(500)
def internal_server_error(e):
    app.logger.exception('error 500: %s', e)

    return "500"


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    print("register in........")  ##TO DELETE
    if request.method == 'POST' and form.validate():
        print("valid form")
        user = User(form.user_id.data, form.password.data, form.phone_number.data)

        if controller.verify_register(user):
            print("注册成功，准备加入数据库。。。") ##TO DELETE
            controller.add_user(user)
            flash('欢迎注册')
            return redirect(url_for('login'))
        else:
            flash('用户名重复，请重新选择')
            return render_template('register.html', form=form)

    return render_template('register.html', form=form)


@login_manager.user_loader
def load_user(user_id):
    return controller.getInstanceOfUser(user_id)


@app.route('/')
@login_required
def index():
    return render_template('index.html', )


@app.route('/login', methods=['GET', 'POST'])
def login():
    app.logger.error("enter login")
    form = LoginForm(request.form)
    if request.method == 'GET':
        return render_template('newlogin.html', form=form)

    if form.validate() and request.method == 'POST':
        print("Valid login Form...")      ##TO DELETE
        user_id = request.form.get('user_id', None)
        password = request.form.get('password', None)

        ##验证密码账号是否正确
        user = controller.verify_password(user_id=user_id, password=password)
        if user is not None:
            login_user(user)
            flash('登陆成功')
            return redirect(url_for('index'))

    ##鉴定失败，返回登录页面
    flash("用户名或密码错误，请重新输入")
    return render_template('login.html', form=form)


@app.route('/logout', methods=['GET','POST'])
@login_required
def logout():
    logout_user()
    flash("你已经登出用户")
    return redirect('/login')




@app.route('/start_process')
@login_required
def start_process():


    ##如果当前用户有进程还在运行，则不允许开始新的进程
    if not controller.startNewProcessPermission(current_user.user_id):
        flash("对不起，你目前还处于信息托管状态，请先点击'结束托管'后再重新开始托管")
        return render_template('index.html')

    wechatProcess = Popen(['/usr/bin/python3', 'weixin_dev.py', current_user.user_id], shell=False)
    #controller.addNewProcess(current_user.user_id, wechatProcess.pid)


    ##等待图片生成
    # time.sleep(10)
    return redirect(url_for('show_image'))


@app.route('/show_image')
@login_required
def show_image():

    return render_template('scan.html')


@app.route('/start_survey', methods=['GET', 'POST'])
@login_required
def start_survey():

    ##如果当前用户还没有启动托管，则需要让用户点击开始托管
    friendList = utils.getFriendList(current_user.user_id)
    if friendList == False:
        flash("对不起，请先点击'开始托管'之后再开始填写您的调查问卷")
        return render_template('index.html')

    ##转到欢迎页面
    return render_template('start_survey.html')



##客户端异步请求好友名单
@app.route('/api/friendList')
def friendList():
    # pydevd.settrace('123.116.203.51', port=5678, stdoutToServer=True, stderrToServer=True)
    friendList = utils.getFriendList(current_user.user_id)
    return jsonify(friendList)


@app.route('/survey', methods=['GET','POST'])
@login_required
def survey():

    ##从欢迎页面跳转过来，返回第一个页面
    if request.method == 'GET':
        survey_type = request.args.get('survey_type')
        print("GET survey_type is {0}".format(survey_type))
        print(survey_type)

        if int(survey_type) == 0:
            return render_template('basicSurvey.html', survey_type=1, user_id=current_user.user_id)

        if int(survey_type) == 2:
            return render_template('contactlistSurvey.html', survey_type=3, notice="是我们的铁哥们或闺蜜，或者经常联系的亲戚，但不如家人与我们那样亲密,从中选择5人",\
                                   user_id=current_user.user_id, min_need_number=3, max_need_number=5)

        if int(survey_type) == 3:
            return render_template('contactlistSurvey.html', survey_type=4, notice="我们愿与其长期交往，可能相互欠人情，相互帮忙的关系,从中选择10人",\
                                   user_id=current_user.user_id, min_need_number=10, max_need_number=10)

        if int(survey_type) == 4:
            return render_template('contactlistSurvey.html', survey_type=5, notice="现在会联系，但不一定与其长期交往，也并不会互相欠人情,从中选择10人",\
                                   user_id=current_user.user_id, min_need_number=10, max_need_number=10)

        if int(survey_type) == 5:
            return render_template('contactlistSurvey.html', survey_type=6, notice="我们存过他们的电话号码，但也不打算与其长期交往，以后也几乎不会联系,从中选择10人",\
                                   user_id=current_user.user_id, min_need_number=10, max_need_number=10)

        if int(survey_type) == 6:
            return render_template('thanks.html', \
                                   user_id=current_user.user_id)

    elif request.method == 'POST':
        survey_type = request.form.get('survey_type')
        print("POST survey_type is {0}".format(survey_type))
        print(survey_type)
        if int(survey_type) == 1:
            gender = request.form.get('gender')
            age = request.form.get('age')
            marriage = request.form.get('marriage')
            literacy = request.form.get('literacy')
            hukou = request.form.get('hukou')
            religion = request.form.get('religion')
            occupation = request.form.get('occupation')
            personal_salary = request.form.get('personal_salary')
            total_venue = request.form.get('total_venue')
            social_status = request.form.get('social_status')

            with open('./static/user/{0}/nickname'.format(current_user.user_id)) as fp:
                nickname = fp.read()

            questionnaire = {
                "user_id": current_user.user_id,
                "nickname": nickname,
                "gender": gender,
                "age": age,
                "marriage": marriage,
                "literacy": literacy,
                "hukou": hukou,
                "religion": religion,
                "occupation": occupation,
                "personal_salary": personal_salary,
                "total_venue": total_venue,
                "social_status": social_status
            }

            session['questionnaire'] = json.dumps(questionnaire)

            return render_template('contactlistSurvey.html', survey_type=2, notice="与我们最亲密的，常常是家人或者被我们看做是家人的极为亲密的好友",\
                               user_id=current_user.user_id, max_need_number=3, min_need_number=2)



        ###处理选出的最亲密的三人
        if int(survey_type) == 2:
            questionnaire = json.loads(session['questionnaire'])


            ##调查过的人需要从列表里面删除掉
            remove_list = request.form.getlist('select_list[]')
            utils.removeSelectPeople(current_user.user_id,remove_list)
            questionnaire['intimate_friend'] = remove_list

            session['questionnaire'] = json.dumps(questionnaire)
            print("LLLLLLLLLLLLLLL")
            return str(2)
        ###处理选出的选出铁哥们五人
        if int(survey_type) == 3:
            questionnaire = json.loads(session['questionnaire'])
            remove_list = request.form.getlist('select_list[]')
            questionnaire['good_friend'] = remove_list
            utils.removeSelectPeople(current_user.user_id,remove_list)
            session['questionnaire'] = json.dumps(questionnaire)
            return str(3)

        ###处理选出互相帮忙的十人
        if int(survey_type) == 4:
            questionnaire = json.loads(session['questionnaire'])
            remove_list = request.form.getlist('select_list[]')
            questionnaire['help_friend'] = remove_list
            utils.removeSelectPeople(current_user.user_id,remove_list)
            session['questionnaire'] = json.dumps(questionnaire)
            return str(4)

        ###处理不一定长期联系的十人
        if int(survey_type) == 5:
            questionnaire = json.loads(session['questionnaire'])
            remove_list = request.form.getlist('select_list[]')
            questionnaire['not_frequently_contact_friend'] = remove_list
            utils.removeSelectPeople(current_user.user_id,remove_list)
            session['questionnaire'] = json.dumps(questionnaire)
            return str(5)

        ###处理几乎不会联系的十人,并且返回感谢页面
        if int(survey_type) == 6:
            questionnaire = json.loads(session['questionnaire'])
            remove_list = request.form.getlist('select_list[]')
            questionnaire['not_contact_friend'] = remove_list


            client = pymongo.MongoClient('localhost', 27017)
            db = client['try']
            questionnaires = db['questionnaire']
            print(questionnaire)
            id = questionnaires.insert(questionnaire)

            return str(6)



@app.route('/check')
def check():
    print("start_check")
    if controller.checkWhetherScanned(current_user.user_id) is False:
        return json.dumps({'status': False})

    os.remove('{0}/{1}/qrcode/qrcode.jpg'.format(saved_directory, current_user.user_id))
    ret = True

    return json.dumps({'status': ret})


@app.route('/kill_process')
@login_required
def kill_processs():
    controller.endProcess(current_user.user_id)
    return render_template("index.html")


@app.route('/generate_report')
def generate_report():
    pass


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=3000)



