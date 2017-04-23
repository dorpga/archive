#! /usr/bin/python3

# Imports
import http.client
from html.parser import HTMLParser
from html.entities import name2codepoint
from bs4 import BeautifulSoup
from jinja2 import Template, Environment
import re
import traceback
import os
import codecs

# Variables
_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')

# Directory document
if os.path.exists("posts/index.md"):
	os.remove("posts/index.md")
directory = open("posts/index.md", "w+")
directory.write("(..)[Go Back]\n# Fourm Directory")

# Templates
posts_template = """
<!DOCTYPE html>
<html lang="en" dir="ltr">
	<head>
		<meta charset="UTF-8">
		<title>{{fourm_title}} - The Archive</title>
		<link rel="stylesheet" href="/assets/fourms/css/style.css" type="text/css" />
	</head>
	<body>
	<header>
	<h1 class="back-button">
		<a href=".">«</a>
	</h1>
	<h1 class="page-title">{{fourm_title}}</h1>
	</header>

	<main>
	{% for author, subject, body, timestamp in zip(authors, subjects, bodies, timestamps) %}
	<article id="{{subject['href']}}">
		<header>
			<h2 class="post-subject">{{subject.contents[0]}}</h3>
			<h3 class="post-author">Posted by <a href="user-{{slugify(author.contents[0])}}">{{author.contents[0]}}</a></h3>
		</header>

		<div class="post-body">
			{{body.parent}}
		</div>

		<footer>
			<time>{{timestamp}}</time>
		</footer>
	</article>
	{% endfor %}
	</main>

	<footer>
	<p>This fourm was generated</p>
	</footer>
	</body>
</html>
"""
# Functions

# Slugify
def slugify(text, delim=u'-'):
    """Generates an ASCII-only slug."""
    result = []
    for word in _punct_re.split(text.lower()):
        if word:
            result.append(word)
    return delim.join(result)

# Render Thread
def render_thread(authors, subjects, bodies, timestamps):
	return env.from_string(posts_template).render(authors=authors, subjects=subjects, bodies=bodies, timestamps=timestamps)

# Settings
MIN_POST = 7;  # First Post
MAX_POST = 16411;  # Last Post
HOST = "archive.raytron.org"  # Host
BASE_URL = "/shiftos/viewtopic.php"  # View Topic page
TOPIC_ARG = 't'  # Topic Argument
FOURM_TITLE = "ShiftOS"  # Title of Fourm

# Jinja2 setup
env = Environment()

env.globals={
	"fourm_title": FOURM_TITLE,
	"zip": zip,
	"slugify": slugify,
	"codecs": codecs
}

# Connect to server
print ("[INFO] Connecting to {}".format(HOST))
conn = http.client.HTTPSConnection(HOST)
print ("[INFO] Connected!")

# Download posts
for t in range(MIN_POST, MAX_POST):
	# Download page
	url = "{}?{}={}".format(BASE_URL, TOPIC_ARG, t)
	print ("[INFO] Trying to get {}.".format(url))
	conn.request("GET", url)
	res = conn.getresponse()

	# Check status
	if res.status == 200:
		print ("[OK] Topic #{} found".format(t))

		# Read data
		data = res.read()

		# Get HTML
		print ("[INFO] Trying to parse HTML")
		
		try:
			# Load HTML into object
			doc = BeautifulSoup(str(data), 'html.parser')

			docPosts = doc.findAll("table", class_="tablebg")[1]

			# Get authors
			dAuthors = docPosts.findAll(class_="postauthor")

			# Get header elements
			dSubjects = []
			dTimestamps = []
			for i in docPosts.findAll(class_="gensmall"):

				# Get subjects
				for j in i.findAll(style="float:left;"):
					dSubjects.append(j.find("a"))
			
				# Get timestamps
				if len(i.findAll(style="float:right;")) > 0:
					dTimestamps.append(i.findAll(style="float:right;")[0].contents[4])

			# Get bodies
			dBodies = docPosts.findAll(class_="postbody")

			#print ("Authors: {}\nSubjects: {}\nBodies: {}\nTimestamps: {}".format(len(dAuthors), len(dSubjects), len(dBodies), len(dTimestamps)))

			# Render thread			
			r = render_thread(dAuthors, dSubjects, dBodies, dTimestamps)

			# Save thread
			open ("posts/post-{}.html".format(t), 'w').write(r)

			# Generate listing
			directory.write("{}. [{}](post-{})\n".format(t, dSubjects[0].contents[0], t))
			print("[OK] Thread done")
		except Exception as ex:
			print("[ERROR] Error while parsing thread #{}: {}".format(t, ex))
	else:
		print ("[ERROR] Request for post #{} returned a {} error".format(t, res.status))

	
	# Close the connection
	conn.close()
