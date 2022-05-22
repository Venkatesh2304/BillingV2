import json 

def getlockdetails(session,party_data) :  
  url_rec = '/rsunify/app/billing/partyinfo.do?partyId=_parId_&partyCode=_parCode_&parCodeRef=_parCodeRef_&parHllCode=_parCodeHll_&plgFlag=true&salChnlCode=&isMigration=true&blhSourceOfOrder=0'
  for key,value in party_data.items() : 
      url_rec = url_rec.replace('_'+key+'_',str(value))
  req = session.get(url_rec).json() 
  outstanding = req["collectionPendingBillVOList"] 
  breakup = [ [bill["pendingDays"],bill["outstanding"]]  for bill in outstanding ]
  breakup.sort(key=lambda x: x[0],reverse=True)
  breakup = "/".join( [ str(bill[0])+"*"+str(bill[1]) for bill in breakup ] )
  return { "billsutilised" : req["creditBillsUtilised"] , "creditlimit": breakup } 



def releaselock(session,party_data) :  
  # party_data = { "parCode": "P-P18078" , "parCodeHll": "HUL-413724D-P3364","parCodeRef": "D-P18078" , "parId": 5582 }
  url_rec = '/rsunify/app/billing/partyinfo.do?partyId=_parId_&partyCode=_parCode_&parCodeRef=_parCodeRef_&parHllCode=_parCodeHll_&plgFlag=true&salChnlCode=&isMigration=true&blhSourceOfOrder=0'
  for key,value in party_data.items() : 
      url_rec = url_rec.replace('_'+key+'_',str(value))
  party_data = session.get(url_rec).json()
  response = {"parCodeRef":party_data["parCodeRef"] ,"parCodeHll":party_data["parCodeHll"] ,"showPLG":party_data["showPLG"], "creditLimit":req["creditLimit"],
                 "creditDays":party_data["creditDays"],"newlimit":int(party_data["creditBillsUtilised"])+1  } 
  url_send = '/rsunify/app/billing/updatepartyinfo.do?partyCodeRef=_parCodeRef_&creditBills=_newlimit_&creditLimit=_creditLimit_&creditDays=0&panNumber=&servicingPlgValue=_showPLG_&plgPartyCredit=true&parHllCode=_parCodeHll_'
  for key,value in response.items() : 
      url_send = url_send.replace('_'+key+'_',str(value))
  url_send = session.get( url_send.replace('+','%2B') )

  
  
  
  
  
  
  



#null = { parHULCreditBills,parHULCreditLimit ,parHULCreditDays ,parDETSCreditBills ,parDETSCreditLimit ,parDETSCreditDays ,parFNBCreditBills ,parFNBCreditLimit ,parFNBCreditDays ,parPPCreditBills ,parPPCreditLimit ,parPPCreditDays }