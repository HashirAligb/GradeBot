import discord
from discord.ext import commands
import matplotlib.pyplot as plt
import json
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

with open("grade_data.json") as f:
    data = json.load(f)

def create_chart(grades, name, course_name=None):
    labels = list(grades.keys())
    values = [grades[label] for label in labels]
    plt.figure(figsize=(10, 6))
    plt.bar(labels, values, color='skyblue')
    title = f"{name} Grade Distribution"
    if course_name:
        title = f"{name} - {course_name} Grade Distribution"
    plt.title(title)
    plt.xlabel("Grade")
    plt.ylabel("Number of Students")
    plt.tight_layout()
    plt.savefig("grade_chart.png")
    plt.close()

@bot.command()
async def grades(ctx, *, args: str):
    print(f"Received command: {args}")
    parts = args.strip().split()
    if len(parts) == 0:
        await ctx.send("Please provide a professor's name.")
        return
    # Try to find the longest match for professor key
    prof_key = None
    course_nbr = None
    for i in range(len(parts), 0, -1):
        possible_prof = ' '.join(parts[:i]).lower()
        if possible_prof in data:
            prof_key = possible_prof
            if i < len(parts):
                course_nbr = parts[i]
            break
    if not prof_key:
        await ctx.send("Professor not found. Please check the name and try again.")
        return
    prof = data[prof_key]
    # If course number is provided
    if course_nbr:
        courses = prof.get("courses", {})
        if course_nbr not in courses:
            await ctx.send(f"Course {course_nbr} not found for {prof['name']}.")
            return
        course = courses[course_nbr]
        grades_dict = course["grades"]
        create_chart(grades_dict, prof["name"], course["course_name"])
        file = discord.File("grade_chart.png")
        grade_lines = [f"{grade}: {count}" for grade, count in grades_dict.items()]
        grade_text = "\n".join(grade_lines)
        response = (
            f"**{prof['name']} - {course['course_name']} (CSCI {course_nbr})**\n"
            f"Average GPA: {course['avg_gpa']}\n\n"
            f"Grade Breakdown:\n{grade_text}"
        )
        await ctx.send(response, file=file)
    else:
        # List all courses for this professor
        courses = prof.get("courses", {})
        if not courses:
            await ctx.send(f"No course data found for {prof['name']}.")
            return
        course_list = [f"CSCI {nbr}: {info['course_name']}" for nbr, info in courses.items()]
        response = (
            f"**{prof['name']}** teaches the following courses:\n" +
            "\n".join(course_list) +
            "\n\nTo see grade breakdown for a course, use: !grades [professor] [course number] (e.g., !grades waxman, j 211)"
        )
        await ctx.send(response)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------') 

bot.run(TOKEN)
