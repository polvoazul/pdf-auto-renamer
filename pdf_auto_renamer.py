#!/usr/bin/env python3
import json
from pprint import pprint
import random
import re
import dotenv
import requests
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
@click.option('--folder-for-context', default=None, help='Folder for additional context')
@click.option('--extra-instructions', default='', help='Extra instructions')
def main(file, folder_for_context, extra_instructions):
    if not os.path.exists(file):
        raise FileNotFoundError(f"File {file} does not exist.")
    reader = PdfReader(file)
    base_dir, filename = os.path.split(os.path.abspath(file))
    pdf_text = '\n\n'.join(p.extract_text() for p in reader.pages)
    if folder_for_context: 
        files = os.listdir(folder_for_context)
        if len(files) > 50:
            files = random.sample(files, 50)
        folder_examples = '\n'.join(files)
    print('Sending to model...')
    query = (
        f"I'm organizing files in a directory. I'm renaming a pdf file `{filename}`. Suggest a new name for the file based on its content. Please include pdf extension in your suggestion.\n" +
        (f'Here are some examples of file names in the current directory: \n```\n{folder_examples}\n```\n' if folder_for_context else '') + 
        extra_instructions + '\n' +
        f'Here is the file contents, use it as context to create the file name: \n```\n{pdf_text}\n```'  + 
        'In the end of your response, emit a json {"new_name": ...}'
    )
    chat = model.start_chat()
    response = chat.send_message(query)
    try:
        match = re.search(r'```json.*?(\{.*\}).*?```', response.text, flags=re.MULTILINE | re.DOTALL)
        new_name = json.loads(match.group(1).strip())['new_name']
        print(f'Renaming to {new_name!r}')
        os.rename(file, os.path.join(base_dir, new_name))
    except Exception as e:
        print(e)
        breakpoint()
        raise

def local_llm(response):
    url = "http://localhost:1234/v1/completions"
    data = {"prompt": response}
    return requests.post(url, json=data).json()


main()