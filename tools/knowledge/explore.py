'''
format: python explore.py my_topic interval(float > 1/24)(how many days)
example : python explore.py WinterOlympics 1
'''

import os
import sys
import json
import time

import schedule
import argparse
import numpy as np

file_dir = os.path.dirname(os.path.abspath(__file__))
module_dir = os.path.dirname(file_dir)
BASE_DIR = os.path.dirname(module_dir)
sys.path.append(BASE_DIR)
sys.path.append("../..")

from main import KGPipeline

def read_data(filename):
    filepath = os.path.join(file_dir,filename)
    with open(filepath) as f:
        res = json.load(f)
    return res



def main():
    parser = argparse.ArgumentParser(description='Concept expansion with snippet')
    parser.add_argument('-t','--task', type=str, choices=['init', 'update'], required=True)
    parser.add_argument('-f',"--config_file", type=str, default="data/seed_concept.json",help='the json file with topic and its initial seeds')
    parser.add_argument('-i','--interval', type=float, default=1, help='update per #days')
    args = parser.parse_args()
    filename = args.config_file
    interval = args.interval
    task = args.task

    if task == "init":
        run_init(filename)
    elif task =="update":
        data = read_data(filename)
        topic = data.get("topic")
        run_explore(topic)
        schedule.every(interval).hour.do(run_explore, topic)
        while True:
            schedule.run_pending()
            time.sleep(1)


def run_init(filename):
    data = read_data(filename=filename)
    topic = data.get("topic")
    seeds = data.get("seeds")
    print(f"Start init topic:'{topic}'")
    pipe = KGPipeline(topic=topic)
    pipe.init_seed_concepts(concepts=seeds)
    print(f"Topic:'{topic}' initiated with seed concepts:{seeds}")

def run_explore(my_topic):
    print("Start pipeline...")
    pipe = KGPipeline(topic=my_topic)
    exp_res = pipe.run_expand()
    ext_res = pipe.run_extract()

if __name__ == "__main__":
    main()
