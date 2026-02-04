import re
import icalendar
import requests
import sys
from datetime import timedelta

# --- CONFIGURATION ---
ICS_URL = "https://cloud.timeedit.net/bth/web/sched1/ri67XQoW6l2ZQ9Q5Q58q44n5yWZX3562oZoYXlyQ0276TZ5ycg8WX2t8u0XQWolZ9oZnV3e18771X6o56Qd829Q61WuXXb3bQZ217Z4l5j84j9m87E867E54DC32l161Z72C6tDj71Q3376EC356761215.ics"
OUTPUT_FILE = 'modified_calendar.ics'

COURSE_MAP = {
    'MA1497': 'Transform', 'FY1438': 'Termo',
    'ET2632': 'Projekt 2', 'MT1517': 'Projekt 1'
}

NAME_MAP = {
    'JCH': 'Johan Richter', 'MEO': 'Mattias Eriksson', 'WKA': 'Wlodek Kulesza',
    'RKH': 'Raisa Khamitova', 'IGE': 'Irina Gertsovich', 'JSB': 'Josef Ström',
    'CBG': 'Carolina Bergeling', 'ABR': 'Alessandro Bertoni', 'MJD': 'Majid Joshani',
    'MMU': 'Mohammed Samy Massoum'
}

def modify_event(event):
    summary = str(event.get('summary', ''))
    description = str(event.get('description', ''))
    
    # 1. FILTERING
    if any(x in summary or x in description for x in ['MA0007', 'Mattestuga']):
        return None

        
    # Safety: ensure start isn't >= end
    if event.get('dtstart') and event.get('dtend'):
        if event['dtstart'].dt >= event['dtend'].dt:
            event['dtstart'].dt -= timedelta(minutes=15)

    # 3. PROCESSING SUMMARY
    parts = [p.strip() for p in summary.split(',')]
    found_instructors = []
    event_type = "Gruppövning" 
    
    if parts:
        code = parts[0]
        for p in parts:
            if p in NAME_MAP:
                found_instructors.append(NAME_MAP[p])
            elif any(keyword in p for keyword in ['Föreläsning', 'Laboration', 'Övning', 'Handledning']):
                event_type = p

        for prefix, friendly_name in COURSE_MAP.items():
            if code.startswith(prefix):
                event['summary'] = f"{friendly_name}, {event_type}"
                break
    
    # 4. CLEAN DESCRIPTION
    clean_desc = re.sub(r'ID \d+', '', description).strip().replace('\n', ' ').strip(', ')
    desc_elements = [clean_desc] if clean_desc else []
    if found_instructors:
        desc_elements.append(", ".join(found_instructors))
        
    event['description'] = " | ".join(desc_elements)
    return event

def main():
    try:
        print(f"Downloading calendar...")
        response = requests.get(ICS_URL)
        response.raise_for_status()
        
        # Load the source calendar
        old_cal = icalendar.Calendar.from_ical(response.content)
        
        # Create a brand new calendar object
        new_cal = icalendar.Calendar()
        
        # Add basic required ICS headers
        new_cal.add('prodid', '-//Modified Calendar//mxm.dk//')
        new_cal.add('version', '2.0')

        event_count = 0
        for component in old_cal.walk('VEVENT'):
            # modify_event modifies the component in-place or returns None
            modified = modify_event(component)
            if modified:
                new_cal.add_component(modified)
                event_count += 1

        # Write the new calendar to the file
        with open(OUTPUT_FILE, 'wb') as f:
            f.write(new_cal.to_ical())
            
        print(f"✨ Success! Saved {event_count} events to {OUTPUT_FILE}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()


