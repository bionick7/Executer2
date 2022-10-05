import discord
import random

from message_processing import client
from implementation.randomgen_impl import name_generator

"""
#@client.command()
async def random_sentence(ctx, category="lefty_problem"):
    matrix = [[""]]  #get_globals("function specific|random_sentence_matrix").get(category, [[""]])
    sentence = " ".join([random.choice(i) for i in matrix])
    await ctx.send(sentence)
"""


@client.command(name="Rword", help="Generates Random (non-exisiting) word. If syllable count is left blank, uses "
                                   "random amount of syllables")
async def random_word(ctx, syllable_count: int = -1):
    await ctx.send(name_generator.gen_word(syllable_count))


@client.command(name="Rname", help="Generates Random person's name")
async def random_name(ctx):
    await ctx.send(name_generator.gen_person_name())


@client.command(name="Rshipname", help="Generates Random ship name")
async def random_name(ctx):
    await ctx.send(name_generator.gen_ship_name())


@client.command(name="Rtemplate", help="Generates a random word according to a template")
async def random_name(ctx, template: str):
    await ctx.send(name_generator.gen_name_from_template(template))
