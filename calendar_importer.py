import mechanize
import requests
import time
import datetime
import json
import getpass
from bs4 import BeautifulSoup

class CalendarImporter:

  def getAuthInfo(self):
    self.__STUDENT_NUMBER = raw_input("What is your student number? ")
    self.__STUDENT_MY_TCD_PASSWORD = getpass.getpass("What is your my.tcd.ie password?")
    self.__GOOGLE_EMAIL = raw_input("What is your Google email or username? ")
    self.__GOOGLE_PASSWORD = getpass.getpass("What is your Google account password? (If using 2FA, use app specific password.)")

    print "Wait like 30-40s"

    self.__MY_TCD_LOGIN_URI = "https://my.tcd.ie/urd/sits.urd/run/siw_lgn"
    self.__GOOGLE_LOGIN_ENDPOINT = "https://www.google.com/accounts/ClientLogin"
    self.__GOOGLE_CALENDAR_EVENT_ENDPOINT = "https://www.googleapis.com/calendar/v3/calendars/primary/events"

    self.__getMyTcdCalendar()

  def __getMyTcdCalendar(self):
    self.appointments = []

    br = mechanize.Browser()
    br.set_handle_robots(False)
    br.set_handle_refresh(False)
    br.set_handle_redirect(True)
    br.open(self.__MY_TCD_LOGIN_URI)
    br.select_form("f")

    username = br.form.find_control("MUA_CODE.DUMMY.MENSYS.1")
    password = br.form.find_control("PASSWORD.DUMMY.MENSYS.1")
    username.value = self.__STUDENT_NUMBER
    password.value = self.__STUDENT_MY_TCD_PASSWORD

    br.submit()
    br.open(br.click_link(text="here"))
    br.open(br.click_link(text="My Timetable"))
    br.open(br.click_link(text="View My Own Student Timetable"))


    soup = BeautifulSoup(br.response().read())
    text = br.response().read()
    json_data = json.loads(text.split('var eventdata = ')[1].split(';    sits_timetable_widget')[0])

    for appointment in json_data:

      appointment = {
        "size": int(self.__parseAppointmentText(appointment['info'], "Size:")),
        "group": self.__parseAppointmentText(appointment['info'], "Group:"),
        "activity": self.__parseAppointmentText(appointment['info'], "Activity:"),
        "room": self.__parseAppointmentText(appointment['info'], "Room:", "</a>", index=0).split('target=\"_blank\">')[1],
        "module": self.__parseAppointmentText(appointment['ttip'], "Module:", "\n"),
        "day": self.__parseAppointmentText(appointment['ttip'], "Date:", "\n"),
        "time": self.__parseAppointmentText(appointment['ttip'], "Time:")
      }

      self.appointments.append(appointment)
    self.__createAppointmentsOnGoogleCal()

  def __createAppointmentsOnGoogleCal(self):
    self.__getGoogleAuthToken()

    for appointment in self.appointments:
      start_and_end_times = appointment["time"].split("-")
      start_time = self.__createTimeDelimiter(start_and_end_times[0], appointment["day"])
      end_time = self.__createTimeDelimiter(start_and_end_times[1], appointment["day"])

      event = {
        "summary": appointment["module"] + " " + appointment["activity"],
        "location": appointment["room"],
        "description": "Activity: "+appointment["activity"]+", "+str(appointment["size"])+" Students"+" "+appointment["group"],
        "start": {
          "dateTime": start_time.isoformat(),
          "timeZone": "Europe/Dublin"
        },
        "end": {
          "dateTime": end_time.isoformat(),
          "timeZone": "Europe/Dublin"
        },
        "recurrence": [
            "RRULE:FREQ=WEEKLY;UNTIL=20150403T160000Z"
        ]
      }

      request_headers = {
        "Authorization": "GoogleLogin auth="+self.__GOOGLE_AUTH_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json"
      }

      request_params = {
        "key": "AIzaSyDLt2lWCNKnSyJNz3qB4OJjT0QwB4ExG50"
      }

      requests.post(self.__GOOGLE_CALENDAR_EVENT_ENDPOINT, data=json.dumps(event), headers=request_headers, params=request_params)

    print "kthxbai"

  def __getGoogleAuthToken(self):
    req = requests.post(self.__GOOGLE_LOGIN_ENDPOINT, {
      "accountType": "HOSTED_OR_GOOGLE",
      "Email": self.__GOOGLE_EMAIL,
      "Passwd": self.__GOOGLE_PASSWORD,
      "service": "cl"
    })

    self.__GOOGLE_AUTH_TOKEN = req.text.split("Auth=")[1].replace("\n", "")

  def __parseAppointmentText(self, text, key, needle="<br/>", index=0):
    return text.split(key)[1].split(needle)[index].strip() # (this should be less ew)

  def __createTimeDelimiter(self, time, day):
    return datetime.datetime.strptime("2015 2 " + day.strip() + " " + time.strip(), '%Y %W %A %H:%M')

importer = CalendarImporter()
importer.getAuthInfo()
