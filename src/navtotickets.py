import os
import smtplib

from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait


MAIL_FROM = "tillevents@kaktus42.de"


def main():
    smtp_host = os.getenv("SMTP_HOST", "localhost")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_to = os.getenv("SMTP_TO", "mail@example.com")
    events_filename = os.getenv("EVENTS_FILE", "./events.csv")

    if not os.path.exists(events_filename):
        with open(events_filename, "w") as f:
            f.write("id,title,date,location\n")

    with open(events_filename, "r") as f:
        old_events = pd.read_csv(f, dtype=str)

    curr_events = fetch_events()
    curr_events.to_csv(events_filename, index=False)

    new_events = curr_events[~curr_events.id.isin(old_events.id)]
    print(new_events.to_markdown(index=False))

    if len(new_events) > 0:
        text = "Es gibt neue Till Reiners Events!\n\n" + new_events.to_markdown(
            index=False
        )
        notify(host=smtp_host, port=smtp_port, to=smtp_to, text=text)


def fetch_events():
    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    options.add_argument("no-sandbox")
    options.add_argument("disable-gpu")
    driver = webdriver.Chrome(options=options)

    driver.get("https://tickets.tillreiners.de/tickets")
    element_present = expected_conditions.presence_of_element_located(
        (By.ID, "ticket-listing")
    )
    WebDriverWait(driver, 5).until(element_present)
    html = driver.page_source
    soup = BeautifulSoup(html, features="html.parser")

    event_listing = soup.find("section", {"id": "ticket-listing"})
    if not event_listing:
        raise Exception("Could not find event listing")
    articles = event_listing.find_all("article")

    events_structured = []
    for event in articles:
        event_id = event.attrs["id"].split("-")[1]
        event_title = event.find("h2", {"class": "title"}).text
        event_date = event.find("time").text
        event_location_city = event.find("span", {"class": "city"}).text

        events_structured.append(
            [event_id, event_title, event_date, event_location_city]
        )

    driver.quit()

    return pd.DataFrame(events_structured, columns=["id", "title", "date", "location"])


def notify(host: str, port: int, to: str, text: str):
    msg = f"From: {MAIL_FROM}\r\nTo: {to}\r\nSubject: Neue Till Reiners Events verfügbar!\r\n\r\n{text}"

    server = smtplib.SMTP_SSL(host=host, port=port)
    server.set_debuglevel(1)
    server.sendmail(MAIL_FROM, to, msg)
    server.quit()


if __name__ == "__main__":
    main()
