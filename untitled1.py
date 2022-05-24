import requests
import pandas as pd
import json
import dateparser
from datetime import timedelta

def get_data_from_url(arg_url):
    arg_code = arg_url.split("-")[-1].split("#")[0]
    response = requests.get("https://am.jpmorgan.com/FundsMarketingHandler/product-data?cusip={0}&country=us&role=adv&language=en&userLoggedIn=false&version=5.8.2_1652966088".format(arg_code))
    json_data = json.loads(response.content)
    sec_yield = json_data.get("fundData").get("shareClass").get("yieldMonthEnd").get("thirtyDaySecYield")
    sec_yield_date = json_data.get("fundData").get("shareClass").get("yieldMonthEnd").get("effectiveDate")
    ticker = json_data.get("fundData").get("shareClass").get("ticker")
    for each in json_data.get("fundData").get("portfolioStats").get("data"):
        if each.get("name") == "Duration":
            duration = each.get("value")
            duration_as_of_date = each.get("asOfDate")
    arg_url_data = {
        "Ticker" : ticker,
        "SEC Yield" : sec_yield * 100,
        "SEC Yield Date" : dateparser.parse(sec_yield_date),
        "Duration" : duration,
        "Duration as of Date" : dateparser.parse(duration_as_of_date) - timedelta(days = 1)
    }
    return arg_url_data

def get_info_from_urls(arg_urls):
    df = pd.DataFrame([get_data_from_url(each_url) for each_url in arg_urls])
    return df.to_html(index=False)

def send_html_email_df(sender, receiver, subject, dataframe):
    import smtplib
    from email.message import EmailMessage
    from email.utils import make_msgid
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver
    image_cid = make_msgid()
    msg.add_alternative(dataframe, subtype = "html")
    with smtplib.SMTP('mailhost.jpmchase.net:25') as s:
        s.send(msg)
    
urls = ["https://am.jpmorgan.com/us/en/asset-management/adv/products/jpmorgan-managed-income-fund-l-48121a415#",
 "https://am.jpmorgan.com/us/en/asset-management/adv/products/jpmorgan-short-duration-core-plus-fund-i-46637k455"]
send_html_email_df("aditya.dey@chase.com", "aditya.dey@chase.com", "Near Margin Clients", get_info_from_urls(urls))


             
             
             
             
             
             
             












    
