import time
import pytz
from datetime import datetime
import hashlib
import re

def get_time(stamp=None, form="%Y-%m-%d %H:%M:%S"):
    if not stamp:
        stamp = time.time()
    tz = pytz.timezone("Asia/Shanghai")
    now = datetime.fromtimestamp(stamp, tz)
    strt = now.strftime(form)
    return strt, stamp

def set_now_time(obj, is_end=False):
    t, stamp = get_time()
    if not is_end:
        obj.created_t = stamp
        obj.created_time = t
    else:
        obj.closed_t = stamp
        obj.closed_time = t
        
def hashidx(org_id):
    data_hash = hashlib.new("md5", org_id.encode("utf8"))
    return data_hash.hexdigest()


def remove_replicate_secs(text):
    lis = text.split(",")
    res = []
    for i in lis:
        if i in res or not i:
            continue
        else:
            res.append(i)
    return ",".join(res)


def filter_glm(text, prefix ="(BOT:|USER:)",split="|"):
    if split == "|":
        regex_pattern = f"\<\|startofpiece\|\>([^\|]*)\{split}"
        reg = re.compile(regex_pattern)
    t = re.findall(reg, text)
    if not t:
        t = re.findall(f"<\|startofpiece\|>(.+)", text)

    res = "" if not t else t[0]
    res = res.strip()
    prefix = prefix
    reg = re.compile(prefix)
    t = re.split(reg, res)
    for i in t:
        if i and i not in prefix:
            res = i
            break
    else:
        pass

    res = res.strip()
    return res



if __name__ == "__main__":
    pass