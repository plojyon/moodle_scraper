from datetime import datetime;
from bs4 import BeautifulSoup;
from flask import Flask, json, request
import datetime;
import requests;
import json;
import random;
import time;
import re; #regex
import os;

app = Flask(__name__);

USERNAME = os.getenv("USERNAME");
PASSWORD = os.getenv("PASSWORD");

fmf = {
	"URL": {
		"login":  "https://ucilnica.fmf.uni-lj.si/login/index.php",
		"course": "https://ucilnica.fmf.uni-lj.si/course/view.php?id=", # append course id
		"forum":  "https://ucilnica.fmf.uni-lj.si/mod/forum/view.php?id=", # append forum id
		"discussion": "https://ucilnica.fmf.uni-lj.si/mod/forum/discuss.php?d=" # append discussion id
	},
	"courses": {
		75: {
			"name": "Analiza 1",
			"abbr": "A1"
		},
		77: {
			"name": "Diskretne strukture 1",
			"abbr": "DS1"
		},
		79: {
			"name": "Linearna algebra",
			"abbr": "LINALG"
		}
	}
}

fri = {
	"URL": {
		"login":  "https://ucilnica.fri.uni-lj.si/login/index.php",
		"course": "https://ucilnica.fri.uni-lj.si/course/view.php?id=", # append course id
		"forum":  "https://ucilnica.fri.uni-lj.si/mod/forum/view.php?id=", # append forum id
		"discussion": "https://ucilnica.fri.uni-lj.si/mod/forum/discuss.php?d=" # append discussion id
	},
 	"courses": {
		46: {
			"name": "Osnove digitalnih vezij",
			"abbr": "ODV"
		},
		45: {
			"name": "Programiranje 1",
			"abbr": "P1"
		}
	}
}

def find_forums(course_url, cookie):
	c = requests.get(course_url, headers={"Cookie":cookie}).content.decode("utf-8");
	soup = BeautifulSoup(c, 'html.parser');
	anchors = soup.find_all('a', href=True);
	forums = [];
	for a in anchors:
		if "/mod/forum/view.php?id=" in a["href"]:
			if "#unread" in a["href"]: continue;
			try:
				id = re.search(r"/mod/forum/view.php\?id=(\d+)", a["href"])[1];
				title = a.find(class_="instancename").text;
			except:
				title = id = "error";

			forums.append({"title": title, "id": id});
	if len(forums) == 0:
		print("No forums found. Invalid credentials or subject has no forums? Course: "+course_url);
	return forums;

def find_posts(forum_url, cookie):
	c = requests.get(forum_url, headers={"Cookie":cookie}).content.decode("utf-8");
	soup = BeautifulSoup(c, 'html.parser');
	table = soup.find_all(class_="table discussion-list");
	if len(table) == 0:
		print("Could not find a table at "+course_url);
		return [];
	entries = table[0].find('tbody').find_all('tr');
	posts = [];
	for entry in entries:
		title = author = timestamp = 0;
		try:
			title = entry.find(class_="topic").find('a').text.strip();
			id = re.search(r"/mod/forum/discuss\.php\?d=(\d+)", entry.find(class_="topic").find('a')["href"])[1];
			author = entry.find(class_="author").find(class_="author-info").find('div').text.strip();
			timestamp = entry.find('time')["data-timestamp"];
		except:
			title = id = author = timestamp = "error";

		posts.append({"title": title, "id": id, "author": author, "timestamp": timestamp});

	if (len(posts) == 0):
		print("No results. Invalid credentials or forum has no posts? Forum: "+forum_url);

	return posts;

def find_details(post_url, cookie):
	c = requests.get(post_url, headers={"Cookie":cookie}).content.decode("utf-8");
	soup = BeautifulSoup(c, 'html.parser');
	'''
	page structure:

	article - main post
		div - main post body
		div.indent - replies
			article - reply 1
				div - reply body
				div.indent - replies
					...
			article - reply 2
				div - reply body
				div.indent - replies
					article - reply 2.1
						div - reply body
						...
					...
			...
	'''
	main = soup.find("article", class_="forum-post-container");
	discussion = find_replies(main);
	return discussion;

def find_replies(article):
	title = article.find("div").find("header").find("h3").text;

	author = article.find("div").find("header").find("a").text;

	t = article.find("div").find("header").find("time")["datetime"];
	time = datetime.datetime.strptime(t[:-3]+t[-2:], "%Y-%m-%dT%H:%M:%S%z");
	timestamp = int(time.timestamp());

	post_container = article.find("div").find(class_="post-content-container");
	paragraph_array = post_container.find_all("p");
	content = "";
	for p in paragraph_array:
		content += p.text+"\n";
	if (content == ""):
		d = post_container.find(class_="text_to_html");
		content += d.text.replace("<br>", "\n");

	replies = [];
	try:
		reply_articles = article.find(class_="indent").find_all("article");
		for r in reply_articles:
			replies.append(find_replies(r));
	except:
		pass;

	return {"title": title, "author": author, "content": content, "timestamp": timestamp, "replies": replies};



def get_cookie(login_url):
	global USERNAME;
	global PASSWORD;
	session = requests.Session();
	resp = session.get(login_url).content.decode("utf-8");
	token = re.search(r'name="logintoken" value="(\w+)"', resp)[1];
	login_data = {
		"username":USERNAME,
		"password":PASSWORD,
		"anchor": "",
		"logintoken": token
	};
	session.post(login_url, data=login_data);
	if (len(session.cookies.keys()) == 0):
		print("Received 0 cookies. Is the server offline?");
		exit();
	cookie = "MoodleSession="+session.cookies.get("MoodleSession");
	print("Got login cookie: "+cookie);
	return cookie;

@app.route('/getForums', methods=['GET'])
def get_forums():
	location = request.args.get('location', default="", type=str);
	filter_abbr = request.args.get('abbr', default="", type=str);
	if location == "fmf":
		faks = fmf;
	elif location == "fri":
		faks = fri;
	else:
		return '{"error": "Invalid location"}';

	forums = {};
	faks["cookie"] = get_cookie(faks["URL"]["login"]);
	for course_id in faks["courses"]:
		abbr = faks["courses"][course_id]["abbr"];
		if filter_abbr and abbr != filter_abbr: continue;
		forums[abbr] = find_forums(faks["URL"]["course"]+str(course_id), faks["cookie"]);
	return forums;

@app.route('/getPosts', methods=['GET'])
def get_posts():
	location = request.args.get('location', default="", type=str);
	forum_id = request.args.get('forum_id', default=0, type=int);
	if not forum_id:
		return '{"error": "Missing forum id"}';

	if location == "fmf":
		faks = fmf;
	elif location == "fri":
		faks = fri;
	else:
		return '{"error": "Invalid location"}';

	faks["cookie"] = get_cookie(faks["URL"]["login"]);
	posts = find_posts(faks["URL"]["forum"]+str(forum_id), faks["cookie"]);
	return posts;

@app.route('/getPostDetails', methods=['GET'])
def get_post_details():
	location = request.args.get('location', default="", type=str);
	post_id = request.args.get('post_id', default=0, type=int);
	if not post_id:
		return '{"error": "Missing post id"}';

	if location == "fmf":
		faks = fmf;
	elif location == "fri":
		faks = fri;
	else:
		return '{"error": "Invalid location"}';

	faks["cookie"] = get_cookie(faks["URL"]["login"]);
	details = find_details(faks["URL"]["discussion"]+str(post_id), faks["cookie"]);
	return details;


@app.errorhandler(500)
def err500(e):
	if (not production):
		return json.dumps([{"error": "500", "e": e}]);
	else:
		return json.dumps([{"error": "500"}]);

@app.errorhandler(404)
def err404(e):
	if (not production):
		return json.dumps([{"error": "404", "e": e}]);
	else:
		return json.dumps([{"error": "404"}]);


production = os.getenv("DEBUG") == '0';
if not production:
	print("Running in debug mode. Do not deploy in this state.");

if __name__ == '__main__':
	try:
		PORT = int(os.getenv("PORT"));
	except:
		PORT = 5000;
	if not PORT: PORT = 5000;
	print("Using port "+str(PORT));
	app.run(port=PORT);
