from pywebio.input import *
from pywebio.output import *
from pywebio.session import set_env, hold
from pywebio import start_server
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import date

# Global variable which will hold our dataset
df = None

# Function to scrape the desired web page and retrieve the results
def scrape():
    # The URL to MyGov Covid-19 information portal
    URL = "https://www.mygov.in/covid-19/"
    # Get the HTML of the web page corresponding to the url
    html = requests.get(URL).text
    # Initiate the scraper
    soup = BeautifulSoup(html, "lxml")
    # Get the div corresponding to the dashboard
    dashboard = soup.select("div#dashboard")[0]

    # Get the list of numbers corresponding to total cases, active cases, discharged and deaths
    totals = dashboard.select("span.icount")
    for i in range(len(totals)):
        totals[i] = int(totals[i].text.replace(',', '').strip())
    # Create a dictionary for the numbers
    totalLabels = ["total_confirmed", "total_active", "total_discharged", "total_deaths"]
    totalsDict = dict(zip(totalLabels, totals))
    # Add the total vaccinations to the dict
    totalsDict["total_vaccinations"] = int(soup.select("div.total-vcount")[0].strong.text.replace(',', '').strip())

    # Get the list of numbers corresponding to the daily increase in total cases, active cases, discharges and deaths
    increases = dashboard.select("div.increase_block")
    for i in range(len(increases)):
        increases[i] = int(increases[i].text.replace(',', '').strip())
    
    # Create a dictionary for the numbers
    increaseLabels = ["confirmed_increase", "active_increase", "discharged_increase", "deaths_increase"]
    increasesDict = dict(zip(increaseLabels, increases))
    # Add the increase in vaccinations to the dict
    increasesDict["vaccinations_increase"] = int(soup.select("div.yday-vcount")[0].strong.text.replace(',', '').strip())

    # Get the list of the divs corresponding to the data for different states
    states = soup.select("div.views-row")
    # Get the dict of name of the region : corresponding dict of data
    statesDict = {}
    for state in states:
        stateName = state.select("span.st_name")[0].text.strip()
        stateLabels = totalLabels + ["total_vaccinations"]
        stateData = [int(d.text.replace(',', '').strip()) for d in state.select("div.st_all_counts")[0].select("small")]
        statesDict[stateName] = dict(zip(stateLabels, stateData))
    
    # Create a dataframe for the corresponding data
    df = pd.DataFrame(index = ["INDIA", "INDIA (Increases)"] + list(statesDict.keys()), columns = list(list(statesDict.values())[0].keys()))
    # Add the data for India
    df.loc["INDIA"] = totalsDict
    df.loc["INDIA (Increases)"] = list(increasesDict.values())
    # Add the data for the states
    for n, d in statesDict.items():
        df.loc[n] = d
    # Make the column names look more natural
    df.columns = ["Confirmed", "Active", "Discharged", "Deaths", "Vaccinations"]

    return df

# Just a simple formatter for displaying the data
def show(htmlText):
    return put_success(put_markdown("<center>" + htmlText + "</center>"))

# Return the filename for the the CSV file to be downloaded
def filename():
    return str(date.today()) + "-corona-daily-india.csv"

# Show a drop-down list of states and union territories for enabling the user to see state-specific data
def displayStateInput():
    stateName = select("State / UT", options = list(df.index)[2:])
    st = df.loc[stateName].values.tolist()
    popup(stateName, [
        put_row([show(f"<h1>Confirmed</h1>\n<b>{st[0]:,}</b>"), None, show(f"<h1>Active</h1>\n<b>{st[1]:,}</b>")]),
        put_row([show(f"<h1>Discharged</h1>\n<b>{st[2]:,}</b>"), None, show(f"<h1>Deaths</h1>\n<b>{st[3]:,}</b>")]),
        show(f"<h1>Vaccinations</h1>\n<b>{st[4]:,}</b>")
    ])


# The main function which drives the web application
def main():
    set_env(title = "Corona Tracker")

    # Get the dataframe corresponding to the data
    global df
    df = scrape()
    # Get the CSV string of the dataset
    dfstr = df.to_csv()

    # Display the data for India
    ind = df.loc["INDIA"].values.tolist()  # Totals for India
    indin = df.loc["INDIA (Increases)"].values.tolist()  # Last day increases for India
    put_info(put_html("<center><h1><u>INDIA</u></h1><center>"))
    put_row([show(f"<h1>Confirmed</h1>\n<b>{ind[0]:,}</b> (+{indin[0]:,})"), None, show(f"<h1>Active</h1>\n<b>{ind[1]:,}</b> (+{indin[1]:,})")])
    put_row([show(f"<h1>Discharged</h1>\n<b>{ind[2]:,}</b> (+{indin[2]:,})"), None, show(f"<h1>Deaths</h1>\n<b>{ind[3]:,}</b> (+{indin[3]:,})")])
    show(f"<h1>Vaccinations</h1>\n<b>{ind[4]:,}</b> (+{indin[4]:,})")

    # Display button to display a drop-down list to view the data of any state, and a link to download the complete data into a CSV file
    put_warning(put_row([put_buttons(["Show State / UT Data"], onclick = [displayStateInput]), put_file(filename(), dfstr.encode())]))
    hold()

if __name__ == "__main__":
    start_server(main, port = 80, debug = True)

