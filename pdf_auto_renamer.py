#!/usr/bin/env python3
from pprint import pprint
import random
import dotenv
dotenv.load_dotenv()

import better_exceptions; better_exceptions.hook()
from ratelimiter import RateLimiter
import google.generativeai as genai
import os
from pypdf import PdfReader
import click



genai.configure(api_key=os.getenv("API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash-latest')
# model = genai.GenerativeModel('gemini-1.0-pro-latest')

@RateLimiter(max_calls=14, period=60)
def gen_content(c): return model.generate_content(c)

@click.command()
@click.argument('file')
@click.option('--folder_for_context', default=None, help='Folder for additional context')
def main(file, folder_for_context):
    reader = PdfReader(file)
    pdf_text = '\n\n'.join(p.extract_text() for p in reader.pages)
    if folder_for_context: 
        files = os.listdir(folder_for_context)
        if len(files) > 50:
            files = random.sample(files, 50)
        folder_examples = '\n'.join(files)
    response = gen_content(
        f'Here are examples of pdf names in the current directory: \n```\n{folder_examples}\n```\n' if folder_for_context else '' + 
        f'Given the following content in a pdf, suggest a name for the file. Please include pdf extension in your suggestion.'
        f'```\n{pdf_text}\n```'
    )
    breakpoint()