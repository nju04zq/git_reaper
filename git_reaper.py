#!/usr/bin/env python

import os
import sys
import shutil
import hashlib
import tarfile
import datetime
import subprocess
from subprocess import Popen, PIPE

def run_cmd(cmd):
    print cmd
    p = Popen(cmd.split(), stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    print out, err

def get_git_dirs():
    dir_list = ["."]
    git_list = []
    while len(dir_list):
        dir_path = dir_list.pop()
        if os.path.islink(dir_path):
            continue
        elif os.path.basename(dir_path) == ".git":
            git_list.append(dir_path)
            continue
        dir_entries = os.listdir(dir_path)
        for entry in dir_entries:
            entry_path = os.path.join(dir_path, entry)
            if os.path.isdir(entry_path):
                dir_list.append(entry_path)
    print "Git dir list:"
    for git_dir in git_list:
        print git_dir
    return git_list

def get_now_ts():
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S")

def move_out_git(git_list):
    temp_dirname = "git_collect_" + get_now_ts()
    os.mkdir(temp_dirname)
    print "Move out git dir to {0}".format(temp_dirname)
    for git_dir in git_list:
        dst_path = os.path.join(temp_dirname, git_dir)
        dst_parent_path = os.path.dirname(dst_path)
        if not os.path.exists(dst_parent_path):
            print "mkdir -p {0}".format(dst_parent_path)
            os.makedirs(dst_parent_path)
        print "mv {0} {1}".format(git_dir, dst_path)
        os.rename(git_dir, dst_path)
    return temp_dirname

def collect_into_tar(git_pool):
    tar_fname = git_pool + ".tar"
    tar = tarfile.open(tar_fname, "w")
    tar.add(git_pool)
    tar.close()
    print "Generate tar file {0}".format(tar_fname)
    return tar_fname

def generate_passwd():
    m = hashlib.md5()
    m.update(datetime.datetime.now().strftime("%Y%m%d%H%M%S%f"))
    return m.hexdigest()

def encrypt_tar(git_tar):
    zip_fname = os.path.splitext(git_tar)[0] + ".zip"
    passwd = generate_passwd()
    cmd = "zip -P {0} {1} {2}".format(passwd, zip_fname, git_tar)
    run_cmd(cmd)
    print "Encrypt tar file to {0}\npasswd {1}".format(zip_fname, passwd)
    return zip_fname

def git_collect():
    git_list = get_git_dirs()
    git_pool = move_out_git(git_list)
    git_tar = collect_into_tar(git_pool)
    git_zip = encrypt_tar(git_tar)
    shutil.rmtree(git_pool)
    os.remove(git_tar)

def read_passwd():
    ticket_fname = "git_ticket"
    cmd = "vim " + ticket_fname
    subprocess.call(["vim", ticket_fname])
    with open(ticket_fname, "r") as fp:
        passwd = fp.read().rstrip()
    os.remove(ticket_fname)
    return passwd

def decrypt_zip(zip_fname, passwd):
    cmd = "unzip -P {0} {1}".format(passwd, zip_fname)
    run_cmd(cmd)
    tar_fname = os.path.splitext(zip_fname)[0] + ".tar"
    return tar_fname

def untar_file(git_tar):
    tar = tarfile.open(git_tar, "r")
    tar.extractall()
    tar.close()
    git_pool = os.path.splitext(git_tar)[0]
    return git_pool

def apply_git_pool(git_pool):
    old_cwd = os.getcwd()
    os.chdir(git_pool)
    git_list = get_git_dirs()
    for git_dir in git_list:
        dst_path = os.path.join("..", git_dir)
        dst_parent_dir = os.path.dirname(dst_path)
        if not os.path.exists(dst_parent_dir):
            os.makedirs(dst_parent_dir)
        print "mv {0} {1}".format(git_dir, dst_path)
        os.rename(git_dir, dst_path)
    os.chdir(old_cwd)

def git_apply(zip_fname):
    passwd = read_passwd()
    git_tar = decrypt_zip(zip_fname, passwd)
    git_pool = untar_file(git_tar)
    apply_git_pool(git_pool)
    shutil.rmtree(git_pool)
    os.remove(git_tar)

if len(sys.argv) == 1:
    print "Arguments expected"
    sys.exit(1)
elif sys.argv[1] == "collect":
    git_collect()
elif sys.argv[1] == "apply":
    git_apply(sys.argv[2])
