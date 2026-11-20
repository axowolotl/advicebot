import discord
from discord.ext import commands
import os
import json
import db 
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    print('------')

@bot.command()
async def hello(ctx):
    await ctx.send(f'Hello! I am {bot.user.name}, your companion to help you discover your potential future career paths through a quiz with some personalized advice! Use !help to see the available commands.')

@bot.command()
async def help(ctx):
    await ctx.send('Here are the available commands:\n!ping - Check the bot\'s latency\n!help - Show this help message')

class CareerQuizView(discord.ui.View):
    def __init__(self, user: discord.User, questions: list):
        super().__init__(timeout=180)
        self.user = user
        self.questions = questions
        self.current_q_index = 0
        self.scores = {}
        self.setup_buttons()

    def setup_buttons(self):
        self.clear_items()
        current_q = self.questions[self.current_q_index]
        
        for idx, option in enumerate(current_q["options"]):
            button = discord.ui.Button(
                label=option["label"],
                style=discord.ButtonStyle.primary,
                custom_id=f"opt_{idx}"
            )
            button.callback = self.create_callback(option["weights"])
            self.add_item(button)

    def create_callback(self, weights: dict):
        async def callback(interaction: discord.Interaction):
            # Ensure only the person who started the quiz can click buttons
            if interaction.user.id != self.user.id:
                await interaction.response.send_message("Start your own quiz with `!careerquiz`!", ephemeral=True)
                return

            # Add option weights to the user's running score
            for career, points in weights.items():
                self.scores[career] = self.scores.get(career, 0) + points

            self.current_q_index += 1

            # Check if there are more questions
            if self.current_q_index < len(self.questions):
                self.setup_buttons()
                embed = self.build_question_embed()
                await interaction.response.edit_message(embed=embed, view=self)
            else:
                await self.finish_quiz(interaction)

        return callback

    def build_question_embed(self):
        q_data = self.questions[self.current_q_index]
        embed = discord.Embed(
            title=f"Career Finder Quiz ({self.current_q_index + 1}/{len(self.questions)})",
            description=f"**{q_data['question']}**",
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Taking quiz: {self.user.display_name}")
        return embed

    async def finish_quiz(self, interaction: discord.Interaction):
        # Determine the highest scoring career
        top_career = max(self.scores, key=self.scores.get)
        
        # Save result to SQLite database
        await db.save_user_result(self.user.id, str(self.user), top_career, self.scores)

        # Format score breakdown
        breakdown = "\n".join(
            f"• **{career}:** {pts} pts"
            for career, pts in sorted(self.scores.items(), key=lambda x: x[1], reverse=True)
        )

        embed = discord.Embed(
            title="🎯 Your Recommended Career Path",
            description=f"Based on your answers, your top match is **{top_career}**!",
            color=discord.Color.green()
        )
        embed.add_field(name="Affinity Breakdown", value=breakdown, inline=False)
        embed.set_footer(text="Result saved! Type !mycareer anytime to view it again.")

        self.stop()
        await interaction.response.edit_message(embed=embed, view=None)

@bot.event
async def on_ready():
    await db.init_db()
    print(f"Logged in as {bot.user} | Database initialized.")

@bot.command(name="careerquiz")
async def start_quiz(ctx):
    """Starts an interactive career & profession quiz."""
    questions = await db.get_all_questions()
    if not questions:
        await ctx.send("No questions found in the database.")
        return

    view = CareerQuizView(ctx.author, questions)
    embed = view.build_question_embed()
    await ctx.send(embed=embed, view=view)

@bot.command(name="mycareer")
async def check_career(ctx, member: discord.Member = None):
    """Checks your (or another user's) saved career quiz result."""
    target = member or ctx.author
    result = await db.get_user_result(target.id)

    if not result:
        await ctx.send(f"{target.display_name} hasn't taken the quiz yet! Type `!careerquiz` to start.")
        return

    career, scores_json, taken_at = result
    scores = json.loads(scores_json)
    breakdown = "\n".join(f"• **{k}:** {v} pts" for k, v in sorted(scores.items(), key=lambda x: x[1], reverse=True))

    embed = discord.Embed(
        title=f"💼 {target.display_name}'s Career Profile",
        description=f"**Top Match:** {career}",
        color=discord.Color.gold()
    )
    embed.add_field(name="Score Breakdown", value=breakdown, inline=False)
    embed.set_footer(text=f"Last taken: {taken_at} UTC")
    await ctx.send(embed=embed)


bot.run('')