from datetime import datetime;
from bs4 import BeautifulSoup;
from flask import Flask, json, request;
from dateutil.relativedelta import relativedelta;
from datetime import datetime;
import requests;
import json;
import random;
import time;
import re; #regex
import os;
app = Flask(__name__);

USERNAME = os.environ.get('USERNAME');
PASSWORD = os.environ.get('PASSWORD');
print("Using credentials of "+USERNAME);

courses = {
	"fmf": {
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
	},
	"fri": {
		46: {
			"name": "Osnove digitalnih vezij",
			"abbr": "ODV"
		},
		389: { # used to be 45
			"name": "Programiranje 1",
			"abbr": "P1"
		}
	}
}

urls = {
	"login":  "/login/index.php",
	"course": "/course/view.php?id=", # append course id
	"forum":  "/mod/forum/view.php?id=", # append forum id
	"assign":  "/mod/assign/view.php?id=", # -\\-
	"quiz":  "/mod/quiz/view.php?id=", # -\\-
	"discussion": "/mod/forum/discuss.php?d=", # ?d= is NOT a typo!
	"calendar": "/calendar/view.php?view=month&time=" # append month timstamp
}

def now():
	return int(datetime.timestamp(datetime.now()));
def prev_month():
	return int(datetime.timestamp(datetime.now() - relativedelta(months=1)));
def next_month():
	return int(datetime.timestamp(datetime.now() + relativedelta(months=1)));

def url(location, type, id=""):
	return "https://ucilnica."+location+".uni-lj.si"+urls[type]+str(id);

def find_deadlines(faks, cookie, type, time=""):
	c = requests.get(url(faks, "calendar")+str(time), headers={"Cookie":cookie}).content.decode("utf-8");
	soup = BeautifulSoup(c, 'html.parser');
	anchors = soup.find_all('a', class_="aalink day");
	results = {};
	for a in anchors:
		timestamp = a["data-timestamp"];
		candidates = a.parent.find_all("a", href=True);
		for cand in candidates:
			if url(faks, type) in cand["href"]:
				id = re.search(re.escape(urls[type])+r"(\d+)", cand["href"])[1];
				if not id in results: results[id] = {}
				event_type = cand.find_parent('li')["data-event-eventtype"] # "open" | "close"
				results[id][event_type] = timestamp
	return results;

def find_in_course(course_url, cookie, type):
	c = requests.get(course_url, headers={"Cookie":cookie}).content.decode("utf-8");
	soup = BeautifulSoup(c, 'html.parser');
	anchors = soup.find_all('a', href=True);
	results = [];
	for a in anchors:
		if urls[type] in a["href"]:
			if "#unread" in a["href"]: continue;
			try:
				id = re.search(re.escape(urls[type])+r"(\d+)", a["href"])[1];
				title = a.find(class_="instancename").text;
			except:
				title = id = "error";

			results.append({"title": title, "id": id});
	if len(results) == 0:
		print("No "+type+" found. Invalid credentials or subject has no "+type+"? Course: "+course_url);
	return results;

def find_posts(forum_url, cookie):
	c = requests.get(forum_url, headers={"Cookie":cookie}).content.decode("utf-8");
	soup = BeautifulSoup(c, 'html.parser');
	table = soup.find_all(class_="table discussion-list");
	if len(table) == 0:
		print("Could not find a table at "+forum_url);
		return [];
	entries = table[0].find('tbody').find_all('tr');
	posts = [];
	for entry in entries:
		title = author = timestamp = 0;
		try:
			title = entry.find(class_="topic").find('a').text.strip();
			id = re.search(re.escape(urls["discussion"])+r"(\d+)", entry.find(class_="topic").find('a')["href"])[1];
			author = entry.find(class_="author").find(class_="author-info").find('div').text.strip();
			timestamp = entry.find('time')["data-timestamp"];
		except:
			title = id = author = timestamp = "error";

		posts.append({"title": title, "id": id, "author": author, "last_submission": timestamp});

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
	time = datetime.strptime(t[:-3]+t[-2:], "%Y-%m-%dT%H:%M:%S%z");
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
	print("Got login token: "+token)
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

def assign_deadlines(assignments, deadlines):
	for abbr in assignments:
		for ass in assignments[abbr]: # hehe ass
			if ass["id"] not in deadlines: continue;
			if "timestamps" not in ass: ass["timestamps"] = {};
			ass["timestamps"] |= deadlines[ass["id"]];

def get_course_item(faks, filter_abbr, cookie, type):
	results = {};
	for course_id in courses[faks]:
		abbr = courses[faks][course_id]["abbr"];
		if filter_abbr and abbr != filter_abbr: continue;
		results[abbr] = find_in_course(url(faks,"course",course_id), cookie, type)
	return results;

@app.route('/getDeadlines', methods=['GET'])
def get_deadlines(faks="", cookie="", type="assign", time=""):
	type = request.args.get('type', default=type, type=str);
	faks = request.args.get('location', default=faks, type=str);
	if (faks != "fri" and faks != "fmf"): return '{"error": "Invalid location"}';
	if not cookie: cookie = get_cookie(url(faks, "login"));
	return json.dumps(find_deadlines(faks, cookie, type, time))

def append_deadlines_to_submissions(type, submissions, faks, cookie, fetch_deadlines):
	# get list of submissions (without deadlines)
	if fetch_deadlines:
		# add this month's deadlines
		deadlines = json.loads(get_deadlines(faks, cookie, type, now()));
		assign_deadlines(submissions, deadlines);
		# add next month's deadlines
		deadlines = json.loads(get_deadlines(faks, cookie, type, next_month()));
		assign_deadlines(submissions, deadlines);
		# add last month's deadlines
		deadlines = json.loads(get_deadlines(faks, cookie, type, prev_month()));
		assign_deadlines(submissions, deadlines);
	return submissions;

@app.route('/getQuizzes', methods=['GET'])
def get_quizzes():
	faks = request.args.get('location', default="", type=str);
	filter_abbr = request.args.get('abbr', default="", type=str);
	fetch_deadlines = request.args.get('deadlines', default=False, type=bool);
	if (faks != "fri" and faks != "fmf"): return '{"error": "Invalid location"}';
	cookie = get_cookie(url(faks, "login"));

	quizzes = get_course_item(faks, filter_abbr, cookie, "quiz");
	return json.dumps(append_deadlines_to_submissions("quiz", quizzes, faks, cookie, fetch_deadlines));

@app.route('/getAssignments', methods=['GET'])
def get_assignments():
	faks = request.args.get('location', default="", type=str);
	filter_abbr = request.args.get('abbr', default="", type=str);
	fetch_deadlines = request.args.get('deadlines', default=False, type=bool);
	if (faks != "fri" and faks != "fmf"): return '{"error": "Invalid location"}';
	cookie = get_cookie(url(faks, "login"));

	assignments = get_course_item(faks, filter_abbr, cookie, "assign");
	return json.dumps(append_deadlines_to_submissions("assign", assignments, faks, cookie, fetch_deadlines));

@app.route('/getForumList', methods=['GET'])
def get_forum_list():
	faks = request.args.get('location', default="", type=str);
	filter_abbr = request.args.get('abbr', default="", type=str);
	if (faks != "fri" and faks != "fmf"): return '{"error": "Invalid location"}';
	cookie = get_cookie(url(faks, "login"));

	return json.dumps(get_course_item(faks, filter_abbr, cookie, "forum"))

@app.route('/getForum', methods=['GET'])
def get_forum():
	faks = request.args.get('location', default="", type=str);
	forum_id = request.args.get('forum_id', default=0, type=int);
	if not forum_id:
		return '{"error": "Missing forum id"}';
	if (faks != "fri" and faks != "fmf"): return '{"error": "Invalid location"}';
	cookie = get_cookie(url(faks, "login"));

	return json.dumps(find_posts(url(faks,"forum",forum_id), cookie));

@app.route('/getPostDetails', methods=['GET'])
def get_post_details():
	faks = request.args.get('location', default="", type=str);
	post_id = request.args.get('post_id', default=0, type=int);
	if not post_id:
		return '{"error": "Missing post id"}';
	if (faks != "fri" and faks != "fmf"): return '{"error": "Invalid location"}';
	cookie = get_cookie(url(faks, "login"));

	return json.dumps(find_details(url(faks,"discussion",post_id), cookie));


@app.errorhandler(500)
def err500(e):
	return json.dumps([{"error": "500"}]);

@app.errorhandler(404)
def err404(e):
	return json.dumps([{"error": "404"}]);


if __name__ == '__main__':
	try:
		PORT = int(os.environ.get('PORT', 5000));
	except:
		PORT = 5000;
	print("Using port "+str(PORT));
	app.run(port=PORT);
