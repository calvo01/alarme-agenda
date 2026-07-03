import os
import json
import time
import threading
import logging
import tkinter as tk
from datetime import datetime, timedelta, timezone

import winsound
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")
CREDENTIALS_FILE = os.path.join(SCRIPT_DIR, "credentials.json")
TOKEN_FILE = os.path.join(SCRIPT_DIR, "token.json")
STATE_FILE = os.path.join(SCRIPT_DIR, "alerted.json")
LOG_FILE = os.path.join(SCRIPT_DIR, "alarme.log")

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


CATCH_UP_WINDOW_SECONDS = 180

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    encoding="utf-8",
)


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_state():
    if not os.path.exists(STATE_FILE):
        return set()
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(list(state), f)


def get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as e:
            logging.warning(f"Erro carregando token: {e}")
            creds = None

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception as e:
            logging.warning(f"Erro no refresh: {e}")
            creds = None

    if not creds:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)

    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        f.write(creds.to_json())
    return creds


def get_upcoming_events(service, calendar_id, look_ahead_minutes):
    now = datetime.now(timezone.utc)
    end = now + timedelta(minutes=look_ahead_minutes)
    try:
        result = service.events().list(
            calendarId=calendar_id,
            timeMin=now.isoformat(),
            timeMax=end.isoformat(),
            singleEvents=True,
            orderBy="startTime",
            maxResults=25,
        ).execute()
        return result.get("items", [])
    except HttpError as e:
        logging.error(f"Erro na API: {e}")
        return []


def parse_event_datetime(event):
    dt_str = event.get("start", {}).get("dateTime")
    if not dt_str:
        return None
    return datetime.fromisoformat(dt_str).astimezone()


def show_alarm(event_name, event_time, minutes_before, beep_freq, beep_dur, beep_interval_ms):
    stop_flag = threading.Event()

    def beep_loop():
        while not stop_flag.is_set():
            try:
                winsound.Beep(beep_freq, beep_dur)
            except Exception:
                pass
            stop_flag.wait(beep_interval_ms / 1000)

    threading.Thread(target=beep_loop, daemon=True).start()

    root = tk.Tk()
    root.title("Alarme de Agenda")
    root.geometry("520x260")
    root.configure(bg="#ffebeb")
    root.attributes("-topmost", True)
    root.resizable(False, False)

    header = f"Faltam {minutes_before} min para:" if minutes_before > 0 else "AGORA:"
    txt = f"{header}\n\n{event_name}\n\nHorario: {event_time.strftime('%H:%M')}"

    tk.Label(
        root, text=txt, bg="#ffebeb", fg="#222",
        font=("Segoe UI", 13, "bold"), justify="center", wraplength=480,
    ).pack(pady=25)

    def close():
        stop_flag.set()
        root.destroy()

    tk.Button(
        root, text="OK, vi!", command=close,
        bg="#50c878", fg="white", font=("Segoe UI", 12, "bold"),
        width=15, height=2, relief="flat", cursor="hand2",
    ).pack()

    root.protocol("WM_DELETE_WINDOW", close)
    root.lift()
    root.focus_force()
    root.mainloop()


def main():
    config = load_config()
    calendar_id = config.get("calendarId", "primary")
    alerts_before = config.get("alertMinutesBefore", [5, 0])
    poll_seconds = config.get("pollIntervalSeconds", 120)
    beep_freq = config.get("beepFrequency", 880)
    beep_dur = config.get("beepDurationMs", 400)
    beep_interval = config.get("beepIntervalMs", 1500)

    creds = get_credentials()
    service = build("calendar", "v3", credentials=creds, cache_discovery=False)

    logging.info(f"Alarme iniciado. calendarId={calendar_id} polling={poll_seconds}s")
    print(f"Alarme rodando. Polling a cada {poll_seconds}s.")
    print(f"Log em: {LOG_FILE}")

    look_ahead = max(alerts_before) + 5

    while True:
        try:
            state = load_state()
            events = get_upcoming_events(service, calendar_id, look_ahead)
            now = datetime.now().astimezone()

            for ev in events:
                event_time = parse_event_datetime(ev)
                if event_time is None:
                    continue
                summary = ev.get("summary", "(sem titulo)")
                uid = ev.get("id", "")
                seconds_to = (event_time - now).total_seconds()

                for min_before in alerts_before:
                    target = min_before * 60
                    if target - CATCH_UP_WINDOW_SECONDS < seconds_to <= target:
                        key = f"{uid}_{min_before}"
                        if key not in state:
                            logging.info(f"Disparando: '{summary}' [-{min_before} min]")
                            show_alarm(summary, event_time, min_before, beep_freq, beep_dur, beep_interval)
                            state.add(key)
                            save_state(state)
        except Exception as e:
            logging.exception(f"Erro no loop: {e}")

        time.sleep(poll_seconds)


if __name__ == "__main__":
    main()
