import os
import sys
import time

commitInfo=input("Input commit info:")
os.chdir("F:/NoteBook/Java八股文")

if commitInfo=="":
    commitInfo="\"defalut commit on "+time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()) +"\""

print("git add .")
print(os.popen("git add .").read())

print("git commit -m "+str(commitInfo))
print(os.popen("git commit -m "+str(commitInfo)).read())

print("git pull origin master")
print(os.popen("git pull origin master").read())

print("git push origin master")
print(os.popen("git push origin master").read())

input("执行完毕，按回车结束...")
