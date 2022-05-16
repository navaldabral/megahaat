from flask import Flask, render_template, make_response, Response, request,redirect,session,flash,url_for,jsonify, send_file
import time,random, string
from os.path import basename
from datetime import datetime
from functools import wraps
from flask_mysqldb import MySQL
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os,re, sys
import base64
import qrcode 
import qrcode.image.svg
from os.path import exists
import json,requests
import pdfkit
import pdb
import tldextract
from pdfdoc import *
from reportlab import *
from toolbox import *

app = Flask(__name__)

app.secret_key='5+rij1Nb5Sr1nB3bMpLqOWZSHdwK1usUga+Mwy0T'
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='Cisco123!@#'
app.config['MYSQL_DB']='archives'
app.config['MYSQL_CURSORCLASS']='DictCursor'
mysql=MySQL(app)
gmail_pwd = "test12343@$"


#check if user logged in
def is_logged_in(f):
        @wraps(f)
        def wrap(*args,**kwargs):
                print(session)
                if 'logged_in' in session:
                        return f(*args,**kwargs)
                else:
                        flash('Unauthorized, Please Login','danger')
                        return render_template('index.html')
        return wrap

@app.route('/')
@is_logged_in
def index():
	print(session['logged_in'])
	if session['logged_in'] == True:
	   print(session['site'])
	   return redirect(url_for('getData',url=session['site']))
	   #return render_template('dashboard.html', url=session['site'])
	else:
	   return render_template('index.html')


@app.route('/qrcode')
def qr_redirect():
    site=request.args.get('site')
    product=request.args.get('handle')
    print(product)
    data={}
    url=''
    if site == 'lilify':
       url="https://www.lilify.com/products/{}".format(product)
    #data['user']=user
    #f = open("_products.json","r")
    #d = f.read()
    return render_template('qrreader.html',data=url)

def emailer(receiver_email,data):
    sender_email = "kumar.k303@gmail.com"
    password = 'test12343@$'

    message = MIMEMultipart("alternative")
    message["Subject"] = "Download product catalog PDF!!!"
    message["From"] = sender_email
    message["To"] = receiver_email

    part = MIMEText(data, "html")

    message.attach(part)

    # Create secure connection with server and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(
             sender_email, receiver_email, message.as_string()
       )

def emailer2(receiver_email,site, template):
    sender_email = "kumar.k303@gmail.com"
    password = 'test12343@$'
    print(receiver_email)
    print(site)
    message = MIMEMultipart("alternative")
    message["Subject"] = "Download product catalog PDF!!!"
    message["From"] = sender_email
    message["To"] = receiver_email

    part = MIMEBase('application', "octet-stream")
   
    ext = tldextract.extract(site)
    directory = r'static/'+ext.domain+'/pdfs'
    filename=ext.domain+"_"+template+"_color.pdf"
    part.set_payload(open(directory+"/"+filename, "rb").read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment; filename='+filename)
    message.attach(part)
    # Create secure connection with server and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(
             sender_email, receiver_email, message.as_string()
       )

@app.route('/login',methods=['POST','GET'])
def login():
    print(session)
    #print(current_user.is_authenticated)
    status=True
    print(request.method)
    if request.method=='POST':
        print(request.form["email"])
        email=request.form["email"]
        pwd=request.form["upass"]
        print(email,pwd)
        cur=mysql.connection.cursor()
        cur.execute("select * from profile where USER_NAME=%s and PASSWORD=%s",(email,pwd))
        data=cur.fetchone()
        url=''
        if data:
            session['logged_in']=True
            session['username']=data["USER_NAME"]
            company = data['COMPANY']
            print(company)
            cur.execute("select * from company where COMPANY=%s",[company])
            d=cur.fetchone()
            print(d)
            url=d["SITE"]
            session['site']=url
            flash('Login Successfully','success')
            print('login success!!!! redirecting to home')
            return redirect(url_for('getData', url=url))
            #return render_template("dashboard.html",url=url)
        else:
            flash('Invalid Login. Try Again','danger')
            return render_template("index.html")


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

#Registration  
@app.route('/reg',methods=['POST','GET'])
def reg():
    status=False
    if request.method=='POST':
     print(request)
     print(request.form["company"])
     company=request.form["company"]
     address=request.form["address"]
     email=request.form["email"]
     phone=request.form["phone"]
     firstname=request.form['firstname']
     lastname=request.form['lastname']
     site=request.form['site']
     print(company, address)
     cur=mysql.connection.cursor()
     cur.execute("select * from company where COMPANY=%s and ADDRESS=%s",(company, address))
     data=cur.fetchall()
     print(data)
     if(len(data) == 0):
           
        current=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cur=mysql.connection.cursor()
        cur.execute("insert into company(COMPANY,ADDRESS,PHONE,EMAIL, CREATED_DATE, STATUS, SITE) values (%s,%s,%s,%s,%s,%s, %s)",(company,address,phone,email,datetime.now(),'INITIATED', site))
        print(cur.lastrowid)
        tmp_pwd="magik123" 
        #tmp_pwd=id_generator()
        cur.execute("insert into profile(COMPANY_ID,COMPANY,USER_NAME,PHONE,EMAIL,PASSWORD,CREATED_DATE, STATUS, FIRST_NAME, LAST_NAME) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(cur.lastrowid, company,email, phone, email,tmp_pwd,datetime.now(),'NEW', firstname, lastname))
        mysql.connection.commit()
        cur.close()
        download_link="http://labelmagik.com"
        data=''
        with open('templates/signin_email.html') as f:
            for line in f:
                data+=line.replace("check1",email).replace("check3",download_link)
                #print(data)
        emailer(email,data)
        print ('email sent')
        flash('Registration Successfully. Login Here...','success')
        return redirect(url_for('getData',url=site))
     else:
        flash('Company already regisetred. Please check with Administrator...','success')
        return redirect(url_for('index'))  
    #return render_template("dashboard.html",status=status)

#Home page
@app.route("/home")
@is_logged_in
def home():
	print("home here")
	return render_template('dashboard.html')
    
#Home page
@app.route("/dashboard")
def dashboard():
	print("====================",session)
	site=request.args.get('url')
	print(site)
	if 'logged_in' in session:
	 if session['logged_in'] == True:
           return redirect(url_for('getData',url=site)) 
	 else:  
	   return render_template('dash.html', site=site)
	else: 
	 return render_template('dash.html', site=site)  

#Home page
@app.route("/registration")
@is_logged_in
def registration():
        site=request.args.get('url')
        print(site)
        return render_template('registration.html', site=site)


#logout
@app.route("/logout")
@is_logged_in
def logout():
	session.clear()
	headers = {'Content-Type': 'text/html'}
	flash('You are now logged out','success')
	return make_response(render_template('index.html'),200,headers)
	#return redirect(url_for('index')) 


def choose_template(_template):
    #_picked_template=
    try:
       if _template=='5260':
          _picked_template=AVERY_5260_LABEL_DOC_STYLE
       elif _template=='5262':
          _picked_template=AVERY_5262_LABEL_DOC_STYLE
       elif _template=='5263':
          _picked_template=AVERY_5263_LABEL_DOC_STYLE
       elif _template=='5267':
          _picked_template=AVERY_5267_LABEL_DOC_STYLE
       elif _template=='5164':
          _picked_template=AVERY_5164_LABEL_DOC_STYLE
       else:
          _picked_template=AVERY_5263_LABEL_DOC_STYLE 
       return _picked_template
    except Exception as e:
       print(e)

def create_pdf_template(_e):
    try:
       _text_dict = {
           "border-outline": True,
           "border-width": 0.01 * inch,
           "border-colour": (1.0, 0.1, 0.2),
           # "border-colour": (0.1, 0.1, 1.0),
           # "top-margin": 0.25 * inch,
           "top-margin": 0.0025 * inch,
           "bottom-margin": 0.025 * inch,
           "left-margin": 0.15 * inch,
           "right-margin": 0.05 * inch,
           "top-padding": 0.1 * inch,
           "bottom-padding": 0.2 * inch,
           "left-padding": 0.15 * inch,
           "right-padding": 0.25 * inch,
           "background-colour": (1.0, 0.1, 0.2),
           # "background-fill": True,
           "overlay_content": False,
           "border-radius": 1,
       }
       print(_e)
       #_data=json.loads(_e)
       #print(_data)
       directory = r'static/'+_e['site']+'/images'
       _file_name=_e['site']+"_"+_e['format']
       print(directory,_file_name)
       dir = r'static/'+_e['site']+'/pdfs'
       if not os.path.exists(dir):
                os.makedirs(dir) 
       template=AVERY_5263_LABEL_DOC_STYLE
       if _e['type'] != 'demo':
          template = choose_template(_e['format'])
          _file_name = _file_name+"_color"
          directory = r'static/'+_e['site']+'/images/color'
       _file_path="static/{}/pdfs/{}.pdf".format(_e['site'],_file_name)
       print(_file_name, _file_path)
       print("pkarra",template)
       ld = LabelDoc(_file_path, style=template)
       labels = [i for i in os.listdir(directory)]
       print("before setting up the pdf")
       counter=0
       for label, row, col in ld.iter_label(labels):
           _qr_image_item_row=directory+"/"+os.listdir(directory)[counter]
           print(_qr_image_item_row)
           print(counter)
           tr = ImageRect(1 * inch, 1 * inch, _qr_image_item_row, _text_dict)
           tr.style.set_attr("horz-align", "centre")
           ld.set_table_cell(tr, row, col)
           counter+=1
           #os.remove(_qr_image_item_row)
       return _file_name
    except Exception as e:
       print(e)

def generate_pdf(e):
  try:
    print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^",e)
    ext = tldextract.extract(e)
    domain=ext.domain
    print(domain)
    directory = r'static/'+domain+'/images'
    format='5263_sample'
    type='demo'
    _json_params_from_site={"site":domain,"format":format, "type": type}
    create_pdf_template(_json_params_from_site)
  except Exception as e:
    print(e)  


@app.route("/emailpdf", methods=['GET', 'POST'])
def pdfDownload():
    email=request.args.get('email')
    site=request.args.get('url')
    ext = tldextract.extract(site)
    generate_pdf(site)
    print("==============",ext.domain) 
    gmail_user = "kumar.k303@gmail.com"
    TO = email
    SUBJECT = "[LabelMagik] Product Catalog PDF Template "
    tmp_pwd="welcome123" 
    data = ''
    length=64
    randomstr = ''.join(random.choices(string.ascii_letters+string.digits,k=length))
    download_link="http://labelmagik.com/download?template=demo&site={}&session={}".format(ext.domain,randomstr)
    print("***********",download_link)
    with open('templates/email.html') as f:
       for line in f:
          data+=line.replace("check1",email).replace("check2","magik123").replace("check3",download_link)
    #print(data)
    emailer(email,data)   
    print ('email sent')
    d={}
    d['email']=email
    d['status']='success'
    #return jsonify(d)  
    return render_template('index.html')  
    #return send_file('static/pdfs/check.pdf', as_attachment=True)


@app.route("/download", methods=['GET', 'POST'])
def download():
    try:
       ss_id=request.args.get('session')
       print(ss_id)
       site=request.args.get('site')
       type=request.args.get('template')
       template='5263_sample'
       if type != 'demo':
          template = type 
       newpath = r'static/'+site+"/pdfs/"+site+"_"+template+".pdf"
       return send_file(newpath, as_attachment=True)
    except Exception as e:
       print(e)


def repeat_qr(_data):
    try:
      site = _data['site']
      print(site)
      link = "https://"+site+".com/products.json?limit=1000"
      print(link)
      resp = requests.get(url=link)
      data = resp.json()
      product_list=[]
      company = ''
      items=json.loads(resp.text)
      print("------------------",len(items['products']))
      x=0
      #while x <= len(items['products']:
      for i in data:
        for j in data[i]:
          x = x + 1  
          products = {}
          products['id']=j['id']
          products['title']=j['title']
          products['handle']=j['handle']
          products['vendor']=j['vendor']
          company=j['vendor']
          products['product_type']=j['product_type']
          products['tags']=j['tags']
          if j['images']:
             products['image']=j['images'][0]
          else:
              products['image']='NA'
          if j['variants']:
             products['price']=j['variants'][0]['price']
             products['available']=j['variants'][0]['available']
          else:
             products['price']='NA'
             products['available']='NA'  
          checkout_link = 'http://'+site+'.com/products/'+j['handle']
          products['checkout']=checkout_link
          newpath = r'static/'+site+'/images/color'
          if not os.path.exists(newpath):
                os.makedirs(newpath)
          file_exists = exists(newpath+'/'+j['handle']+'.png')
          #file_exists = exists('static/images/'+j['handle']+'.png')
          if not file_exists:
               print("************ doesnt exists **********")
               qr = qrcode.QRCode(
                 version=1,
                 box_size=10,
                 border=5)
               qr.add_data(checkout_link)
               qr.make(fit=True)
               #factory = qrcode.image.svg.SvgPathImage
               #img = qrcode.make(checkout_link, image_factory = factory)
               img = qr.make_image(fill_color=_data['qrcolor'], back_color='white')
               img.save(newpath+'/'+j['handle']+'.png')
          products['qr']=newpath+'/'+j['handle']+'.png'
          product_list.append(products)
      #return jsonify({'var1':product_list})
      #data = jsonify({'var1':product_list})
      headers = {'Content-Type': 'text/html'}
      return render_template('home.html', data=product_list)
      #return make_response(render_template('home.html',  data=product_list),200,headers)
      #return Response(response=render_template('home.html', data=product_list)) 
    except Exception as e:
      type, value, traceback = sys.exc_info()
      print(sys.exc_info())


@app.route("/getData", methods=['GET'])
@is_logged_in
def getData():
    try:
      site = request.args.get('url')
      ext = tldextract.extract(site)
      print(ext.domain)
      link = site+"/products.json?limit=1000"
      print(link)
      resp = requests.get(url=link)
      data = resp.json()
      product_list=[]
      company = ''
      print('2222222222')
      items=json.loads(resp.text)
      print("------------------",len(items['products']))
      x=0
      #while x <= len(items['products']:
      for i in data:
        print('$#$#$#$#$#$#$#$#$$#$#$')
        for j in data[i]:
          x = x + 1  
          #print("counter",j)
          products = {}
          products['id']=j['id']
          products['title']=j['title']
          products['handle']=j['handle']
          products['vendor']=j['vendor']
          company=j['vendor']
          products['product_type']=j['product_type']
          products['tags']=j['tags']
          if j['images']:
             products['image']=j['images'][0]
          else:
              products['image']='NA'
          if j['variants']:
             products['price']=j['variants'][0]['price']
             products['available']=j['variants'][0]['available']
          else:
             products['price']='NA'
             products['available']='NA'  
          checkout_link = site+'/products/'+j['handle']
          products['checkout']=checkout_link
          newpath = r'static/'+ext.domain+'/images'
          if not os.path.exists(newpath):
                os.makedirs(newpath)
          file_exists = exists(newpath+'/'+j['handle']+'.png')
          #file_exists = exists('static/images/'+j['handle']+'.png')
          if not file_exists:
               print("************ doesnt exists **********")
               qr = qrcode.QRCode(
                 version=1,
                 box_size=10,
                 border=5)
               qr.add_data(checkout_link)
               qr.make(fit=True)
               #factory = qrcode.image.svg.SvgPathImage
               #img = qrcode.make(checkout_link, image_factory = factory)
               img = qr.make_image(fill='black', back_color='white')
               img.save(newpath+'/'+j['handle']+'.png')
          products['qr']=newpath+'/'+j['handle']+'.png'
          product_list.append(products)
      #return jsonify({'var1':product_list})
      #data = jsonify({'var1':product_list})
      headers = {'Content-Type': 'text/html'}
      return render_template('home.html', data=product_list)
      #return make_response(render_template('home.html',  data=product_list),200,headers)
      #return Response(response=render_template('home.html', data=product_list)) 
    except Exception as e:
      type, value, traceback = sys.exc_info()
      print(sys.exc_info())
    finally:
      print('write to file')
      site = request.args.get('url')
      ext = tldextract.extract(site)
      newpath = r'static/'+ext.domain+'/json/'
      if not os.path.exists(newpath):
           os.makedirs(newpath)
      with open(newpath+'_products.json', 'w') as f:
           f.write(json.dumps(product_list))




def generate(e):
  try:
    print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^",e)
    ext = tldextract.extract(e)
    domain=ext.domain
    print(domain)
    directory = r'static/'+domain+'/images'
    print(directory)
    html=''
    html+="<html><body><table>"
    html+="<tr>"
    counter=0
    for filename in os.listdir(directory):
        if counter%3 == 0:
           html+="</tr><tr>"
        if filename.endswith(".svg") or filename.endswith(".png"):
           with open(os.path.join(directory, filename)) as f:
                #img_data=f.read()
                #encoded_string = base64.b64encode(img_data.encode('utf-8'))
                #b64 = encoded_string.decode('utf-8')
                 html+="<td style='border: 1px solid #999;border-radius: 10px;height:260px;width:400px;text-align: center;'><img style='display:block;' width='100%' height='100%' src='"+os.path.join(directory, filename)+"' /><strong>"+filename+"</strong></td>"
                #html+="<td style='border: 1px solid #999;border-radius: 10px;height:260px;width:400px;text-align: center;'><img style='display:block;' width='100%' height='100%' src=data:image/svg+xml;base64,'"+b64+"' /><strong>"+filename+"</strong></td>"
           print(os.path.join(directory, filename))
        else:
           continue
        counter+=1
    html+="</tr>"
    html+="</table></body></html>"
    c_path = r'static/'+domain+'/html/'
    if not os.path.exists(c_path):
       os.makedirs(c_path)
    file1 = open(c_path+domain+'.html', 'w')
    file1.write(html)
    file1.close()
    options = {
          "enable-local-file-access": None
       }
    newpath = r'static/'+domain+'/pdfs'
    if not os.path.exists(newpath):
       os.makedirs(newpath)
    filename=newpath+'/'+domain+'.pdf'
    pdfkit.from_file(c_path+domain+'.html',filename, options=options)
    return filename
  except Exception as e:
    print(e)

@app.route("/downloadbysite", methods=['GET', 'POST'])
def file_download():
    site=request.args.get('url')
    ext = tldextract.extract(site)
    type="registered"
    domain=ext.domain
    template = request.args.get('template')
    qrcolor = request.args.get('qrcolor')
    newpath = r'static/'+domain+'/images/color'
    _json_params_from_site={"site":domain,"format":template, "type": type, "qrcolor":qrcolor}
    print(_json_params_from_site)
    if not os.path.exists(newpath):
       os.makedirs(newpath)
    if len(os.listdir(newpath)) == 0:
       repeat_qr(_json_params_from_site)    
    filename = r'static/'+domain+'/pdfs/'+domain+"_"+template+'_color.pdf'
    if os.path.exists(filename):
       os.remove(filename)
    print(filename)
    if not os.path.exists(filename):
       create_pdf_template(_json_params_from_site)
    for i in os.listdir(newpath):
       os.remove(newpath+'/'+i) 
    if request.args.get('inlineCheckOptions1') == 'download':
       site=request.args.get('url')
       #filename=generate(site)
       return send_file(filename, as_attachment=True)
    if request.args.get('inlineCheckOptions2') == 'email':
        emailer2(session['username'],site,template)
    return redirect(url_for('index')) 


@app.route("/downloadby", methods=['GET', 'POST'])
def file_download1():
    email=request.args.get('inlineCheckOptions2')
    download=request.args.get('inlineCheckOptions1')
    print(email)
    print(download)
    site=request.args.get('url')
    return request

def load_products(site):
    ext = tldextract.extract(site)
    link = site+"/products.json?limit=100"
    print("pkarra",link)
    json_path=r'static/'+ext.domain+'/json'
    if not os.path.exists(json_path):
         os.makedirs(json_path)
    print("load_proeucts from API")
    resp = requests.get(url=link)
    d = resp.json()
    data=d['products']
    #print(data)
    resp_file = open(json_path+'/'+'_products.json', 'w')
    n = resp_file.write(json.dumps(data))
    resp_file.close()
    return data

@app.route('/progress')
def progress():
    try:
        site = request.args.get('url')
        ext = tldextract.extract(site)
        print(ext.domain)
        json_path=r'static/'+ext.domain+'/json'
        data={}
        print("file_path to check",json_path)
        if os.path.exists(json_path):
           file_name='_products.json'
           file_exists = exists(json_path+'/'+file_name)
           print(json_path+'/'+file_name)
           print(file_exists)
           if not file_exists:
              print("first timers!! No worries!! fetching API data")
              data = load_products(site)
           else: 
              print("loading from existing products.json")
              with open(json_path+'/'+file_name) as f:
                  data = json.load(f)
        else:
           print("New Comers!! No worries!! fetching API data")
           data=load_products(site)
        #with open('test.json') as f:
        #    data = json.load(f)
        #create_avery_template(site)
        product_list=[]
        #site='check'
        def generate():
            x = 0
            while x <= len(data):
              #print(len(data), x)
              if x!=len(data):
                #yield "data:" + str(x) + "\n\n"
                #print(data[x]['id'])
                products = {}
                products['id']=data[x]['id']
                products['title']=data[x]['title']
                products['handle']=data[x]['handle']
                products['vendor']=data[x]['vendor']
                #company=j['vendor']
                products['product_type']=data[x]['product_type']
                products['tags']=data[x]['tags']
                if 'images' in data[x]:
                    if 'src' in data[x]:
                      #print(data[x]['images'])
                      products['image']=data[x]['images'][0]['src']
                else:
                    products['image']='NA'
                if 'variants' in data[x]:
                    products['price']=data[x]['variants'][0]['price']
                    products['available']=data[x]['variants'][0]['available']
                else:
                    products['price']='NA'
                    products['available']='NA'
                checkout_link = site+'/products/'+data[x]['handle']
                products['checkout']=checkout_link
                #check if company folder exists
                newpath = r'static/'+ext.domain+'/images'
                if not os.path.exists(newpath):
                   os.makedirs(newpath)
                file_exists = exists(newpath+'/'+data[x]['handle']+'.png')
                if not file_exists:
                    print("************ doesnt exists **********")
                    qr = qrcode.QRCode(
                        version=1,
                        box_size=10,
                        border=5)
                    qr.add_data(checkout_link)
                    qr.make(fit=True)
                    #factory = qrcode.image.svg.SvgPathImage
                    #img = qrcode.make(checkout_link, image_factory = factory)
                    img = qr.make_image(fill='black', back_color='white')
                    img.save(newpath+'/'+data[x]['handle']+'.png')
                products['qr']=newpath+'/'+data[x]['handle']+'.png'
                product_list.append(products)
                x = x + 1
              else:
                x=10000
                #time.sleep(0.2)
              json_data = json.dumps({'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'values': str(x)})
              yield "data:" + json_data + "\n\n"
              #time.sleep(0.1)
        return Response(generate(), mimetype= 'text/event-stream')
        #return render_template("dashboard.html")
    except Exception as e:
        print(e)  


if __name__ == "__main__":
	app.run(debug=True)
