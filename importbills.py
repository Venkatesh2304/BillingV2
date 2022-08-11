from requests import Request, Session
from datetime import datetime,timedelta
import json
from collections import defaultdict 
from creditlock import *
import random
import win32api 
import secondarybills
import time 

class Today : 
    def __init__(self) : 
        self.collection = []
        self.lines_count = {}
class my_session(Session) :
    def __init__(self,base,log) :
        self.base  = base 
        self.log = log 
        super().__init__()
    def download(self,dpath,fpath = "a.txt") :
        response = self.get("/rsunify/app/reportsController/downloadReport?filePath=" + dpath)
        open(fpath, "wb").write(response.content)
        return fpath 
    def post_json(self,url,**kwargs):
        kwargs["headers"] = {'Content-type': "application/json; charset=utf-8"}
        kwargs["data"] = json.dumps(kwargs["data"])
        print(kwargs["data"])
        return self.post(url,**kwargs)
    def get(self,url) : 
        url = self.base + url
        return super().get(url)
    def post(self,url,**kwargs) :
        kwargs["url"] = self.base + url
        data = super().post(**kwargs)
        if data.status_code != 200 : 
            print("Relogin Started")
            self.log.Auth() 
            data = super().post(**kwargs)
        try : 
           data = data.json()
        except Exception as e :
            data = data.text
        return data
def creditunlock(session,pdata) :
   for party_data in pdata : 
     releaselock(session,party_data)
class logdict(dict) : 
    def __init__(self) :
        self.status = 0 
        self.log = ""
        self.ajax = ""
def interpret(file,valid_partys,session) :
   path = "D:\\"
   with open(file) as f : 
      ikea_log = f.read()
   ikea_log = ikea_log.split('Order import process started')[-1]
   ikea_log = ikea_log.split('\n')
   tempcreditlock = []
   for log in ikea_log : 
       if "Credit Bills" in log :
           tempcreditlock.append(log.split(',')[1])
   creditlock = {}
   for party in tempcreditlock :
      party = party.replace(' ','')
      if  party in valid_partys.keys() :
             party_data = valid_partys[party]
             lock_data = getlockdetails(session,party_data) 
             party_data["billsutilised"] =  lock_data["billsutilised"]
             party_data["creditlimit"] =  lock_data["creditlimit"]
             creditlock[party] = valid_partys[party] 
   return creditlock

class Data_Class : 
            pass 
date = lambda : int((datetime.now() - datetime(1970,1,1)).total_seconds() *1000) - (330*60*1000)
class Log :
    def __init__(self,config,today,creditrelease = {}) :
       for key,value in config.items() :
           setattr(self,key,value)
       self.data = Data_Class() 
       self.today = today 
       self.creditlock = {}
       self.date = datetime.now()
       self.failure = False
       self.lines_count = {}
       self.process_time = defaultdict(lambda:-1)
       try : 
           self.session = today.session 
           self.session.log = self 
           self.session.base = self.base
       except Exception as e :
           self.session = my_session(self.base,self)
           print("session created")
       if len(creditrelease.keys()) ==  0 : 
           self.creditrelease = [] 
       else : 
           self.creditrelease =   [ data for name,data in creditrelease.items() if data["status"]  ]
       self.attrib = ["auth","sync","prevbills","collection","order","delivery","download","printbill"]
       for name in self.attrib :
          setattr(self,name,logdict())
    def start(self) :     
       process = self.process
       if not self.session : 
         process("auth")
       process("sync")
       process("prevbills")
       process("collection")
       #process("order")
       self.Order()
       process("delivery")
       if "bills" in self.__dict__.keys()  and self.bills is not None and len(self.bills) != 0 :
           process("download")
           process("printbill")
    def process(self,name,args =()) : 
      start_time = time.time()
      getattr(self,name).status = 2
      try : 
       getattr(self,name).log =  getattr(self,name[0].upper() + name[1:])(*args) 
       getattr(self,name).status = 1  
      except Exception as e: 
       getattr(self,name).log = str(e)
       getattr(self,name).status = -1
       self.error = str(e)
       self.failure =  True
      self.process_time[name] = time.time() - start_time 
      print(name , ' : ',getattr(self,name).log )
    def Auth(self) :
        data  = {'userId': self.ikea_user , 'password': self.ikea_pass , 'dbName': self.dbName , 'datetime': date() , 'diff': -330 }
        self.session.post('/rsunify/app/user/authentication.do',data=data)
        self.session.post("/rsunify/app/user/authenSuccess.htm")
    def Sync(self) :
        print(self.session.post('/rsunify/app/fileUploadId/download'),"Sync Session")
    def Prevbills(self) :
        data = getajax("getdelivery")
        delivery_all_json = self.session.post_json("/rsunify/app/deliveryprocess/billsToBeDeliver.do",data = data)["billHdBeanList"]
        delivery_all_json = delivery_all_json if delivery_all_json is not None else [] #None error tto empty list 
        self.data.prevbills  =  [ bill['blhRefrNo'] for bill in delivery_all_json ]
    def Collection(self) : 
       data  = getajax("getmarketorder")
       replaces = { "importDate": (self.date- timedelta(days = 1 )).strftime("%Y-%m-%d") + "T18:30:00.000Z",
                     "orderDate": (self.date- timedelta(days = 1 )).strftime("%Y-%m-%d") + "T18:30:00.000Z"}
       data.update(replaces)
       self.marketorder = self.session.post_json("/rsunify/app/quantumImport/validateload.do",data=data)
       #with open("market.json","w+") as f  :
       #     json.dump(self.marketorder,f)
       collection_data = self.marketorder["mcl"]
       self.filtered_collection = [ collection for collection in collection_data  if collection["pc"] not in self.today.collection ] 
       data = {"mcl":self.filtered_collection,"id":self.date.strftime("%d/%m/%Y"),
               "CLIENT_REQ_UID":"l2hgg"+str(random.randint(100,999))+"vt8agyg4sjf"}
       req = self.session.post_json("/rsunify/app/quantumImport/importSelectedCollection",data = data)
       print("Collection result : " ,req)

    def Order(self) :
      def filterorders() :
          filtered = [] 
          for orderno , items in  orders.items() :
             itm_det = items[0] #orderno in self.allowed_bills and 
             if (len(items) <= self.count and "WHOLE" not in itm_det["m"]  and  
                                                         sum( [ item["t"]*item["aq"] for item in items ] ) > 100)  : # totalAlloc - aq
                 filtered += items
          return filtered 

      pdata = self.creditrelease.copy()
      creditunlock(self.session,pdata)
      order_data = self.marketorder["mol"]
      orders = defaultdict(list)
      for order in order_data : 
          orders[order["on"]].append(order) 

      self.lines_count = { orderno:len(order) for orderno,order in orders.items() } #dummy rechanged
      self.allowed_bills = []
      self.repeated_bills = []
      for orderno,lines in self.lines_count.items() : 
        if orderno not in self.today.lines_count.keys() :
            self.allowed_bills.append(orderno)
        else :
            if self.today.lines_count[orderno] == lines : 
                self.allowed_bills.append(orderno)
            else :
                self.repeated_bills.append(orderno)
      filtered = filterorders()
      filtered_order_no = list(set([i["on"] for i in filtered ])) 
      self.orders = order_data 
      for order in self.orders : 
          if order["on"] not in filtered_order_no : 
              order["ck"] = False 
     
      valid_partys = defaultdict(lambda : {"billvalue" : 0 } )
      for order in  self.orders : 
         if order["aq"] != 0 : 
               billvalue = valid_partys[order["p"].replace(' ','')]["billvalue"] + (order["t"]*order["aq"]) 
               valid_partys[order["p"].replace(' ','')] = {"partyCode": order["pc"] , "parHllCode": order["ph"], "parId" : order["pi"]  ,
                             "billvalue":round(billvalue,2) , "salesman":order["s"],"parCodeRef": order["pc"] ,"status":False }
      data = {"mol":self.orders ,"id":self.date.strftime("%d/%m/%Y"),"cf":1,"at":True ,"so" : "'N','B'" ,"ca":0,"bm":0,"bb":0,
              "CLIENT_REQ_UID": "l6ltv7s15vr"+str(random.randint(10,99))+"mm"+str(random.randint(10,99))+ "vp"}
      
      self.order_log  =  self.session.post_json("/rsunify/app/quantumImport/importSelected",data=data)
      print(self.order_log)
      
      logfilepath = self.order_log["filePath"]
      logfile = self.session.download(logfilepath)
      
      self.logfile = logfile 
      self.creditlock = interpret(logfile,valid_partys,self.session)
      
    def Delivery(self) : 
     delivery_all_json = self.session.post_json("/rsunify/app/deliveryprocess/billsToBeDeliver.do",
                                                data = getajax("getdelivery"))['billHdBeanList']
     delivery_all_json = delivery_all_json if delivery_all_json is not None else [] #None error tto empty list 
     self.allbills  =  [ bill['blhRefrNo'] for bill in delivery_all_json ]
     delivery_bills_json = [bill for bill in delivery_all_json if bill['blhRefrNo'] not in self.data.prevbills ]
     self.detailed_bills = delivery_bills_json
     self.bills =  [  bill['blhRefrNo'] for bill in delivery_bills_json ]
     data = []
     for bill in delivery_all_json : 
       temp = {"vehicleId": "1" }
       for key in  ["blhDateStr","blhNetAmt" ,"blhRefrNo","blhSourceOfOrder" ,"eposActive","parCstNo","partyPhoneNo","semOutlet","shikharOutletAutoPosting"] :
           temp[key] = bill[key] 
       data.append(temp)
     data = {"deliveryProcessVOList" : data}
     result = self.session.post_json(url = "/rsunify/app/deliveryprocess/savebill.do", data =data)
    def Download(self) :    
      self.billfrom = str(self.bills[0])
      self.billto = str(self.bills[-1])
      _pdf = getajax_string('billpdf').replace('_billfrom_',self.billfrom).replace('_billto_',self.billto) 
      _txt = getajax_string('billtxt').replace('_billfrom_',self.billfrom).replace('_billto_',self.billto)
      _pdf = self.session.get(_pdf)
      _txt = self.session.get(_txt)
      pdf = self.session.download( _pdf.text , fpath = "bill.pdf")
      txt = self.session.download( _txt.text , fpath = "bill.txt")
    def Printbill(self,print_type = {"original":1,"duplicate":1}) : 
     secondarybills.main('bill.txt','bill.docx')
     win32api.ShellExecute (0,'print','bill.docx',None, '.', 0 )
     for i in range(0,print_type["original"] ) :
        win32api.ShellExecute (0,'print',"bill.pdf",None, '.', 0 )
    def status(self) :
     res = {}
     for attr in self.attrib : 
       attrib = getattr(self,attr)   
       classes =  ["unactive","green","blink","red"] 
       res[attr] = {"status" : attrib.status , "log":attrib.log ,"time": round(self.process_time[attr],2) ,
                    "class" : (classes[attrib.status]) } 
     return res 
    def manualprint(self,bills_list,print_type) :
       self.Auth()
       for bills in bills_list : 
            self.bills = bills 
            self.Download() 
            self.Printbill(print_type) 
            
    

   







                           
                
with open("ajax.txt") as f :
    ajax = f.read()
getajax = lambda key : eval(ajax.split("_"+key+"_")[1])
getajax_string = lambda key : ajax.split("_"+key+"_")[1].replace('\n','')















#filterData = {"beatName": "","beatNameList": [],"blhFromDt": "","blhSourceOfOrder": 0,"blhToDt": "","locNameList": [],"localityId": "","optimusSelect": 0,"salesmanNameList": [],"shakthiBusiness": "N","vehId": 0}
#headers = {'Content-type': "application/json; charset=utf-8"}
#p = session.post(base + '/rsunify/app/deliveryprocess/billsToBeDeliver.do',headers=headers,data=json.dumps(filterData))
