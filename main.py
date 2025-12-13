import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from datetime import datetime, timedelta, time


@dataclass
class Shortage:
    start: datetime
    end: datetime
    has_yellow: bool


MONTHS = {
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
  "грудня": 12
}


def parse_ua_date(string: str) -> time:
  day, month_name, year, _ = string.split(' ', 3)
  month = MONTHS[month_name]
  return datetime(int(year), month, int(day))


def load_shortages() -> list[Shortage]:
    url = "https://www.poe.pl.ua/customs/dynamicgpv-info.php"

    try:
        response = requests.get(url)
        response.raise_for_status() 
        html_content = response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        exit()

    soup = BeautifulSoup(html_content, 'html.parser')

    date_numbers = {}
    gpv_divs = soup.find_all(class_='gpvinfodetail')
    for gpv_div in gpv_divs:
        date_string = gpv_div.find('b').text
        tr = gpv_div.select_one('.turnoff-scheduleui-table > tbody:nth-child(2) > tr:nth-child(2)')
        date = parse_ua_date(date_string)
        numbers = [
            int(td["class"][0].split("light_")[1])
            for td in tr.select('td[class^="light_"]')
        ]
        date_numbers[date] = numbers

    shortages = []

    start = None
    soft_finish = None
    for date, numbers in date_numbers.items():
        for idx, n in enumerate(numbers):
            if n == 2 and start is None:
                start = date + timedelta(seconds=idx * 30 * 60)
                continue
            if n == 3:
                soft_finish = date + timedelta(seconds=idx * 30 * 60)
                continue
            if n == 1 and start:
                hard_finish = date + timedelta(seconds=idx * 30 * 60)
                shortages.append(
                    Shortage(start, hard_finish, soft_finish is not None)
                )
                start = None
                soft_finish = None
    
    if start:
        date = list(date_numbers.keys())[-1]
        hard_finish = date + timedelta(seconds=48 * 30 * 60)
        shortages.append(
            Shortage(start, hard_finish, soft_finish is not None)
        )

    return shortages


# OK|Свет есть до 01:30
# OFF|Света нет, может появиться в 06:00
# UNCERTAIN|Точно будет в 06:30
if __name__ == "__main__":
    now = datetime.now()

    shortages = load_shortages()
    current_shortage = next((m for m in shortages if now < m.end and now > m.start ), None)

    shortages_with_delta: dict[int, Shortage] = {}

    for shortage in shortages:
        if now > shortage.start:
            continue
        delta_seconds = int((shortage.start - now).total_seconds())
        shortages_with_delta[delta_seconds] = shortage

    if current_shortage is None:
        min_distance = min(shortages_with_delta.keys())
        closest_shortage = shortages_with_delta[min_distance]

    if current_shortage is None:
        print(f"OK|Свет есть до {closest_shortage.start.strftime("%H:%M")}")
    else:
        if current_shortage.has_yellow:
            print(f"OFF|Света нет, может появиться в {(current_shortage.end - timedelta(minutes=30)).strftime("%H:%M")}")
        else:
            print(f"UNCERTAIN|Точно будет в {current_shortage.end.strftime("%H:%M")}")
