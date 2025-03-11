#!/usr/bin/env python3

import sys, os, subprocess, hashlib, argparse


def get_commit_info():
    return subprocess.check_output(["git", "cat-file", "commit", "HEAD"]).decode('utf8')


def get_commit_dates(commit_info):
    lines = commit_info.split("\n")
    author_date = int(lines[1].split(" ")[-2])
    committer_date = int(lines[2].split(" ")[-2])
    return {
        "author_date": author_date,
        "committer_date": committer_date,
    }


def change_commit_info(commit_info, new_values):
    lines = commit_info.split("\n")
    author_date = lines[1].split(" ")
    committer_date = lines[2].split(" ")
    author_date[-2] = str(new_values["author_date"])
    committer_date[-2] = str(new_values["committer_date"])
    lines[1] = " ".join(author_date)
    lines[2] = " ".join(committer_date)
    return "\n".join(lines)


def get_commit_hash(commit):
    commit_str = 'commit %i\x00%s' % (len(commit), commit)
    return hashlib.sha1(commit_str.encode('utf8')).hexdigest()


def validate_hash(commit_hash):
    if args.prefix and commit_hash[0:len(args.prefix)] != args.prefix:
        return False
    return True


def get_text_item(item):
    return str(item[0]).rjust(4) + ") " + str(item[1][0:7])


def print_by_columns(arr):
    terminal_width = os.get_terminal_size().columns
    terminal_height = os.get_terminal_size().lines
    max_columns = max(terminal_width // 16, 1)
    
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
    

def generate_items():
    commit_info = get_commit_info()
    values = get_commit_dates(commit_info)
    values["author_date"] = values["author_date"] + args.start
    
    arr = []
    committer_date = values["author_date"]
    for i in range(1, 1800):
        values["committer_date"] = committer_date + i
        new_commit_info = change_commit_info(commit_info, values)
        new_commit_hash = get_commit_hash(new_commit_info)
        if validate_hash(new_commit_hash):
            arr.append((i, new_commit_hash))
    
    return arr


def print_select_item():
    commit_info = get_commit_info()
    values = get_commit_dates(commit_info)
    values["author_date"] = values["author_date"] + args.start
    values["committer_date"] = values["author_date"] + args.select
    new_commit_info = change_commit_info(commit_info, values)
    new_commit_hash = get_commit_hash(new_commit_info)
    
    print("Hash=%s" % (new_commit_hash[0:7]))
    print("GIT_COMMITTER_DATE='%s' git commit --amend -C HEAD --date='%s'" % \
        (values["committer_date"], values["author_date"]))
    
    if args.apply:
        env = os.environ.copy()
        env["GIT_COMMITTER_DATE"] = str(values["committer_date"])
        command = ["git", "commit", "--amend", "-C", "HEAD", "--date='%s'" % values["author_date"]]
        subprocess.run(command, env=env)

        
# Create parser
parser = argparse.ArgumentParser()
parser.add_argument("--apply", action="store_true", help="Select and apply")
parser.add_argument("--prefix", help="Set start prefix")
parser.add_argument("--select", type=int, help="Select item")
parser.add_argument("--start", type=int, default=0, help="Time offset")

# Parse arguments
args = parser.parse_args()

if args.select is not None:
    print_select_item()

else:
    arr = generate_items()
    print_by_columns(arr)
