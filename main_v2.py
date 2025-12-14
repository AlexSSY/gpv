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


class Result(BaseModel):
    slot_minutes: datetime
    now: datetime
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


def load_shortages() -> list[Slot]:
    url = "https://www.poe.pl.ua/customs/dynamicgpv-info.php"

    shortages = []

    try:
        response = requests.get(url)
        response.raise_for_status()
        html_content = response.text
    except requests.exceptions.RequestException:
        exit()
    else:
        pass

    return shortages

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

    shortages = []

    start = None
    for date, numbers in date_numbers.items():
        for idx, n in enumerate(numbers):
            if n == 2 and start is None:
                start = date + timedelta(seconds=idx * 30 * 60)
                continue

            if n == 3 and start:
                soft = date + timedelta(seconds=idx * 30 * 60)
                hard = date + timedelta(seconds=(idx + 1) * 30 * 60)
                shortages.append(Shortage(start=start, soft=soft, hard=hard))
                start = None
                continue

            if n == 1 and start:
                hard = date + timedelta(seconds=(idx + 1) * 30 * 60)
                shortages.append(Shortage(start=start, soft=None, hard=hard))
                start = None

    if start:
        date = list(date_numbers.keys())[-1]
        hard = date + timedelta(seconds=48 * 30 * 60)
        shortages.append(Shortage(start=start, soft=None, hard=hard))

    return shortages


# {
#   "from": "2025-12-12T00:00:00+02:00",
#   "to":   "2025-12-13T00:00:00+02:00",
#   "shortages": [
#     {
#       "start": "2025-12-12T01:30:00+02:00",
#       "soft":  "2025-12-12T06:00:00+02:00",
#       "hard":  "2025-12-12T06:30:00+02:00"
#     }
#   ]
# }
if __name__ == "__main__":
    shortages = load_shortages()

    first_shortage_start = shortages[0].start
    last_shortage_hard = shortages[-1].hard

    start_timeline = datetime(
        year=first_shortage_start.year,
        month=first_shortage_start.month,
        day=first_shortage_start.day,
    )

    end_timeline = datetime(
        year=last_shortage_hard.year,
        month=last_shortage_hard.month,
        day=last_shortage_hard.day,
        # hour=23,
        # minute=59,
        # second=59,
        # microsecond=999999
    )

    result = Result(
        from_=start_timeline,
        to=end_timeline,
        shortages=shortages
    )
    
    print(result.model_dump_json(by_alias=True))
    # now = datetime.now()

    # shortages = load_shortages()
    # current_shortage = next(
    #     (m for m in shortages if now < m.end and now > m.start), None
    # )

    # shortages_with_delta: dict[int, Shortage] = {}

    # for shortage in shortages:
    #     if now > shortage.start:
    #         continue
    #     delta_seconds = int((shortage.start - now).total_seconds())
    #     shortages_with_delta[delta_seconds] = shortage

    # if current_shortage is None:
    #     min_distance = min(shortages_with_delta.keys())
    #     closest_shortage = shortages_with_delta[min_distance]

    # if current_shortage is None:
    #     print(f"OK|Свет есть до {closest_shortage.start.strftime('%H:%M')}")
    # else:
    #     if current_shortage.has_yellow:
    #         print(
    #             f"OFF|Света нет, может появиться в {(current_shortage.end - timedelta(minutes=30)).strftime('%H:%M')}"
    #         )
    #     else:
    #         print(f"UNCERTAIN|Точно будет в {current_shortage.end.strftime('%H:%M')}")
