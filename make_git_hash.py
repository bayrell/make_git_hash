#!/usr/bin/env python3

import sys, os, subprocess, hashlib, argparse


def get_commit_info():
    return subprocess.check_output(["git", "cat-file", "commit", "HEAD"]).decode('utf8')


def get_commit_dates(commit_info):
    lines = commit_info.split("\n")
    author_date = ""
    committer_date = ""
    
    for line in lines:
        arr = line.split(" ")
        if len(arr) > 0:
            if arr[0] == "author":
                author_date = int(arr[-2])
            if arr[0] == "committer":
                committer_date = int(arr[-2])
    
    return {
        "author_date": author_date,
        "committer_date": committer_date,
    }


def change_commit_info(commit_info, new_values):
    lines = commit_info.split("\n")
    for i, line in enumerate(lines):
        arr = line.split(" ")
        if len(arr) > 0:
            if arr[0] == "author":
                arr[-2] = str(new_values["author_date"])
            if arr[0] == "committer":
                arr[-2] = str(new_values["committer_date"])
            lines[i] = " ".join(arr)
    return "\n".join(lines)


def get_commit_hash(commit):
    commit_str = 'commit %i\x00%s' % (len(commit), commit)
    return hashlib.sha1(commit_str.encode('utf8')).hexdigest()


def get_commit_short_hash(commit_hash):
    return commit_hash[0:7]


def validate_hash(commit_hash):
    result = True;
    if args.prefix and commit_hash[0:len(args.prefix)] != args.prefix:
        result = False
    if args.number:
        if not get_commit_short_hash(commit_hash).isdigit():
            return False
    return result


def get_text_item(item):
    return get_commit_short_hash(item[1])


def print_by_columns(arr):
    terminal_width = os.get_terminal_size().columns
    terminal_height = os.get_terminal_size().lines
    max_columns = max(terminal_width // 10, 1)
    
    arr = sorted(arr, key=lambda x: x[1])
    
    lines = []
    for i in range(0, len(arr), max_columns):
        items = arr[i:i + max_columns]
        items = [get_text_item(item) for item in items]
        lines.append("   ".join(items))
    
    if len(lines) > terminal_height - 5:
        subprocess.run(["less"], input="\n".join(lines), text=True)
    else:
        for line in lines:
            print(line)


def set_date(values, author_date, committer_date=-1):
    if committer_date == -1:
        committer_date = author_date
    
    values["author_date"] = author_date
    values["committer_date"] = committer_date


def generate_items(commit_info, start=0, end=1800):
    values = get_commit_dates(commit_info)
    
    arr = []
    committer_date = values["author_date"] + args.start
    for i in range(start, end):
        set_date(values, committer_date + i)
        new_commit_info = change_commit_info(commit_info, values)
        new_commit_hash = get_commit_hash(new_commit_info)
        if validate_hash(new_commit_hash):
            arr.append((i, new_commit_hash))
    
    return arr


def print_select_item():
    commit_info = get_commit_info()
    arr = generate_items(commit_info, -3600, 3600)
    
    index = -1
    for i, item in enumerate(arr):
        if get_commit_short_hash(item[1]) == args.select:
            index = item[0]
            break
    
    if index == -1:
        print("Wrong prefix")
        return
    
    values = get_commit_dates(commit_info)
    set_date(values, values["author_date"] + args.start + index)
    new_commit_info = change_commit_info(commit_info, values)
    new_commit_hash = get_commit_hash(new_commit_info)
    
    if not args.apply:
        print("Hash=%s" % (get_commit_short_hash(new_commit_hash)))
        print("GIT_COMMITTER_DATE='%s' git commit --amend -C HEAD --date='%s'" % \
            (values["committer_date"], values["author_date"]))
    else:
        env = os.environ.copy()
        env["GIT_COMMITTER_DATE"] = str(values["committer_date"])
        command = ["git", "commit", "--amend", "-C", "HEAD", "--date='%s'" % values["author_date"]]
        subprocess.run(command, env=env)

        
# Create parser
parser = argparse.ArgumentParser()
parser.add_argument("--apply", action="store_true", help="Select and apply")
parser.add_argument("--number", action="store_true", help="Show only numbers")
parser.add_argument("--prefix", help="Set start prefix")
parser.add_argument("--select", type=str, help="Select item")
parser.add_argument("--start", type=int, default=0, help="Time offset")

# Parse arguments
args = parser.parse_args()

if args.select is not None:
    print_select_item()

else:
    arr = generate_items(get_commit_info())
    print_by_columns(arr)
