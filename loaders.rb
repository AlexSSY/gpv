# encoding: UTF-8
require 'nokogiri'
require 'open-uri'
require 'irb'
require 'yaml'

require_relative "structs2"

MONTHS = {
  "січня" => 1,
  "лютого" => 2,
  "березня" => 3,
  "квітня" => 4,
  "травня" => 5,
  "червня" => 6,
  "липня" => 7,
  "серпня" => 8,
  "вересня" => 9,
  "жовтня" => 10,
  "листопада" => 11,
  "грудня" => 12
}

def parse_ua_date(str)
  day, month_name, year, _ = str.split
  month = MONTHS[month_name]
  Time.new(year.to_i, month, day.to_i, 0, 0, 0)
end

def poe_html_nokogiri_loader
  url = "https://www.poe.pl.ua/customs/dynamicgpv-info.php"
  document = Nokogiri::HTML URI.open(url, "r:utf-8", &:read)

  date_numbers = {}
  gpv_divs = document.css(".gpvinfodetail")
  gpv_divs.each do |gpv_div|
    date_string = gpv_div.css('>b:nth-child(1)').text
    tr = gpv_div.css('.turnoff-scheduleui-table > tbody:nth-child(2) > tr:nth-child(2)')
    date = parse_ua_date date_string
    numbers = tr.css('td[class^="light_"]').map do |td|
      td['class'][/light_(\d+)/, 1].to_i
    end
    date_numbers[date] = numbers
  end

  shortages = []

  start = nil
  soft_finish = nil
  date_numbers.each do |date, numbers|
    numbers.each_with_index do |n, idx|
      if n == 2 && !start
        start = date + (idx * 30) * 60
        next
      end
      if n == 3
        soft_finish = date + (idx * 30) * 60
        next
      end
      if n == 1 && start
        hard_finish = date + (idx * 30) * 60
        shortages << Shortage.new(start, hard_finish, soft_finish)
        start = nil
        soft_finish = nil
      end
    end
  end
  if start
    date = date_numbers.keys.last
    hard_finish = date + (48 * 30) * 60
    shortages << Shortage.new(start, hard_finish, soft_finish)
  end

  shortages
end