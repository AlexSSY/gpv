#!/home/alex/code/python/gpv/.venv/bin/python
# -*- coding: utf-8 -*-
import enum
import requests
from pydantic import BaseModel
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, time


class State(str, enum.Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class Slot(BaseModel):
    time: datetime
    state: State
    i: int


class Result(BaseModel):
    slot_minutes: int
    now: datetime
    timezone: str
    slots: list[Slot]


MONTHS: dict[str, int] = {
    "січня": 1,
    "лютого": 2,
    "березня": 3,
    "квітня": 4,
    "травня": 5,
    "червня": 6,
    "липня": 7,
    "серпня": 8,
    "вересня": 9,
    "жовтня": 10,
    "листопада": 11,
    "грудня": 12,
}


def parse_ua_date(string: str) -> time:
    day, month_name, year, _ = string.split(" ", 3)
    month = MONTHS[month_name]
    return datetime(int(year), month, int(day))


def load_slots() -> list[Slot]:
    url = "https://www.poe.pl.ua/customs/dynamicgpv-info.php"
    slots = []

    try:
        response = requests.get(url)
        response.raise_for_status()
        html_content = response.text
    except requests.exceptions.RequestException:
        exit()
    else:
        soup = BeautifulSoup(html_content, "html.parser")
        date_numbers = {}
        gpv_divs = soup.find_all(class_="gpvinfodetail")
        for gpv_div in gpv_divs:
            date_string = gpv_div.find("b").text
            tr = gpv_div.select_one(
                ".turnoff-scheduleui-table > tbody:nth-child(2) > tr:nth-child(2)"
            )
            date = parse_ua_date(date_string)
            numbers = [
                int(td["class"][0].split("light_")[1])
                for td in tr.select('td[class^="light_"]')
            ]
            date_numbers[date] = numbers

        for date, numbers in date_numbers.items():
            for idx, n in enumerate(numbers):
                time = date + timedelta(seconds=idx * 30 * 60)
                match n:
                    case 1:
                        state = State.GREEN
                    case 2:
                        state = State.RED
                    case 3:
                        state = State.YELLOW

                slots.append(
                    Slot(time=time, state=state, i=idx)
                )

    return slots


if __name__ == "__main__":
    print(
        Result(
            slot_minutes=30,
            now=datetime.now(),
            timezone="Europe/Kyiv",
            slots=load_slots()
        ).model_dump_json()
    )
