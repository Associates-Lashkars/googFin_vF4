from twilio.rest import Client
import logging
from pyfcm import FCMNotification
import smtplib


logger = logging.getLogger(__name__)   

def percentage(part, whole):
    return 100*float(part)/float(whole)


def ratio(part, whole):
    return float(part)/float(whole)


def convertTo_12_DigitOntlNumber ( pPhoneNum): 
    logger.info('Converting if need for SMS : ' + pPhoneNum) 
    
    if (len(pPhoneNum) == 12 and ("+1" in pPhoneNum )): 
            return pPhoneNum
    elif  (len(pPhoneNum) == 10  and pPhoneNum.isdigit()):
            return "+1" + pPhoneNum
    else: return "Un-formatable" 


def sendSMS(pToStr, pAlertMessage): 
        
    account = "AC2414df6119a0d3b4fafae84416e4a2f3"
    token = "458668728715b99595a0942fcd893c45"
    #toStr = "+14087582044" 
    toStr = "+17186184028" 
    fromStr = "+14083421197"
    
    client = Client(account, token)
    formattedNumber =  convertTo_12_DigitOntlNumber(pToStr)
    logger.info('Sending SMS to the formatted number : ' + formattedNumber) 
    
    if formattedNumber != "Un-formatable":  
        try: 
            message = client.messages.create(formattedNumber,from_=fromStr, body=pAlertMessage)
            logger.info('Successfully sent the SMS') 
        except:
            logger.error ("..............................Failed to send the SMS")

    else: logger.error ("..............................Un-formatable SMS number :" + pToStr)


def sendEmail(pTargetAlertRecipient, pAlertMessage ):

    logger.info('About to sent email to '+ pTargetAlertRecipient) 

    gmail_user = "noti.lashkar"
    gmail_pwd = "XX" 
    FROM = "noti.lashkar@gmail.com"
    SUBJECT = "Notification from FinMonster_v1_WALL" 

    #EmergencyCodeToAccessAccount = "8x080s5RbG+2rrR7RN66m1ZolpIIaWg3YnKkAxrS" 
    # Prepare actual message

    message = """From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (FROM, ", ".join(pTargetAlertRecipient), SUBJECT, pAlertMessage)
    logger.info("Tryng to send Message = " + message)

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_pwd)
        server.sendmail(FROM, pTargetAlertRecipient, message)
        server.close()
        logger.info('Successfully sent the mail')
    except (smtplib.SMTPException, smtplib.SMTPAuthenticationError, smtplib.SMTPConnectError) as  error :
        errStr  = "-----------------Failed to send mail. Error = " + str(error)
        logger.info(errStr)
        
        
def sendFCM(pTargetAlertRecipient, p_ticker, p_currentP, p_percentChnage, p_targetP, p_date, p_time, p_priority ):


    api_key="AIzaSyAY5l0-sK65UOBcFp2aLDCGRR_NlNYKmL4"
    serverKey ="AAAA1-gsgdk:APA91bEzlt_0DKVgEhOCurnlo19k-acbNNhZ65GMzZlu26UW5IvxLs93a4pKnU6bMHdwmfmynmkoEKosYx9bx8pSbfOPlN33Ttn-peJ3INENcFduWjYL266_zW6vxoLp7h57ChpTvFYQ"
    appID = "1:927313199577:android:1e66fc4cede0b84a"
    pkg_name = "com.s3.assoandlash.notification_aug15"
    senderId = "927313199577"
    localserverKey = "AIzaSyAKBnmE9n7tJbTle6Ez-kTCIND7WS0okQY"
    registration_id ="eaMO5dbKmqc:APA91bELwfmC62ZKwNYVd1WNgfjDZByII_PxZNR29AnxM3TyBMuXhOsqjvF0nLt2-6QPEcG56k0VzYuEb6_J2tK9B3kcl7b6LGzcVu5yrDnWkKrVMOg-AYWRwFfW1w8RJkJ_4eLXVSb0"


    push_service = FCMNotification(api_key=serverKey)

    msg_body = " Ticker: "+  p_ticker +", current price:" + str(p_currentP)+", which is within :"+ str( p_percentChnage) + " ,% of target price of :"+ str(p_targetP)  +", on date :"+ p_date + ", time: "+ p_time +"."
    msg_title = "Message " + p_priority

    message_data ={
         "body": msg_body  ,
         "title": msg_title
      }

    message_noti ={
        "p_ticker" : p_ticker,
        "p_currentP" : p_currentP,
        "p_percentChnage" : p_percentChnage,
        "p_targetP" : p_targetP,
        "p_date" : p_date ,
        "p_time" : p_time,
        "p_priority" : p_priority
    }


    message_to =  "ffEseX6vwcM:APA91bF8m7wOF MY FCM ID 07j1aPUb"
    result = push_service.notify_topic_subscribers(topic_name="FinNoti", message_body=msg_body,  data_message=message_noti )

        

