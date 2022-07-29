from googlefinance import *
import json
import numpy as np
import sqlite3
import time 
import utility_ml
import os
import logging.config
import requests 
import logging
import datetime


from urllib2 import urlopen #( pyton 2.7) 
#from urllib.request import urlopen # python3 

#collecting current path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

#Setup logging configuration
logPath = os.path.join(BASE_DIR, 'loggingConfig.json')
logExsists = os.getenv('LOG_CFG', None)


if logExsists:
        logPath = logExsists
if os.path.exists(logPath):
        print( "Application Loading........ \n Logger config Found, starting to LOG ....." ) 
        with open(logPath, 'rt') as f:
                config = json.load(f)
        logging.config.dictConfig(config)
else:
        logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)      




class SEVENTEEN_MIN_STRCT:
        def __init__ (self):
                self.ticker= None # or whatever
                self.date = None 
                self.time = None
                self.price = None
                self.volume = None
                self.opening_price = None 
                self.us_fetch_date_time = None
                self.last_closing_price = None 
                self.current_ratio  = None 
                self.target_price = None 


        def printContent(self): 
                contentStr=  '\n\n\n         Ticker =' +  str(self.ticker) + '\n         Date =' +  str(self.date) + '\n         Time =' +  str(self.time) +  '\n         Price =' + str(self.price) + '\n         Volume =' + str(self.volume) + '\n         Opening price =' + str(self.opening_price)+  '\n         US Date Time = '+ str(self.us_fetch_date_time) +  '\n         Last closing Proce = '+ str(self.last_closing_price)
                print ( contentStr ) 
                logger.info (contentStr) 


def createConnection(db_file):
        try:
                logger.info("Trying to Open connection") 
                conn = sqlite3.connect(db_file)
                return conn
        except sqlite3.Error as e:
                print(e)

        return None



def loadInto_17MinTable_DB ( pTableDataStrct, pConn ): 

        logger.info("Loading into 17Min Table.")    

        cur = pConn.cursor() 

        sql_query = "insert into SEVENTEEN_MIN_TABLE (TICKER, PRICE, VOLUME, US_FETCH_DT, DATE, TIME, LAST_CLOSING_PRICE, OPENING_PRICE ) values (?, ?, ?, ?, ?, ?, ?, ?)"   
        sql_data = (pTableDataStrct.ticker,  pTableDataStrct.price,  pTableDataStrct.volume, pTableDataStrct.us_fetch_date_time, pTableDataStrct.date, pTableDataStrct.time, pTableDataStrct.opening_price, pTableDataStrct.last_closing_price)


        try:
                logger.info("Trying to execute "+ sql_query +  " \n with data" + str(sql_data) ) 
                cur.execute(sql_query, sql_data)
                pConn.commit()
                logger.info("Trying to COMMIT" ) 
        except sqlite3.Error as er:
                logger.info( 'Error = ', er)



def pushoutAlert(pTargetAlertRecipient, pMethodOfAlertStr, pAlertMessage, pTickerContainer17):

        logger.info("Pushing out Alerts!")   

        if (pMethodOfAlertStr.lower() == str("Urgent").lower() ): 
                utility_ml.sendFCM(pTargetAlertRecipient, pTickerContainer17.ticker, pTickerContainer17.price , pTickerContainer17.current_ratio, pTickerContainer17.target_price, pTickerContainer17.date, pTickerContainer17.time, "Urgent" )   
               
        elif (pMethodOfAlertStr.lower() == str("Normal").lower() ): 
                utility_ml.sendEmail(pTargetAlertRecipient, pAlertMessage )
        else: logger.info(" No aleart could be sent " + str(locals().keys())) 


def verifyAlertThreshold (pTickerContainer17, pConn): 

        logger.info("Checking against Target Database")   
        sql_query = "SELECT SCORE_CARD.TARGET_PRICE, SCORE_CARD.TICKER, SCORE_CARD.NOTI_TARGET_NORMAL, SCORE_CARD.NOTI_TARGET_URGENT, SCORE_CARD.URGENT_THRESH_RATIO, SCORE_CARD.NORMA_THRESH_RATIO, SCORE_CARD.BUY_PRICE, SCORE_CARD.OPERATION_TYPE FROM SCORE_CARD WHERE TICKER='" +pTickerContainer17.ticker  + "' ORDER BY ROWID ASC LIMIT 1"
        buyOrSell = "SELL"
        
        cur = pConn.cursor() 
        logger.info("Got connection. Trying to execute " + sql_query)

        cur.execute (sql_query)
        allRows = cur.fetchall()


        if (len(allRows)> 0 ): 
                for row in allRows:
                        targetPrice = row[0]
                        targetNoti_norm = row[2] 
                        targetNoti_urg = row[3]
                        targetNormRatio = row[5]
                        targetUrgRatio = row[4]
                        costPrice = row[6]
                        currentRatio = utility_ml.ratio (float(pTickerContainer17.price), targetPrice)
                        pTickerContainer17.current_ratio = currentRatio
                        pTickerContainer17.target_price = targetPrice
                        
                        buyOrSell= row[7]
                        
                        logger.info("pTickerContainer17.price = " + str(pTickerContainer17.price) + "  , targetPrice = " + str(targetPrice )) 



        if (buyOrSell == 'SELL'): 


                if ( currentRatio >= targetUrgRatio ):                                                                                                                                                                                                                                                                                                                                                                                      
                        logger.info("Notification: " + targetNoti_urg + "   Type= Urgent, " +  "Urgent notice for :" + pTickerContainer17.ticker +  ". CurrentRatio ="+ str(currentRatio) +"  targetUrgRatio =" +  str(targetUrgRatio)  )                                                                                                                                                                                                       
                        pushoutAlert(targetNoti_urg,"Urgent", "Urgent notice for "+pTickerContainer17.ticker + ". Running sale price  at : " + pTickerContainer17.price + " which is within " + str( abs (round(((currentRatio*100) - 100),2 ))) + " % of your target Price of : " +str(targetPrice)  , pTickerContainer17)                                                                                                                                              

                elif ( currentRatio >= targetNormRatio ):                                                                                                                                                                                                                                                                                                                                           
                        logger.info("Notification: " + targetNoti_norm + " Type= Normal  " + "Normal notice for :"+pTickerContainer17.ticker)                                                                                                                                                                                                                                                                                                   
                        pushoutAlert(targetNoti_norm, "Normal", " CurrentRatio ="+ str(currentRatio) +"  targetUrgRatio =" +  str(targetUrgRatio) +    ". Heads-Up notice for "+pTickerContainer17.ticker + " Its cost at: " +str(costPrice)+ " while running sale price at : " + pTickerContainer17.price + " which is " + str(abs(round((100- (currentRatio*100) ),2 ))) + " % remaining to hit the target Price of : " +str(targetPrice)  , pTickerContainer17)        

                else:logger.info("No Notification condition at " + str(currentRatio) + "  for:  " + pTickerContainer17.ticker )       

        elif ((buyOrSell == 'BUY') and (currentRatio > 0 )) :  
                if (  currentRatio <= targetUrgRatio):  
                        logger.info("Notification: " + targetNoti_urg + "   Type= Urgent, " +  "Urgent BUY notice for :" + pTickerContainer17.ticker )
                        pushoutAlert(targetNoti_urg, "Urgent", "Urgent BUY notice for "+pTickerContainer17.ticker + " Its Running price  at : " + pTickerContainer17.price + " which is " + str(round(((currentRatio*100) - 100),2 )) + " % higher than target Price of : " +str(targetPrice)  , pTickerContainer17)     

                elif ( (currentRatio  >  targetUrgRatio ) and  currentRatio <= targetNormRatio ):  
                        logger.info("Notification: " + targetNoti_norm + " Type= Normal  " + "Normal BUY notice for :"+pTickerContainer17.ticker)
                        pushoutAlert(targetNoti_norm, "Normal",  "Heads-Up BUY notice for "+pTickerContainer17.ticker + " Its running sale price at : " + pTickerContainer17.price + " which is " + str(round((100- (currentRatio*100) ),2 )) + " % remaining to hit the target Price of : " +str(targetPrice)  , pTickerContainer17)     

                else:logger.info("No BUY Notification condition at " + str(currentRatio) + "  for:  " + pTickerContainer17.ticker )              


        else: logger.info(" No Data Found in Score_Card Table")



def getDataFromAPI ( pTickerContainer17, pTargetTickersAry, pConn): 

        for item in pTargetTickersAry: 
                                
                rsp = requests.get('https://finance.google.com/finance?q='+str(item)+'&output=json')
                if rsp.status_code in (200,):       
        
                        fin_data = json.loads(rsp.content[6:-2].decode('unicode_escape'))
        
                        pTickerContainer17.ticker = str(item)
                        pTickerContainer17.time = datetime.datetime.now().strftime("%I:%M%p")
                        pTickerContainer17.price = str(fin_data['l'])
                        pTickerContainer17.date = datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")
                        pTickerContainer17.us_fetch_date_time =  time.asctime( time.localtime(time.time()) )                         
        
                else:
                        logger.info("Status Code did not include 200 . Ticker = "+ str(item)+ " . Moving on to next ticker.")

                


                #logger.info(pTickerContainer17.printContent())       

                loadInto_17MinTable_DB(pTickerContainer17, pConn)        
                verifyAlertThreshold( pTickerContainer17, pConn)


def getTargetTickerFromDB ( pConn): 

        logger.info("Reading DB for Target Tickers .")    
        pTargetTickersAry = [] 
        
        pConn.row_factory = lambda cursor, row: row[0]
        cur = pConn.cursor() 

        sql_query = "SELECT TICKER FROM SCORE_CARD"     
        
        pTargetTickersAry = cur.execute (sql_query).fetchall()
                      
        pConn.close()
        return pTargetTickersAry


def callDriver():


        logger.info("\n\n\n\n ================== Application Started : WALL ==============================\n\n")

        #targetTickersAry = np.array(["C" , "AIG", "F", "QCOM", "VSLR" , "FOSL", "AKS", "JMBA", "NOK"])  


        db_loc_1  = os.path.join(BASE_DIR,  'GOOG_scraper_DB_v13.sqlite')

        if ( os.path.isfile(db_loc_1)): 
                tickerContainer17 = SEVENTEEN_MIN_STRCT()

                conn = createConnection(db_loc_1)                     
                targetTickersAry = getTargetTickerFromDB (conn) 
                logger.info( "DB location = " + db_loc_1) 
                logger.info("Collecting all data 1 by 1 from Goog API for Tickers in : "  + str (targetTickersAry))                
                conn.close() 
                
                conn2 = createConnection(db_loc_1)                     
                getDataFromAPI (tickerContainer17, targetTickersAry, conn2)
        else: 
                logger.info("\n\nXXXXXXXXXXXXXXXXXXXXXXXX  DB File Not found. Exiting XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n\n")   


        logger.info("\n\n============================== Application ENDssssssssss ==============================\n\n")   


def main(): 
        callDriver()


if __name__ == '__main__':
        main() 




