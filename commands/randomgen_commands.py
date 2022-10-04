import discord
import random

from message_processing import client


@client.command()
async def random_sentence(ctx, category="lefty_problem"):
    matrix = [[""]]  #get_globals("function specific|random_sentence_matrix").get(category, [[""]])
    sentence = " ".join([random.choice(i) for i in matrix])
    await ctx.send(sentence)
