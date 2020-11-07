"""Comparison of fetching web pages sequentially vs. asynchronously

Requirements: Python 3.5+, Requests, aiohttp, cchardet

For a walkthrough see this blog post:
http://mahugh.com/2017/05/23/http-requests-asyncio-aiohttp-vs-requests/
"""
import asyncio
from timeit import default_timer
from termcolor import colored

from aiohttp import ClientSession
import requests

def demo_sequential(urls):
    """Fetch list of web pages sequentially."""
    start_time = default_timer()
    for url in urls:
        start_time_url = default_timer()
        _ = requests.get(url)
        elapsed = default_timer() - start_time_url
        print('{0:30}{1:5.2f} {2}'.format(url, elapsed, asterisks(elapsed)))
    tot_elapsed = default_timer() - start_time
    print(colored(' TOTAL SECONDS: '.rjust(30, '-') + '{0:5.2f} {1}'. \
        format(tot_elapsed, asterisks(tot_elapsed)) + '\n','yellow'))

def demo_async(urls):
    """Fetch list of web pages asynchronously."""
    start_time = default_timer()

    loop = asyncio.get_event_loop() # event loop
    future = asyncio.ensure_future(fetch_all(urls)) # tasks to do
    loop.run_until_complete(future) # loop until done

    tot_elapsed = default_timer() - start_time
    print(colored(' WITH ASYNCIO: '.rjust(30, '-') + '{0:5.2f} {1}'. \
        format(tot_elapsed, asterisks(tot_elapsed)),'green'))

async def fetch_all(urls):
    """Launch requests for all web pages."""
    tasks = []
    fetch.start_time = dict() # dictionary of start times for each url
    async with ClientSession() as session:
        for url in urls:
            task = asyncio.ensure_future(fetch(url, session))
            tasks.append(task) # create list of tasks
        _ = await asyncio.gather(*tasks) # gather task responses

async def fetch(url, session):
    """Fetch a url, using specified ClientSession."""
    fetch.start_time[url] = default_timer()
    async with session.get(url) as response:
        resp = await response.read()
        elapsed = default_timer() - fetch.start_time[url]
        print('{0:30}{1:5.2f} {2}'.format(url, elapsed, asterisks(elapsed)))
        return resp

def asterisks(num):
    """Returns a string of asterisks reflecting the magnitude of a number."""
    return int(num*10)*'*'

if __name__ == '__main__':
    URL_LIST = ['https://facebook.com',
                'https://github.com',
                ]
    demo_sequential(URL_LIST)
    demo_async(URL_LIST)