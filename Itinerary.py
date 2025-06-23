import openai
from openai import OpenAI
import os
import math
import random
import re
from datetime import datetime, timedelta

# Initializes the OpenAI client with personal API Key (Do Not Share This Key)
client = OpenAI(api_key="API Key Goes Here")

# Generates day-to-day plan based on user-selected activities and trip length
def generate_itinerary(activities, days, shuffle=False):
    itinerary = {}

    # If no activities provided, fill all days with "Free Time"
    if not activities:
        for i in range(days):
            itinerary[f'Day {i + 1}'] = ["Free time"]
        return itinerary

    total_activities = len(activities)

    # Shuffle the activities only for the initial itinerary creation
    if shuffle:
        random.shuffle(activities)

    # If number of activities matches trip length, assign one activity per day
    if total_activities == days:
        for i in range(days):
            itinerary[f'Day {i + 1}'] = [activities[i]]
        return itinerary

    # If more activities than days, distribute them evenly across the days
    elif total_activities > days:
        base = total_activities // days
        remainder = total_activities % days
        idx = 0
        for i in range(days):
            count = base + (1 if i < remainder else 0)
            itinerary[f'Day {i + 1}'] = activities[idx:idx+count]
            idx += count
        return itinerary

    # If fewer activities than days, repeat some activities and insert "Free Time"
    else:
        estimated_activity_days = math.ceil(days * 0.65)  # Aims for a 65% activity days, 35% free time distribution
        total_free_days = days - estimated_activity_days

        # Repeat activities to fill activity days
        repeated_activities = []
        while len(repeated_activities) < estimated_activity_days:
            repeated_activities.extend(activities)
        repeated_activities = repeated_activities[:estimated_activity_days]

        # Fill remaining days with "Free Time" and shuffle for randomness
        mixed_plan = repeated_activities + ["Free time"] * total_free_days
        random.shuffle(mixed_plan)

        for i in range(days):
            itinerary[f'Day {i + 1}'] = [mixed_plan[i]]

    return itinerary


# Generate time slots throughout the day for the activities (Time slot range between 8 AM and 10 PM)
def generate_day_time_slots(activity_count, start_time="8:00 AM", end_time="10:00 PM"):
    fmt = "%I:%M %p"
    start = datetime.strptime(start_time, fmt)
    end = datetime.strptime(end_time, fmt)
    available_minutes = int((end - start).total_seconds() // 60)

    # If only one activity per day, assign a random time (Will always happen unless days < activities)
    if activity_count == 1:
        # Choose a single random time within the window
        rand_minutes = random.randint(0, available_minutes)
        slot_time = start + timedelta(minutes=rand_minutes)
        return [slot_time.strftime(fmt)]

    # Otherwise generate incrementing random times
    slots = []
    current_time = start
    for _ in range(activity_count):
        if current_time >= end:
            break
        slots.append(current_time.strftime(fmt))
        current_time += timedelta(minutes=random.choice([90, 100, 120]))        # Sets a time limit of either 90, 100, or 120 minutes for each activity

    return slots

# Prompts ChatGPT for a message and estimated cost for a given activity and city
def get_chatgpt_message_and_cost(activity, city, is_last_day=False):
    # Prompts for when "Free Time" is the activity
    if activity.lower() == "free time":
        if is_last_day:
            prompt = (
                f"You’re spending your final day in {city} with no fixed plans. Write a short, warm closing travel message "
                f"without suggesting specific activities. End with a heartfelt goodbye for the user on a new line."
            )
        else:
            prompt = (
                f"Write a short, relaxed message for someone spending a free day in {city}. "
                f"Do not suggest any specific places or activities. Let them feel like they can do whatever they want. "
                f"Avoid greetings or goodbyes unless it's the first day."
            )

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )
            message = response.choices[0].message.content.strip()
            return message, "$0.00", 0.0        # Budget cost of a "Free Time" day

        except Exception as e:
            return f"(GPT error: {e})", "$0.00", 0.0

    # Prompts for activities. Suggests a city-specific activity idea based on the users activity selections and includes its real-world estimated cost.
    else:
        if is_last_day:
            prompt = (
                f"Don't say hello, write a short, friendly travel message for someone visiting {city} "
                f"and doing this activity (give only 1 specific idea): {activity}. "
                f"Include a warm goodbye. VERY IMPORTANT: End your message on a new line with exactly this format:\n"
                f"Estimated Cost: $XX.XX"
            )
        else:
            prompt = (
                f"Write a short, unique travel message for someone visiting {city} and doing this activity: {activity}. "
                f"Give 1 specific idea that hasn’t been mentioned before. "
                f"Make it different from earlier days. Avoid greetings or goodbyes unless it's the first day. "
                f"Also, give the real-world 2025 cost of this activity in USD. "
                f"On a new line at the end of your message, write this exactly:\nEstimated Cost: $XX.XX"
            )


    try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )

            full_text = response.choices[0].message.content.strip()
            match = re.search(r'[Ee]stimated [Cc]ost[:\-]?\s*\$?(\d+(?:\.\d{1,2})?)', full_text, re.IGNORECASE)     # Extracts the estimated cost produced from ChatGPT using regex

            # If cost value found in the GPT response, format it, Otherwise, mark cost as unavailable
            if match:
                cost_val = float(match.group(1))
                cost_str = f"${cost_val:.2f}"
            else:
                cost_val = None
                cost_str = "N/A"

            message = full_text  # Keep cost line inside the message (Without it, it will remove the estimated cost: XX.XX at the bottom of the activity message)

            return message, cost_str, cost_val

    except Exception as e:
            return f"(GPT error: {e})", "N/A", None

# Gemerates full itinerary with message, cost, and time for each activity
def create_itinerary_with_messages(activities, days, city, shuffle=False):
    itinerary = generate_itinerary(activities, days, shuffle=shuffle)
    detailed_plan = {}

    # Loop through each day in itinerary with its lists of activities
    for i, (day, activity_list) in enumerate(itinerary.items()):
        is_final_day = (i == len(itinerary) - 1)        # Checks if this is last day of trip
        time_slots = generate_day_time_slots(len(activity_list))        # Generates time slots for the day's activities

        messages = []
        for j, activity in enumerate(activity_list):
            is_last_activity = (j == len(activity_list) - 1)        # Check if thius is the last activity of the day
            is_last_day = is_final_day and is_last_activity         # True only if this is the final activity of last day

            # Get GPT Message and estimated cost
            message, cost_str, cost_val = get_chatgpt_message_and_cost(activity, city, is_last_day)
            time = time_slots[j] if j < len(time_slots) else "Unscheduled"

            # Append this activity's details to the day's plan
            messages.append({
                "Activity": activity,
                "Message": message,
                "Time": time,
                "Cost": cost_str,
                "RawCost": cost_val
            })

        detailed_plan[day] = messages

    return detailed_plan

