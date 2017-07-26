from flask import Flask, url_for, redirect, render_template, flash, request
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



app = Flask(__name__)

saved_directory = os.path.dirname(os.path.abspath(__file__)) + '/static'






# 增加flask验证代码============
app.secret_key = 's3cr3t'
login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.login_view = 'login'
login_manager.init_app(app)


@app.teardown_request
def shutdwon_session(exception=None):
    database.db_session.remove()


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
    form = LoginForm(request.form)
    if request.method == 'GET':
        return render_template('login.html', form=form)

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

    wechatProcess = Popen('python3 weixin_dev.py ' + current_user.user_id, shell=True)
    controller.addNewProcess(current_user.user_id, wechatProcess.pid)


    ##等待图片生成
    time.sleep(10)
    return redirect(url_for('show_image'))


@app.route('/show_image')
@login_required
def show_image():
    print("refresh message")
    return render_template('scan.html')


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
    process_id = controller.getProcessId(current_user.user_id)
    os.kill(process_id, 9)
    print("process {0} has been killed".format(process_id))
    controller.endProcess(current_user.user_id)
    return render_template("index.html")


@app.route('/generate_report')
def generate_report():
    pass


if __name__ == '__main__':
    database.init_db()
    from werkzeug.contrib.fixers import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.run(debug=False)



