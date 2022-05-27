from flask import Flask,render_template,request,redirect,send_file
from os import remove
from importbills import *
import secondarybills
from time import sleep
import sys
#import firebase_admin
#from firebase_admin import credentials
#from firebase_admin import firestore
import os
import webbrowser
from flask_cors import CORS
from collections import defaultdict
import dill as pickle 
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
CORS(app)
def save() :
   with open("logs.pkl", "wb") as f : 
     pickle.dump(Logs,f, byref=True,recurse=True) 
 

def getstringbills(arr) : 
   if len(arr) > 0 : 
     return arr[0] + ' - ' + arr[-1]
   else : 
       print(arr)
       return "" 

class Date :
    def __init__(self) : 
        self.logs = []
        self.bills = []
        self.lines_count = {}
        self.creditlock = {}
        self.collection = []
        self.success = 0 
        self.failure = 0 
        self.sessionid = False 
    def addlogs(self,count_bills = 10,creditrelease={}) :
        print("New Process started")
        config["count"]  = count_bills 
        config["sessionid"] = self.sessionid 
        log = Log(config,self,creditrelease) 
        self.current_log = log
        log.start()
        self.failure += (1 if log.failure else 0 )
        self.success += (0 if log.failure else 1 )
        self.bills += log.bills
        for key,value in log.lines_count.items() : 
            if key not in self.lines_count.keys() :
                self.lines_count[key] = value
        self.lines_count.update(log.lines_count)
        self.collection += [ collection["parCode"] for collection in  log.filtered_collection ]
        self.creditlock = log.creditlock 
        self.session = log.session
        save()
        return  { "stats" : { "Current Process Bills Count" :len(log.bills)  ,'Current Process Collection Count' : len(log.filtered_collection)  ,
                 "Today Total Bills Count": len(self.bills)  ,'Today Total Collection Count' : len(self.collection) ,
                 "Bills (Total) " : getstringbills(self.bills)   , "Bills (Last Sync) " : getstringbills(log.bills)  ,
                 "SuccessFull" : self.success , "Failures" : self.failure }  ,
                 "creditlock" : self.creditlock } 
       

@app.route('/start/<count>',methods = ["POST"])
def start(count) :  
    res = today.addlogs(int(count),request.json)
    return res  

@app.route('/status',methods = ["POST"])
def status() :
    return today.current_log.status()

@app.route('/configget',methods=['POST',"GET"])
def configget() :
        return config 
@app.route('/configsave',methods=['POST'])
def configsave() :
    new_config = request.form 
    global config 
    config.update(new_config)
    with open('config.txt','w+') as f :
        f.write(str(config))
    return config 
@app.route('/config') 
def renderconfig() :
    return app.send_static_file('config.html')
 

@app.route('/billprint')
def billprint() :
    return app.send_static_file('billprint.html')
@app.route('/print',methods=['POST'])
def prints() :
    bills=[]
    billprefix = config["name"]
    x=request.form['p']
    for i in x.split('**') :
        if i=='' :
            continue
        else :
            try :
              billfrom=i.split('-')[0]
              billto=i.split('-')[1]
              billfrom = billprefix + billfrom.replace(billprefix,"")
              billto = billprefix + billto.replace(billprefix,"")
              bills.append([billfrom,billto])
            except Exception as e:
                print(e)
    temp = Log(config,None)
    print_type = { "duplicate" : 1 ,"original":0}
    if request.form["types"] == "Both copy"  :
        print_type["original"] = 1 
    temp.manualprint(bills,print_type)
    return redirect('/billprint')




@app.route('/billindex')
def index() :
    return app.send_static_file('index.html')

try : 
  with open('logs.pkl','rb') as f : 
   Logs = pickle.load(f,ignore=False)
except :
    print("New Logs created , Before is stuck couldnt retrieve ")
    Logs = defaultdict(Date)

print(type(Logs))
try : 
  today = Logs[datetime.now().strftime('%d/%m/%Y')]
except Exception as e :
    print(e)
    Logs = defaultdict(Date)
    today = Logs[datetime.now().strftime('%d/%m/%Y')]

dates = list(Logs.keys())
dates.sort(key = lambda date : datetime.strptime(date,'%d/%m/%Y'))
if len(dates) >= 10 : 
  dates = dates[-10:]
Logs = {key:value for key,value in Logs.items() if key in dates }


with open('config.txt') as f : 
     config = eval(f.read())

webbrowser.open('http://127.0.0.1:5000/billindex')
app.config['JSON_SORT_KEYS'] = False
app.run(threaded=True)
